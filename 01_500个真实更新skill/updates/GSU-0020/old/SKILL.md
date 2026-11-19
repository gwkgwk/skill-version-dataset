---
name: matching-engine
description: Core matching algorithm using pgvector semantic similarity for bidirectional resource matching. This is the most critical business logic in YHIN.
---

## Matching philosophy

The hardest problem in a barter platform is the "double coincidence of wants":
A must have what B needs AND B must have what A needs.

Our approach: **bidirectional semantic similarity**.

## How matching works

### Step 1: Generate embeddings on resource creation

When a user creates a Resource (HAVE or WANT), generate a text embedding:

```typescript
// server/services/embedding.ts
import OpenAI from 'openai';

const openai = new OpenAI();

export async function generateEmbedding(text: string): Promise<number[]> {
  const response = await openai.embeddings.create({
    model: 'text-embedding-3-small',
    input: text,
    dimensions: 1536,
  });
  return response.data[0].embedding;
}

export function buildEmbeddingText(resource: {
  title: string;
  description: string;
  tags: string[];
  category?: string;
}): string {
  // Combine all semantic signals into one string
  return [
    resource.title,
    resource.description,
    resource.tags.join(', '),
    resource.category ?? '',
  ].filter(Boolean).join(' | ');
}
```

### Step 2: Find matches with pgvector

```sql
-- Find top matches for user A's HAVE resource
-- by comparing against all other users' WANT resources
SELECT
  w.id AS want_id,
  w.user_id AS seeker_id,
  1 - (h.embedding <=> w.embedding) AS forward_score
FROM resources h
CROSS JOIN LATERAL (
  SELECT id, user_id, embedding
  FROM resources
  WHERE type = 'WANT'
    AND user_id != h.user_id
    AND status = 'ACTIVE'
  ORDER BY embedding <=> h.embedding
  LIMIT 50
) w
WHERE h.id = $1 AND h.type = 'HAVE';
```

### Step 3: Bidirectional scoring

```typescript
// server/services/matching.ts
export async function findMatches(userId: string): Promise<Match[]> {
  // 1. Get user's HAVE resources
  const haves = await getActiveResources(userId, 'HAVE');
  // 2. Get user's WANT resources
  const wants = await getActiveResources(userId, 'WANT');

  const candidates = new Map<string, MatchCandidate>();

  for (const have of haves) {
    // Forward: my HAVE vs their WANTs
    const forwardMatches = await findSimilarResources(have.embedding, 'WANT', userId);

    for (const match of forwardMatches) {
      const key = match.userId;
      if (!candidates.has(key)) {
        candidates.set(key, { userId: key, forwardScore: 0, reverseScore: 0 });
      }
      const c = candidates.get(key)!;
      c.forwardScore = Math.max(c.forwardScore, match.score);
    }
  }

  for (const want of wants) {
    // Reverse: my WANT vs their HAVEs
    const reverseMatches = await findSimilarResources(want.embedding, 'HAVE', userId);

    for (const match of reverseMatches) {
      const key = match.userId;
      if (candidates.has(key)) {
        const c = candidates.get(key)!;
        c.reverseScore = Math.max(c.reverseScore, match.score);
      }
    }
  }

  // 3. Bidirectional score = forward × reverse
  // Both must be high for a good match
  return Array.from(candidates.values())
    .map(c => ({
      ...c,
      score: c.forwardScore * c.reverseScore,
    }))
    .filter(c => c.score > 0.3)  // minimum threshold
    .sort((a, b) => b.score - a.score)
    .slice(0, 20);
}
```

## Performance notes

- pgvector with IVFFlat index: good enough for 100k resources
- Create index: `CREATE INDEX ON resources USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);`
- Matching is not real-time — run on resource creation/update and cache results
- Re-run matching as a background job every few hours for all active users

## What NOT to do

- Don't build a recommendation engine — simple similarity is enough for MVP
- Don't use tag-only matching — semantic similarity catches "resume design" ≈ "CV formatting"
- Don't run matching on every page load — cache match results in a Match table
- Don't try chain matching yet — that's v2
