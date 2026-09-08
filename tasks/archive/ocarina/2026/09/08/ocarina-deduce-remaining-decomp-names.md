# Ocarina: deduce names for the symbols zeldaret/oot also leaves address-named

**Status:** in-progress — **steps 1-8 are DONE, including step 8's in-scope
half.** `z_en_zl2.c` (118 names) and `z_en_zl3.c` (203 names) are both named and
compiling; `z_player.c` stays out of scope. Both work-lists are exhausted:
`next_symbols.py` and `gap_symbols.py` report zero actionable work, and the only
address-named symbols left in the tree are the four in the declared exclusions
(`func_800FBCE0` / `func_800FBFD8` in `code_800FBCE0.c`, `func_80837C0C` /
`func_80838940` in `z_player.c`). Builds clean; 3,799 patches.
**Step 9 is done too** (2026-09-08): the series was regrouped from 3,799
one-rename commits into **488 commits, one per definition file**, proven
content-neutral (identical tree SHA to the pre-squash tip). The task is
complete pending the maintainer's review.
**Priority:** 5
**Difficulty:** 8
**Started:** 2026-09-07

## BLUF

The zeldaret/oot oracle is **exhausted**: 770 of 4,235 address-named symbols
(18.2%) now carry upstream names, and every remaining candidate has been checked
against two oot revisions. **2,719 of the 3,465 that remain are address-named in
oot too**, so
there is no authoritative name left to adopt — each needs one *deduced* from its
body and callers, marked `[LLM:HIGH]` or `[LLM:GUESS]` with the evidence. This
task is that work. "Done" is not realistically all 3,470; done is a sustainable
batch loop that keeps the tree compiling and every name traceable, run until the
maintainer calls it.

## Context

### Read first

- **[`tasks/reference/ocarina/decomp-renaming.md`](../../../../../reference/ocarina/decomp-renaming.md)**
  — the governing conventions: the provenance-comment forms, the declaration
  tag, one rename per commit, the safe-rename mechanic, and the gotchas that
  have actually bitten. **Do not deviate from it.**
- **[`tasks/archive/ocarina/2026/09/08/ocarina-decomp-rename-and-cleanup.md`](ocarina-decomp-rename-and-cleanup.md)**
  — the parent effort, including the 2026-09-07 oracle batches and how to
  rebuild in-sandbox. This task is its remainder.
- **`tasks/adhoc/ocarina-decomp-rename-and-cleanup/oracle.tsv`** — the work-list.
  Filter `verdict == BOTH`; those are the ones needing deduction.
- **[`tasks/reference/ocarina/decomp-map.md`](../../../../../reference/ocarina/decomp-map.md)**
  — where OoT subsystems live; essential for guessing what a function does.

### Current state (2026-09-07)

- The `personal` stream is **789 patches**, one rename per commit, applying
  clean onto pin `acdbc651d`.
- The patched tree **compiles**: `soh.elf` links, 0 errors.
- Every name currently in the tree is either upstream-sourced (629, verified) or
  an LLM guess from the maintainer's 2026-07-31 batch (142); 629 + 142 = 771, one
  more than the 770 renamed symbols because the `RumbleMgr` type rename carries
  a marker I authored for a name that was already in the tree. **Nothing in this
  task's scope has been guessed yet** — that starts here.

### What remains, and why the oracle cannot help

| Verdict | Count | Meaning |
|---|---|---|
| `BOTH` | **2,719** | Address-named in oot too. **This task.** |
| `UNSAFE` | 23 | Alignment found no safe mapping through drift |
| `MISMATCH` | 13 | Bodies diverged past both the literal and structural thresholds |
| `NOFILE` | 2 | No oot counterpart: `code_800FBCE0.c` (RCP) and `system_heap.c` |
| `ADOPT` | 1 | `EnDivingGame_TalkDuringMinigame` — oot's name is already taken by a different SoH function; needs a hand-picked alternative |

The 38 non-`BOTH` rows are worth one more look **before** guessing — they failed
mechanically, not for lack of an upstream name. But the cheap levers are already
pulled: two oot revisions are queried, the audio paths are corrected, and both
a body and a structural comparison run. Expect little.

### Decisions already made

