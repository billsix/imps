# Squashing a fine-grained patch series into reviewable units, losslessly

**What this is:** the method for taking a series that was *produced* at one
change per commit and regrouping it into the units a human would actually read
and merge — without losing any of the per-commit reasoning. Written after doing
it to the Ocarina decomp-rename series (3,799 → 488 commits, 2026-09-08); the
full play-by-play is in that task's archived record,
[`../../archive/ocarina/2026/09/08/ocarina-deduce-remaining-decomp-names.md`](../../archive/ocarina/2026/09/08/ocarina-deduce-remaining-decomp-names.md),
"Step 9 as executed".

**The inverse operation** -- taking one monolithic commit apart into a
fine-grained series -- is
[`splitting-a-patch-series.md`](splitting-a-patch-series.md). The two are
halves of one story: split to PRODUCE the work, regroup to REVIEW it. The
Ocarina rename went through both, in that order.

**Why it will be needed again:** imps carries more than one mechanical-rename
effort ([`../../mario64-decomp-rename-and-cleanup.md`](../../mario64-decomp-rename-and-cleanup.md)
is the live one), and they all hit the same tension.

## The tension, stated once

**One change per commit is right for PRODUCING the work and wrong for REVIEWING
it.** Producing: when something breaks, the breakage localises to a single
symbol — that is how a macro-continuation bug got pinned to one commit out of
three thousand. Reviewing: nobody wants to read thirty consecutive commits that
rename thirty entries of one function-pointer array.

So produce fine, then regroup once, at the end. Do not compromise in the middle
by producing at a coarse grain — you lose the bisectability while the work is
still going wrong, which is exactly when you need it.

## The method

