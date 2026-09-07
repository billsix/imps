# Ocarina: split the monolithic rename patch into one-rename-per-patch, and make every rename traceable at its declaration

**Status:** in-progress
**Priority:** 3
**Difficulty:** 6
**Started:** 2026-09-07

## BLUF

`n64/OcarinaOfTime/patches/personal/0001-LLM-generated-renames.patch` is one
6,854-line commit carrying **206 symbol renames + 20 file renames across 145
files** — too big to review in one sitting, and its provenance comments sit only
at each symbol's *definition*, so a reader of `soh/include/functions.h` sees a
new name with no trace of the address name it replaced. Two jobs: **(1)** add
provenance at the **66 header declaration sites** that currently carry a renamed
symbol with no comment (one of them the only rename with no comment anywhere —
`UnkRumbleStruct` → `RumbleMgr`), and **(2)** rebuild the `personal/` stream as
**one commit per renamed symbol** (that symbol renamed everywhere; never two
symbols in one commit). Done = `patches/personal/` holds ~210+ numbered patches
that `git am` clean onto the pin and produce a tree **byte-identical** to today's
`7ce750506` plus the new comments.

## Context

### Read first

- **[`tasks/reference/ocarina/decomp-renaming.md`](reference/ocarina/decomp-renaming.md)** —
  the method, the zeldaret/oot oracle, the provenance-comment convention, and
  every gotcha that has bitten. **This is the governing doc**; the work below
  must not contradict it, and any convention change (see Q1) belongs there.
- **[`tasks/ocarina-decomp-rename-and-cleanup.md`](ocarina-decomp-rename-and-cleanup.md)** —
  the parent, still-open renaming effort. The patch this task splits is that
  task's output as of its 2026-07-31 stopping point. **This task does not add
  renames**; it re-shapes what already exists.
- **`n64/CLAUDE.md`** → "Patches are grouped into purpose STREAMS" — the split
  happens entirely inside `patches/personal/`; the other streams are untouched
  and commute with it.
- **`n64/OcarinaOfTime/CLAUDE.md`** — pin, patch list, build/run gotchas.

### Current state

- **Pin:** `acdbc651d4b11e29518442d6875a3ec181414cfc` (Shipwright 9.2.3-421),
  set in `n64/OcarinaOfTime/fetch.sh` as `PIN_SHA`.
- **Checkout:** `n64/OcarinaOfTime/Shipwright/` is at `7ce750506` = the pin +
  the single "LLM generated renames" commit. `commit.gpgsign` is already
  `false` repo-locally there (set by `fetch.sh`), so `git am` will not abort
  mid-series.
- **The patch:** `patches/personal/0001-LLM-generated-renames.patch`, 6,854
  lines, 145 files, 1,149 insertions / 903 deletions.

### What the patch actually contains (measured 2026-09-07, not estimated)

Every number below came from the scripts saved in
`tasks/adhoc/ocarina-split-rename-patch/`; re-run them rather than trusting
these figures after any change.

| Thing | Count |
|---|---|
| Symbols renamed (`func_*`, `D_*`, `Struct_*`) | **206** |
| ├─ carrying a `Name from zeldaret/oot` citation | 64 |
| ├─ carrying an `LLM generated name` marker | 141 |
| └─ `Struct_8016E320` → `SeqRequest` (typedef; comment above the `typedef struct {`) | 1 |
| Renames with **no** provenance comment anywhere | **0** |
| Renames that are **incomplete** (old name still in real code) | **0** |
| File renames (`code_<addr>.c` → meaningful name) | **20** |
| Distinct definition files holding a renamed symbol | 70 |
| Symbols that are file-local statics (1 file) | 133 |
| Symbols that cross files | 71 |
| └─ of those, touching a shared header | 62 |
| Build-system files touched | **0** (the build globs `soh/src/*`) |

**The commit is renames + comments and nothing else.** Verified mechanically:
reversing every rename and stripping the provenance comments reproduces the
pin's tree (`residue.py` — 69 residual lines, every one either a static-name
collision the reversal itself causes, one of the two renames the inventory
cannot carry, or a stale-path comment updated by a file rename; **no
behavioural change**). One extra rename falls
outside the address-name convention and so is invisible to the
`git grep 'LLM generated name'` audit: the struct type
**`UnkRumbleStruct` → `RumbleMgr`** (`soh/include/z64.h`, plus three
declarations in `functions.h`) — it has **no comment at all**.

### The gap the maintainer flagged

The convention in `decomp-renaming.md` puts the comment **above the
definition**. That is satisfied — but it leaves the **declaration** bare, which
is exactly where a reader meets the name first:

