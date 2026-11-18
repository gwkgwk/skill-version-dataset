---
name: matching-engine
description: Core matching algorithm using pgvector semantic similarity. Finds "I have, they need" and "I need, they have" connections between users.
---

## Matching goal

Connect users in two independent directions:

1. **"I have, they need"** (forward): My HAVE resource is semantically similar to someone's WANT
2. **"I need, they have"** (reverse): Someone's HAVE resource is semantically similar to my WANT

Each direction is scored and displayed independently. There is no combined "bidirectional" score — the two directions are separate sections on the matches page.

## Threshold configuration

All scoring thresholds live in **`src/lib/constants.ts`** under `MATCH_THRESHOLDS`. Never hardcode threshold values elsewhere — always import from constants.

```typescript
import { MATCH_THRESHOLDS } from '@/lib/constants';
// MATCH_THRESHOLDS.MIN_SCORE     — minimum to store a match
// MATCH_THRESHOLDS.STRONG        — "strong match" badge
// MATCH_THRESHOLDS.GOOD          — "good match" badge
// MATCH_THRESHOLDS.MAX_PER_USER  — max matches stored per user
// MATCH_THRESHOLDS.CANDIDATE_POOL — nearest-neighbor candidates per query
```

These values depend on the embedding model's score distribution. When switching embedding models, recalibrate by:
1. Running `scripts/recalculate-all-matches.ts`
2. Checking the actual score distribution with SQL
3. Adjusting thresholds in `constants.ts` so badge tiers produce meaningful separation

## How matching works

### Step 1: Generate embeddings on resource creation

See `src/server/services/embedding.ts`. The embedding provider is configurable (Gemini, OpenAI, mock).

### Step 2: Find matches with pgvector

`src/server/services/matching.ts` uses cosine similarity (`1 - (a <=> b)`) to find nearest-neighbor resources across users.

### Step 3: Per-direction scoring

For each candidate user, we track the best forward score and best reverse score independently. A match is stored if either direction exceeds `MATCH_THRESHOLDS.MIN_SCORE`.

### Step 4: Dual-row insert

Each match inserts TWO rows in a single transaction:
- **Primary row** (A → B): A's perspective
- **Mirror row** (B → A): Scores and resource IDs swapped, so B immediately sees the match

Mirror rows use `ON CONFLICT DO UPDATE` to handle the case where B already has a row for that pair.

## Match table: four resource references

The Prisma schema stores both directions per row:

- `forwardHave` / `forwardWant` — my HAVE matched their WANT
- `reverseHave` / `reverseWant` — their HAVE matched my WANT

A row may have only forward, only reverse, or both populated.

## API: querying matches by direction

`src/server/routers/match.ts` — the `myMatches` endpoint accepts a `direction` param:

- `direction: 'forward'` → filter by `forwardScore >= minScore`
- `direction: 'reverse'` → filter by `reverseScore >= minScore`
- `direction: undefined` → filter by `score >= minScore`

## UI: two-section matches page

`/matches` displays two stacked sections (not tabs):

- **"I have, they need"** — forward matches. Card shows: who needs + resource title
- **"I need, they have"** — reverse matches. Card shows: who has + resource title

Score badge is displayed on its own row below the resource title.

## When matching runs

1. **On resource create/update** — recalculate for the triggering user
2. **On resource close/pause** — recalculate (closed resources excluded)
3. **Vercel Cron (every 4 hours)** — reconcile stale users + clean up matches referencing non-ACTIVE resources
4. **Never on page load** — always serve from cached Match table

## Performance notes

- pgvector with IVFFlat index: good enough for 100k resources
- Create index: `CREATE INDEX ON resources USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);`
- Cron processes at most 20 users per invocation (60s timeout)

## What NOT to do

- Don't hardcode threshold values — always use `MATCH_THRESHOLDS` from constants
- Don't treat forward and reverse as a single combined score
- Don't require both directions for a match to be valid
- Don't run matching on every page load — serve from cached Match table
- Don't try chain matching yet — that's v2
