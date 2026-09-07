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
(Origin: the mario64 graphics reference-doc initiative,
`tasks/mario64-graphics-refdocs.md`, which will add doc-region markers to
both lanes in a later pass.)

### Patches are grouped into purpose STREAMS — no total ordering across them

(Family contract, William Emerison Six <billsix@gmail.com>, 2026-09-06.) Within
each lane, patches are NOT one numbered series but are grouped into
**purpose streams** — subfolders by intent:

- `patches/cheats/` — personal gameplay cheats/enhancements (SuperMario64).
- `patches/upstream-candidates/` — fixes shaped for upstream submission
  (MM audio + doc fixes; Banjo's fixOnFedora PR; SM64's libshaderc doc fix).
- `patches/personal/` — personal refactors not bound for upstream
  (Ocarina's decomp rename).
- `patches/book/` — comment-only `doc-region` markers for a game's book
  `literalinclude` (grows per chapter). Same subfolders under
  `patches-libultraship/` for the LUS lane.
- (future) `patches/lua-extraction/` — a scripting-extraction stream, etc.

**Why streams exist at all: so a stream can be submitted upstream on its own.**
`upstream-candidates/` is a set of patches shaped for a PR; `cheats/` and
`personal/` never will be. Keeping them in separate folders means an upstream
submission is "send this folder", not "untangle a series". **Grouping is
therefore not negotiable — do not merge streams to solve an ordering problem**
(see `ORDER` below, which solves ordering without touching grouping).

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

- **OcarinaOfTime is the live case** (William Emerison Six <billsix@gmail.com>,
  2026-09-07): its `personal` stream renames ~206 decomp symbols and 18 files,
  so **every later stream must be written against the renamed tree** — a `book/`
  stream added later would otherwise sort first and try to patch symbols that no
  longer exist under those names. `n64/OcarinaOfTime/patches/ORDER` lists
  `personal` first.

`apply.sh` walks the streams in that order, `git am`-ing each stream's numbered
patches. It refuses to run if the checkout is not at the pin, and refuses if an
interrupted `git am` left `.git/rebase-apply` behind (telling you to
`git -C <checkout> am --abort`). **Regenerating one stream:** rebuild just that
stream's commits in the checkout and `git format-patch --base=<pin>` them into
their subfolder — the other streams are untouched. This is the SuperMario64
shape; all four games were converted to it 2026-09-06 (verified: each game's
streams `git am` clean onto its pin).

### The series must still apply — gated across all projects

`tools/check_patches_apply.sh` (imps root) resets each project to its pin and
runs its own `apply.sh`, so it exercises stream `ORDER`, both lanes, and the pin
guard. Verified 2026-09-07: BanjoKazooie 4, MajorasMask 2, OcarinaOfTime 225,
SuperMario64 5 + 1 libultraship — all clean; `libultraship/` skipped (docs-only,
no `apply.sh`). This is the gate for the repo's primary goal (master
`CLAUDE.md`, "Patch philosophy"): a patch that no longer applies has failed at
its job.

### A `book/` stream is comment-only BY CONTRACT — and that is gated

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

### Never build a checkout from a foreign toolchain via a bind mount — copy the source into the throwaway container first

