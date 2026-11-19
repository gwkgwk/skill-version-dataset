---
name: spec-tasks
description: Decompose design into ordered, atomic, independently-verifiable tasks.
user-invocable: true
tools: [Read, Write, Task]
---

# Spec: Tasks Phase

Precondition: design.md approved.

Output: `.claude/specs/<id>/tasks.md`

## Rules for a valid task

- Implementable in ONE subagent context (< 50K tokens total)
- Has a single binary acceptance test
- Has explicit dependencies listed (references other task IDs)
- Lists exact files it will touch
- Has an estimated token budget and timeout
- Must either compile clean OR be tagged `[scaffold]` (intentionally incomplete)

## Template per task

```markdown
### Task N: <short title>
- **Status**: `- [ ]` (unchecked; `- [x]` when done)
- **Dependencies**: [T1, T3]
- **Files touched**:
  - `src/modules/auth/auth.service.ts`
  - `src/modules/auth/auth.service.test.ts`
- **Acceptance**:
  - Command: `npm test -- auth.service`
  - Expected: all pass, coverage delta ≥ 0
- **Rollback**: `git revert <commit>`
- **Budget**: 20K tokens / 10 min wall time
```

## Process

1. Read design.md fully
2. Draft task list in dependency order
3. For each task, verify ALL 6 rule items are satisfied
4. If a task would touch more than 5 files OR change more than 300 LOC, SPLIT IT
5. Identify parallelizable tasks (no shared files, no dependency edges)
6. STOP after writing. User types `/spec-implement` to proceed.
