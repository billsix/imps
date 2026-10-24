# Upstreamable AppImage patch: standard Dockerfile/Makefile `make appimage` + CI rewire, per N64 port

**Status:** in progress — go-ahead given 2026-10-26 (William Emerison Six <billsix@gmail.com>:
"go ahead with your recommendations"); open questions resolved below.
**Priority:** 5 **Difficulty:** 6
**Created:** 2026-10-24 (William Emerison Six <billsix@gmail.com>). Requested: "for all of the n64
projects, make a patch that is intended to be upstreamed that looks at the CICD for making the linux
appimage, and make a Dockerfile/Makefile (using the normal contract) that includes a 'make appimage'
target, and update the CICD file to use that to create the output."

## BLUF

For each of the five N64 ports in imps (github.com/billsix/imps), add an **upstream-bound patch** (a
`patches/upstream-candidates/` stream entry) that commits, **into the upstream repo**, a standard
`Dockerfile` + `Makefile` with a **`make appimage`** target, and rewires that repo's Linux CI workflow
to **produce its AppImage by calling `make appimage`** instead of the current inline build+cpack+mv
steps. "Done" = each port carries such a patch (applies cleanly via the imps gate, `make appimage`
yields the same AppImage artifact the port's CI produces today, and the rewired workflow uses it), each
patch's commit message is shaped for upstream submission, and PaperMario — the one port with no
container build at all — first gets the imps-side Dockerfile/Makefile it's missing. The patches are
**offered upstream**; actually opening PRs is a later, maintainer-driven step.

## Context (read first)

- **Read first:** `/foo/opt/imps/CLAUDE.md` (master build contract — the `fetch.sh`→`apply.sh`→
  `build.sh`→`run.sh` model), `/foo/opt/imps/n64/CLAUDE.md` (family contract, project index, the
  derived-artifact-drift rule), and the reference docs `tasks/reference/imps/{patch-streams-design.md,
  derived-artifact-drift.md,n64-build-gotchas.md}`.
- **The five ports (all HarbourMasters libultraship-based PC ports; verified 2026-10-24):**

  | imps dir | Upstream repo | Checkout dir | Pin | Container build in imps today? | Upstream CI AppImage today |
  |---|---|---|---|---|---|
  | `OcarinaOfTime/` | github.com/HarbourMasters/Shipwright | `Shipwright/` | `41ae6cd3` | **Yes** (Dockerfile+Makefile) | `generate-builds.yml` (build-linux) |
  | `MajorasMask/` | github.com/HarbourMasters/2ship2harkinian | `2ship2harkinian/` | `f1dda4c2` | **Yes — reference impl** | `main.yml` |
  | `SuperMario64/` | github.com/HarbourMasters/Ghostship | `Ghostship/` | `40eef138` | **Yes** | `main.yml` |
  | `BanjoKazooie/` | github.com/HarbourMasters/Lighthouse | `Lighthouse/` | `4e8dfd23` | **Yes** | `main.yml` |
  | `PaperMario/` | github.com/HarbourMasters/PaperBoat | `PaperBoat/` | **No — the gap** | `build.yml` + `release.yml` |

- **Key finding — most of the machinery already exists.** Four of five ports already have an imps-side
  containerized build with a working **`make appimage`** (reference: `n64/MajorasMask/{Makefile,
  Dockerfile,Dockerfile.ubuntu26.04}`), and **every** upstream repo already produces a Linux AppImage in
  its own CI via **CPack `-G External` + linuxdeploy** (machinery in each repo's `CMake/Packaging.cmake`
  / `cmake/packaging.cmake`; downloads `linuxdeploy-x86_64.AppImage` pinned to `1-alpha-20240109-1`,
  builds an AppDir with the per-game `.desktop`+icon, emits `--output=appimage`; CI = ubuntu runner →
  cmake/ninja Release → `cpack -G External` → `mv build-cmake/*.appimage <name>.appimage` → upload). So
  this task is **not inventing an AppImage build** — it is (a) packaging the existing container build as
  an upstreamable Dockerfile+Makefile, and (b) replacing each workflow's inline build+cpack+mv with a
  single `make appimage` call. The seam is exact: the imps `appimage` target already does
  `cpack -G External` inside the container.
- **imps patch-series mechanics (how to add the patch):** two lanes — game-tree (`patches/`, base = the
  port pin, applied by `apply.sh`) and the libultraship submodule (`patches-libultraship/`). Within a
  lane, patches are grouped into **purpose streams** (subfolders: `standard-c/`, `upstream-candidates/`,
  `personal/`, `cheats/`, `book/`), each internally numbered `0001-…`. A new AppImage-CI patch is a
  textbook **`upstream-candidates/`** entry: its own commit with a reviewer-facing message, touching only
  CI/docker/make files (disjoint from code streams → commutes, needs no `ORDER` change). Workflow: do the
  work as a commit in the checkout, then `git format-patch --no-cover-letter --base=<pin> <pin>..HEAD -o
  patches/upstream-candidates/`, stage in imps, gate with `tools/check_patches_apply.sh <Game>`, and note
  it in the per-project `CLAUDE.md` patch list. Precedent: `BanjoKazooie/patches/upstream-candidates/
  0001-fix-build-dependencies…Fedora.patch`, and the existing task `tasks/banjo-upstream-container-ci.md`.
- **The imps-side container template (the "normal contract" to mirror in the patch):** the MM reference
  `Makefile` exposes `help image image-export image-import build appimage run shell clean distclean`;
  `image` builds with context = the checkout; `build` runs `cmake -S /src -B /src/build-cmake -GNinja
  -DCMAKE_BUILD_TYPE=Release` then `cmake --build`; `appimage: build` does `cd build-cmake && cpack -G
  External` then copies `*.appimage`→`/out/<game>.appimage`; `run` runs on the host; `clean` never
  touches `runDir/`. `PODMAN_RUN_FLAGS` (nested `--cgroups=disabled`) on every `run`, never `build`. The
  `Dockerfile` is `FROM ubuntu:22.04`, **deliberately mirrors the upstream CI environment** (CC/CXX
  gcc-12, the `apt-deps.txt` list, SDL2/tinyxml2/libzip-no-crypto from source) — see Q1: an upstream
  patch must target the port's CI base, not the maintainer's Fedora-44 template.

## Plan (per port; sketch)

0. **PaperMario first** — it has neither Dockerfile nor Makefile on the imps side. Give it the standard
   container build (modelled on MM, adapted for PaperBoat's no-submodule / vendored-LUS layout and its
   `run.sh <ROM>` SHA-1 trim) **before** shaping its upstream patch. (Note PaperBoat already
   `APPIMAGE_EXTRACT_AND_RUN=1`s and has a `release.yml` that drafts a release.)
1. **For each port, build the upstreamable artifact in the checkout:** add a `Dockerfile` + `Makefile`
   (mirroring the upstream CI build env, with `make appimage` wrapping `cpack -G External`) committed
   into the upstream tree, and edit that repo's workflow (`generate-builds.yml` / `main.yml` /
   `build.yml`) so the Linux job's build+package steps become a `make appimage` invocation that emits the
   same-named artifact (`soh.appimage`, `Paperboat.AppImage`, …) and uploads it unchanged.
