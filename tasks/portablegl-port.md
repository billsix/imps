# Port PortableGL into imps, with every demo easy to build in debug and release

**Status:** proposed — needs go-ahead (filed 2026-11-22 at the request of William Emerison Six <billsix@gmail.com>)
**Priority:** 5
**Difficulty:** 3 (no patches needed to start; the work is the carrier scripts and a build-everything target)
**Created:** 2026-11-22

## BLUF

Add PortableGL (`https://github.com/rswinkle/PortableGL`, a software implementation of OpenGL 3.x core
in one C99 header) to imps as a pinned, self-contained project folder, following the imps per-project
contract. Done means: from a fresh clone, `installdependencies.sh` then `build.sh` builds **every demo,
example and regression test** in the upstream tree, in **debug** and in **release** (`./build.sh debug`,
`./build.sh release`, default release), `run.sh` launches a chosen program, and a podman
`Dockerfile`/`Makefile` offers the same on top. No upstream patches are needed to start.

## Maintainer request (2026-11-22)

> make a task in imps to add https://github.com/rswinkle/PortableGL/ to a port, where all demos in it
> are easily built both in debug mode and release mode

## Context (cold start)

- **imps contract.** Read `CLAUDE.md` (master) "Per-project folder contract" and `games/CLAUDE.md`
  (the family build/patch contract, the `fetch.sh` pin convention, the Dockerfile/Makefile targets).
  The native host build is the baseline: `fetch.sh`, `installdependencies.sh`, `build.sh`, `run.sh`, each
  host-runnable, with the checkout gitignored and a `runDir/` beside the scripts (never inside the
  checkout, never deleted). `apply.sh` and `patches/` exist only once there is a patch.
  The closest existing folders to copy from: `games/gzdoom/` (scripts plus a Dockerfile and Makefile) and
  `games/mineclonia/` (a pinned build with no patch series).
