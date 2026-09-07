# Ocarina: split the monolithic rename patch into one-rename-per-patch, and make every rename traceable at its declaration

**Status:** DONE — implemented and proven equivalent 2026-09-07; archived the same day.
An on-host rebuild remains available as optional confirmation, not a gate.
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
63 comments. That is **proven, not asserted**: `tools/prove_comment_only.sh` applies
the old patch and the new series side by side and shows no file changes line
count and every differing file is byte-identical once **gcc** strips the
comments — so the two build the same program.

## Context

### Read first

- **[`tasks/reference/ocarina/decomp-renaming.md`](../../../../../reference/ocarina/decomp-renaming.md)** —
  the method, the zeldaret/oot oracle, the provenance-comment convention, and
  every gotcha that has bitten. **This is the governing doc**; the work below
  must not contradict it, and any convention change (see Q1) belongs there.
- **[`tasks/ocarina-decomp-rename-and-cleanup.md`](../../../../../ocarina-decomp-rename-and-cleanup.md)** —
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

Every number below was measured, not estimated. The measuring scripts were
one-shots and were removed at archive (recoverable from git history); the live
figures now come from `n64/OcarinaOfTime/tools/check_renames.py`.

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
pin's tree (checked during the survey — 69 residual lines, every one either a static-name
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
`RumbleMgr` typedef; 3 of the 66 were commented-out placeholders and are
not declarations, leaving 63 real sites). Run
`n64/OcarinaOfTime/tools/check_renames.py declarations` for the live figure.

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

All steps are complete. Every gate below is re-runnable; the reusable ones were
promoted to `tools/` and `n64/OcarinaOfTime/tools/` afterwards (see Notes), so
they are named here by their **final** locations.

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
      now `tools/tag_declarations.py`, idempotent).
      `check_renames.py declarations` reports **0 bare sites**. The first sweep
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
      the target. `check_renames.py` still reports 0 untraceable / 0 incomplete.
- [x] **8. Updated [`tasks/reference/ocarina/decomp-renaming.md`](../../../../../reference/ocarina/decomp-renaming.md)**
      with the declaration-tag rule, the type-rename rule, and a new "One rename
      per commit" section, so the remaining ~3,988 symbols are done this way
      from the start. Also updated `n64/OcarinaOfTime/CLAUDE.md`'s patch list.
- [x] **9. Proved the two series compile to the same program.**
      `tools/prove_comment_only.sh` applies the OLD single patch and the NEW 225-patch
      series to two scratch branches off the pin, then shows (a) only 5 files
      differ at all, (b) **no file changes line count** — so `__LINE__`/
      `__FILE__` and the debug prints built on them are untouched — and (c)
      each differing file is **byte-identical once gcc strips the comments**
      (`gcc -fpreprocessed -dD -E -P`). The compiler receives an identical
      token stream from an identical number of lines, so the object code is
      the same. The equivalence rests on a compiler, not on a regex here.
- [x] **10. Promoted the reusable scripts to tools** and gated the conventions
      repo-wide — see Notes for the inventory, and **How it went §4** for what
      promotion exposed (a type rename that no tool could discover, and a peel
      bug that deleted a code line carrying a marker).
- [ ] **11. Maintainer's on-host build/run** (optional). The pre-split tree was
      build- and run-verified on-host 2026-09-01, and step 9 proves the split is
      compile-identical to it, so a rebuild is confirmation, not a gate.

## Notes / decisions

The chronological record of what was decided and why is in **How it went**
below; this section holds only what a future reader needs as reference.

**Scripts.** The reusable ones were **promoted to `tools/`**; the one-shots were
**removed at archive** — they were committed during the task (that is the audit
trail for the 225-commit diff) and are recoverable with
`git log --diff-filter=A -- tasks/adhoc/ocarina-split-rename-patch/`. The
*method* they implemented is written up in
[`tasks/reference/imps/splitting-a-patch-series.md`](../../../../../reference/imps/splitting-a-patch-series.md).

| Promoted | Role |
|---|---|
| `tools/prove_comment_only.sh` (imps root) | **Cross-project.** Proves two refs differ only in comments: no line-count change, then gcc strips comments and compares. Also the gate for a `book/` stream (`--allow-line-shift`). |
| `tools/check_comment_only_streams.sh` | Runs the above over every project's `book/` streams, both lanes. |
| `tools/check_patches_apply.sh` | Every project's series still applies onto its pin — the gate for the repo's primary goal. |
| `n64/OcarinaOfTime/tools/check_renames.py` | Gates the renaming conventions: `traceable`, `declarations`, `series`, `all`. |
| `n64/OcarinaOfTime/tools/tag_declarations.py` | Adds the short declaration tags. Idempotent. |
| `n64/OcarinaOfTime/tools/renames_common.py` | Shared helpers; discovers renames from the tree's provenance comments, so no external table. |

| One-shot (removed at archive) | Role |
|---|---|
| `_common.py` | helpers for the one-shots below |
| `inventory.py` | first-pass rename table parsed from the provenance comments |
| `build_rename_table.py` | adds the 2 underivable rows, computes scope + confidence |
| `add_decl_comments.py` | the split's tagging pass, incl. the long marker for the `RumbleMgr` type rename |
| `rebuild.py` | the split engine — peel backwards, replay forwards |