```c
/* soh/include/functions.h:1626 — no trace of what these were */
void AudioMgr_StopAllSfx(void);
void AudioMgr_NotifyTaskDone(AudioMgr* audioMgr);
void AudioMgr_HandleRetrace(AudioMgr* audioMgr);   /* pre-existing upstream name */
```

while the traceability lives one file away:

```c
/* soh/src/code/audio_stop_all_sfx.c:8 */
// Name from zeldaret/oot, was func_800C3C20: loops sSfxBankIds calling
// Audio_StopSfxByBank on each [oot: .../src/code/audio_stop_all_sfx.c]
void AudioMgr_StopAllSfx(void) {
```

Reading the header, there is no way to tell a renamed symbol from an upstream
one. **66 header sites** are in this state: 56 in `soh/include/functions.h`, 6
in `soh/include/variables.h`, 2 in `ovl_En_Zl4/z_en_zl4.h`, 1 in
`ovl_Item_B_Heart/z_item_b_heart.h`, and 1 in `soh/include/z64.h` (the
`RumbleMgr` typedef). Run `header_gap.py` for the live figure.

### Decisions already made

- **These names are guesses.** 141 of 206 are LLM-deduced because zeldaret/oot
  leaves the symbol address-named too; 64 are adopted from oot. The whole point
  of the provenance comment is that a later reader can re-derive or overturn the
  guess — which is why declaration-site traceability matters.
- **Call sites do not get comments.** Only the definition and (new, this task)
  the declaration. There are 773 non-header occurrences; commenting them all
  would be noise.
- **The split stays inside `patches/personal/`.** Streams touch disjoint files
  and commute, so no other stream is renumbered or regenerated.
- **`git am` needs unsigned commits**; `fetch.sh` already sets
  `commit.gpgsign false` in the checkout.

### Hazards that will bite (all confirmed present in this patch)

1. **File-local statics must be renamed file-scoped, never tree-wide.** 133 of
   the 206 are `static`. `sColChkInfoInit` — the new name for `D_80A65F38` in
   `ovl_En_Md/z_en_md.c` — **already exists as a static in 60 other files**. A
   tree-wide `sed` would corrupt all of them. Scope the rename *and* its
   collision check to the single defining file.
2. **Two distinct old symbols were given the same new name.**
   `D_809B8118` and `D_809D2560` both became `sTentacleTextures`, in different
   files. They are separate renames and must be separate commits.
3. **`soh/include/` is easy to forget.** `functions.h` / `variables.h` carry the
   prototypes and externs; a rename that skips them is incomplete. (48 symbols
   were left half-renamed this way during the original effort.)
4. **`savestates.cpp` `_copy` entanglement.** `\b` does not match `NAME_copy`
   (underscore is a word character), so a rename silently half-updates. Grep
   `soh/soh/Enhancements/savestates.cpp` before renaming any `D_` global.
5. **20 file renames are their own commits.** Several are file *splits* git
   reports as add+delete, not rename: `code_800A9F30.c` → `z_rumble.c`,
   `code_800C3C20.c` → `audio_stop_all_sfx.c`, `code_800D31A0.c` →
   `debug_ctrlr2.c`. Use `git mv` so the rename is recorded.
6. **Build verification is the maintainer's**, outside the sandbox. Our gate is
   the tree-equality proof (step 5), not a compile.

## Goal

Turn one unreviewable 6,854-line rename commit into a reviewable series — one
commit per renamed symbol, each renaming that symbol everywhere it appears and
nothing else — while closing the traceability gap by putting a provenance
comment at every declaration site as well as every definition, so a reader of
`functions.h` can tell a guessed name from an upstream one without leaving the
file. The rebuilt series must reproduce today's tree exactly, plus the added
comments.

## Plan

- [ ] **1. Freeze a baseline.** `git -C Shipwright branch baseline-renames
      7ce750506`. Every later check diffs against it. Never touch it.
- [ ] **2. Build the authoritative rename inventory.**
      `python3 tasks/adhoc/ocarina-split-rename-patch/inventory.py` →
      `inventory.tsv` (`old`, `new`, `provenance`, `def_file`, `def_line`).
      **Hand-verify every row** — it parses C declarations with a regex. One
      mis-parse was already found and fixed during the survey (`D_80133344`
      resolved to the macro `VT_COL` instead of `sSfxDistOverPrintMsg`, because
      a `(` appeared inside an initializer), so assume more. Add the two rows it
      cannot derive: `Struct_8016E320` → `SeqRequest` (typedef, name on the
      closing brace) and `UnkRumbleStruct` → `RumbleMgr` (no comment to parse).
