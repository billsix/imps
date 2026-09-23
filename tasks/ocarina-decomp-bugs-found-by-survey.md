# OcarinaOfTime: real bugs the assembly-isms survey found (not cleanups — separate fixes)

**Status:** proposed — needs go-ahead
**Priority:** 4 · **Difficulty:** 3
**Project key:** ocarina
**Found by:** the 2026-09-22 survey (`tasks/adhoc/ocarina-assembly-isms/reports/booleans-comments-whole-functions.md`,
"Out of scope but found", and `raw-memory-and-numeric.md` §3). None of these is a decomp
artefact to rewrite; each is live behaviour in the port and belongs in its own
`upstream-candidates` patch, with the maintainer's in-game check. Sister:
`tasks/mario64-surface-collision-dangling-pointer.md`.

## The list

1. **Uninitialised `s32 getItemId`** — `soh/src/overlays/actors/ovl_En_Ge1/z_en_ge1.c` (the
   `switch` that assigns it has no `default`, so an unexpected value reads garbage; GCC-UB, not
   only ROM junk).
2. **Uninitialised `s32 fairyType`** — `soh/src/overlays/actors/ovl_Shot_Sun/z_shot_sun.c`, same
   shape.
3. **Out-of-bounds read of `sOwEntranceFlag[20]`** — `soh/src/code/z_map_exp.c` indexes
   `owEntranceFlag[≤23]` (`z_map_data.c` holds 20 entries).
4. **64-bit sentinel truncation** — `soh/src/overlays/actors/ovl_En_Horse/z_en_horse.c`
   `(uint32_t)(uintptr_t)linkCsAction != 0xABABABAB`: a debug-fill check written for a 32-bit
   pointer; on the PC port the compare only sees the low half.
5. (From the control-flow report) `sIrqMgrResetTime` is write-only and `D_8016A578` has zero
   references — dead `volatile` globals; harmless, delete or leave.

## Plan

- [ ] Confirm each with the port's flags + `-Wall -Wuninitialized`/`-Warray-bounds`, quote the
      warning.
- [ ] Fix on a scratch branch at the applied series tip (these sit ABOVE `personal`, so they use the
      renamed names), export to `patches/upstream-candidates/`, `tools/check_patches_apply.sh
      OcarinaOfTime`, list in `n64/OcarinaOfTime/CLAUDE.md`.
- [ ] Maintainer plays the affected scenes.

## Open questions

1. Fix shape for #1/#2: a `default:` that sets a safe value (smallest) or an initialiser at the
   declaration? Recommendation: initialiser, and keep the switch as is.
