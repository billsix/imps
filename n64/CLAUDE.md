# n64 — HarbourMasters N64 PC-port family

The N64 family: patch series carried on top of the HarbourMasters PC ports of
Nintendo 64 games, all of which share the **libultraship** engine. This
tier-2 family `CLAUDE.md` holds the N64/HarbourMasters-specific contracts —
the concrete build/patch machinery, the derived-artifact drift table, the
port-specific gotchas, and the per-project index. It auto-loads (via Claude
Code's ancestor-`CLAUDE.md` loading) for any session working anywhere under
`n64/`, and only for those sessions — a textbook (`openstax/`) session never
pays for this file's N64 detail. The cross-family principles (what imps is,
the doc-tier design, the patch philosophy, the unsigned-commits rule, the
tasks/archive convention) live in the master `CLAUDE.md` at the imps root.

## N64 build/patch contract — the concrete per-project folder machinery

The master `CLAUDE.md` states the generic self-contained-folder contract
(`fetch.sh`/`apply.sh`/`build.sh`/`run.sh` + `patches/` + docs). The N64
family adds a concrete **HarbourMasters-port** shape on top of it:

- The upstream is a HarbourMasters port; `fetch.sh` clones it at a pinned base
  SHA and `git submodule update --init --recursive` (libultraship + the
  torch/ZAPDTR asset pipeline). `apply.sh` `git am --3way`s the series onto the
  pin (fetch pristine upstream → `git am` the series → build). ROM/asset
  acquisition stays out of scope — each game's own in-app extraction handles it
  in `runDir/`.
- Optionally a **podman build**: `Dockerfile` + `Makefile` (native imps files,
  never patches) derived from the project's own CI workflow —
  `make image/build/appimage/run`, image context = the checkout,
  `PODMAN_RUN_FLAGS` threaded into every `run` (never `build`), and where
  multiple base images exist, a `VARIANT` switch with per-variant image
  tags. `n64/MajorasMask/` is the reference implementation.

### Patches live in TWO lanes: the game tree and the libultraship submodule

(Family contract, William Emerison Six <billsix@gmail.com>, 2026-09-06.)
A game's delta can touch either the port's own tree OR the shared engine,
so a project may carry **two separate patch series**:

- **Game-tree lane** — the existing `n64/<Game>/patches/`, base = the
  Ghostship/Shipwright/… pin, applied by `apply.sh` on the game checkout.
  This is the only lane in use today (cheats, doc fixes, port tweaks).
- **libultraship lane** — a SEPARATE series applying INSIDE
  `<Game>/<checkout>/libultraship/`, base = that game's **pinned submodule
  SHA**, with its own apply step. The submodule is its own git repo, so
  gpg signing must be disabled in ITS config too
  (`git config commit.gpgsign false`, repo-local, never global).

Each game pins a **different** libultraship commit (Ocarina/MM on older
mainline, Banjo `1.3.1-482`, Mario 64 the `1.3.1-544` KiritoDv fork), so
the LUS lane is per-game, keyed to that game's submodule SHA — a doc-region
marker or fix authored for one game's LUS may need re-anchoring against
another's via `git am`/rebase. On a game pin bump, replay BOTH lanes.

### Patches are grouped into purpose STREAMS — no total ordering across them

(Family contract, William Emerison Six <billsix@gmail.com>, 2026-09-06.) Within
each lane, patches are NOT one numbered series but are grouped into
**purpose streams** — subfolders by intent:

- `patches/upstreamable-<slug>/` — an **upstreamable unit = one PR** (2026-10-27).
  Each folder is one submission-ready unit (own reviewer-facing commits, no
  entanglement with personal changes), possibly many bite-sized patches. Live
  units: `upstreamable-standard-c` (SM64 46, OoT 36 — codegen-identical
  assembly-ism rewrites, listed FIRST in each `ORDER` so the personal streams sit
  on it); `upstreamable-rename-decomp` (OoT, the 490-patch decomp rename, re-cut
  on top of standard-c, `DEPENDS upstreamable-standard-c`); `upstreamable-ci-appimage`
  (every port, the `docker/` AppImage build); `upstreamable-fixonfedora` (Banjo,
  the 4-patch JeodC-reviewed PR); `upstreamable-audio-64bit` (MM);
  `upstreamable-fedora-shaderc-deps` (SM64); `upstreamable-rom-cli-import`
  (PaperMario, the 2-patch PaperBoat PR). **Invariant: an upstreamable unit depends
  only on pristine upstream and other upstreamable units — never on
  cheats/book/personal**; cross-unit prerequisites go in `patches/<slug>/DEPENDS`.
  Apply/build one in isolation with `tools/apply_unit.sh <Project> <slug>`; the gate
  is `tools/check_upstreamable_applies.sh`.
