---
name: ingest
description: Ingest raw source material from raw/tool-docs/ into the tech/ wiki. Reads source files, synthesizes takeaways, negotiates page structure with the human, writes or updates tool/technique pages, updates reverse links, and appends to the index and log.
argument-hint: <tool-name | path-to-raw-dir>
---

# ingest

You are ingesting raw source material into the Frobnicate tech wiki. The argument identifies the source:

**Argument:** $0

**Resolve the source directory:**
- If $0 looks like a path (contains `/` or `\`, or starts with `raw/`), use it directly.
- Otherwise treat it as a tool or technique name and resolve to `raw/tool-docs/<$0>/`.

Work through these steps in order. Stop at each human checkpoint before proceeding.

---

## Step 1: Read the source material

Glob all `.md` files in the resolved directory. Read every file. Note the `source_url` and `fetched_on` from each file's frontmatter so you can cite sources precisely.

Also read:
- `tech/index.md` — to understand what pages already exist
- `schemas/templates/tool.template.md` and `schemas/templates/technique.template.md` — to know the expected page structure
- Any existing `tech/tools/` or `tech/techniques/` pages that seem related, so you can detect contradictions

---

## Step 2: Synthesize and present takeaways

Distill the source material into 5–8 key facts worth capturing in the wiki. Group them by likely destination:

**Tool-level facts** — things that are true of this software as a whole (what it does, strengths, weaknesses, install, operational gotchas). These go on `tech/tools/<Tool>.md`.

**Technique-level facts** — reusable methods that transcend this one tool (e.g. LoRA training, ControlNet depth guidance, inpainting). These belong on their own `tech/techniques/<Technique>.md` pages, not on the tool page. List them as candidates for future technique pages if they don't exist yet.

**Out-of-scope** — anything that violates the hard rules in `CLAUDE.md`: game-specific content, studio-specific content, magic numbers without rationale. Flag these and do not include them.

Present your synthesis clearly. For technique candidates, indicate whether a page already exists in `tech/techniques/` or whether it would be a new stub.

**Stop and wait for the human to confirm, redirect, or add to the takeaways before writing anything.**

---

## Step 3: Determine affected pages

Based on the confirmed takeaways, identify every page that needs to be created or updated:

- **New tool page** → `tech/tools/<Tool>.md` using `schemas/templates/tool.template.md`
- **New technique page** → `tech/techniques/<Technique>.md` using `schemas/templates/technique.template.md`
- **Update to existing page** → read the current file first; note any claims that contradict what the new source says — do not silently overwrite, surface the contradiction to the human

For each page, state what you plan to write or change. **Wait for confirmation if any contradictions were found.**

---

## Step 4: Write or update wiki pages

Write each page using the appropriate template structure. Follow these rules:

- Keep parameter guidance in **ranges with rationale**, never magic numbers. "Weight 0.7–0.9 preserves silhouette; below 0.5 the generator rewrites structure" is useful forever. "Use 0.85" is not.
- Cross-link using Obsidian-style `[[wiki-links]]`: every technique referenced in a tool page links to `[[techniques/<Technique>]]`, and vice versa.
- In the Sources section of each page, use relative markdown links back to the raw files in `raw/tool-docs/`.
- If a technique page is referenced but does not exist yet, still add the `[[wiki-link]]` — it will show as a dead link in Obsidian until the page is created, which is intentional.

---

## Step 5: Update reverse links

For every technique page that already exists and is referenced by a newly created or updated page:
- Open the technique page
- Add the new page to its "Used by recipes" or related section if not already present

For every tool page that already exists and is referenced:
- Add the new page to its "Used by recipes" section if not already present

---

## Step 6: Update tech/index.md

Add or update one row per new or changed page in the appropriate table (Tools, Techniques, Recipes, or Comparisons). Keep the summary to one line.

Update the `last_updated` frontmatter date.

---

## Step 7: Append to tech/log.md

Append one entry using the format:

```
## [YYYY-MM-DD] ingest | <subject>

<One or two sentences: what was created/updated, what sources were used, what was flagged for future work.>
```

Use today's date. Do not modify existing entries.

---

## Step 8: Report

Summarize everything touched:

- Files created or updated in `tech/`
- Reverse links added
- Technique stubs flagged (referenced but not yet created)
- Any contradictions found and how they were resolved
- Any out-of-scope content that was excluded