- **What PortableGL is (checked 2026-11-22 against the upstream tree).** MIT licence (also contains
  Fabrice Bellard's TinyGL clipping code, MIT). `portablegl.h` is generated from `src/` by
  `generate_gl_h.py` and also committed. Tags are `0.98.0`, `0.99.0`, `0.100.0`; **`0.100.0` is commit
  `63a55db75ab07619797a93ff9bf3909355d27950`**; `master` was at
  `5a0b12c003eb834e9718d01db9eb9664f0778d87` (2026-10-30) when this was written. The pin is the
  maintainer's choice (open question 2).
- **What there is to build.** Four groups, each with a **premake5-generated GNU Makefile that takes
  `config=debug|release`** (debug is the default; `make config=release` builds optimized; `make verbose=1`
  shows commands; `make help` lists targets):
  - `examples/` (`original/` c and c++ examples, `classic/gears.c`, `webgl_lessons/lesson1..16`),
  - `demos/` (about 20 targets: sphereworld variants, cubemap, grass, modelviewer, pointsprites,
    shadertoy, raytracing_1weekend, texturing, multidraw, testprimitives, particles, three ImGui demos,
    `assimp_convert`, `video_texturing`),
  - `testing/` (regression `run_tests` and its compile-time variants `d16`, `rgb565`, `no_depth_no_stencil`,
    `clamp_border`, plus the performance programs; `make run_tests` needs only a C++ compiler),
  - `backends/` (hello-triangle on x11, wayland, win32, gtk3/4, qt, fltk; each needs its own toolkit).
- **Dependencies.** The header itself has none. The examples and demos need **SDL2** (`libsdl2-dev` on
  Debian; `SDL2-devel` on Fedora). Per-demo extras that the audit step must pin down:
  `assimp_convert` needs libassimp, `video_texturing` needs a video decoder library, the ImGui demos use
  vendored ImGui from `external/` (verify it builds without network), and the backend programs need
  their toolkits (leave them out of "all demos" unless the maintainer wants them, open question 3).
- **Upstream's own rules.** Upstream has an `AGENTS.md`: do not edit files before being told to, do not
  strip comments, keep scripting paths relative, and use asserts for invariants instead of
  always-on checks. It matters only if a patch is ever upstreamed; the imps scripts are the maintainer's.
- **Where it lives.** A new top-level family `graphics/` (see Decisions): PortableGL is a graphics library with
  demos, which fits neither `games/` nor the documentation-only families. The master `CLAUDE.md` "Families"
  list gets a line and `graphics/CLAUDE.md` is new.

## Plan

1. **Confirm the build by hand first.** In a throwaway fedora container: `git clone`, checkout the pin,
   `dnf install SDL2-devel gcc gcc-c++ make`, then `make -C examples config=debug`, the same for
   `release`, and for `demos/` and `testing/`; record in a reference doc
   (`tasks/reference/portablegl/build-and-demo-inventory.md`) which of the ~60 targets build, which need
   extra libraries, and the first error for each that fails. The Makefiles are generated and committed, so
   a fresh premake5 run is not needed for Linux (the upstream tree ships premake5 binaries for Windows and
   Mac only; do not add a premake dependency unless the committed Makefiles prove broken).
2. **The folder `graphics/portablegl/`**, with the new family doc `graphics/CLAUDE.md` and the master index line: `fetch.sh` (URL, pinned full
   SHA with tag and date comment, `commit.gpgsign false` repo-locally), `installdependencies.sh` (host
   package manager, inline package list, fails loudly if none), `build.sh`, `run.sh`, `README.md`
   (commands first), `CLAUDE.md` (tier-3: upstream, pin, build facts, index of reference docs),
   `.gitignore` (`checkout/`, `bldInstall/`, `runDir/`).
3. **`build.sh` takes the configuration and the group.** `./build.sh [debug|release] [examples|demos|testing|all]`,
   default `release all`; it runs `make -C checkout/<group> config=<cfg> -j"$(nproc)"` for each group,
   keep-going so one demo that needs a missing library does not hide the others, and prints a summary of
   which programs built and which did not. Output goes to a directory beside the scripts
   (`bldInstall/<config>/`): the upstream Makefiles write binaries into the source tree
   (`checkout/<group>/`), so `build.sh` copies the built programs out, and `clean` removes only the
   built programs, never `runDir/` or the checkout's tracked files. Verify where the premake Makefiles put
   their `obj/` and binaries (they are gitignored upstream) before deciding.
4. **`run.sh <program>`** runs a built demo with `runDir/` as the working directory, after linking or
   copying `media/` where upstream expects it (many programs load `../media/...` relative paths; check each
   and set the working directory or symlink accordingly, outside the checkout).
5. **Container layer** `Dockerfile` + `Makefile` following `games/CLAUDE.md`: image holds the toolchain and
   SDL2 only, source bind-mounted, `build` takes `BUILD_TYPE=Debug|Release` mapped to `config=`,
   `shell`/`shell-exec` share `SHELL_RUN_FLAGS`, `PODMAN_RUN_FLAGS` on `run` lines only, never on `build`.
   A headless smoke target runs each demo under Xvfb for a few frames, or `testing`'s `run_tests`, which
   needs no display and checks every frame against `expected_output`.
6. **Gate:** `make smoke` runs `run_tests` in debug and release (both must print "All tests passed") and
   starts each SDL demo headless long enough to render a frame, reporting a table. Debug vs release is also
   the first thing to compare: PortableGL has assert-based invariants that only fire in debug.
7. **Docs.** Reference doc from step 1, the tier-2 and master index lines, and `README.md` of the project.

## Decisions (maintainer, 2026-11-22)

1. **Location (corrected 2026-11-22):** a new top-level family **`graphics/`**, not a folder under `games/`. The
   project folder is `graphics/portablegl/`. A new family needs its tier-2 `graphics/CLAUDE.md` (the family's
   build contract and a one-line project index; copy the shape of `games/CLAUDE.md`, minus the game-data rules)
   and a line in the master `CLAUDE.md` "Families" list, so step 2 of the plan also creates those two files.
2. **Pin:** the release tag `0.100.0`, commit `63a55db75ab07619797a93ff9bf3909355d27950`.
3. **"All demos" means `examples/` and `demos/`.** `backends/` and the `testing/` performance programs
   are out of the default build. The regression program `run_tests` (needs only a C++ compiler) stays in
   as the smoke gate in step 6, because it is the cheapest proof that debug and release both work.

## Open questions

None. Steps 1 to 7 above already carry the answers; the `backends` group is not part of `build.sh`'s default and
stays an opt-in argument only if it is cheap to keep.

## History

- 2026-11-22: created at the maintainer's request.
- 2026-11-22: the maintainer answered the three questions (see Decisions), then corrected the location to a
  top-level `graphics/` family. Facts about PortableGL (tags, SHAs, build layout,
  dependencies) were read from the upstream repository's README, Makefiles and API on the same day; nothing
  has been built yet.
