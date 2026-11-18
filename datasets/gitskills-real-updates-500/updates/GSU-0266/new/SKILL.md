---
name: qmd-collection
description: Manage qmd collections — add/remove/list indexed folders, attach context meta descriptions, and browse indexed files with ls.
when-to-use: |
  INVOKE when: user wants to add/remove/list indexed folders, check which folders are indexed, attach descriptions to collections, browse indexed files
  Triggers: "add collection", "indexed folders", "which folders are indexed", "collection list", "add context", "which files are indexed"
allowed-tools: Bash(qmd:*)
---

## Overview

Manage target folders as collections for search. Run `qmd embed` (qmd-index skill) after adding a collection to enable vector search.

## collection Subcommands

```bash
# add folder (uses folder name if no --name given)
qmd collection add ~/notes --name notes
qmd collection add ./docs

# list collections
qmd collection list

# show details
qmd collection show notes

# rename
qmd collection rename notes my-notes

# remove
qmd collection remove notes
```

## context Subcommands

Attach meta descriptions to collections or subpaths. Helps improve search quality.

```bash
# attach description to entire collection
qmd context add qmd://notes/ "Personal notes and project documentation"

# attach description to specific path
qmd context add qmd://notes/meeting-notes "Weekly team meeting notes"

# list contexts
qmd context list

# remove context
qmd context rm qmd://notes/meeting-notes
```

## ls — Browse Indexed Files

```bash
# list all indexed files
qmd ls

# list files in a collection
qmd ls notes

# browse specific path
qmd ls notes/journal
```

## Important

Run `qmd embed` after adding collections (qmd-index skill). `qmd collection add` only performs text indexing; vector embedding requires a separate step.