**Conventions this task changed**, all recorded in
[`tasks/reference/ocarina/decomp-renaming.md`](../../../../../reference/ocarina/decomp-renaming.md):
the declaration-site tag, the append-never-insert rule, type renames, and one
rename per commit. The remaining ~3,988 un-named symbols are to be done that way
from the start.

## How it went — the decision record (harvested pre-squash, 2026-09-07)

The squash collapses five working commits, so this is the record of what was
decided and why, in order. Each heading names the working commit it came from.

### 1. Survey (`c18b96b`) — the gap was not where it looked

Measuring the monolith first changed the shape of the task. **Every one of the
206 renames already had a provenance comment**, and none was half-finished — so
the "add the missing comments" job was not what it appeared. What was actually
missing was the **declaration** side: the comments sat at each symbol's
definition, leaving `soh/include/functions.h` — where a reader meets a name
first — with no way to tell an upstream name from a guess. Also established
here: the commit was renames + comments and nothing else, so the split had no
behavioural change to untangle.

Two hazards surfaced that shaped everything after: **133 of 206 symbols are
file-local statics** (`sColChkInfoInit` already exists in 60 other files, so a
tree-wide rename would corrupt them), and **two distinct old symbols share one
new name** (`sTentacleTextures`).

### 2. The split (`faaf704`) — peel backwards, replay forwards

**Method decision.** Re-deriving each rename forwards from the pin would have
given no guarantee the result matched. Instead the split peels one rename at a
time off the *finished* tree; landing exactly on the pin proves the
decomposition is complete, and only then is it replayed forward. Each peel is
scoped to the files holding the old name **at the pin**, which is what makes the
file-local statics safe.

**Three judgement calls, taken under standing discretion:**

- *Short inline declaration tag*, not the full comment repeated —
  `// was func_800C3C20 [oot]` / `[LLM:HIGH]`. Same grep handle, without adding
  63 long lines to two shared headers. Rationale and citation stay at the
  definition.
- *One commit per symbol, strictly.* Letting a file rename absorb the symbols
  defined only in it would have cut 225 commits to ~150 and read better by
  subsystem, but it re-couples exactly what the split exists to separate: 141 of
  206 names are guesses, and a wrong guess must cost one `git revert`.
- *`residue.py` retired.* Its question — "is the monolith renames-only?" —
  cannot be re-asked once the monolith is gone. Its permanent successors are the
  `series` check in `check_renames.py` and `tools/prove_comment_only.sh`.

### 3. The equivalence proof (`a8497c2`) — a challenge that found a real hole

Asked to *prove* the patches give the same result, the existing claim turned out
to be weaker than stated. It was tree-equality; the type rename's comment had
been inserted as a **new line** in `z64.h`, which shifts `__LINE__` for
everything below it. Small, but it meant "only comments differ" was not the same
as "compiles identically".

**Fix: every tag is appended to an existing line, never inserted.** No file
changes line count, so `__LINE__`/`__FILE__` are untouched. The proof then rests
on a compiler rather than a regex here: `gcc -fpreprocessed -dD -E -P` strips
the comments and the results are compared. Also found here: 3 of the 66 sites
were commented-out placeholders (`// ? Audio_ResetData(?);`), which are not
declarations — skipped, leaving 63.

### 4. Promotion to tools (`1434ca5`) — and what promotion exposed

Making the checkers work from a *clean* tree exposed that the type rename
`UnkRumbleStruct` → `RumbleMgr` carried only a short tag, so
`git grep 'LLM generated name'` could not see it and nothing could discover it
from a pristine baseline. It now carries the long marker on the line that names
it, still with no line inserted. Fixing that surfaced a second bug: peeling a
marker that sits on a *code* line was deleting the declaration itself.

Generalising the proof tool for the other games found the **`book/` streams**,
which are comment-only by contract and had no gate — and which *cannot* pass the
no-line-shift check, because a `doc-region` marker must occupy its own line.
Hence `--allow-line-shift`: strict for stream reshapes, relaxed for book
streams.

**Cross-stream ordering.** The renames must apply before any later stream, which
contradicts the family's "streams commute" invariant. Rather than merge streams
— which would destroy the upstreamability that is the whole reason streams exist
— ordering was made explicit in `patches/ORDER`, honoured by `apply.sh`.
Grouping and ordering stay independent. See `n64/CLAUDE.md`.

### 5. Repo-wide follow-through (`2026fb8`)

`tools/check_patches_apply.sh` turns the repo's primary goal — the patches keep
applying as upstream moves — from a claim into a gate across all four games.
`runDir/` was documented as sacred in the master `CLAUDE.md`, and the guarantee
validated against real save data and a 547 MB texture pack that survived many
`reset --hard`/`clean -fd` cycles. Fixing one bug on the way:
`check_comment_only_streams.sh` had been leaving checkouts parked on scratch
branches instead of restoring them.

### Corrections to the first survey

The file renames number **18**, not 20 (15 git-detected plus 3 that git reports
as add+delete because the content changed too much). The provenance split is
**64 oot / 141 LLM / 1 typedef**, not the 65/141 recorded on 2026-07-31; that
off-by-one was corrected in
[`decomp-renaming.md`](../../../../../reference/ocarina/decomp-renaming.md) too.

## Open questions

None. The three that existed were settled under standing discretion — see
**How it went §2**. The only outstanding item is step 11, the optional on-host
build/run.