- **Bar for naming: only where the body supports a specific claim about what
  the function does; otherwise leave the symbol address-named** (William
  Emerison Six <billsix@gmail.com>, 2026-09-07 — *"keep going until you have to
  start guessing"*). This yields fewer names of higher quality. The alternative,
  naming everything and leaning on `[LLM:GUESS]` to carry the doubt, was
  **rejected**: it fills the tree with labels nobody should trust.
- **Guessed names are acceptable where they clear that bar, provided each is
  marked with its confidence and reason.** Form:
  `// LLM generated name (HIGH|GUESS), was <addr>: <reason from the code>` at
  the definition, plus the short `// was <addr> [LLM:HIGH]` tag at every header
  declaration.
- **A name invented without reading the function is the one outcome that
  actively damages a decomp.** Bulk-generating plausible names would poison the
  tree with confident wrong labels that later readers trust. Read the body and
  the callers, or leave the symbol alone.
- **One rename per commit**, so a wrong guess costs one `git revert`.
- `code_800FBCE0.c` (RCP) was deliberately skipped by the 2026-07-31 batch —
  oot leaves its two functions address-named too and there is no oracle. Skip it
  again unless someone genuinely understands the code.

### Shape of the work

153 files hold the 2,719. The distribution is extremely skewed:

- 4 files have exactly 1; ~30 have ≤3 — **start here** (richest context per
  symbol, lowest risk, per the documented method).
- The tail is brutal: `z_player.c` alone has **390**, `z_en_zl3.c` 201,
  `z_en_zl2.c` 118. Those three are ~28% of the work and should come last, if at
  all — `z_player.c` is 16.6k lines and its action machine is the hardest code
  in the game to name confidently.

## Goal

Give meaningful names to the decomp symbols that upstream also leaves
address-named, working file-by-file from the smallest, deducing each name from
the function's body and callers rather than its shape, marking every one with
its confidence and the reason, and keeping the tree compiling throughout. The
measure of success is not the count renamed but that a later reader can trust —
or overturn — every name, because the evidence for it is recorded next to it.

## Plan

- [x] **0. Harvest the remaining oracle-backed names.** DONE 2026-09-07: adding
      a second oot revision cut the mechanical failures 146 → 38 and recovered 5
      names. 38 rows (23 UNSAFE, 13 MISMATCH, 2 NOFILE) remain and are unlikely
      to yield more.
- [x] **1. Pick the smallest-file batch** (`oracle.tsv`, `verdict == BOTH`,
      fewest per file). Roughly 30 files at ≤3 symbols each.
- [x] **2. For each symbol: read the body and every caller.** Name it for what
      it does. `HIGH` when the body makes it unambiguous; `GUESS` when the name
      is inference. If neither, leave it.
- [x] **3. Apply with the safe-rename mechanic** — scope to the files holding
      the old name, collision-check, one commit per symbol, declaration tags in
      the same commit.
- [x] **4. Gate:** `n64/OcarinaOfTime/tools/check_renames.py all`.
- [x] **5. Build** (see the parent task for the in-sandbox recipe — copy the
      checkout out of the repo first).
- [x] **6. Regenerate the stream** and re-run
      `tools/check_patches_apply.sh OcarinaOfTime`.
- [x] **7. Log the batch here**, then repeat from step 1.
- [x] **8. DECISION POINT — reached only when the small files run out.** Three
      files hold ~28% of the remaining work: `z_player.c` (390),
      `z_en_zl3.c` (201), `z_en_zl2.c` (118). Do not decide their fate up front;
      decide here, with evidence the earlier batches will have produced:
      - How often did step 2 have to leave a symbol alone? A high rate on
        *easy* files is a strong argument against attempting the hard ones.
      - Did any earlier name have to be revised or reverted?
      - `z_player.c` is 16.6k lines and oot leaves it address-named after years
        of effort, which is itself evidence about the difficulty.

      **The default, absent a reason to change it, is to declare all three out
      of scope** and stop with the tree at whatever percentage the defensible
      work reached. A smaller set of trustworthy names beats a complete set of
      doubtful ones.

      **DECIDED 2026-09-08, with the evidence the batches produced.** The
      maintainer deferred the call. Split it, because the three files are not
      one kind of problem:

      - **`z_player.c` (407 names): OUT OF SCOPE, standing by the default.**
        Its unnamed functions are `Player_Action_*`-adjacent state machine
        internals. The evidence step 8 asked for points the wrong way here: the
        files that forced the most GUESS confidence were exactly the ones whose
        bodies only set unnamed fields (`z_en_niw.c`'s `unk_308`,
        `z_en_poh.c`'s `unk_845`), and `z_player.c` is that problem at 16.6k
        lines. zeldaret/oot leaving it address-named after years is the same
        evidence from a second source.
      - **`z_en_zl3.c` (203) and `z_en_zl2.c` (118): IN SCOPE.** These are
        cutscene actors of the same shape as `z_demo_im.c` (97 names) and
        `z_en_xc.c` (80), both finished in this session at mostly HIGH
        confidence. They dispatch through an action table, their helpers are
        cue checks and animation setups, and the naming schemes that worked
        there transfer directly. Nothing in the earlier batches argues against
        them; they were excluded for size, not difficulty.

      Doing those two also frees the four names currently stranded in
      `functions.h` — `func_80837C0C` and `func_80838940` stay stranded with
      `z_player.c`, and the RCP pair `func_800FBCE0` / `func_800FBFD8` stays
      with `code_800FBCE0.c`.

      **EXECUTED 2026-09-08.** Both in-scope files are done — see the batch-log
      entries below. `gap_symbols.py` now reports exactly those four excluded
      names and nothing else, so the deduction work is finished.
- [x] **9. FINAL STEP — squash the series into reviewable units.** DONE
      2026-09-08. See "Step 9 in full" for the plan and "Step 9 as executed"
      for what actually happened and the four decisions it required.

## Step 9 in full — squash the series into reviewable units

**Authorized by William Emerison Six <billsix@gmail.com>, 2026-09-08**, who gave
explicit permission to squash and interactively rebase the checkout's working
branch for this step. That permission is scoped to step 9 and to this session's
successor; it does not generalise (see the global "Git: I commit, you don't").

### Why this step exists

One rename per commit was the right way to **produce** the work. It isolates
variables: when a rename breaks something, the breakage localises to a single
symbol, which is exactly how the `z_en_insect.c` macro-continuation bug got
pinned to one commit out of three thousand. But it is the wrong granularity to
**review**. Nobody upstream wants to read thirty consecutive commits that rename
thirty entries of one function-pointer array.

Because the work was done at the fine grain, the boundaries between logical
units are already visible in the history and the reasoning is already written
down per symbol. So this step is a reading-and-regrouping job, not a
reconstruction.

### The reasoning in the commit messages is the point — none of it may be lost

**Every squashed commit must carry the full message history of the commits
folded into it.** For each symbol in the unit: its old name, its new name, and
the reason that name was chosen. A thirty-commit squash produces one commit
whose message opens with a header explaining the logical unit to an upstream
reviewer, and then preserves all thirty individual justifications beneath it.

The squash changes the **shape** of the history for review; it does not discard
what the history records. A reviewer gets one readable unit at the top and can
still see, symbol by symbol, why each name was deduced. Nothing is summarised
away, and nothing is dropped for brevity.

### The sequence

1. **Backup branch first.** `git branch -f squash-backup HEAD` in the checkout,
   then never touch it. It is the undo: `git reset --hard squash-backup`
   restores everything. Do this before any rewrite command runs.
2. **Group the patches into logical units.** Read `patches/personal/` in order
   and mark the runs that are one idea — a function-pointer array's entries, one
   file's per-page vertex tables, one actor's setup/action pairs. The worked
   example the maintainer pointed at: a run of roughly thirty commits each
   renaming one entry of the same array is **one** unit.
3. **Squash to those units**, each with an upstream-facing header plus the
   preserved per-symbol reasoning described above.
4. **Prove the rewrite changed history only, never content.** `git diff
   squash-backup HEAD` must be **empty** — byte-identical tree — and the diff
   from the pin `acdbc651d4b11e29518442d6875a3ec181414cfc` unchanged. If the
   tree differs at all, stop and investigate; something got dropped.
5. **Rebuild** and confirm `soh` still links clean.
6. **Regenerate `patches/personal/`** from the squashed history and re-run
   `tools/check_patches_apply.sh OcarinaOfTime`. The patches are the deliverable;
   the checkout is scaffolding.

### Three things that will bite, recorded before they do

- **`check_renames.py series` asserts one rename per commit, and will fail by
  design the moment the squash lands.** Decide its fate as part of this step:
  either relax it to accept a grouped commit whose subject and body cover every
  rename in it, or retire that check and keep the other two. Do not discover
  this mid-rebase.
- **There is no interactive editor in the container**, so a literal
  `git rebase -i` cannot run. Drive it with `GIT_SEQUENCE_EDITOR` (a `sed`
  one-liner over the todo list) or rebuild the history with `git cherry-pick -n`
  onto a temp branch — the technique that repaired eleven commits in place on
  2026-09-07. Commit signing is already off repo-locally via `fetch.sh`.
- **`runDir/` stays untouched.** It is a sibling of the checkout, so no git
  operation on the checkout can reach it; keep any `git clean` scoped to the
  source subtree rather than the whole tree.

## Step 9 as executed — 2026-09-08

> The reusable half of this section is harvested to
> [](../../../../../reference/imps/squashing-a-produced-series-for-review.md)
> — read that first if you are squashing another series; what follows is
> this series specifically.

**Result: 3,799 commits -> 488**, one per definition file, in the checkout
`n64/OcarinaOfTime/Shipwright/`. Branches left in place:

- **`squash-backup`** — the pre-squash tip, 3,799 commits. The undo:
  `git reset --hard squash-backup`. Never write to it.
- **`squash-rebuild`** — the regrouped history, 488 commits.

The script is `tasks/adhoc/ocarina-deduce-remaining-decomp-names/squash_series.py`,
saved because the "how" behind a 4,287-file diff is not recoverable from the
diff itself. It is re-runnable: it rebuilds the work branch from the pin every
time rather than stacking onto a previous run.

### Four decisions the step required

**1. The unit is the definition file, and units are runs of CONSECUTIVE
commits.** A commit's unit key is the file its provenance marker landed in —
the symbol's definition site. That answers the maintainer's worked example
directly (a function-pointer array's thirty entries all live in one file, so
they become one commit) and it gives a reviewer the natural unit: one file at a
time. 488 units, of which 156 are files carrying a single rename.

*Rejected: grouping every commit for a file globally* (which would give ~342
units instead of 488). It requires reordering commits, and the shared headers
`functions.h` / `variables.h` are touched by almost every unit — so partitioning
their content per unit means splitting the diff hunk by hunk. More risk for a
30% reduction that does not change the review experience, since the residue is
dominated by the 156 single-rename files either way. 83 files therefore appear
as more than one commit, because their renames were made in more than one batch.

**2. Trees were SET, not replayed.** Each unit commits with
`git read-tree --reset -u <last sha of the unit>` — pointing at a tree that
already exists in history — rather than `git cherry-pick`. No patch is applied,
so there is nothing that can conflict and nothing that can be silently dropped,
and the final tree is byte-identical to the pre-squash tip *by construction*
rather than by luck. The doc's step 4 proof still runs as a check, and passed.

**3. The reasoning is preserved per symbol; only the invariant boilerplate is
hoisted.** Each original message is subject + a name-source paragraph + an
optional `Reason:` + `Defined in <path>` + a closing paragraph. The closing
paragraph and most of the name-source text are **byte-identical across every
commit that shares a source type** — 36 distinct templates across 3,799
messages. Repeating that 203 times inside one commit message would bury the
reasoning rather than preserve it, so the squashed message states it once in a
header and then carries one entry per symbol:

```
  * func_80B5A1D0 -> EnZl3_DrawXlu
    deduced, confidence HIGH: sDrawFuncs[2]: SkelAnime_DrawFlex into
    POLY_XLU_DISP after Gfx_SetupDL_25Xlu, using this->alpha
```

Every per-symbol fact survives: old name, new name, source, confidence or the
upstream similarity score, and the reason. **This is enforced, not asserted:**
`check_lossless()` fails the run if any `Reason:` recorded in an original
message does not appear in its squashed unit. It earned its keep on the first
run by catching 12 genuine losses — `textwrap` was breaking hyphenated words
(`joint-sphere` -> `joint-` / `sphere`) across a newline, quietly altering the
recorded text. Fixed by disabling `break_on_hyphens` and `break_long_words`.

A file with exactly one rename keeps its **original message verbatim**; wrapping
a single symbol in a page of preamble would make it worse, not better. All 488
messages gained the `Co-Authored-By` trailer, which the unsquashed series lacked.

**4. `check_renames.py series` was relaxed, not retired.** The doc predicted it
would fail the moment the squash landed. In fact the failure mode was worse than
predicted: its `SUBJECT_RE` simply would not match a grouped subject, so every
grouped commit would be **skipped** and the check would report OK having
verified nothing — a green gate over zero work. It now accepts both commit
shapes: a single-symbol subject, or a grouped commit that states its count in
the subject and lists `  * <old> -> <new>` entries in its body, with the count
and the entries required to agree. The property being gated is unchanged and is
the one that always mattered: **no rename may happen that its commit message
does not account for**, and every claimed rename must be total. That the
regrouped history claims **3,781** renames — exactly the number the unsquashed
series performed — is an independent cross-check that nothing fell out.

The generalised check reported two false failures on its first run, both worth
knowing about: SoH forks some upstream functions and names the fork after the
same address with a suffix (`func_808C1554_Raw`, `func_80AB70A0_nocutscene`),
which `ADDR_RE`'s closing `\b` cannot match — so those names never appear in the
"symbols that disappeared" set however correctly they are renamed. The claimed
set is now filtered through `ADDR_RE` before that comparison, and the suffixed
names are still held to account by the totality scan, which greps the literal
name. Recorded in
[`tasks/reference/ocarina/decomp-renaming.md`](../../../../../reference/ocarina/decomp-renaming.md)
because a false failure of this shape is indistinguishable at a glance from a
dropped rename.

### Should MORE have been collapsed? Measured, 2026-09-08

488 commits cover 392 distinct files, so 65 files appear as more than one
commit — `z_en_ik.c` as six (36, 2, 2, 10, 11 and 2 symbols), `z_en_ru1.c` as
five. Gathering each file into one commit would give **392**. Tempting, and the
right instinct: a reviewer who wants to check `z_en_ik.c` should not have to
visit six places.

**Tested rather than assumed, and the answer is no.** Replaying all 3,799
commits in file-grouped order (3,474 of them change position — a near-total
reshuffle) conflicts after **38 commits**: renaming `func_800F4524` in
`audio_general.c` also rewrites call sites in `z_en_go2.c`, and the reorder had
already moved a `z_en_go2.c` commit across it. That is structural, not bad luck:
a unit's changes are not confined to its key file. The median unit touches one
file; the largest touches 138.

Beyond the conflicts, the reorder would cost a property worth more than the
tidiness: with the original order kept, **every one of the 488 commits is a tree
the unsquashed history actually passed through**, so the series stays bisectable
and each commit compiles. Reordering can also strand an intermediate state with
two symbols sharing a name, wherever a collision-driven rename gets moved ahead
of the commit that caused the collision.

Nor is a coarser axis better. The size profile is healthy — 10 commits carry 914
renames, 22 more carry 767, while the 157 single-symbol commits are simply files
with one address-named symbol (100 of them actor overlays). Grouping by
directory would fuse unrelated actors into thousand-symbol commits; there is no
unit between "file" and "everything".

The experiment script is not kept: it answered one question, its finding is
recorded here and in
[`../../../../../reference/imps/squashing-a-produced-series-for-review.md`](../../../../../reference/imps/squashing-a-produced-series-for-review.md).

### The commit wording was wrong on the first pass, and was fixed

The maintainer read `soh: name the 203 address-named symbols **in**
z_en_zl3.c` and asked the right question: does that mean the commit touches only
that file, in which case you could not check one out and build it?

The premise was wrong but the reading was fair. The definition file **names** a
unit; it does not **bound** it. Every commit carries the whole rename —
declaration, definition and every call site — so the units touch a mean of 2.4
files, and `z_actor.c`'s 63 symbols reach **138** files including
`functions.h`, `variables.h` and a dozen `soh/soh/Enhancements/*.cpp`. 363 units
do touch exactly one file, but those are file-statics with no header declaration
and no external caller, so one file is the complete rename.

Verified directly rather than argued: for each of the 487 symbol-rename commits,
grep **that commit's tree** for the old names its own message retires —
**0 commits leave a dangling reference**. Every commit is a checkout-and-build
point.

The patches were regenerated 2026-09-08 with the subject reading `symbols
**defined in** <file>`, the preamble saying outright that the file names the
unit rather than bounding it, and a per-unit reach line in the body
(`All 63 are defined in soh/src/code/z_actor.c; updating their references
touches 138 files in total.`). 98 units advertise cross-file reach, 233 state
they are self-contained, 157 are single-symbol commits keeping their original
message.

Two bugs in the squash script surfaced during that re-run, both recorded in the
reference doc: it read `HEAD` rather than `squash-backup`, so re-running it
re-squashed its own output into 488 units of one (it now refuses when the
grouping yields fewer than two multi-item units); and changing the subject broke
`check_renames.py`'s `GROUP_RE`, which would have **skipped all 331 grouped
commits and reported green** — the same silent-skip trap the original
generalisation was written to avoid, re-entered from a different direction. The
gate now accepts both spellings.

### Verification

| check | result |
| --- | --- |
| `git diff squash-backup squash-rebuild` | empty |
| tree SHA, both branches | `881936bc3` — identical |
| `git diff <pin> <branch>`, both branches | identical sha256 |
| every recorded `Reason:` survives | enforced by `check_lossless()` |
| build | `ninja: no work to do` — byte-identical to the tree that linked clean |
| `tools/check_patches_apply.sh OcarinaOfTime` | 488 patches apply cleanly onto the pin |
| `check_renames.py all` (on the `git am`-ed patches) | ALL CHECKS PASSED — 488 commits, 3,781 renames claimed |
| `runDir/` | untouched — it is a sibling of the checkout |
| `make image` + `make build` (ubuntu-22.04 CI mirror, nested podman) | 1,581/1,581 targets, 0 errors, `soh.elf` linked |
| `make appimage` | `out/soh.appimage`, 31 MB, `Ship-9.2.3-jammy` |

The game has **not been run**: launching it writes config, logs and saves into
`runDir/`, which the project `CLAUDE.md` declares sacred, so the run stays the
maintainer's.

**imps' own history was not rewritten.** All of the above happens inside the
gitignored `Shipwright/` checkout; imps sees one ordinary commit that replaces
3,799 patch files with 488.

## Measuring progress — use the PLANNED denominator

`tasks/adhoc/ocarina-decomp-rename-and-cleanup/progress.py` reports against the
scope we intend to work on, not against every address-named symbol. (It lived in
`/tmp` for batches 1-8 and was saved into the repo on 2026-09-07, together with
`next_symbols.py`, which prints the remaining work-list smallest-file-first.
Both run from the imps repo root.) Quoting the raw fraction understates the
position by counting work we have already decided not to do:

| Excluded by decision | count |
|---|---|
| the 3 huge files (`z_player`, `z_en_zl3`, `z_en_zl2`) | 720 |
| segmented asset addresses (`D_0x…`, not RAM — need asset-pipeline edits) | 5 |
| `code_800FBCE0.c` (RCP, skipped since 2026-07-31) | 1 |

**Planned scope 3,509 of 4,235.** At 1,048 renamed that is **29.9% of planned**
(24.7% of everything). Projecting the observed abstain rate over the ~1,976
still on the work-list gives an expected end state of **~3,000 of 3,509 (86%)**,
with ~500 left honestly address-named and 726 out of scope.

**The work-list is smaller than the planned denominator, and that is expected.**
`oracle.tsv` is regenerated as work lands, so it holds only what is *still*
unnamed; it is not the original census. Never compute progress as
"oracle rows renamed / oracle rows" — that mixes a shrinking numerator with a
shrinking denominator and reported 9.9% at a moment the real figure was 29.9%.
`progress.py` counts symbol-rename commits on the series against the fixed
3,509, which is the honest ratio.

## Batch log

### Batches 150-151 — 2026-09-08: the two Zelda cutscene actors, 321 names

Step 8's in-scope half. Both files are the same actor written twice — Zelda in
the Ganon's-tower escape (`z_en_zl3.c`) and its sibling (`z_en_zl2.c`) — and
both dispatch every frame through three tables: `sActionFuncs`,
`sOverrideLimbDrawFuncs`, `sDrawFuncs`. Reading the tables first, before any
individual body, is what made the files tractable: a function's index in
`sActionFuncs` IS its name, and the setup that installs `this->action = N`
pairs with it unambiguously.

**Batch 150 — `z_en_zl2.c`, 118 names.** Schemes: `EnZl2_Action0`..`Action35`
by table position; `EnZl2_SetupActionN` for the unconditional setups and
`EnZl2_SetupActionNOnAnimDone` / `...OnCueEnd` for the guarded ones; the hair
physics as `EnZl2_StepHairYaw` / `Pitch` / `Roll` plus
`EnZl2_OverrideLimbDrawHair`; eye animation as `EnZl2_ShutEyes` /
`OpenEyes` / `ShutEyesToEye5` / `OpenEyesFromEye5`; draws as
`EnZl2_DrawNothing` / `DrawOpa` / `DrawXlu`. One collision:
`EnZl2_OverrideLimbDraw` was already the dispatcher's name, so the table entry
became `EnZl2_OverrideLimbDrawHair` — recorded in its reason.

**Batch 151 — `z_en_zl3.c`, 203 names, and the debug strings are an oracle.**
The single most valuable find in this file was that it still carries its
original Japanese `osSyncPrintf` debug strings, and several of them name the
enclosing function outright:

| debug string | function | name adopted |
| --- | --- | --- |
| `En_Zl3_Actor_inFinal_Init` | `func_80B54FB4` | `EnZl3_InitInFinal` |
| `En_Zl3_inFinal_Check_DemoMode` | `func_80B55444` | `EnZl3_CheckDemoModeInFinal` |
| `En_Zl3_Actor_inFinal2_Init` | `func_80B55780` | `EnZl3_InitInFinal2` |
| `En_Zl3_inFinal2_Check_DemoMode` | `func_80B564A8` | `EnZl3_CheckDemoModeInFinal2` |
| `En_Zl3_Get_path_info` | `func_80B56F10` | `EnZl3_GetPathInfo` |

Those five are HIGH on the strongest evidence available short of an upstream
name: the function says what it is called. **Grep a decomp file for its debug
strings before deducing anything** — it costs one command and can hand you the
original names for free. (Recorded as a durable rule in
`tasks/reference/ocarina/decomp-renaming.md`.)

The rest followed the zl2 schemes deliberately, so the two sibling files read
the same way: `EnZl3_Action0`..`Action39`, `EnZl3_SetupActionN`,
`EnZl3_ChangeAnimOnAnimDone1`..`13` (numbered by definition order, with the
paired action named in each reason — one of them is called from two different
actions, which is why the action number could not be the discriminator), the
three hair springs mapped by which Euler component `EnZl3_OverrideLimbDrawHair`
feeds them (`sp30.y` → Yaw, `sp30.x` → Pitch, `sp30.z` → Roll), and the ten
file-static data symbols named from their single use each.

Both files: `check_renames.py all` green, `soh.elf` relinked clean.

### Batches 136-149 — 2026-09-08: the census-gap pass, 614 -> 0

The second pass ran to completion the same way as the first: read the code, name
per symbol, one rename per commit. `gap_symbols.py` drove it, and it is the
durable sibling of `next_symbols.py` -- where that one replays the census,
this one reads the checkout, which is what made the gap visible at all.

**The gap turned out to be four distinct populations, not two.** The task doc
had recorded two (function-local statics, census-missed file-scope symbols).
The scan found two more:

- **Generated `.inc` data files the census never walked.**
  `z_onepointdemo_data.inc` alone held 97 names and `z_camera_data.inc` 23.
  These named cleanly because every one maps to a one-point cutscene id through
  the switch in `z_onepointdemo.c`, so they became `sCs3050AtPoints`,
  `sCs4100KeyFrames` and kin -- the id is the discriminator, and it is a checked
  fact rather than a guess.
- **OTR asset identifiers, which must NOT be renamed.** `soh/assets/**/*.h`
  declares names like `D_809AD278` as
  `static const char D_809AD278[] = "__OTR__overlays/ovl_Elf_Msg/D_809AD278"`,
  so the identifier IS the archive key: renaming it renames nothing in the C and
  breaks the lookup. That is the same reasoning that put segmented addresses out
  of scope, so `gap_symbols.py` now derives the exclusion list from the asset
  headers rather than hard-coding it. Sixteen names fall in this class.

**Function-local statics named honestly by the function that owns them.** The
biggest group was scratch state kept static to stay off the N64 stack --
`z_collision_check.c`'s thirty are the pure case, where each AC check splits a
quad into two triangles and records one hit position. They became
`sJntSphVsQuadTri0`, `sCylVsQuadHitPos` and so on: the enclosing function names
the pair, and the reason says which of the two colliders each triangle came
from.

**A recurring find worth recording: dead copies.** Several actors declare a
static, copy it into a local, and never read the local -- `z_en_rd.c` does it
twice, six symbols' worth. Those are named `sUnusedWalkPos` and kin at GUESS,
with the reason stating the checked fact (the copy is never read) rather than
guessing at the effect they once fed.

**Collisions rose sharply in this pass**, because so many of the names are the
same idea in different overlays (`sFocusOffset`, `sSwordTipOffset`,
`sHeadFocusOffset`, `sCursorColorSets`, `sEquipAnimTimer`). Each was renamed with
the clash named in the reason -- `sDodongoFocusOffset`, `sStalfosSwordTipOffset`,
`sGoHeadFocusOffset`, `sPageCursorColorSets`, `sEquipAnimPhase`. Two were real
pre-existing names rather than same-batch clashes (`sSeqFlags` in
`audio_general.c`, `sEquipAnimTimer` in `z_kaleido_item.c`), which is why the
tool's collision check has to be tree-wide and not per-batch.

**What is left, precisely.** Four distinct names, all defined in the declared
exclusions: `func_800FBCE0` and `func_800FBFD8` in `code_800FBCE0.c`, and
`func_80837C0C` and `func_80838940` in `z_player.c`. They surface in
`functions.h` and in two call sites (`main.c`, `sched.c`); renaming a
declaration without its definition would split the pair, so they wait on the
step 8 decision along with the files themselves.

### Batches 103-135 — 2026-09-07/08: the planned work-list reaches zero

Worked the remaining files in one run, from `z_en_test.c` (18 names) up to
`z_demo_im.c` (97). `next_symbols.py` now reports **files: 0 symbols: 0** — every
symbol the 4,235-entry census marked as needing deduction, minus the declared
exclusions, has a name. 3,025 rename commits, 3,043 patches, `check_renames.py
all` green, `soh` builds clean.

Files finished in this stretch: `z_en_test.c`, `z_en_du.c`, `z_player_lib.c`,
`z_boss_tw.c`, `z_en_ko.c`, `z_bg_jya_cobra.c`, `z_bg_spot16_bombstone.c`,
`z_en_niw.c`, `z_en_zl4_cutscene_data.c`, `z_en_zl1_camera_data.c`,
`z_bg_spot18_obj.c`, `z_demo_6k.c`, `z_boss_ganon2_data.c`, `z_demo_go.c`,
`z_en_heishi2.c`, `z_en_sw.c`, `z_en_nb.c`, `z_en_rl.c`, `z_demo_gj.c`,
`z_bg_bdan_switch.c`, `z_en_bigokuta.c`, `z_en_poh.c`, `z_en_elf.c`,
`audio_general.c`, `z_boss_ganon2.c`, `z_en_owl.c`, `z_kaleido_scope_PAL.c`,
`z_demo_gt.c`, `z_actor.c`, `z_en_po_sisters.c`, `z_en_xc.c`, `z_demo_im.c`.

**Naming schemes that earned their keep on the repetitive files.** Several
overlays are dozens of near-identical helpers, and inventing a distinct
descriptive name for each would have been fiction. Three honest schemes carried
them, each stating the discriminator in the reason:

- **Table position.** `z_demo_gt.c`'s sixty-odd effect steps belong to eight
  collapsing tower pieces, so they are `DemoGt_SpawnDustParams2A` and kin --
  the params value is the piece, the letter its order in that piece's effect
  list, and each reason gives the cutscene frame window that distinguishes it.
- **Action index.** `z_demo_im.c` and `z_en_rl.c` dispatch through an action
  table, so their entries are `DemoIm_Action0` .. `DemoIm_Action30`, with the
  reason naming the beat each covers. `z_en_xc.c`'s guard wrappers became
  `EnXc_NextAfterAction30`, the reason spelling out that they fire only when a
  shared step has already moved the action off the expected one.
- **Slot number.** `z_kaleido_scope_PAL.c`'s four per-page vertex tables became
  `sPageVtxX0` .. `sPageVtxX5` under `sPageVtxX`, because the pages they index
  are not named anywhere in the file either.

**Four collisions, each renamed with the reason recorded:** `Audio_RestorePrevBgm`
-> `Audio_RestoreStackedBgm`, `sUnusedDebugValue` -> `sUnusedAudioDebugValue`
(z_debug.c owns the plain name), `EnXc_SetupIdleInNocturne` ->
`EnXc_SetupIdleAfterNocturneFall`, and the earlier `sCsCameraAngle` pair, which
turned out not to collide at all because both are file-static.

**The second pass is now the remaining work, and it is bigger than expected.**
A fresh scan of the checkout -- ignoring the census, reading the code with
comments stripped -- finds **614 address names still in code** outside the three
huge files. These are exactly the two gaps recorded above: statics declared
inside function bodies, and files the census never walked (the generated
`z_onepointdemo_data.inc` alone holds 97, `z_camera_data.inc` 23).
`tasks/adhoc/ocarina-decomp-rename-and-cleanup/gap_symbols.py` generates that
work-list the same way `next_symbols.py` generates the first.

### Batches 25-102 — 2026-09-07: 832 more names (1,880 of 3,509 planned, 53.6%)

The small files ran out, so this stretch is the middle of the distribution: ~155
files, mostly actor overlays of 5-20 symbols each, plus the first of the big
shared engine files (`z_camera.c`, `z_actor.c`, `z_parameter.c`, `z_bgcheck.c`,
`z_play.c`, `z_kankyo.c`, `z_rcp.c`, the four `audio_*.c`). Actor overlays stay
the fastest reading per symbol — follow the `actionFunc` chain and the state
machine names itself — while the engine files needed the surrounding subsystem
read first and produced the session's only real name collisions.

**Collisions rejected by the tool's duplicate check, and what they became.**
Each was renamed with the reason recorded in the commit: `WaterBox_GetSurface2`
-> `WaterBox_GetSurface3`, `Camera_BGCheckInfo` -> `Camera_BGCheckLine`,
`EnGo_UpdateTalking` -> `EnGo_RunTalkUpdate`, `EnGuest_Update` ->
`EnGuest_UpdateMain`, `EnSkj_SetupResetFight` -> `EnSkj_SetupLookAround`,
`DoorWarp1_AdultWarpOut` -> `DoorWarp1_AdultWarpTrigger`, `sZeroVec` ->
`sRoomZeroVec`.

**Bug found and fixed: a multi-line prototype's tag goes on its CLOSING line.**
Eleven `EffectSsDust_Spawn*` prototypes in `soh/include/functions.h` wrap onto a
second line, so the renamed name sits on a first line ending in `,`. The tagger
inferred "definition vs declaration" from that punctuation, read the wrapped
prototype as a definition, and skipped the tag entirely — leaving eleven
declarations untagged. This failure is the mirror image of the backslash bug
above: the **build stayed clean** and the *gate* went red, where the backslash
bug did the reverse. Three fixes, all durable:

1. `apply_deduced_names.py` now treats every top-level match in a `.h` as a
   declaration (a header holds only prototypes, so the punctuation guess was
   never needed there), and defers the tag to the line that closes the prototype
   with `;`.
2. `check_renames.py`'s declarations check accepts a tag on the closing line
   when the name-bearing line ends in neither `;` nor `{`.
3. The rule is written into `tasks/reference/ocarina/decomp-renaming.md`
   alongside the backslash rule.

The eleven existing commits were repaired **in place** rather than with a fixup
commit, to preserve one-rename-per-commit:
`tasks/adhoc/ocarina-decomp-rename-and-cleanup/tag_multiline_decls.sh` marks them
`edit` in a non-interactive rebase and amends each. Amending a commit shifts the
context that later commits' diffs expect, so the replay conflicts in this header
— every such conflict resolves identically (take the incoming version, re-run the
tagger, which only tags prototypes whose new name is already present and is
therefore idempotent), and the script does that automatically. Verified by
`git diff backup-decltags HEAD`: exactly 11 lines changed, all tag additions, and
the commit count unchanged at 1,898.

**Two scope gaps found and deliberately deferred.** Neither is in the 4,235-symbol
census, so naming them now would make the progress fraction incomparable; both get
their own pass at the end:

- `D_`-named statics declared *inside* a function body (e.g. `D_809B3270` in
  `EnAnubiceFire_Draw`) — the census only walked file scope.
- File-scope symbols the census missed outright (e.g. `D_808A9508`).

The one deliberate exception was `func_808C1554_Raw`, renamed alongside
`func_808C1554` so its name would not point at a symbol that no longer exists.

### Batches 9-24 — 2026-09-07: 202 more names (1,048 of 3,509 planned, 29.9%)

Worked strictly smallest-file-first off `next_symbols.py`. The shape of the work
changed as the small files ran out: batches 9-19 were mostly one- and two-symbol
*data* files (collider inits, texture and display-list tables, per-params scale
and lifetime tables, cutscene scripts), batches 20-24 mostly four- and
five-function *actor state machines*, which read faster per symbol because the
`actionFunc` chain names itself once you follow it.

Files completed: `z_demo_sa.c`, `z_en_niw_girl.c`, `xldtob.c`, `xlitob.c`,
`padutils.c`, `fault_drawer.c`, `speed_meter.c`, `z_kaleido_scope_call.c`,
`z_skin.c`, `audio_load.c`, `audio_data.c`, `graph.c`, `idle.c`,
`z_message_PAL.c`, `z_scene_table.c`, `z_eff_blure.c`, `PreRender.c`,
`z_en_item00.c`, `z_file_copy_erase.c`, `z_file_nameset_data.c`,
`z_kaleido_scope_PAL.c` (cloud tables), and eighteen actor overlays
(`Bg_Ganon_Otyuka`, `Bg_Mizu_Movebg`, `Bg_Spot18_Basket`, `Bg_Haka_MeganeBG`,
`Bg_Jya_Haheniron`, `Bg_Jya_Ironobj`, `Bg_Jya_Megami`, `Bg_Gate_Shutter`,
`Bg_Hidan_Hrock`, `Bg_Hidan_Syoku`, `Bg_Ice_Shutter`, `Bg_Jya_Kanaami`,
`Bg_Mori_Elevator`, `Bg_Mori_Hineri`, `Bg_Relay_Objects`, `Bg_Spot01_Objects2`,
`Bg_Spot18_Shutter`, `Bg_Toki_Hikari`, `Bg_Ydan_Maruta`, `Boss_Dodongo`,
`Demo_Du`, `Demo_Tre_Lgt`, `Door_Gerudo`, `En_Anubice_Fire`, `En_Arrow`,
`En_Diving_Game`, `En_Dh`, `En_Fire_Rock`, `En_Fw`, `En_Ganon_Mant`, `En_Ge1`,
`En_Goma`, `En_Insect`, `En_Light`, `En_Ma1`, `En_Ma3`, `En_Ossan`, `En_Sth`,
`En_Tite`, `En_Wonder_Talk`, `En_Yukabyun`, `En_Zf`, `Efc_Erupc`,
`Item_Etcetera`, `Item_Shield`, `Magic_Dark`, `Mir_Ray`, `Obj_Lightswitch`,
`Object_Kankyo`, `Effect_Ss_Fhg_Flash`, `Effect_Ss_KiraKira`).

**Bug found and fixed: never append a `//` tag to a line ending in `\`.**
Batch 10's rename of `D_80A7DEB0` -> `sSoilHomingProgress` put its short tag
after the backslash of a macro continuation line in `z_en_insect.c`'s
`EN_INSECT_SHIP_SAVESTATE_FIELDS` list, commenting the backslash out and
breaking the macro; the file then produced 29 cascading compile errors while
`check_renames.py all` stayed green, because the tagging *is* correct by the
gate's rules -- only the compiler sees the damage. `apply_deduced_names.py` now
skips tagging any line whose code ends in `\`. The bad commit was repaired in
place with a scripted `git rebase -i` (`GIT_SEQUENCE_EDITOR='sed -i
"1s/^pick/edit/"'`) so the series kept one rename per commit rather than
carrying a follow-up fix commit. **Lesson: the rename gate does not replace the
build.** Rebuild after every few batches, not at the end.

**Two scope gaps found, both deferred to a follow-up sweep.** The oracle only
censused file-scope symbols, so it misses (a) `D_`-named statics declared
*inside* a function (e.g. `D_809B3270` in `EnAnubiceFire_Draw`, `D_80B871F4` and
friends in `ItemShield_Burn`) and (b) a few file-scope symbols it skipped anyway
(`D_808A9508` in `z_bg_relay_objects.c`). Neither is in the 4,235 census, so
naming them would make the progress fraction incomparable across batches; they
get their own pass once the censused list is exhausted. The one exception made
deliberately was `func_808C1554_Raw`, a SoH-added sibling of `func_808C1554`:
renaming only the base would have left a function whose name points at a symbol
that no longer exists, so both moved together.

**Naming a parameter you cannot identify is still worth doing.** Several debris
tables feed `EffectSsKakera_Spawn`'s seventh argument, which is `arg6` in the
signature and unidentified. Rather than skip them, they became
`sPillarDebrisArg6` / `sThroneDebrisArg6` / `sDebrisArg6` at GUESS confidence:
the name records exactly what is known (which call and which parameter) and
nothing more, and it will be trivially re-renamed the day `arg6` gets a name.
This is the same principle as the `gUnused` reversal above -- assert the checked
part, tag the rest.


### Batches 1-8 — 2026-09-07: 51 symbols read, 39 named, 12 left alone

Batches 7-8 added: `BgJyaIronobj_SetupWaitForHit`, `BgJyaIronobj_WaitForHit`,
`sDebrisYawOffsets`, `sPillarDebrisScales`, `sThroneDebrisScales`,
`Locale_IsForeignRegionWithoutCtrlr3`, `Locale_IsForeignRegionWithCtrlr3`,
`BgSpot08Bakudankabe_InitCollider`, `BgSpot08Bakudankabe_SpawnDebris`,
`sDebrisOffsets`, `EnHeishi3_ChasePlayer`, `EnHeishi3_ThrowPlayerOut`.

**A whole category is un-nameable and should be recognised on sight:** a bare
declaration with no initialiser and no references anywhere
(`char D_8016B6C0[0x20];`, `volatile OSTime D_8016A578;`, `u32 D_8016139C;`).
The type and the file are all the evidence there is, which supports no claim
about what the symbol is *for*. Skip these without reading further.

**Reversed in batch 11 (2026-09-07).** Those exact three symbols were named
`gUnusedFaultDrawerBuffer`, `gUnusedTotalTime` and `gUnusedKaleidoScopeVar`, and
the category is now *nameable at GUESS confidence* rather than skipped. The
argument that changed it: "nothing anywhere in the tree reads or writes this" is
not a guess — it is a checked fact, and it is the single most useful thing a
reader can be told about the symbol, because it stops them hunting for a caller
that does not exist. What stays out of the name is any claim about *purpose*; the
`gUnused`/`sUnused` prefix asserts only the verified part, and the GUESS tag plus
the provenance comment carry the rest ("size suggests a scratch print buffer, but
nothing confirms the use"). The prefix follows storage class, `s` for `static`
and `g` for file-scope-without-`static`.

**Tracing a data symbol to the parameter it feeds is what makes it nameable.**
`D_808994E0` became `sPillarDebrisScales` only after matching its position in
the `EffectSsKakera_Spawn` argument list to the `scale` parameter. Its siblings
feeding unidentified parameters (`arg6`) were left alone — same file, same
shape, different evidence.

### Batches 1-5 detail — 26 symbols read, 21 named, 5 left alone

Working the smallest files first, as the method prescribes. Named:
`Assert_Fail`, `Skin_Draw`, `Skin_DrawOverrideLimb`, `Skin_DrawAll`,
`EnKz_UpdateTextId`, `EnSa_WaitToTriggerSariasSong`, `Sched_SwapFrameBufferImpl`,
`Sched_GetTaskIfFramebufferFree`, `AudioHeap_ComputeRecurrences`,
`EnBox_AllocXluRenderModeDList`, `EnBox_AllocOpaRenderModeDList`,
`EnHs_OfferOddMushroom`, `EnHs_StartOddMushroomTimer`,
`ItemOcarina_GetThrownInCutscene`, `ItemOcarina_FlyInCutscene`,
`ObjRoomtimer_Start`, `ObjRoomtimer_WaitForClear`, `BgSpot17Funen_DrawSmoke`,
`BgSpot17Funen_DoNothing`, `EnBdfire_BreatheFire`,
`EnBdfire_TravelAlongGround`. Two are GUESS (`Skin_DrawAll`,
`AudioHeap_ComputeRecurrences`); the rest are HIGH.

**Left alone (5):** `func_800FCB70` (empty body, no callers),
`func_800A6394` (no callers, exists only to expose an unidentified parameter),
plus three more whose bodies would not support a specific claim.

**The naming often came from the actor's wiring, not the body.** Several were
settled by finding where the function is *installed* — `actor.draw` vs
`actor.update` vs an `actionFunc` slot, or which `params` branch selects it.
`BgSpot17Funen_DoNothing` is an empty function that is nonetheless nameable,
because it is assigned to `actor.update`; `func_800FCB70` is an identical empty
function that is not, because nothing references it.

**Check the file's existing vocabulary before naming.** `ItemOcarina_Fly` and
`ItemOcarina_GetThrown` already existed, which is what revealed the two unnamed
ocarina actions to be the *cutscene* variants of that same pair — hence
`ItemOcarina_FlyInCutscene`. A name proposed without reading the sibling list
would have collided or misled.

### Detail — batch 1 (kept as the worked example)

| Symbol | Outcome |
|---|---|
| `func_80002384` → `Assert_Fail` | **HIGH** — prints the failed expression with file and line, then spins forever. Not `__assert`: that clashes with libc in a PC port (cf. `Math_FMod`). |
| `func_800A6330` → `Skin_Draw` | **HIGH** — the basic `Skin_DrawImpl` wrapper; four horse actors call it. |
| `func_800A6360` → `Skin_DrawOverrideLimb` | **HIGH** — same, plus the `overrideLimbDraw` callback. |
| `func_800A63CC` → `Skin_DrawAll` | **GUESS** — the full-passthrough wrapper. Named for the wrapper's *shape*, not observed behaviour, since `arg6` and `drawFlags` are still unidentified. |
| `func_800FCB70` | **LEFT ALONE** — empty body, no callers. Nothing to deduce. |
| `func_800A6394` | **LEFT ALONE** — no callers, and it exists only to expose the unidentified `arg6`. |

**Abstain rate across batches 1-8: 12 of 51 (24%) on the *easiest* files in the
tree** — and rising as the trivially-nameable ones are used up. That is the number step 8 should weigh: if a fifth of the simplest
symbols cannot be named honestly, the hard files will be far worse.

**Reading the file, not the symbol, changed the outcome.** `z_skin.c` turned out
to hold a *family* of four wrappers over `Skin_DrawImpl`, each exposing one more
parameter. Naming one and leaving three would have been worse than naming none;
seeing the family is what made three of the four nameable and the fourth
honestly not.

**Two tooling bugs this batch exposed**, both fixed:
- Header *declarations* look like definitions at column 0 (both start with a
  type and a name), so they were being skipped for tagging. A declaration ends
  in `;`; a definition opens a body.
- The oracle could not see function definitions whose parameter list **wraps**
  onto a second line — 23 of them. Found via this very family. No adoptable
  names were lost, but the work-list was understated by 22.

## Notes / decisions

**Why this is separated from the parent task.** Everything before it was
*adoption* — mechanical, verifiable against upstream, and safe to run in bulk to
a fixpoint. This is *deduction*: irreducibly per-symbol, unverifiable except by
reading, and the place where a bad batch does lasting harm. Mixing the two would
have let the safe work's momentum carry into the unsafe part.

**Throughput is the real constraint, not tooling.** The tools already exist and
are gated. 2,565 symbols means reading 2,565 functions; there is no shortcut
that is not fabrication.

**A note on `z_player.c`.** Its 390 un-named functions are mostly
`Player_Action_*`-adjacent state machine internals — the hardest code in the
game to name confidently. Its fate, and that of the other two large files, is
decided at **step 8**, not before.

## Open questions

None blocking. The one real decision — whether to attempt the three huge files —
is deliberately deferred to **step 8**, because it should be made with evidence
from the earlier batches rather than guessed at now.
