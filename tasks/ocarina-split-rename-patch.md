# Ocarina: split the monolithic rename patch into one-rename-per-patch, and make every rename traceable at its declaration

**Status:** implemented and proven equivalent 2026-09-07 — all gates green; an on-host rebuild is optional confirmation, not a gate
**Priority:** 3
**Difficulty:** 6
**Started:** 2026-09-07

## BLUF

`patches/personal/` carried the OoT decomp renaming as **one 6,854-line commit**
— 206 symbol renames plus 18 file renames across 145 files — too big to review
in a sitting, and its provenance comments sat only at each symbol's
*definition*, so a reader of `soh/include/functions.h` met a new name with no
trace of the address name it replaced. Two jobs, both done 2026-09-07: **(1)**
put a short provenance tag at all **63** header declaration sites (one of them
the only rename that had no comment anywhere — the type rename
`UnkRumbleStruct` → `RumbleMgr`), and **(2)** rebuild the stream as **one commit
per renamed symbol**, that symbol renamed everywhere, never two per commit.
The stream is now **225 patches, median 50 lines**, which `git am` clean onto
the pin and produce a tree byte-identical to the pre-split `7ce750506` plus the
63 comments. That is **proven, not asserted**: `prove_equivalence.sh` applies
the old patch and the new series side by side and shows no file changes line
count and every differing file is byte-identical once **gcc** strips the
comments — so the two build the same program.

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
| File renames (`code_<addr>.c` → meaningful name) | **18** |
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
one. **66 header sites** were in this state: 56 in `soh/include/functions.h`, 6
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
5. **18 file renames are their own commits.** Several are file *splits* git
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

All steps are complete; the work is staged for review. Every gate below is
re-runnable from `tasks/adhoc/ocarina-split-rename-patch/`.

- [x] **1. Froze a baseline** — `baseline-renames` in the checkout still points
      at the pre-split commit `7ce750506`, so the split can be re-proved at any
      time. (A local branch in a disposable checkout: it disappears on a fresh
      `fetch.sh`, which is fine — the proof is the gate script, not the branch.)
- [x] **2. Built the rename table.** `inventory.py` derives 205 rows by parsing
      the declaration under each provenance comment; `build_rename_table.py`
      adds the two it cannot (`Struct_8016E320` → `SeqRequest`,
      `UnkRumbleStruct` → `RumbleMgr`) and computes each rename's **scope** (the
      files holding the old name at the pin) and confidence. **207 rows.** One
      parser mis-read was caught and fixed: `D_80133344` resolved to the macro
      `VT_COL` instead of `sSfxDistOverPrintMsg`, because a `(` appeared inside
      an initializer rather than a parameter list.
- [x] **3. Annotated all 63 header declaration sites** (`add_decl_comments.py`,
      idempotent). `header_gap.py` now reports **0 bare sites**. The first sweep
      found 66; 3 of those turned out to be commented-out placeholder
      declarations (`// ? Audio_ResetData(?);`), which are not declarations and
      are correctly skipped. **Every tag is appended to an existing line, never
      inserted as a new one**, so no file changes line count — see the proof
      below.
- [x] **4. Rebuilt the stream as 225 commits** (`rebuild.py`): 18 file renames
      then 207 symbol renames, one symbol each, grouped by defining file.
- [x] **5. Proved the rebuild is content-neutral.** The rebuilt tip is
      **byte-identical** to the target tree, and differs from the pre-split tree
      **only** in the 63 comment additions.
- [x] **6. Regenerated the stream** — `patches/personal/0001…0225`, median
      patch **50 lines** (max 367, min 19), replacing the 6,854-line monolith.
- [x] **7. Verified from scratch** — reset to the pristine pin, ran `./apply.sh`:
      all 225 patches `git am` clean and the resulting tree is byte-identical to
      the target. `completeness.py` still reports 0 untraceable / 0 incomplete.
- [x] **8. Updated [`tasks/reference/ocarina/decomp-renaming.md`](reference/ocarina/decomp-renaming.md)**
      with the declaration-tag rule, the type-rename rule, and a new "One rename
      per commit" section, so the remaining ~3,988 symbols are done this way
      from the start. Also updated `n64/OcarinaOfTime/CLAUDE.md`'s patch list.