- [ ] **3. Decide the declaration-comment form** (blocks the rest — see Q1),
      then write it at all **66** header sites — including a first-ever comment
      for `UnkRumbleStruct` → `RumbleMgr`. `header_gap.py` must then report 0.
- [ ] **4. Rebuild the stream, one rename per commit**, replaying onto the pin
      on a scratch branch:
      1. the 20 file renames (`git mv`), one commit each, message naming the
         old path and why the new name was chosen;
      2. then one commit per symbol, in `inventory.tsv` order, each applying
         that symbol's rename **everywhere** (definition, declaration, all call
         sites) plus its provenance comments — **file-scoped for statics**;
      3. commit subject `soh: rename <old> -> <new>`, body carrying the
         provenance sentence and, for oot-sourced names, the citation URL.
- [ ] **5. Prove the rebuild is content-identical.**
      `git diff <rebuilt-tip> baseline-renames` must be **empty except for the
      added declaration comments** — history changed, content did not. If it
      differs anywhere else, stop and investigate; do not proceed.
- [ ] **6. Regenerate the stream:**
      `git format-patch --no-cover-letter --base=<pin> <pin>..<rebuilt-tip> -o
      patches/personal/`, delete the old `0001-LLM-generated-renames.patch`.
- [ ] **7. Verify from scratch:** `./fetch.sh && ./apply.sh` on a clean
      checkout, then confirm the resulting HEAD tree matches `baseline-renames`
      plus comments. Re-run `completeness.py` — it must still report 0
      untraceable and 0 incomplete renames.
- [ ] **8. Update [`tasks/reference/ocarina/decomp-renaming.md`](reference/ocarina/decomp-renaming.md)**
      with the declaration-site rule and the one-rename-per-commit rule, so the
      remaining ~3,988 un-named symbols are done this way from the start.
- [ ] **9. Hand to the maintainer for the build/run gate.**

## Notes / decisions

- **Why ~226 commits is the right answer, not a smell.** The maintainer's ask is
  explicit: one name per commit. Each is small and independently reviewable or
  revertable — which is the point, since 141 of the names are guesses. A wrong
  guess should be one `git revert`, not a 6,854-line untangle.
- **Ordering within the stream.** File renames first (so later commits touch
  final paths), then symbols. Within symbols, grouping by definition file keeps
  a reviewer in one area at a time; `inventory.tsv` is already sorted that way
  after step 2.
- **Scripts** live in `tasks/adhoc/ocarina-split-rename-patch/` — repo-relative
  and re-runnable: `inventory.py` (the rename table), `completeness.py` (proves
  no untraceable/incomplete rename), `header_gap.py` (sizes the declaration
  gap), `residue.py` (proves the commit is renames-only). `completeness.py` and
  `residue.py` are the regression gates for steps 5 and 7. `header_gap.py`
  should report **0 uncommented header sites** once step 3 lands.

## Open questions

1. **What form should the declaration-site comment take?** The definition-site
   comment is a full sentence with rationale and (for oot names) a URL —
   repeating all of that 65 times in `functions.h` would bloat the header. My
   recommendation: a **short one-line form** carrying only the old name and the
   confidence marker, e.g.
   `void AudioMgr_StopAllSfx(void); // was func_800C3C20 [oot]` and
   `... // was func_800F5B58 [LLM:HIGH]` — greppable by the same
   `was func_`/`[LLM` patterns, enough to flag "this name is ours, go read the
   definition", without duplicating the prose. Alternative: repeat the full
   comment above each declaration (consistent, but adds ~65 long lines to two
   headers). Which do you want?
2. **Should `UnkRumbleStruct` → `RumbleMgr` get a marker, and which one?** It is
   a *type* rename, so the existing `func_`/`D_` convention doesn't cover it and
   the `git grep 'LLM generated name'` audit misses it entirely. I recommend
   `// LLM generated name (HIGH), was UnkRumbleStruct: the rumble manager
   state, per sys_rumble.c` above the typedef in `z64.h`, and extending
   `decomp-renaming.md` to say type renames follow the same convention. OK?
3. **One commit per symbol, or may a file rename absorb the symbols defined
   only in that file?** Strictly one-per-symbol gives ~226 commits; letting a
   file rename like `code_800A9F30.c` → `z_rumble.c` carry the 8
   `Rumble_*` symbols defined solely there would cut it to roughly ~150 and
   arguably reads better as a unit. I recommend **strict one-per-symbol** (it is
   what you asked for, and it keeps every guessed name individually
   revertable), but the file-scoped grouping is a defensible alternative if you
   would rather review by subsystem. Which?