2. **Capture as a patch:** `git format-patch` the commit into `<game>/patches/upstream-candidates/`, with
   an upstream-reviewer-facing message. Verify with `tools/check_patches_apply.sh <Game>`.
3. **Verify the build equivalence:** nested, `make image` + `make appimage` for the port produces a
   working AppImage (artifact parity with what the port's CI emits today). Per the derived-artifact-drift
   rule, these files are derived from the pinned checkout and must be re-verified on any pin bump.
4. **Document:** note each new patch in the per-project `CLAUDE.md` patch list; update
   `tasks/reference/imps/derived-artifact-drift.md` if the drift surface changes.

## Decisions (maintainer, 2026-10-24)

- **Container base = match each port's current CI, as-is.** Keep the container "whatever corresponds to
  the CICD as it is right now" — i.e. the existing ubuntu-CI-mirror base (`FROM ubuntu:22.04`, CC/CXX
  gcc-12, the port's own `apt-deps.txt` + from-source SDL2/tinyxml2/libzip-no-crypto). The family
  template applies to the **Makefile target shape** (`help/image/appimage/run`, `PODMAN_RUN_FLAGS`
  only on `run`), **not** the Fedora-44 base. Do **not** re-base onto Fedora.
- **Patches are standard upstream patches, and the goal is to actually land them.** Shape each like
  every other upstream-bound patch (own commit, reviewer-facing message, `patches/upstream-candidates/`,
  gated by `tools/check_patches_apply.sh`). The maintainer **intends to get these upstreamed** and
  judges them low-effort to land — so keep the diff minimal and CI-shaped. Agent stages the patches;
  the maintainer submits the PRs.

## Decisions — open questions resolved (William Emerison Six <billsix@gmail.com>, 2026-10-26)

All three resolved per the agent's recommendations ("go ahead with your recommendations"):

1. **Docker vs. podman in the committed Makefile → auto-detect `CONTAINER_CMD` (podman→docker).** The
   upstreamed Makefile uses `CONTAINER_CMD ?= $(shell command -v podman >/dev/null 2>&1 && echo podman
   || echo docker)` so it runs on upstream's bare-ubuntu runners (Docker) and the maintainer's podman
   host unchanged. Unlike the imps-side Makefiles, which hardcode `podman`, the upstream-bound one must
   NOT hardcode.
2. **One task, not a step-task tree.** Kept as this single task with the per-game status table; promote
   a port to its own step-task only if it genuinely diverges.
3. **PaperMario folded in as step 0.** Giving PaperMario the standard imps container build (it's the one
   port missing it) is step 0 of this task, not a separate prerequisite task.

## Superseded tasks (folded into this one)

The four earlier per-port CI tasks — `banjo-upstream-container-ci`, `mario64-upstream-container-ci`,
`mm-upstream-container-ci`, `ocarina-upstream-container-ci` (all P6, "FUTURE, not for the 2026-09-01
batch") — are subsumed by this consolidated task (which also covers the fifth port, PaperMario). They
were archived 2026-10-26 under `tasks/archive/{banjo,mario64,mm,ocarina}/2026/10/26/` with a
supersession banner pointing here.

## Related

- Existing related task: `tasks/banjo-upstream-container-ci.md` (Banjo-specific precedent), and the
  existing upstream build/dep patches under `BanjoKazooie/patches/upstream-candidates/`.
- Also present: `tasks/gzdoom-appimage-packaging.md` (a non-N64 AppImage task — different toolchain).
- Reference: `tasks/reference/imps/{patch-streams-design.md,derived-artifact-drift.md,n64-build-gotchas.md}`.