**1. Pick a unit key that is a property of the CHANGE, not of the batch order.**
For renames it is the file the symbol is *defined* in (find it as the file the
commit's provenance comment landed in). A reviewer takes one file at a time, and
"all thirty array entries" falls out for free because they share a file.

**2. Group CONSECUTIVE runs sharing that key, and accept the duplicates.** A file
touched in three different batches becomes three commits, and that looks untidy:
in the worked example, 65 of 392 files are split, so gathering each file into
exactly one commit would cut 488 units to 392. **Do not do it** — and the reason
is measured, not assumed:

- **It is a near-total reshuffle, not a nudge.** 3,474 of the 3,799 commits
  change position under file-grouping, and the runs of one file sit 11 to 380
  units apart.
- **It conflicts almost immediately.** Replaying the file-grouped order broke
  after **38 of 3,799** commits: renaming `func_800F4524` in `audio_general.c`
  also rewrites its call sites in `z_en_go2.c`, and the reorder had already
  moved a `z_en_go2.c` commit across it. A unit's changes are not confined to
  its key file — the median unit touches 1 file but the largest touches 138 —
  so "group by file" and "replay safely" are in direct tension.
- **It would destroy a property worth more than the tidiness.** With the
  original order preserved, every squashed commit's tree is a state the
  unsquashed history *actually passed through*, so the series stays bisectable
  and every commit compiles. Reordering can also strand an intermediate state
  with two symbols sharing a name, where a later collision-driven rename was
  moved ahead of the commit that caused the collision.

Run this experiment before accepting the tidier grouping; it is cheap and
decisive, and asserting either answer without it is guessing.

**3. SET each unit's tree; do not replay its patches.**

```sh
git checkout -B <work-branch> <base>
# per unit, in order:
git read-tree --reset -u <sha of the unit's LAST commit>
git commit -F <message file>
```

`read-tree` points at a tree that **already exists in history**, so no patch is
applied: there is nothing that can conflict and nothing that can be silently
dropped, and the final tree is byte-identical to the pre-squash tip *by
construction* rather than by luck. `git cherry-pick -n <first>^..<last>` also
works and is conflict-free when replaying a contiguous range onto its own base,
but it proves less.

**4. Hoist the invariant boilerplate; keep every per-item fact.** Generated
commit messages are template plus variables — the Ocarina series had 36 distinct
templates across 3,799 messages. Repeating a paragraph 203 times inside one
commit message *buries* the reasoning rather than preserving it. State the
template once in the squashed commit's header, then one entry per item carrying
only what varies:

```
  * func_80B5A1D0 -> EnZl3_DrawXlu
    deduced, confidence HIGH: sDrawFuncs[2]: SkelAnime_DrawFlex into
    POLY_XLU_DISP after Gfx_SetupDL_25Xlu, using this->alpha
```

**A unit of ONE keeps its original message verbatim.** Wrapping a single item in
a page of preamble makes it worse.

**Say in the SUBJECT that the key file names the unit rather than bounding it.**
This is the one wording mistake that actively misleads. "name the 203 symbols
**in** z_en_zl3.c" reads as "this commit touches only that file", and a reader
who believes it concludes the commits are not independently checkout-able. They
are: a rename reaches the declaration, the definition and every call site, so
these units touch a mean of 2.4 files and one of them touches **138**. Write
"defined in <file>", and state the reach in the body —

```
All 63 are defined in soh/src/code/z_actor.c; updating their references
touches 138 files in total.
```

— so the message cannot be read the wrong way. (The maintainer caught this on
the first pass and was right to; the body said "defined in" but nobody reads
past the subject.) The property that makes the units genuinely independent is
worth checking directly: for every commit, grep THAT commit's tree for the old
names its own message retires. Zero hits outside comments means no commit leaves
a dangling reference.

**5. Enforce losslessness with an assertion, not an intention.** Before
committing anything, check that every free-text justification in an original
message appears in the composed message. This is not ceremony: it caught 12 real
losses on the first run of the worked example, where `textwrap` broke hyphenated
words (`joint-sphere` → `joint-` / `sphere`) across a newline and quietly
altered the recorded text. Pass `break_on_hyphens=False, break_long_words=False`
to `textwrap.fill` when the text is data rather than prose.

## Proving it changed history only

Three checks, all cheap, and the whole point of the exercise:

```sh
git diff <backup> <work>                      # must be EMPTY
git rev-parse <backup>^{tree} <work>^{tree}   # must be the SAME sha
git diff <base> <backup> | sha256sum          # must equal the same for <work>
```

Make the backup branch **before any rewrite command runs** and never write to
it; it is the undo (`git reset --hard <backup>`).

**Read the unsquashed series from the BACKUP branch, never from `HEAD`.** After
one successful run `HEAD` *is* the squashed output, so a re-run — to fix wording,
say — silently re-squashes the squash into N units of one and destroys the
per-symbol reasoning. It fails quietly, because every check still passes on the
degenerate input. Guard it: refuse to rewrite when the grouping produces fewer
than two multi-item units.

## A regrouping BREAKS the gate that policed the old grain — and may break it silently

Any check written as "exactly one X per commit" is invalidated by the squash.
**The dangerous failure is not that it goes red; it is that it goes green having
checked nothing** — the Ocarina gate's subject regex simply would not match a
grouped subject, so it would have skipped all 488 commits and reported OK.

Relax such a gate rather than retiring it, by separating the property from the
grain. And note the trap has a second edge: **changing the commit SUBJECT later
re-breaks the gate the same silent way.** Editing "symbols in" to "symbols
defined in" stopped the gate's regex matching, so all 331 grouped commits would
have been skipped with a green result. Accept both spellings, and after any
subject change assert that the gate still matches every grouped subject before
trusting its verdict. The property worth keeping was never "one per commit"; it was **"no
change may happen that its commit message does not account for."** A grouped
commit satisfies that by stating its count in the subject and listing its items
in the body, with the count and the list required to agree. A good cross-check
after the rewrite: the regrouped history should claim exactly as many changes as
the original performed.

## In imps specifically

- The rewriting happens in the **gitignored upstream checkout**, which is
  disposable scaffolding. imps sees one ordinary commit replacing the old patch
  files with the new ones — **imps' own history is never rewritten.**
- Regenerate the stream afterwards
  (`git format-patch --no-cover-letter --base=<pin> -o <stream dir>`) and re-run
  `tools/check_patches_apply.sh <Project>`; the patches are the deliverable.
  **Pass `-o` an absolute path** — a relative one resolves against the `git -C`
  directory and will scatter the output somewhere surprising.
- `runDir/` is a sibling of the checkout, so no git operation here can reach it.