- `patches/cheats/` — personal gameplay cheats/enhancements (SuperMario64).
- `patches/book/` — comment-only `doc-region` markers for a game's book
  `literalinclude` (grows per chapter). Same subfolders under
  `patches-libultraship/` for the LUS lane.
- (future) `patches/lua-extraction/` — a scripting-extraction stream, etc.

**Grouping is not negotiable — do not merge streams to solve an ordering
problem** (`ORDER` below solves ordering without touching grouping). Why streams
exist and why a stream must stay independently submittable:
`tasks/reference/imps/patch-streams-design.md`.

**The rule that makes this work: WITHIN a stream, order matters (numbered
0001…); ACROSS streams it usually does NOT** — the streams touch **disjoint
files** and therefore commute, so a new stream (a book, a Lua experiment) is
added without renumbering anything. The invariant to preserve: **streams should
stay independent** (disjoint files/regions).

**When a real cross-stream dependency exists, pin it in `patches/ORDER`.**
One stream name per line; those apply first, in that order, and every unlisted
stream follows alphabetically (`#` comments and blank lines ignored). This keeps
the stream folders — and their upstreamability — intact while making the
sequence explicit, instead of silently relying on folder-alphabetical order.
The mechanism also exists for `patches-libultraship/ORDER`.

**All four projects' `apply.sh` implement this.** It walks the streams in that
order, `git am`-ing each stream's numbered patches; it refuses to run unless the
checkout is at the pin, and refuses if an interrupted `git am` left
`.git/rebase-apply` behind (`git -C <checkout> am --abort`). **Regenerating one
stream:** rebuild just that stream's commits and `git format-patch --base=<pin>`
them into their subfolder — the others are untouched.

The live ORDER cases (OcarinaOfTime's `upstreamable-standard-c`-then-`upstreamable-rename-decomp`,
SuperMario64's `upstreamable-standard-c`-first and cheats-before-book) and the `apply.sh` internals:
`tasks/reference/imps/patch-streams-design.md`.

### The series must still apply — gated across all projects

`tools/check_patches_apply.sh` (imps root) resets each project to its pin and
runs its own `apply.sh`, so it exercises stream `ORDER`, both lanes, and the pin
guard (`libultraship/` is skipped — docs-only, no `apply.sh`). This is the gate
for the repo's primary goal (master `CLAUDE.md`, "Patch philosophy"): a patch
that no longer applies has failed at its job.

### A `book/` stream is comment-only BY CONTRACT — and that is gated

(2026-09-07.) A `book/` stream adds `// doc-region-begin/end` markers so a
Sphinx book can `literalinclude` spans by NAME. Adding a marker must **never
change the program** — if one ever does, the book has silently started patching
the game. Two tools at the imps root gate that:

```sh
tools/check_comment_only_streams.sh            # all projects, both lanes
tools/check_comment_only_streams.sh SuperMario64
```

The proof mechanics (gcc `-fpreprocessed` comment-stripping, the
`--allow-line-shift` allowance for book streams vs the strict rule for a
patch-stream reshape): `tasks/reference/imps/patch-streams-design.md`.

### Never build a checkout from a foreign toolchain via a bind mount

Copy the source into the throwaway container; don't bind-mount (libultraship
1.3.1-482+ writes artifacts into its submodule source dir, poisoning the next
podman build). Post-mortem + recovery: `tasks/reference/imps/n64-build-gotchas.md`.
Three more cross-port lessons (2026-09-22, from PaperMario): headless testing of a port
(`tasks/reference/imps/headless-gui-port-testing.md`), why every Linux `run.sh` seeds OpenGL
(`tasks/reference/imps/lus-render-backend-selection.md`), and telling a bad ROM dump from a good
one (`tasks/reference/imps/n64-rom-dump-identification.md`).

## Derived artifacts — re-verify each at every pin bump

Much of the N64 family is DERIVED from files inside the pinned checkouts
(Dockerfiles, `installdependencies.sh`, `build.sh`/Makefile targets, pin
comments, per-project CLAUDE.md facts, …). Those copies are correct **at the
pin** and rot silently when it moves — so **every pin bump must re-verify each
derived artifact against its source** (part of the pin-bump operation in the
master `CLAUDE.md` agent contract). The full artifact↔source drift table:
`tasks/reference/imps/derived-artifact-drift.md`.

