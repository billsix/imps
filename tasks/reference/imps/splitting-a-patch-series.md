# Reference: splitting a monolithic patch into a reviewable series

> **Provenance:** harvested 2026-09-07 from
> `tasks/archive/ocarina/2026/09/07/ocarina-split-rename-patch.md`, which split
> Ocarina's 6,854-line rename commit into 225 one-rename-per-commit patches. The
> scripts that did it were one-shots, removed at archive; **this doc is the
> method, which is what outlives them.** Recover the code from git history
> (`git log --diff-filter=A -- tasks/adhoc/ocarina-split-rename-patch/`) if a
> second split ever needs it.

> **Read with its inverse:**
> [`squashing-a-produced-series-for-review.md`](squashing-a-produced-series-for-review.md).
> Splitting is how a series is PRODUCED (one change per commit, so a
> breakage localises); squashing is how it is made REVIEWABLE afterwards.
> Ocarina's rename did both: 1 commit -> 3,799 -> 488.

## When this applies

A patch stream has grown one commit too large to review — a bulk rename, a
sweeping refactor, a mechanical codemod. You want it as many small commits,
**with the tree provably unchanged**. The risk is obvious: a hand-redone split
can silently drop or alter something, and nobody would notice until a build
broke months later.

## The method: peel backwards, replay forwards

The instinct is to re-derive each small change forwards from the base. **Don't.**
That gives no guarantee the result matches what you started with — you are
re-doing the work and hoping.

Instead:

1. **Start from the finished tree** and peel ONE change off at a time, deriving
   the state before it.
2. **Check the fully-peeled state equals the base, exactly.** If it does, the
   decomposition is *provably complete* — nothing was invented, nothing lost.
   If it does not, the residue tells you precisely what you have not accounted
   for. Do not proceed until it is empty or every difference is explained.
3. **Only then replay forwards**, committing each state in turn.
4. **Confirm the replayed tip is byte-identical to the finished tree.**

The asymmetry is the whole point: peeling is checkable against a known-good
endpoint, re-deriving is not.

## Scoping each peel

A peel must know **which files a change may touch**. Deriving that from the
finished tree is wrong (names have already moved). Derive it from the **base**:
the files containing the old name *at the base commit*.

This is what makes file-local symbols safe. In the Ocarina split, `D_80A65F38`
became `sColChkInfoInit` in one file — while **60 other files already had their
own static of that name**. A tree-wide rename would have corrupted all of them;
a base-scoped one cannot, because `D_80A65F38` existed in exactly one file.

Watch for the converse too: two distinct old symbols given the **same** new name
(there, `sTentacleTextures` in two files). They are separate changes and must
stay separate commits.

## Proving the split changed nothing

Tree equality is necessary but not sufficient if the split also **adds
comments**, as a rename split usually does. Two further checks:

- **Line counts must not change** — or `__LINE__`/`__FILE__`, and every log or
  assert string built on them, shift. Append comments to existing lines rather
  than inserting new ones, and this holds. (A `book/`-style doc-region stream
  *cannot* satisfy this: a marker must occupy its own line. That is a documented
  exception, not a licence to ignore the check.)
- **The compiler must see identical tokens** —
  `tools/prove_comment_only.sh <checkout> <before> <after>` strips comments with
  `gcc -fpreprocessed -dD -E -P` and compares. The argument then rests on a
  compiler, not on a regex in this repo.

## Gotchas that cost time

- **A marker on a CODE line.** Provenance comments usually occupy a whole line,
  so peeling drops the line. But a type rename tags the line that *names* the
  type (`} RumbleMgr; // … was UnkRumbleStruct …`) — dropping that deletes the
  declaration. Cut back to just before the marker text and **fall through** to
  the rename substitution, rather than skipping the line.
- **Cut at the marker, not at `//`.** If the line already ended in a comment
  (`// size = 0x10E`), partitioning at `//` removes that pre-existing comment
  too, and the peel no longer matches the base.
- **File renames go first,** as their own commits, and carry any comment
  elsewhere in the tree that cross-referenced the old filename. Some will be
  reported by git as add+delete rather than R when the content also changed a
  lot — list those explicitly.
- **An interrupted `git am` leaves `.git/rebase-apply`,** and the next run dies
  with a cryptic "previous rebase directory … still exists". The project
  `apply.sh` scripts now check for this; a bare `git am` loop should too.
- **Piping an apply loop into `head` kills it mid-series** via SIGPIPE, leaving
  exactly that stale state. Redirect to a file instead.

## Afterwards

Gate the conventions the split established, or they rot — a stated rule with no
check is a suggestion. For Ocarina that is
`n64/OcarinaOfTime/tools/check_renames.py`; the cross-project equivalence and
apply gates are `tools/prove_comment_only.sh` and `tools/check_patches_apply.sh`.
