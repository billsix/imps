# Port GZDoom into imps (new `games/` family) + a CLI-WAD-loading patch

**Status:** in progress — **Phase A (the `games/gzdoom/` carrier + Release build) is DONE + launch-verified
2026-09-20**: GZDoom `g4.14.2` + ZMusic `1.3.0` build in a Fedora-44 container, `make version` prints the
banner (exit 0), `make smoke WAD=<iwad>` loads an IWAD headless. Build needed `-DSYSTEMINSTALL=ON` so an
out-of-tree install finds `gzdoom.pk3` (see the Phase-C note). A first reference doc landed
(`tasks/reference/gzdoom/build-and-cli-wad-repro.md`). **Phase B is underway** — the Sphinx book
beginning shipped 2026-09-20, three chapters deep through the OpenGL renderer (`games/gzdoom/book/`).
**Also now required (maintainer, 2026-09-20): native host-build scripts** — `installdependencies.sh`,
`build.sh`, `run.sh` (the n64 games' host script set) so GZDoom builds and runs with **no container**; not
yet written (Phase A2 below). The Vulkan renderer chapter and the Phase-C CLI-WAD fix also remain. The
optional AppImage packaging is split to its own task (`tasks/gzdoom-appimage-packaging.md`). Filed 2026-09-20
(William Emerison Six <billsix@gmail.com>).
**Priority:** 5
**Difficulty:** 6 (a real C++ build with deps; the patch needs reading GZDoom's IWAD-selection code)

## BLUF

Bring **GZDoom** (the open-source Doom-engine source port, `github.com/ZDoom/gzdoom`) into imps as a
**code-patch carrier** under a NEW **`games/`** family, in three phases, in this order:
1. **Port it first** — fetch pristine GZDoom (pinned) + its ZMusic dependency and **build it in a
   container** (CMake, the maintainer's Fedora-44 template).
2. **Then plenty of reference docs** on how GZDoom works.
3. **Then a patch** that lets the built GZDoom **play a WAD file passed on the command line**, so the
   maintainer can skip GZDoom's startup **GUI** (which he hasn't learned) and just launch his many WADs from
   the CLI. Shape it as an upstream-submittable change — **nice if upstream takes it, but not required.**

"Done" = `games/gzdoom/` builds and runs GZDoom **natively on the host** (fetch → installdependencies →
build → run) *and* in a container from the pinned source, `tasks/reference/gzdoom/` documents it, and a
`patches/` change lets a CLI-passed WAD play without the GUI IWAD picker.

## Context (cold-start)

- **Upstream + pin.** GZDoom: `github.com/ZDoom/gzdoom`, pinned at tag **`g4.14.2`**. It requires **ZMusic**
  (`github.com/ZDoom/ZMusic`, pinned at **`1.3.0`**) built first. Both are the maintainer's known-good pins.
- **Build recipe (host-proven; adapt to a container).** CMake, ZMusic then GZDoom, each with
  `-DCMAKE_INSTALL_PREFIX=<install>` and `-DCMAKE_BUILD_TYPE=Debug|Release`, then `cmake --build` +
  `cmake --install`. GZDoom writes/uses a `gzdoom.ini` whose `[FileSearch.Directories]` `PATH=` points at the
  install's `share/games/doom/` (where its bundled `.pk3` resources land). Launch:
  `gzdoom -config gzdoom.ini -iwad <wad>` (base game WAD) and `-file <pwad>` (extra WADs) — **but the
  maintainer reports these did NOT reliably load a WAD for him** (he only got one to load by dropping it into
  a `~/` dot-folder), so the CLI-WAD path is genuinely broken/confusing, which is what Phase C fixes. Other
  GZDoom deps (SDL2, zlib, libjpeg, fluidsynth/OpenAL, bzip2, …) come from distro packages — CMake reports
  what's missing.
- **imps carrier model.** imps is a **code-patch carrier** (`../CLAUDE.md`): per-project `fetch.sh` (clone a
  pinned upstream into a gitignored `checkout/`) → `apply.sh` (`git am` the `patches/` series) → build. The
  `n64/` family is the exemplar of a *code-patch* family (real patch streams), which is what `games/` is —
  NOT a docs-only carrier like `unixutils/`/`android/`. Reference docs live natively in imps
  (`tasks/reference/gzdoom/`); patches carry only code. Unsigned checkout commits are authorized (fetch.sh
  sets `commit.gpgsign false`).
- **WADs / IWADs are the maintainer's own game data — NEVER committed** (same rule as the N64 ROMs): the
  build ships the engine + its bundled resources; the user supplies `doom.wad`/PWADs at runtime.

## Phase A — the `games/` family + the GZDoom carrier (port/build)

1. **New tier-2 family** `games/CLAUDE.md` — the "buildable open-source game/engine" carrier contract
   (a code-patch family like `n64/`; per-project fetch→apply→build; game data stays out; one line per game).
2. **`games/gzdoom/`** per the imps per-project contract:
   - `fetch.sh` — clone `github.com/ZDoom/gzdoom` @ `g4.14.2` AND `github.com/ZDoom/ZMusic` @ `1.3.0` into a
     gitignored `checkout/` (record each `PIN_SHA` with its tag/date); `commit.gpgsign false`; idempotent.
   - `apply.sh` — `git am --3way` the `patches/` series onto the GZDoom checkout, guarded at the pin.
   - `Makefile` + `Dockerfile` — Fedora-44 image with the C++/CMake toolchain + GZDoom's build deps; targets
     `fetch`, `apply`, `image`, `build` (**Release by default**: ZMusic then GZDoom via CMake into an install
     prefix; **document a `Debug` build too**, e.g. `make build BUILD_TYPE=Debug`), and a `run` that launches
     the built binary with a CLI-passed WAD. Thread `PODMAN_RUN_FLAGS`; `shell`/`shell-exec`.
     (GUI/display: GZDoom needs X/Wayland + audio to actually play — reuse the maintainer's GUI-passthrough
     Makefile blocks; a headless `-norun`/version check can gate the build in CI where no display exists.)
   - `patches/` (+ `ORDER`), `.gitignore` (checkout + build/install dirs), tier-3 `CLAUDE.md` (upstream URLs,
     both pins, build deps, the CLI-WAD patch summary, run instructions), `README.md` (fetch → apply → build
     → run `<wad>`).
3. **Verify the port:** `./fetch.sh && ./apply.sh && make image && make build` produces a runnable `gzdoom`;
   `make run WAD=<path>` launches it. Build + run are **self-verifiable in-session** (X/Wayland is
   available), so reproduce the failing CLI-WAD load with a real WAD and validate the Phase-C fix directly.

## Phase A2 — native host-build scripts (the main 2026-09-20 ask)

The maintainer wants GZDoom buildable and runnable **without a container**, through the same host-runnable
scripts the n64 games carry (`n64/OcarinaOfTime/` is the exemplar) — this is now the **primary** build path;
the podman `Dockerfile`/`Makefile` stays as an extra convenience layer (keep it). Per the master `CLAUDE.md`
native-baseline contract, add beside the existing `fetch.sh`/`apply.sh`:

1. **`installdependencies.sh`** — install GZDoom's *and* ZMusic's Fedora build deps on the host with `dnf`,
   run as root/`sudo`, guarded on `dnf` (fail loudly otherwise), package list **inlined** so it runs before
   the first fetch. Take the list from the Dockerfile's current dep set (`gcc-c++ cmake make git ninja-build
   pkgconf-pkg-config SDL2-devel zlib-devel libjpeg-turbo-devel bzip2-devel openal-soft-devel
   fluidsynth-devel libvpx-devel mesa-libGL-devel vulkan-loader-devel vulkan-headers gtk3-devel`); the Xvfb
   packages are a container-only smoke dep, not needed for a real host run.
2. **`build.sh`** — host cmake build: ZMusic then GZDoom into an install prefix **beside the script**
   (`bldInstall/`-style, no hardcoded home paths), with `-DSYSTEMINSTALL=ON` (the Phase-A fix so the binary
   finds its own `gzdoom.pk3`). Calls `./fetch.sh` when `checkout/` is missing, so with
   `installdependencies.sh` it is all a fresh clone needs. Release by default; document `BUILD_TYPE=Debug`.
3. **`run.sh`** — launch the built `gzdoom` with a gitignored `runDir/` as its cwd (so `gzdoom.ini`, saves,
   and config live there, not in the build tree), passing a CLI WAD via `-iwad`. WADs stay the maintainer's
   own game data — **never committed**, location never recorded here.

Then update `README.md` to lead with the native `installdependencies → fetch → apply → build → run` sequence
(container path second), the tier-3 `games/gzdoom/CLAUDE.md` to document the scripts, and `.gitignore` for
`bldInstall/` + `runDir/`. **Verify:** `./installdependencies.sh && ./build.sh && ./run.sh <wad>` reaches a
running GZDoom with **no `make`/podman** (stand in a bare `fedora:44` container for a host if needed).

## Phase B — a Sphinx teaching book ("How a Doom Engine Works") + reference docs

**Underway (2026-09-20).** The book beginning lives at `games/gzdoom/book/` (mario64 machinery: doc-region
markers in the checkout as the comment-only `patches/book/` stream, `literalinclude`d by name; builds HTML;
`patches/LANG=c`, proven comment-only). **Three chapters ship so far**, in the maintainer's teaching voice
(transformations as functions, terms defined before jargon):
1. **From launch to the main loop** (`d_main.cpp`) — startup → `D_DoomLoop`.
2. **IWADs, PWADs, and the lump filesystem** (`d_iwad.cpp`, `filesystem.cpp`) — with an admonition tying the
   IWAD picker to the Phase-C CLI-WAD goal.
3. **The OpenGL renderer** — the maintainer's *main* first interest, DONE. One 3D frame traced from
   "render the world now" to the single `glDrawArrays`: the shared HW renderer decides *what*
   (`src/rendering/hwrenderer/`), the GL backend decides *how* (`src/common/rendering/gl/`), and the
   pure-virtual `FRenderState::Draw` is the GL/Vulkan seam. Nine doc-region markers (`patches/book/0002`).

**Direction (maintainer, 2026-09-20): the RENDERER is the priority.** Remaining chapters, in order:
1. **The Vulkan renderer** — also wanted (`src/common/rendering/vulkan/`; the shared HW renderer feeds both
   the GL and Vulkan backends, so the chapter starts most of the way up the OpenGL chapter's picture and
   covers only the Vulkan backend's *how*).
2. Then the rest at whatever depth is useful (the resource/`.pk3` model, ZScript, sound via ZMusic, the CLI
   flags). **There is a lot of good material online about the Doom / GZDoom source — look it up to guide the
   narrative and anchor claims** (verify against the pinned `g4.14.2` source before writing a `file:line`).

## Phase C — the CLI-WAD-loading patch (`patches/`, upstream-candidate)

Goal: run the built GZDoom, pass a **WAD file on the command line, and it plays** — no GUI. GZDoom already
has `-iwad <file>` and `-file <pwad>`, but the **IWAD-selection dialog** pops when the IWAD isn't
unambiguously determined, which is the GUI the maintainer wants to avoid. From the Phase-B understanding of
`d_iwad.cpp`/the picker, add a clean CLI path — e.g. a single-WAD argument (auto-classified as IWAD or PWAD)
and/or a flag that **skips the IWAD picker and uses the CLI-provided WAD**. Then:
- Commit it as a focused, reviewer-facing change (its own commit + message), regenerate the `patches/`
  series (`git format-patch --no-cover-letter --base=<pin>`), and mark it an **upstream candidate** in the
  tier-3 `CLAUDE.md` (submitting to ZDoom is a nice-to-have, not a blocker — the patch is maintained here
  regardless).
- Re-verify: `apply.sh` applies clean at the pin; the built GZDoom plays a CLI-passed WAD with no GUI.

## Decisions (William Emerison Six <billsix@gmail.com>, 2026-09-20)
2. **Release by default** — the carrier builds a `Release` install; **document the debug build** too, but
   it is not the default.
3. **Keep the pins for now** — GZDoom `g4.14.2`, ZMusic `1.3.0`.
4. **Verify by building AND running here.** A display (X/Wayland) is available in-session, so the carrier's
   `run` can launch the built GZDoom with a real WAD — reproduce the broken CLI-WAD behaviour and validate
   the fix directly, rather than a headless-only check. (Test WADs are available; their location is not
   recorded in this task.)

## Phase-C target — DIAGNOSED (2026-09-20; fix not yet written)

Reproduced the failure and split it into two independent halves (full evidence in
`tasks/reference/gzdoom/build-and-cli-wad-repro.md`):
1. **Resource half — a BUILD issue, already fixed in Phase A.** A default (out-of-tree) GZDoom couldn't find
   its base `gzdoom.pk3` (which carries the IWAD-identification data), so even a valid `-iwad <path>` failed
   (headless: `Cannot find gzdoom.pk3`; on a display: dropped to the picker). Fixed with `-DSYSTEMINSTALL=ON`
   in the Makefile — this is very likely part of what the maintainer experienced as "the CLI didn't work."
2. **Picker half — the genuine Phase-C code target (NOT fixed).** With the working binary, whenever **no
   explicit `-iwad`** is given (a WAD passed via `-file`, or sitting in a search dir), the **GTK
   IWAD-selection dialog pops and blocks**. Proven by setting `queryiwad=false` in a config, which makes the
   same case auto-select and load. This matches the maintainer exactly — flags "failed" (picker), and a WAD
   in a `~/` dot-folder "worked" because `$HOME/.local/share/games/doom` / `$HOME/.config/gzdoom` are default
   IWAD-search dirs.

**Open decision — the fix shape** (code is `src/d_iwad.cpp`, `FIWadManager::IdentifyVersion` / `I_PickIWad`):
auto-classify a single positional/`-file` WAD as the IWAD, or a flag that implies `queryiwad=false` and
honours the CLI-passed WAD — so a CLI WAD **plays without the GTK picker**. Shape as an upstream candidate.

## Related
- Split-out follow-up: `tasks/gzdoom-appimage-packaging.md` — the optional `make appimage` distributable.
- Upstream: `github.com/ZDoom/gzdoom` (@ `g4.14.2`), `github.com/ZDoom/ZMusic` (@ `1.3.0`).
- imps carrier model + the code-patch exemplar: `../CLAUDE.md`, `n64/CLAUDE.md`. Reference-set machinery:
  `tasks/reference/mario64/{README.md,_TEMPLATE.md}`. Patch philosophy (upstream-where-it-fits): `../CLAUDE.md`.