- [x] **9. Proved the two series compile to the same program.**
      `prove_equivalence.sh` applies the OLD single patch and the NEW 225-patch
      series to two scratch branches off the pin, then shows (a) only 5 files
      differ at all, (b) **no file changes line count** — so `__LINE__`/
      `__FILE__` and the debug prints built on them are untouched — and (c)
      each differing file is **byte-identical once gcc strips the comments**
      (`gcc -fpreprocessed -dD -E -P`). The compiler receives an identical
      token stream from an identical number of lines, so the object code is
      the same. The equivalence rests on a compiler, not on a regex here.
- [ ] **10. Maintainer's on-host build/run** (optional now). The pre-split tree
      was build- and run-verified on-host 2026-09-01, and step 9 proves the
      split is compile-identical to it, so a rebuild should be a formality.

## Notes / decisions

**The three open questions were settled under "use your discretion"
(2026-09-07).**

1. **Declaration comment: the short inline form.** `// was func_800C3C20 [oot]`
   / `// was func_800F5B58 [LLM:HIGH]`, appended to the declaration. Greppable
   by the same `was func_` handle as the long form, and `[oot]` vs `[LLM:…]`
   answers the only question a header reader has — *is this name authoritative
   or a guess?* Repeating the full prose would have added 63 long lines to two
   shared headers to say nothing new; the rationale and URL stay at the
   definition, one jump away.
2. **`UnkRumbleStruct` → `RumbleMgr` got a full marker** above the opening
   `typedef struct {` (its name sits on the closing brace, so there is no
   inline slot). `decomp-renaming.md` now says type renames follow the same
   convention — this one shipped untraceable precisely because the address-name
   audit cannot see a type.
3. **Strict one-symbol-per-commit.** Letting a file rename absorb the symbols
   defined only in it would have cut 225 commits to ~150 and read a little
   better by subsystem, but it would re-couple exactly what the split exists to
   separate: 141 of these names are guesses, and a wrong guess must cost one
   `git revert`. The six `Rumble_*` functions are six commits.

**Method — peel backwards, replay forwards.** Re-deriving each rename forwards
from the pin would have given no guarantee that the result matched. Instead the
split peels one rename at a time off the *finished* tree; landing exactly on the
pin proves the decomposition is complete, and only then is it replayed forward.
The peel is scoped to the files holding the old name at the pin, which is what
makes file-local statics safe.

**Confirmed en route:** the original commit really was renames + comments and
nothing else — no behavioural change was hiding in it. (That check lived in a
`residue.py` which is now retired: its question cannot be re-asked once the
monolithic commit is gone, and `verify_series.py` check 1 is its permanent
successor, proving content-neutrality against the pre-split tree.)

**Corrections to the first survey:** the file renames number **18**, not 20 (15
git-detected renames + 3 that git reports as add+delete because the content
changed too much). The oot/LLM split is **64/141 + 1 typedef**, not 65/141.

**Scripts** (`tasks/adhoc/ocarina-split-rename-patch/`, all repo-relative):

| Script | Role |
|---|---|
| `_common.py` | shared helpers: the pin, the applied range, provenance stripping |
| `inventory.py` | first-pass rename table, parsed from the provenance comments |
| `build_rename_table.py` | adds the 2 underivable rows, computes scope + confidence |
| `add_decl_comments.py` | the declaration-tag pass; idempotent, safe to re-run |
| `rebuild.py` | the split itself — peel backwards, replay forwards |
| `completeness.py` | **gate**: 0 untraceable, 0 incomplete renames |
| `header_gap.py` | **gate**: 0 bare header declarations |
| `verify_series.py` | **gate**: content-neutral, one rename per commit, total |

At archive time `rebuild.py`, `add_decl_comments.py`, `inventory.py` and
`build_rename_table.py` are one-shots (their job is done — `git rm`); the three
gates are **reusable** and should be promoted to `tools/` so the next rename
batch is held to the same standard.

## Open questions

None — all three were settled above under standing discretion. The only
outstanding item is step 9, the maintainer's on-host build/run.
