# OcarinaOfTime: review the re-cut `personal` rename patches (the 120 whose content changed)

**Status:** in progress — the maintainer's review (William Emerison Six <billsix@gmail.com>, asked
for 2026-09-23); the agent has prepared the material, the decision is the maintainer's
**Priority:** 2 · **Difficulty:** 3 (reading 120 patch diffs with a known shape; nothing to write)
**Project key:** ocarina
**Depends on:** `tasks/ocarina-de-disassemble-ugly-c.md` (Phase C: the re-cut, 2026-09-22)

## BLUF

The 488-patch `personal` rename stream was re-cut on top of the new `standard-c` stream. 120 of
the 488 patch files differ in *content* from the previous series (87 through mechanical conflict
resolution, 33 only because their context lines moved); all 488 differ in SHAs and in the
`base-commit` footer (now the `standard-c` tip). Done = the maintainer has looked at the 87
resolutions (or a sample plus the totals) and either accepts the re-cut (delete the reference
branch `imps-personal-old` in `Shipwright`) or names the patches to redo by hand.

## Context — what changed, and what already proves it is right

- **What a resolution did** (`tools/resolve_rename_conflicts.py`): in each `git am --3way`
  conflict block, take OUR side (the `standard-c` tree), apply that patch's `old -> new` renames to
  it, and re-insert the lines the patch ADDED beside them (the provenance comments); an inline
  `// was func_… [oot]` tag that the patch appended to a rewritten line is carried over by prefix
  match. Every block was resolved this way; none needed a hand edit. The per-patch list of which
  files conflicted: `tasks/adhoc/ocarina-assembly-isms/data/phase_c_resolved_patches.txt` (87 lines,
  `<patch>: <files>`); the runner is `tasks/adhoc/ocarina-assembly-isms/batches/oot_phase_c.sh`
  (+ `oot_phase_c_resume.sh`), so the re-cut is reproducible from the old series if needed.
- **Machine proof already in hand** (2026-09-22): `tools/check_renames.py series` (every rename the
  history performs is claimed by its commit and total), `traceable`, `declarations` — all pass on
  the new tree; every `.c` file that differs between the OLD applied tree (`imps-personal-old` =
  pin + old series) and the NEW one (`imps-applied`) compiles to byte-identical assembly — 478 by
  path plus the 18 renamed files (496/496); `tools/check_patches_apply.sh OcarinaOfTime` applies
  all 524 patches from the bare pin; the applied tree builds (`soh.elf`).
- So the review is about **taste and provenance**, not correctness: does each resolved patch still
  read as "one file's renames, nothing else"? Did a provenance comment land beside the right
  definition after a rewrite moved lines?

## How to review (host, from `n64/OcarinaOfTime/`)

1. **List the content-changed patches** (ignoring SHAs/index/hunk headers):
   `git diff HEAD~1 -- patches/personal | grep '^diff --git' | wc -l` after the commit, or before it
   the staged diff `git diff --cached --stat -- patches/personal`. To separate real content changes
   from SHA churn, use the same normalisation the agent used: strip `From <sha>`, `index …`,
   `base-commit:`/`prerequisite-patch-id:` and `@@` lines from both versions and compare — 120 files.
2. **Read the 87 resolutions** — they are the patches whose diff, after normalisation, changes lines
   *inside* hunks (not just hunk context). For each: the hunk should show the rename applied to the
   REWRITTEN line (e.g. `(thisx->params >> 8) & 0xFF` — the `(s32)` gone — with the new function
   name and its `// was …` tag), never the old line resurrected.
3. **Spot-check provenance placement:** `git grep -n "LLM generated name\|Name from zeldaret" soh/src`
   in the applied checkout and confirm a comment sits directly above its definition in a few of the
   rewritten files (`z_bg_spot01_objects2.c`, `audio_general.c`, `z_en_horse.c`, `z_player.c`).
4. **Decide:** accept → `git -C Shipwright branch -D imps-personal-old`; reject some → name them here,
   the agent redoes those by hand (or with a corrected resolver) and re-runs all the gates above.

## Notes / decisions

## Open questions

1. Accept the re-cut as is (recommended: the gates prove the tree is unchanged and every rename is
   total), or redo the 87 by hand?