libultraship at 1.3.1-482+ (banjo, mario) writes build artifacts INTO its
submodule source dir even for an out-of-tree configure, so a fedora:44
verification container that builds `-S /proj/<checkout> -B /tmp/b` leaves
Fedora-compiled `.a`s inside the checkout, and the next podman (ubuntu) build
silently reuses them — bit us 2026-09-01 as a `libmonocypher.a … can not be
used when making a PIE object` link failure in mario's `make build`.
Recovery: `git clean -fdx` in the submodule (+ `git checkout --` any tracked
file the build overwrote, e.g. Ghostship's `src/generate_keys_header`) and
wipe `build-cmake/`.

## Derived artifacts — where drift occurs, and what the source of truth is

(Maintainer request, 2026-09-01.) Much of the N64 family is DERIVED from files
inside the pinned checkouts. Those copies are correct **at the pin** and
rot silently when the pin moves — so **every pin bump must re-verify each
derived artifact against its source** (this is part of the pin-bump operation
in the master `CLAUDE.md` agent contract). The pairs:

| Derived artifact (imps) | Source of truth (in the checkout) | Drift notes |
|---|---|---|
| `n64/<Project>/Dockerfile` | the upstream CI workflow's Linux job (Shipwright: `generate-builds.yml`; 2ship/Lighthouse/Ghostship: `main.yml` build-linux) | from-source lib versions (SDL 2.30.3, tinyxml2 10.0.0, libzip 1.10.1), base-OS choice, build flags — all hand-copied. Where a deps list exists as a FILE it is `COPY`d from the checkout at image build (2ship `apt-deps.txt`, Shipwright `linux-build-deps/apt.txt`, Ghostship `libultraship/requirements.txt`) and stays auto-current; the inline extras and steps do not. (`COPY`, not `RUN --mount=type=bind` — a build-time bind mount is read by the confined `container_t` RUN process with the file's on-disk SELinux label, so a `:Z`-poisoned checkout fails a host-side `podman build` with an MCS-mismatch AVC and a build mount has no relabel step; `COPY` is read by buildah as the unconfined host user. Fixed across all four Dockerfiles 2026-09-01.) Also: runner images pre-provide tools a bare base lacks (modern cmake on 22.04 and ≥3.30 on 24.04 → the Kitware blocks; python3; imagemagick for SoH's configure-time AppImage icon; noble's shaderc/spirv-tools ABI skew → the libshaderc_shared.so symlink) — CI won't notice those needs changing, we must. |
| `n64/<Project>/installdependencies.sh` | `docs/BUILDING.md` Fedora section (Lighthouse/2ship/Ghostship) or `linux-build-deps/dnf.txt` (Shipwright) | list is inlined by design (works before first fetch) — re-diff against the doc at every pin bump. Some lines are OURS via patches (banjo SDL2_net = patch 0001; mario libshaderc = patch 0004; mm audio libs ogg/vorbis/opus/opusfile = patch 0002): derive from the PATCHED doc, and if upstream merges those patches, the doc and script converge on their own. |
| `n64/<Project>/build.sh` + `Makefile` build targets | upstream CMake target names and flags (`GenerateSohOtr` / `Generate2ShipOtr` / `GeneratePortO2R`, `BUILD_REMOTE_CONTROL`, `cpack -G External`, Ghostship's `.tcc` dir) | target names have changed across pins before (ocarina's ZAPDTR→torch restructure); check them each bump. |
| `patches/*.patch` | upstream code itself | the core case — covered by the pin-bump rebase procedure. |
| `tasks/reference/<project>/` docs | the pinned source | covered by per-doc provenance banners. |
| pin comments in `fetch.sh` (date, describe, "tip of develop") | the `PIN_SHA` itself | update the prose when updating the SHA. |
| per-project `CLAUDE.md` facts (submodule SHAs, patch lists, gotchas) | the checkout + `patches/` | re-verify at every pin bump and series change. |
| `n64/libultraship/fetch.sh` `PIN_SHA` | the crawl iteration log in `tasks/reference/libultraship/crawl.md` | the two advance together, one commit per iteration; check fork topology (`git merge-base`) before assuming a new pin descends from the documented one. |
| the FUTURE upstream-container-CI patches (`tasks/*-upstream-container-ci.md`) | both the Dockerfile AND the workflow | double-derived; their acceptance strategy requires re-checking fidelity against whatever CI looks like at submission time. |

## libultraship — the shared engine

