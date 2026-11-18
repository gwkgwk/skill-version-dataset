---
name: rarity-tier-scaffold
description: Invoke this to add a new rarity/tier level in a loot, pet, card, or mutation system on any Roblox project — config table, roll weights, integration into the random selection logic.
---

Generic playbook for extending an existing rarity system with a new tier, without breaking the balancing or the roll logic already in place.

## Step 1 — Discover the existing system

1. `grep_scripts` to locate the config `ModuleScript`(s) containing the current rarity tiers (often a table explicitly named around "rarity"/"tier"/"rolltable" or its equivalent in the project's language).
2. `get_script_source` on this module to understand the exact structure: tier name, weight/probability, associated color, effect multiplier (value, power, income depending on the game).
3. `grep_scripts` to find the random roll function that consumes this table (often a cumulative sum of weights followed by a random draw) — understand precisely how the weights are interpreted (raw weight, percentage, inverse weight) before adding an entry.

## Step 2 — Backup check

Check for the presence of a `.git`. Recommend a backup (`export_rbxm` of the relevant module at a minimum) before modification, since a weight error can break the game's economic balance in a way that's hard to detect immediately.

## Step 3 — Design the new tier

Before coding, define:
- The name and position of the tier in the rarity hierarchy (between which existing tiers it sits, or whether it's above/below all of them).
- Its roll weight, consistent with the progression already observed between existing tiers (e.g., if each higher tier has a weight ~5 to 10 times lower than the previous one, respect a similar ratio rather than an arbitrary value).
- Its effect value (income, damage, bonus) following the same progression logic as the existing tiers.
- A distinct color/visual identity, consistent with the color code already used (e.g., progression from cool to warm or vivid colors as rarity increases).

## Step 4 — Implementation

1. Add the new entry to the config `ModuleScript` via `edit_script_lines` (targeted patch to avoid risking altering the rest of the table with a full `set_script_source`).
2. Check that no roll logic has a hardcoded number of tiers (e.g., a `for i=1,5` loop when there are now 6 tiers) — if so, fix it for dynamic iteration over the entire table.
3. If the tier has a visual representation (object color, particle effect, UI icon), configure that as well for consistency with the rest (may require coordinating with a dedicated VFX/UI agent for the visual part).

## Step 5 — Verification

1. `execute_luau`/`eval_server_runtime` to simulate a large number of rolls (e.g., 10,000 iterations) and measure the actual appearance frequency of the new tier against the expected weight.
2. Verify that the probabilities of the other tiers have been correctly recalculated proportionally (adding an extra weight changes the relative probability of all others if the calculation is based on a total sum).
3. `get_runtime_logs` to confirm the absence of errors when rolling with the new tier included.

## Central guardrail

Any random generation (loot, pet, mutation, card) must be executed and validated server-side only — the client must never itself calculate or propose the result of a roll, at the risk of allowing the result to be falsified.
