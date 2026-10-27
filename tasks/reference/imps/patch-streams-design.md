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
An `upstreamable-<slug>/` stream is one PR's worth of patches shaped for a PR;
`cheats/` and `book/` never will be. Keeping them in separate folders means an
upstream submission is "send this unit", not "untangle a series". **Grouping is
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

## Upstreamable units — one PR per `upstreamable-<slug>/` stream (2026-10-27)

(William Emerison Six <billsix@gmail.com>, 2026-10-27.) The currency of
upstreaming is a *unit of work* — one thing upstream accepts as a single PR — not a
patch file. A unit can be many patches on purpose (the OcarinaOfTime decomp rename
is ~488, sliced into bite-sized reviewable commits so a reviewer walks the history
in chunks). Each such unit is carried as its own `patches/upstreamable-<slug>/`
stream, one PR's worth per folder. This generalizes the original `standard-c`
precedent and replaces the coarse `upstream-candidates/` grab-bag, which conflated
several distinct PRs in one folder (e.g. MM's audio fix and its CI patch).

**The invariant that makes a unit submittable:** an `upstreamable-<slug>` unit
depends only on **pristine upstream** and **other upstreamable units** — never on a
`personal`/`cheats`/`book` patch. A candidate that needs your cheats to apply is not
upstreamable; that dependency is the bug. Upstreamable units form a DAG whose every
node is upstream-bound; a unit with no prerequisites applies on the bare pin.

**DEPENDS vs ORDER.** `ORDER` is the cross-stream apply order for the *full* series
(your personal stack). A unit's upstreamable prerequisites are declared separately
in `patches/<slug>/DEPENDS` (one upstreamable stream per line; absent = stands on the
bare pin) — the *per-unit closure* for isolated apply. They must stay consistent: a
DEPENDS edge implies an ORDER edge. Today only `upstreamable-rename-decomp/DEPENDS`
has an entry (`upstreamable-standard-c`).

**The isolated build IS the real upstream test.** `tools/apply_unit.sh <Project>
<slug>` resets the checkout to the pin and applies only the unit's DEPENDS closure
(prerequisites first, then the slug), leaving branch `imps-<slug>` to build
(`make -C <checkout>/docker appimage`) and cut a PR from. That build answers "will
this PR build on upstream by itself"; the full-series build (`apply.sh` /
`check_patches_apply.sh`) answers the different question "does my whole stack build".
The gate `tools/check_upstreamable_applies.sh` proves every upstreamable unit applies
in isolation AND enforces the invariant (each unit's DEPENDS closure contains only
`upstreamable-*` streams); `--build` also runs the container AppImage build. Both are
host-side (git only) unless `--build`.

## Two live cases

> **Naming note (2026-10-27):** the streams below were renamed when every
> upstream-bound unit took the `upstreamable-` prefix — `standard-c` →
> `upstreamable-standard-c`, `personal` → `upstreamable-rename-decomp`, and
> `upstream-candidates/` split into one `upstreamable-<slug>/` per PR. The
> historical narrative keeps the old names; the current ORDER-listing claims below
> use the new ones.

Two live cases (William Emerison Six <billsix@gmail.com>, 2026-09-07):

- **OcarinaOfTime** — its `personal` stream renames ~206 decomp symbols and 18
  files, so **every later stream must be written against the renamed tree**; a
  `book/` stream added later would otherwise sort first and try to patch symbols
  that no longer exist under those names. `patches/ORDER` lists `upstreamable-rename-decomp`.
- **SuperMario64** — `cheats` and `book` **both touch `src/game/mario.c`**, so
  that project's streams are not disjoint. They do not collide today (the hunks
  sit ~370 lines apart), but the book grows a doc-region per chapter and covers
  Mario's action machine, which is what the cheats edit. `patches/ORDER` lists
  `cheats` then `book`, so the markers are placed against the cheated tree
  rather than the reverse: the cheats are the substantive code, the markers are
  commentary on whatever that code ends up being. Verified the reorder changes
  history only — the applied tree hash is unchanged.
- **SuperMario64 again, `standard-c` FIRST** (2026-09-22): the upstream-bound
  assembly-isms→standard-C stream rewrites many decomp files that the personal
  streams (`cheats`: `mario.c`; `book`: its marker files) also touch. Because it
  is meant to be merged upstream, it must be the BASE the personal streams sit
  on — then the personal patches apply to the code as upstream would see it
  after merging, and any conflict surfaces here, on our side, rather than in a
  rebase we cannot do. `patches/ORDER` lists `upstreamable-standard-c`, `cheats`, `book`
  (rationale inline in the file); `tasks/archive/mario64/2026/09/23/mario64-assembly-isms-to-standard-c.md`
  Phase C is the replay that keeps the personal streams applying on top.
- **OcarinaOfTime, `standard-c` UNDER `personal`** (2026-09-22): the same
  upstream-first argument, but here the personal stream is the 488-patch decomp
  rename, which touches 509 files against the rewrites' 477. The rename patches
  were **re-cut** on top of `standard-c` (the maintainer's call: "I version
  control all of these patches, so I will lose nothing"): `git am --3way` with
  diff3 markers, and every conflict resolved mechanically — our side of the
  block, that patch's `old -> new` renames applied to it, the patch's added
  provenance lines re-inserted — by
  `tools/resolve_rename_conflicts.py`; 87 of 488
  needed it. Proof the re-cut changed nothing: `tools/check_renames.py`
  (series/traceable/declarations) on the new tree, and an assembly gate of every
  file that differs between the old applied tree and the new one. `ORDER` lists
  `upstreamable-standard-c`, `upstreamable-rename-decomp`. Method: `tasks/archive/ocarina/2026/09/23/ocarina-de-disassemble-ugly-c.md`.

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