`libultraship` is the shared engine under all four N64 ports
(https://github.com/Kenix3/libultraship). Docs-only project: no patches, no
build scripts — its `fetch.sh` pins whichever commit the reference-doc crawl
currently describes. The crawl is **complete** (2026-09-01, 18 iterations —
13 release tags + the 4 games' submodule pins + Ghostship's newer fork pin);
the 8-doc set lives at `tasks/reference/libultraship/` with git history as
the time axis, and `tasks/reference/libultraship/crawl.md` holds the protocol
+ iteration log (a game's future LUS pin bump reopens it). Current doc state =
Ghostship's `c151cc91` (1.3.1-544, a KiritoDv FORK branch — see the drift
table's fork-topology caveat).

## Projects

- `n64/OcarinaOfTime/` — Ship of Harkinian
  (https://github.com/HarbourMasters/Shipwright), pinned at `acdbc651d`
  (tip of `develop`, 2026-09-01; submodules libultraship + torch). Details:
  `n64/OcarinaOfTime/CLAUDE.md`. Status: one code patch (a 145-file decomp
  rename), ported from the maintainer's old fork; patched tree
  **build-verified on-host 2026-09-01 (William Emerison Six
  <billsix@gmail.com>)**. The old fork's
  docs-only commits were migrated into
  `n64/OcarinaOfTime/CLAUDE.md` + `tasks/reference/ocarina/` per the
  documentation structure above (stale fork-era claims fixed or bannered
  in the move); its submodule-pin changes were dropped as obsolete.
  Also carries a podman build (`Dockerfile` ubuntu-22.04 CI mirror +
  `Makefile` → `out/soh.appimage`, verified nested 2026-09-01 and
  **built + run on-host 2026-09-01 (William Emerison Six
  <billsix@gmail.com>)** — pipeline closed) and a container-verified
  `installdependencies.sh`.
- `n64/MajorasMask/` — 2 Ship 2 Harkinian
  (https://github.com/HarbourMasters/2ship2harkinian), pinned at
  `04a1a4319` (tip of `develop`, 2026-05-31; submodules libultraship +
  ZAPDTR + OTRExporter — pre-torch pipeline). Details:
  `n64/MajorasMask/CLAUDE.md`. Status: two patches — the 64-bit audio/scheduler
  fixes (a strong upstream-submission candidate), exported verbatim from
  the maintainer's old `fedora44Fixes` fork branch and verified
  byte-identical on apply, plus a BUILDING.md fix adding the four
  required audio libraries (upstream candidate, found 2026-09-01 by the
  install-script container verification); patched tree **build- and
  run-verified on-host 2026-09-01 (William Emerison Six
  <billsix@gmail.com>)**. Also carries a
  podman build (`Dockerfile` + `Makefile` → AppImage), ported from the old
  fork's `podmanBuildAppImage` branch as native imps files — the first
  container build in imps; the `ci` variant's AppImage built on-host
  2026-09-01 (William Emerison Six <billsix@gmail.com>).
- `n64/SuperMario64/` — Ghostship
  (https://github.com/HarbourMasters/Ghostship), pinned at `49c5312a`
  (tip of `develop`, 2026-09-01 — deliberately modern: upstream had
  merged the maintainer's always-fly-on-triple-jump cheat, so it needs no
  patch; submodules libultraship 1.3.1-544 + Torch). Details:
  `n64/SuperMario64/CLAUDE.md`. Status: 3-patch cheat series (Super Jump,
  Infinite Air Jumps, Disable Skybox — plus a libshaderc-devel doc fix,
  an upstream candidate) ported 2026-09-01 from the old fork's topic
  branches across upstream's hooks→events restructure; **fully verified
  2026-09-01**: byte-identical on apply, builds in sandbox and on the
  maintainer's host, runs with all three cheats in the menu. Also carries a **Sphinx book** (`SuperMario64/book/`, *How a Production Game
  Is Built* — 16 chapters + appendices, HTML/EPUB/PDF) that `literalinclude`s
  this source by doc-region; see `SuperMario64/CLAUDE.md`. Run
  gotchas (Vulkan-on-RADV hang → OpenGL config; libtcc rpath) recorded
  in `n64/SuperMario64/CLAUDE.md`. The old
  fork's doc set migrated to `tasks/reference/mario64/` (bannered — the
  events restructure postdates them) and its cheat-idea task stubs to
  `tasks/mario64-*.md`; the messy `bill` branch history was deliberately
  not ported. Also carries a podman build (`Dockerfile` ubuntu-24.04 CI
  mirror + `Makefile` → `out/ghostship.appimage`, verified nested
  2026-09-01 and **built on-host 2026-09-01 (William Emerison Six
  <billsix@gmail.com>)**; `run.sh` seeds the OpenGL renderer by default
  for the from-source build (2026-09-06), while a directly-launched
  AppImage still picks Vulkan — see the RADV Vulkan-hang caveat in
  `n64/SuperMario64/CLAUDE.md`) and a
  container-verified `installdependencies.sh`. Also carries a
  **Sphinx book** (`SuperMario64/book/`, *How a Production Game Is Built* —
  16 chapters + appendices, HTML/EPUB/PDF via its own Dockerfile/Makefile) that
  `literalinclude`s this source by doc-region; see `SuperMario64/CLAUDE.md`.
- `n64/BanjoKazooie/` — Lighthouse
  (https://github.com/HarbourMasters/Lighthouse), pinned at `6d30df9a`
  (tip of `develop`, 2026-09-01, just past the 1.0.0 release; submodules
  libultraship 1.3.1-482 + Torch). Details: `n64/BanjoKazooie/CLAUDE.md`.
  Status: 4-patch series exported from the maintainer's `fixOnFedora`
  branch (Fedora build-deps doc fix, bk.o2r version stamp, the
  post-ROM-import freeze fix, and a JeodC review round — the series is a
  submitted upstream PR and retires if merged); patch 0002's lost commit
  subject repaired during export; verified byte-identical on apply, and
  the patched tree **builds and runs** (2026-09-01: compiled in the
  podman builder nested; AppImage `make run` confirmed on the
  maintainer's host). Also carries a podman build (`Dockerfile`
  ubuntu-24.04 CI mirror + `Makefile`, derived from upstream's
  `main.yml` build-linux job) — verified end to end
  (image/build/appimage/run); its task is archived at
  `tasks/archive/banjo/2026/09/01/`. The `bill` branch's doc set (8 reference docs + the
  freeze investigation) migrated to `tasks/reference/banjo/`.
- `n64/libultraship/` — the shared engine (see the "libultraship" section
  above). Docs-only; the reference crawl lives at
  `tasks/reference/libultraship/`.
