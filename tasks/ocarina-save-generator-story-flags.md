# OcarinaOfTime: save generator — make saves read like real playthroughs

**Status:** proposed — needs go-ahead
**Priority:** 4
**Difficulty:** 5

## BLUF

A generated save currently gets the *mechanical* progression right
(dungeons beaten, rewards, items, stocks) but leaves the game's **story
and world state at minute zero**: the maintainer's first generated save
spawns adult Link with medallions while the game still announces that
the Great Deku Tree wants to talk to him. Fix the default so a generated
save reads like an actual playthrough of the chosen progression — while
keeping the current minimal-flags behavior available as an option (the
maintainer explicitly finds the weird state funny and worth keeping).
Done when a "through Water Temple" generated save drops the player into
a world whose NPCs/cutscenes/state match a real playthrough that far.

## Context

- The generator: `OcarinaOfTime/tools/save_generator.py`; format
  knowledge: `tasks/reference/ocarina/save-file-generator.md`; completed
  predecessor task:
  `tasks/archive/ocarina/2026/09/01/ocarina-save-file-generator.md`.
- **Root cause:** the generator sets only the dungeon-beaten flags,
  quest rewards, and warp-song bits. OoT's world state lives in hundreds
  of OTHER `eventChkInf` / `itemGetInf` / `infTable` bits — intro
  cutscenes seen, NPCs met (Mido, Saria, Zelda, Kaepora), Door of Time
  opened, Master Sword pulled, era-transition story beats — all left at
  0, so the world believes the game just started.
- **The method the maintainer proposed (2026-09-01), which is the right
  one:** he plays the game and provides REAL save states at known
  progression points; those become ground truth to learn from. The
  generator's own `deep_diff` (used by `--selftest`) is exactly the tool
  to diff a real save at stage X against a generated stage-X save — the
  diff IS the missing-flag list for that stage.
- Supplements: `z64save.h`'s `EVENTCHKINF_*` constant names make the
  diffed bits legible; online research stays authorized (per the
  predecessor task) for flag semantics the constants don't explain.

## Plan

1. Maintainer supplies real saves at a few checkpoint stages (suggested:
   post-Deku-Tree; all-stones child; just-pulled-Master-Sword;
   post-Forest; through-Water; all-eight). Drop them somewhere
   convenient (NOT committed — they're personal; a `tools/refsaves/`
   dir, gitignored, would do).
2. For each stage: diff real vs generated, decode the differing
   `eventChkInf`/`itemGetInf`/`infTable` bits against the constants,
   and record the per-stage flag sets in the reference doc.
3. Encode cumulative "story stage" flag sets in the generator, applied
   by default according to the dungeon answers; add a
   `--minimal-flags` option preserving today's funny minute-zero
   behavior.
4. Verify: generate each stage, load in-game, walk around — NPC and
   cutscene states should match a real playthrough (the Deku Tree
   should be appropriately dead, not chatty).

## Open questions

None — awaiting the maintainer's reference saves to begin.
