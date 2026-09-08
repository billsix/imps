# Squashing a fine-grained patch series into reviewable units, losslessly

**What this is:** the method for taking a series that was *produced* at one
change per commit and regrouping it into the units a human would actually read
and merge — without losing any of the per-commit reasoning. Written after doing
it to the Ocarina decomp-rename series (3,799 → 488 commits, 2026-09-08); the
full play-by-play is in that task's archived record,
[`../../archive/ocarina/2026/09/08/ocarina-deduce-remaining-decomp-names.md`](../../archive/ocarina/2026/09/08/ocarina-deduce-remaining-decomp-names.md),
"Step 9 as executed".

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
touched in three different batches becomes three commits. Resist the urge to
merge them: that means reordering commits, and any shared file — a header every
unit touches — then has to be partitioned hunk by hunk. In the worked example
that trade was 488 units versus ~342 for a large jump in risk, with the residue
dominated by single-change files either way.

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

## A regrouping BREAKS the gate that policed the old grain — and may break it silently

Any check written as "exactly one X per commit" is invalidated by the squash.
**The dangerous failure is not that it goes red; it is that it goes green having
checked nothing** — the Ocarina gate's subject regex simply would not match a
grouped subject, so it would have skipped all 488 commits and reported OK.

Relax such a gate rather than retiring it, by separating the property from the
grain. The property worth keeping was never "one per commit"; it was **"no
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