## libultraship — the shared engine

`libultraship` is the shared engine under all four N64 ports
(https://github.com/Kenix3/libultraship). Docs-only project: no patches, no
build scripts — its `fetch.sh` pins whichever commit the reference-doc crawl
describes. The crawl is **complete**; current doc state = Ghostship's `c151cc91`
(1.3.1-544, a KiritoDv FORK branch — see the drift table's fork-topology caveat).
The 8-doc set and crawl protocol/iteration log: `tasks/reference/libultraship/`
(a game's future LUS pin bump reopens it). Crawl-history detail:
`tasks/reference/imps/game-port-history.md`.

## Projects

One line each (upstream URL, pin SHA, one-line status). Per-project operational
facts are in each game's tier-3 `n64/<Game>/CLAUDE.md`; the detailed patch-count
/ verification-date / fork-migration history is
`tasks/reference/imps/game-port-history.md`.

- `n64/OcarinaOfTime/` — Ship of Harkinian
  (https://github.com/HarbourMasters/Shipwright), pin `41ae6cd3` (develop HEAD,
  bumped from ecd889c2/9.3.0 2026-10-20). 36-patch upstream-bound
  `upstreamable-standard-c` stream (assembly-isms → standard C) under the 490-patch
  `upstreamable-rename-decomp` series (re-cut onto the new base 2026-10-20: 2 conflicts / 8 blocks mechanical, 0 by
  hand; +2 tail patches reconciling new-at-pin references). `check_renames all`
  + `check_patches_apply` green (526 patches from the bare pin); LUS
  `62e973ae`→`da6daf1a`. **asmdiff codegen re-gate + build + play-test pending**
  (the maintainer's). Details: `n64/OcarinaOfTime/CLAUDE.md`.
- `n64/MajorasMask/` — 2 Ship 2 Harkinian
  (https://github.com/HarbourMasters/2ship2harkinian), pin `f1dda4c2`
  (re-bumped from e8757c14 2026-10-19; before that 04a1a4319 2026-10-08). One
  patch (the 64-bit audio/scheduler fixes; the BUILDING.md audio-libs patch was
  dropped — upstream absorbed it); replays clean at the new pin (gate green, LUS
  gitlink unchanged 7f9b86a5); build/run re-verify pending (maintainer's).
  Details: `n64/MajorasMask/CLAUDE.md`.
- `n64/SuperMario64/` — Ghostship (https://github.com/HarbourMasters/Ghostship),
  pin `40eef138` (bumped from 49c5312a 2026-10-08). 46-patch upstream-bound `upstreamable-standard-c`
  stream (assembly-isms → standard C, all codegen-identical, 2026-09-22) + 3-patch cheat series +
  libshaderc doc fix; fully verified; podman build; carries a Sphinx book
  (`SuperMario64/book/`). Details:
  `n64/SuperMario64/CLAUDE.md`.
- `n64/BanjoKazooie/` — Lighthouse
  (https://github.com/HarbourMasters/Lighthouse), pin `4e8dfd23` (re-bumped from
  5c948c59 2026-10-19; before that 6d30df9a 2026-10-08). 4-patch `fixOnFedora`
  series (a submitted upstream PR); replays clean at the new pin (gate green, LUS
  gitlink unchanged 62e973ae); build/run re-verify pending (maintainer's). Podman
  build. Details: `n64/BanjoKazooie/CLAUDE.md`.
- `n64/PaperMario/` — PaperBoat (https://github.com/HarbourMasters/PaperBoat),
  pin `1.0.3` (`7f038b85`, bumped from 1.0.2 2026-10-20). 2-patch game-tree series
  (CLI ROM import on Linux + a precise refusal of unsupported ROMs); the former
  libultraship-lane Vulkan crash fix was **DROPPED at 1.0.3** (upstream absorbed the
  identical null-Context guard — LUS `3e3cd2ed`→`7f1bd60e`). Upstream candidates;
  build-verified in-sandbox at 1.0.3, play-test the maintainer's. Uses JeodC
  LUS/Torch forks (`external/`), NOT the crawl's engine pin. `run.sh <ROM>`
  verifies the SHA-1 and trims a padded dump. Details: `n64/PaperMario/CLAUDE.md`.
- `n64/libultraship/` — the shared engine (see the "libultraship" section above).
  Docs-only; the reference crawl lives at `tasks/reference/libultraship/`.
