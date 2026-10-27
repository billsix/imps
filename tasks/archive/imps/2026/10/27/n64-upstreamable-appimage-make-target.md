# Upstreamable AppImage patch: standard Dockerfile/Makefile `make appimage` + CI rewire, per N64 port

**Status:** done 2026-10-27 — all five ports carry the `upstreamable-ci-appimage` patch and all five
AppImages are build-verified (Results table). Go-ahead 2026-10-26 (William Emerison Six
<billsix@gmail.com>: "go ahead with your recommendations"). The streams were later reorganized under the
`upstreamable-<slug>` convention (`tasks/archive/imps/2026/10/27/imps-upstreamable-stream-reorg.md`).
**Priority:** 5 **Difficulty:** 6
**Created:** 2026-10-24 (William Emerison Six <billsix@gmail.com>). Requested: "for all of the n64
projects, make a patch that is intended to be upstreamed that looks at the CICD for making the linux
appimage, and make a Dockerfile/Makefile (using the normal contract) that includes a 'make appimage'
target, and update the CICD file to use that to create the output."

## BLUF

For each of the five N64 ports in imps (github.com/billsix/imps), add an **upstream-bound patch** (a
`patches/upstreamable-ci-appimage/` stream entry) that commits, **into the upstream repo**, a standard
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
  lane, patches are grouped into **purpose streams** (subfolders: `upstreamable-<slug>/` for each PR unit,
  plus `cheats/`, `book/`), each internally numbered `0001-…`. The AppImage-CI patch is its own
  **`upstreamable-ci-appimage/`** unit: a commit with a reviewer-facing message, touching only
  CI/docker/make files (disjoint from code streams → commutes, needs no `ORDER` change). Workflow: do the
  work as a commit in the checkout, then `git format-patch --no-cover-letter --base=<pin> <pin>..HEAD -o
  patches/upstreamable-ci-appimage/`, stage in imps, gate with `tools/check_patches_apply.sh <Game>` (and
  the isolation gate `tools/check_upstreamable_applies.sh <Game> upstreamable-ci-appimage`), and note it
  in the per-project `CLAUDE.md` patch list. (The streams were reorganized under the `upstreamable-<slug>`
  convention 2026-10-27 — `tasks/archive/imps/2026/10/27/imps-upstreamable-stream-reorg.md`.)
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
2. **Capture as a patch:** `git format-patch` the commit into `<game>/patches/upstreamable-ci-appimage/`, with
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
  every other upstream-bound patch (own commit, reviewer-facing message, `patches/upstreamable-ci-appimage/`,
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

## Findings at execution (2026-10-26) + placement decision

Reading each port's upstream tree showed the "add a root `Dockerfile` + `Makefile`" premise is only
partly right — the collisions are heterogeneous, and two ports already containerize for a *different*
purpose:

| Port | Root `Makefile`? | Root `Dockerfile`? | Note |
|---|---|---|---|
| SuperMario64 (Ghostship) | **yes** (upstream's generic CMake-driver) | no | must not clobber the Makefile |
| OcarinaOfTime (Shipwright) | no | **yes** | `ubuntu:20.04` *local dev* container, **unused by any workflow** |
| MajorasMask (2ship2harkinian) | no | **yes** (+ `run-docker.sh`) | 32-bit *GUI dev* container, **unused by CI** |
| BanjoKazooie (Lighthouse) | no | no | clean |
| PaperMario (PaperBoat) | no | no | clean |

**Decision (William Emerison Six <billsix@gmail.com>, 2026-10-26): put the CI build container in a
per-port top-level `docker/` directory** — `docker/Dockerfile` (the CI-mirror env, from the imps-side
Dockerfile, build context = repo root) + `docker/Makefile` (the `make appimage` wrapper,
`CONTAINER_CMD` auto-detect, accepts a CI-supplied o2r). Each Linux CI job is rewired to call
`make -C docker appimage`, keeping its checkout / o2r-download / artifact-bundle / upload steps. This is
uniform across all five, collides with nothing upstream ships, and leaves the existing dev
Dockerfiles/`run-docker.sh` untouched.

## Results (2026-10-26) — all five patches landed

Each port carries a `docker/Dockerfile` + `docker/Makefile` (CI-mirror env, `make -C docker appimage`,
`CONTAINER_CMD` auto-detects podman→docker) committed into the upstream tree as a
`patches/upstream-candidates/` entry, with its Linux CI job rewired to call `make -C docker appimage`
(the generate-otr/o2r job and the uploaded artifact left unchanged). `tools/check_patches_apply.sh`
is green for all five.

The CI patch is its own **`upstreamable-ci-appimage` unit** in every port (the streams were reorganized
under the one-PR-per-`upstreamable-<slug>`-stream convention 2026-10-27,
`tasks/archive/imps/2026/10/27/imps-upstreamable-stream-reorg.md`; it had briefly been `upstream-candidates/0001` after a
2026-10-26 renumber). It is `0001-` and the sole patch in that unit, disjoint (only `docker/` + the workflow)
so the applied tree is unchanged and `check_patches_apply` stayed green for all five.

| Port | New patch | Apply-gate | AppImage build |
|---|---|---|---|
| SuperMario64 | `upstreamable-ci-appimage/0001` | ✅ 52+1 | ✅ **verified** (nested `make -C docker appimage` → valid AppImage) |
| MajorasMask | `upstreamable-ci-appimage/0001` | ✅ 2 | ✅ **verified** 2026-10-27 (16 MB x86-64 ELF; o2r injected) |
| BanjoKazooie | `upstreamable-ci-appimage/0001` | ✅ 5 | ✅ **verified** 2026-10-27 (13 MB x86-64 ELF; o2r injected) |
| OcarinaOfTime | `upstreamable-ci-appimage/0001` | ✅ 527 | ✅ **verified** 2026-10-27 (24 MB x86-64 ELF; build self-generated the o2r) |
| PaperMario | `upstreamable-ci-appimage/0001` (step 0: container built from scratch) | ✅ 3 | ✅ **verified** 2026-10-27 (21 MB x86-64 static-pie ELF; o2r self-generated) |

Per-port seam notes:
- **SM64 / Banjo** download the o2r into `build-cmake(/…)`; **MM** into `build-cmake/mm`; **OoT** into
  `build-cmake/soh` — each Makefile's `O2R` points there, and `make appimage` requires it (accept-only;
  generation is `tasks/n64-container-generate-o2r.md`).
- **PaperMario** has NO separate o2r job — its build self-generates `paperboat.o2r` (GeneratePortO2R is
  a build dependency), so its `make appimage` just builds + cpacks (no `O2R`). This is step 0: it had no
  container build at all; one was created from scratch.
- **OoT** build-linux is an x86_64/aarch64 **matrix**; its Dockerfile is arch-generic (`$(uname -m)`) so
  both legs are preserved. Its `.gitignore` gained `!docker/Makefile` (blanket CMake `Makefile` ignore).
- Each port's stale checkout needed a one-off `git fetch origin <pin>` to obtain the pin object —
  `fetch.sh` only clones-then-checks-out and never fetches new commits into an existing clone, so after a
  pin re-bump it fails with "unable to read tree". Offered to add a `git fetch` to the `fetch.sh`es.

## Verification status — all five ports build-verified (2026-10-27)

The per-port patches were written from the SuperMario64 template, and at the maintainer's instruction
(William Emerison Six <billsix@gmail.com>, 2026-10-26: "just go ahead and do all of them, note that I
haven't confirmed") were completed BEFORE their builds ran. The four remaining nested
`make -C docker appimage` builds (MM, Banjo, OoT, PaperMario) were then run from scratch, sequentially,
by a one-shot harness — **all four produced valid x86-64 ELF AppImages** (`VERIFY_OK`), so the shared
template carries no replicated bug. That harness was **promoted to `tools/verify_appimage_builds.sh`**
(generalized to all five ports, logs to `/tmp/verify-appimage-<Port>.log`); re-run it at every pin bump
(the derived-artifact-drift rule).

Notes from the run:
- **MM / Banjo** are accept-only: the harness injected the port-o2r (ROM-free port assets) from each
  checkout's root copy into the `build-cmake/…` path cpack reads. **OoT's build self-generated
  `build-cmake/soh/soh.o2r`** with no injection, so for OoT the accept-only guard is already moot — the
  follow-up `tasks/n64-container-generate-o2r.md` is effectively satisfied there, and is the model to
  push to the other accept-only ports.
- **PaperMario** self-generates `paperboat.o2r` in-build (no o2r step) and links static-pie.

## Superseded tasks (folded into this one)

The four earlier per-port CI tasks — `banjo-upstream-container-ci`, `mario64-upstream-container-ci`,
`mm-upstream-container-ci`, `ocarina-upstream-container-ci` (all P6, "FUTURE, not for the 2026-09-01
batch") — are subsumed by this consolidated task (which also covers the fifth port, PaperMario). They
were archived 2026-10-26 under `tasks/archive/{banjo,mario64,mm,ocarina}/2026/10/26/` with a
supersession banner pointing here.

## Related

- Existing related task: `tasks/banjo-upstream-container-ci.md` (Banjo-specific precedent), and the
  existing upstream build/dep patches under `BanjoKazooie/patches/upstreamable-fixonfedora/`.
- Also present: `tasks/gzdoom-appimage-packaging.md` (a non-N64 AppImage task — different toolchain).
- Reference: `tasks/reference/imps/{patch-streams-design.md,derived-artifact-drift.md,n64-build-gotchas.md}`.
