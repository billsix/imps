# OcarinaOfTime — the rename stream's codegen check at a pin bump cannot pass as documented

**Status:** ready — decision recorded 2026-11-26
**Priority:** 6
**Difficulty:** 4 (a rename-aware normalisation step for `tools/asmdiff.sh`, plus making the old side compile)
**Created:** 2026-11-26 (agent, third upstream sweep; a sync item that did not resolve gets a task: `CLAUDE.md`, "Staying current with upstream").

## BLUF

The master `CLAUDE.md` says a pin bump needs two codegen checks for OcarinaOfTime, and the second is "prove the rename re-cut changed no code — `asmdiff_tree.sh <new-standard-c-tip> <re-cut-tip>`". Run for the first time on 2026-11-26, that command cannot pass: it compares code before the renames with code after them, so every renamed symbol shows up as a difference. Done means either the tool can compare across renames and the check is green, or the docs say what replaces it.

## Context

**Read first:** `CLAUDE.md` ("What the asmdiff gate actually needs"), `tasks/reference/imps/standard-c-tooling.md`, `tasks/reference/imps/recutting-a-stream-under-a-new-base.md` (step 5, the re-cut gate) and `tools/asmdiff.sh`.

**What ran (2026-11-26, pin `64df9cb8`, a cmake tree configured in a sandbox-only directory):**

- Check 1, `asmdiff_tree.sh <pin> <standard-c tip>`: green, see the sweep log in `tasks/imps-check-upstreams-and-rebase-patches.md`.
- Check 2, `asmdiff_tree.sh <standard-c tip> <rename tip>`: 457 files, 17 identical, 411 "differ", 29 skipped.

**Why the 411 are not findings.** `tools/asmdiff.sh` compiles the working-tree file and the old ref's copy of the same file with the same recorded command, inside the working tree. For the rename stream:

- 152 files compile on both sides and differ only in symbol names, for example `func_80002384` against `Assert_Fail` in `soh/src/boot/is_debug.c` (`.globl`, `.type`, the label and `.size`: 8 lines).
- 259 files fail to compile on the old side: the old source calls the old names, and the headers in the working tree declare only the new ones.

**Why the re-cut gate in the reference doc did work.** Step 5 of the re-cut method compares the *old applied* tree with the *new applied* tree. Both carry the renames, so names agree and only resolution mistakes can differ (OoT, 2026-09-22: 496/496). That comparison is valid when the base is the same. At a pin bump the base moved, so old-applied against new-applied is dominated by upstream's changes, which is why `CLAUDE.md` substituted the command that does not work.

**What stands in for it today.** In this sweep the rename stream replayed with no conflict, so there was no hand or tool resolution to get wrong, and `n64/OcarinaOfTime/tools/check_renames.py all` passed (every rename claimed by its commit and total). That argues the stream is still pure renames; it is not a codegen proof.

## Options

- **(a) Rename-aware comparison.** Teach `tools/asmdiff.sh` (or `tools/asmdiff_normalise.py`) to apply the stream's `old -> new` map (the pairs `tools/resolve_rename_conflicts.py` already reads from the patch bodies) to the old side's assembly, and compile the old side against the old ref's headers (a second worktree at the standard-c tip with its own configured tree) instead of the working tree's.
- **(b) Per-patch check.** A pure-rename patch can be checked alone: compile each touched file before and after that patch in two worktrees and compare after substituting that patch's pairs. Slower (490 patches), but it localises a failure.
- **(c) Drop the second check from the docs** and state that `check_renames.py all` plus a conflict-free replay is the gate, with the codegen comparison required only when a replay needed resolutions.

## Plan

1. Decide the option (question 1).
2. Implement it; prove it on the current pin (expected: every file identical).
3. Correct `CLAUDE.md` and `tasks/reference/imps/standard-c-tooling.md` to describe the check that exists.

## Decision (William Emerison Six <billsix@gmail.com>, 2026-11-26)

Option (a): build the rename-aware comparison across two worktrees. Until it exists, the rule in `CLAUDE.md` holds: a conflict-free replay plus `check_renames.py all` stands in, and a replay that needed resolutions is not accepted without the codegen comparison.

## Open questions

None.
