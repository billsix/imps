# Reference: patch streams — why they exist, worked cases, apply.sh internals, book-stream gate

> **Provenance:** relocated 2026-09-13 from the N64 family `n64/CLAUDE.md`
> ("Patches live in TWO lanes", "Patches are grouped into purpose STREAMS", and
> "A `book/` stream is comment-only BY CONTRACT") as part of the CLAUDE.md trim
> (`tasks/trim-claude-md.md`). `n64/CLAUDE.md` keeps the two-lane contract, the
> stream-folder list, the within/across ordering rule, the `ORDER` one-liner, and
> the gate commands inline, and points here for the rationale, the worked cases,
> the `apply.sh` internals, and the comment-only proof mechanics.

## The two-lane origin

(Origin: the mario64 graphics reference-doc initiative,
`tasks/mario64-graphics-refdocs.md`, which will add doc-region markers to
both lanes in a later pass.)

## Why streams exist at all

(Family contract, William Emerison Six <billsix@gmail.com>, 2026-09-06.)

**Why streams exist at all: so a stream can be submitted upstream on its own.**
`upstream-candidates/` is a set of patches shaped for a PR; `cheats/` and
`personal/` never will be. Keeping them in separate folders means an upstream
submission is "send this folder", not "untangle a series". **Grouping is
therefore not negotiable — do not merge streams to solve an ordering problem**
(see `ORDER` below, which solves ordering without touching grouping).

The rule that makes this work: WITHIN a stream, order matters (numbered
0001…); ACROSS streams it usually does NOT — the streams touch **disjoint
files** and therefore commute, so a new stream (a book, a Lua experiment) is
added without renumbering anything. The invariant to preserve: **streams should
stay independent** (disjoint files/regions).

When a real cross-stream dependency exists, pin it in `patches/ORDER`.
One stream name per line; those apply first, in that order, and every unlisted
stream follows alphabetically (`#` comments and blank lines ignored). This keeps
the stream folders — and their upstreamability — intact while making the
sequence explicit, instead of silently relying on folder-alphabetical order.
The mechanism also exists for `patches-libultraship/ORDER`.

**All four projects' `apply.sh` implement this** (ported 2026-09-07 — the
mechanism briefly existed only in OcarinaOfTime while this section already
described it family-wide).

## Two live cases

Two live cases (William Emerison Six <billsix@gmail.com>, 2026-09-07):

- **OcarinaOfTime** — its `personal` stream renames ~206 decomp symbols and 18
  files, so **every later stream must be written against the renamed tree**; a
  `book/` stream added later would otherwise sort first and try to patch symbols
  that no longer exist under those names. `patches/ORDER` lists `personal`.
- **SuperMario64** — `cheats` and `book` **both touch `src/game/mario.c`**, so
  that project's streams are not disjoint. They do not collide today (the hunks
  sit ~370 lines apart), but the book grows a doc-region per chapter and covers
  Mario's action machine, which is what the cheats edit. `patches/ORDER` lists
  `cheats` then `book`, so the markers are placed against the cheated tree
  rather than the reverse: the cheats are the substantive code, the markers are
  commentary on whatever that code ends up being. Verified the reorder changes
  history only — the applied tree hash is unchanged.

## apply.sh internals

`apply.sh` walks the streams in that order, `git am`-ing each stream's numbered
patches. It refuses to run if the checkout is not at the pin, and refuses if an
interrupted `git am` left `.git/rebase-apply` behind (telling you to
`git -C <checkout> am --abort`). **Regenerating one stream:** rebuild just that
stream's commits in the checkout and `git format-patch --base=<pin>` them into
their subfolder — the other streams are untouched. This is the SuperMario64
shape; all four games were converted to it 2026-09-06 (verified: each game's
streams `git am` clean onto its pin).

## The book-stream comment-only proof mechanics

(2026-09-07.) A `book/` stream adds `// doc-region-begin/end` markers so a
Sphinx book can `literalinclude` spans by NAME rather than line numbers. Adding
a marker must **never change the program** — if one ever does, the book has
silently started patching the game. Two tools at the imps root enforce that:

```sh
tools/check_comment_only_streams.sh            # all projects, both lanes
tools/check_comment_only_streams.sh SuperMario64
```

It finds every `book/` stream, builds "the pin plus every OTHER stream" and
"that plus the book stream", and compares them with
`tools/prove_comment_only.sh`: no code may differ once **gcc** strips the
comments (`gcc -fpreprocessed -dD -E -P` — the argument rests on a compiler,
not on a regex here). Projects without a book stream are skipped, so it stays a
whole-repo gate as more books appear. Verified 2026-09-07 on SuperMario64's two
book streams (game tree + libultraship lane): both comment-only.

`--allow-line-shift` is passed for book streams because a `doc-region` marker
must occupy its own line, so line numbers below it move; only `__LINE__` /
`__FILE__`-derived strings are affected. **A patch-stream RESHAPE gets no such
allowance** — run `tools/prove_comment_only.sh <checkout> <before> <after>`
strictly there, as the Ocarina rename split did (it appends its provenance tags
to existing lines precisely so no line moves).
