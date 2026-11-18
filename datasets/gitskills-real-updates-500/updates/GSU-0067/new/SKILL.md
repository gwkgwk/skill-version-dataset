---
name: worktree-merge-discipline
description: Enforce that every git worktree (especially under `.claude/worktrees/`) has its branch merged or its work captured before the worktree is deleted. Trigger when the user asks to clean up worktrees, delete branches, run `git worktree prune`, or "kill all the agent worktrees" — and any time a parallel-task system is producing branches that may carry orphan work.
kind: discipline
version: 1
---

## Why this skill exists

Background agents (Codex rescue, /ultrareview waves, parallel-task spawns, /loop runs) commonly check out into `.claude/worktrees/<adjective>-<author>-<hash>/` on a `claude/<adjective>-<author>-<hash>` branch. When their session ends, the *worktree directory survives*, the *branch survives*, and the work-in-progress is silent.

Two failure modes have actually happened in this repo:

1. **Orphan commit.** A worktree's branch has commits that never made it back to `main`. We discovered this on 2026-04-28 with `claude/great-visvesvaraya-8eaf87` (1 commit ahead, 40 behind — the "T-OBS Phase 3 + O-06 Arize URL builder" work; O-06 was never on main).
2. **Orphan documentation / scratch work.** Whole investigative passes (e.g. "how Linear behaves when connected") lived inside worktrees and were never harvested into `harness-research/` or `docs/`. Searching workshop top-level returns scattered fragments while the substantive work sits in `.claude/worktrees/*` with 100+ Linear references.

Both modes share the same root cause: **a worktree was abandoned without its branch being merged into `main` or its scratch being moved to a workshop-tracked location.** This skill makes that abandonment impossible to do silently.

## When to invoke

- The user asks to delete worktrees, prune worktrees, or clean up `.claude/worktrees/`.
- The user asks to delete `claude/*` branches in bulk.
- A scheduled cleanup job is about to run that touches worktrees.
- Background agents are reporting "done" and you're about to discard their worktree.

If the work-tree being destroyed is a research/synthesis worktree (e.g. harness-research), apply the same discipline to its scratch directory — orphan docs are as bad as orphan commits.

## The mandatory pre-deletion check

Before `git worktree remove`, `git branch -d`, or `rm -rf .claude/worktrees/*`, run this for **every** branch about to be touched:

```bash
git worktree list
for b in $(git branch --format='%(refname:short)' | grep '^claude/'); do
  ahead=$(git rev-list --count main..$b 2>/dev/null)
  behind=$(git rev-list --count $b..main 2>/dev/null)
  echo "$b ahead=$ahead behind=$behind"
done
git branch --no-merged main
```

### Also check: tooling that may be pointing INTO a worktree

The worktree path may be baked into things outside `.git/`. Before deletion, also audit:

```bash
# 1. Any settings.json hook command path under $HOME that names a worktree
find "$HOME" -maxdepth 7 -name 'settings.json' -path '*/.claude/*' \
  -not -path '*/node_modules/*' -not -path '*/.Trash/*' \
  -exec grep -l "/.claude/worktrees/" {} +

# 2. npm-global symlinks pointing at a worktree (this is the easy one to miss
#    — `npm link` from inside a worktree bakes the worktree path into the
#    npm-global lib, and silently breaks when the worktree is deleted)
ls -la "$(npm prefix -g)/lib/node_modules/" 2>/dev/null | grep '/.claude/worktrees/'
ls -la "$(npm prefix -g)/bin/" 2>/dev/null | xargs -I {} sh -c 'readlink "{}" 2>/dev/null | grep -q "/.claude/worktrees/" && echo "{}"'

# 3. Editor / IDE workspace files (.code-workspace, .idea/, etc.) referencing the path
grep -rln "/.claude/worktrees/" "$HOME/.config" "$HOME/.vscode" 2>/dev/null
```

If any of these surface, repoint them BEFORE the worktree is deleted. The npm symlink case is the load-bearing one: a broken `ryu` (or any other) global binary will not error gracefully — `which ryu` simply returns nothing.

For the npm-global case specifically, the fix is:

```bash
rm -f "$(npm prefix -g)/lib/node_modules/<package>"  # drop the dangling link
cd <workshop-root> && npm link                       # re-link from a stable path
```

For each branch, classify:

| Status | Action |
|---|---|
| ahead=0, behind≥0 | Safe to delete. Branch is fully reachable from main. |
| ahead=N (N>0), behind=0 | **DO NOT DELETE.** Branch has commits not on main. Merge or rebase first. |
| ahead=N, behind=M (both >0) | **DO NOT DELETE.** Cherry-pick the unique commits, or attempt merge with conflict review. |
| Detached/orphan ref | Investigate before destroying. |

## Required steps before deletion

1. **List every worktree and branch** (`git worktree list`, `git branch -a`).
2. **Compute ahead/behind** for every `claude/*` branch vs `main`.
3. **Surface a STOP report** to the user if ANY branch is ahead. Format:
   ```
   STOP — unmerged branches detected:
     - claude/<name>: <N> commits ahead, <M> behind
       last commit: <oneline>
       worktree: <path>
   Do not delete until each is resolved (cherry-pick, merge, or explicit discard).
   ```
4. **For research worktrees**, also `find <worktree> -name '*.md' -newer .claude/worktrees -mtime -14` to surface recently-modified scratch docs that haven't been harvested.
5. **Only after the user explicitly confirms** ("discard", "merged via X", "moved to Y") proceed with deletion.

## Deletion procedure (after green-lit)

```bash
# For each cleared worktree:
git worktree remove .claude/worktrees/<name>
git branch -d claude/<name>           # safe: -d refuses unmerged branches
# If -d errors, STOP — do NOT use -D. Re-run the ahead/behind check.

# After all individual removes:
git worktree prune
```

**Never use `-D` (force-delete) or `git worktree remove --force` to bypass the safety check.** Those flags exist for true emergencies, not for cleanup hygiene.

## Push discipline (CLAUDE.md rule 7)

Any merge commit / cherry-pick used to land orphan work follows the standing rule: push to `origin/main` in the same turn as the commit. Cleanup that involves history-touching operations is not exempt.

## Anti-patterns to refuse

- "Just delete them all, they're old" — without a per-branch ahead/behind check.
- "Use --force / -D, the user said yes" — the user said yes to deletion of *merged* branches; force-delete is a separate authorization.
- "We'll harvest the docs later" — later doesn't happen. Move research scratch to `harness-research/` *before* destroying the worktree.
- Skipping the check because there are "only a few" worktrees. The check is fast; the failure mode is silent.

## When you find orphan work

- **Orphan commit on a branch**: `git show <sha> --stat` to inspect; check whether the same logical change already landed via a different commit (search log for the task ID). If it did, the branch is safe to delete. If not, cherry-pick or surface to the user for direction.
- **Orphan docs in worktree scratch**: copy to `harness-research/raw/` or `harness-research/synthesis/` (per the existing taxonomy) with a note about provenance, commit, then delete the worktree.

## Catalog this discipline

Each invocation of this skill on a non-trivial cleanup should leave a trail:
- The pre-deletion ahead/behind table → committed to `harness-research/cleanup-logs/<date>.md` (or surfaced in the PR/commit body).
- Any salvaged orphan commits → referenced in their landing commit message.
- Any salvaged scratch docs → noted in `harness-research/CLAUDE.md` or the synthesis index.

The goal is that "we lost work in a worktree" stops being a recurring failure mode in this repo.
