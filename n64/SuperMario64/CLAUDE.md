# SuperMario64 — Ghostship (SM64 PC port), under imps

**Ghostship** is the Super Mario 64 PC port in the Ship of Harkinian
family (it derived its approach from SoH — see
`../OcarinaOfTime/CLAUDE.md`): the SM64 decomp (`src/game/`, ROM-derived,
near-1:1), a C++ port layer (`src/port/`), and the **libultraship**
runtime + **Torch** asset extractor as submodules.

Managed by imps: `Ghostship/` here is a pristine clone of
https://github.com/HarbourMasters/Ghostship, pinned by `fetch.sh` at
`49c5312a` (tip of upstream `develop` as of 2026-09-01), with the
maintainer's patches applied by `apply.sh`. Not a fork; the patch series
is the whole delta. The pin was chosen deliberately modern because
upstream had merged the maintainer's always-fly-on-triple-jump cheat
(restructured into the events layer as `SetTripleJumpAction` /
`FlyingTripleJumpLaunch` under `gCheats.AlwaysFlyTripleJump`) — so that
cheat ships with upstream and needs no patch.

## Scripts

- `./installdependencies.sh` — dnf install of the Fedora build deps
  (inline list; run once, as root). Verified 2026-09-01 in a fresh
  fedora:44 container: script + full configure + o2r + build all green.
- `./fetch.sh` — clone if missing, checkout the pin, init submodules.
- `./apply.sh` — `git am` the series (refuses unless HEAD is at the pin).
- `./build.sh` — cmake+ninja → `bldInstall/`; skips the ROM-needing
  `ExtractAssets` target (in-app extraction covers `sm64.o2r`); builds
  `GeneratePortO2R` for `ghostship.o2r`. Configure needs network
  (`gamecontrollerdb.txt` download).
- `./run.sh` — launch `build-cmake/Ghostship` (binary is not installed;
  o2r archives are found next to the executable) with `runDir/` as cwd.

## Patches — ported 2026-09-01 from the old fork's topic branches

The old fork's topic branches (`highjump`, `infiniteJump`, `noSkybox`,
all based 120+ commits back at `67e561c6`) were linearized into one
series and ported across upstream's hooks→events restructure
(`src/port/hooks/` became `src/port/events/`; the merged fly cheat served
as the template for the new shape). Byte-identical `git am` reproduction
verified against the ported branch.

- `0001-cheat-high-jump.patch` — "Super Jump" (`gCheats.SuperJump`): all
  upward jumps launch 3× higher via a `MarioHighJumpLaunch` event in
  `set_mario_action_airborne`, with a `MarioHighJumpFallHeight` event
  correcting effective fall height so the boosted jumps don't cause fall
  damage / stuck-in-ground. Port notes: events moved into
  `src/port/events/list/PlayerEvent.h`; in `check_fall_damage` the event
  now runs after upstream's new `PlayerLanded` event (both kept).
- `0002-cheat-infinite-jumps.patch` — "Infinite Air Jumps"
  (`gCheats.InfiniteAirJumps`): pressing A while airborne re-jumps, via a
  cancellable `MarioAirborneActionUpdate` event wrapping
  `mario_execute_airborne_action`. Port note: the cancel field is
  `Cancelled` (capital) in the events layer — the original commit's
  lowercase `cancelled` was fixed during the port.
- `0004-docs-add-libshaderc-devel-to-the-Fedora-build-depend.patch` —
  adds `libshaderc-devel` to both Fedora dnf lines in
  `docs/building.md` (the LUS Vulkan backend includes
  `shaderc/shaderc.hpp`; found the hard way, 2026-09-01). Doc fix to
  upstream's own file, hence a patch; upstream-submission candidate.
- `0003-disable-skybox.patch` — "Disable Skybox"
  (`gEnhancements.DisableSkybox`). **Slimmed in the port:** upstream now
  ships a cancellable `SkyboxRender` event already wired into
  `level_geo.c` (the same idea the original commit implemented), so the
  patch reduces to a listener cancelling that event plus the menu widget
  — no game-code or event-definition changes remain.

## Version notes

- Submodules at the pin: **libultraship `c151cc91` (1.3.1-544)** — the
  newest LUS of any imps project — and Torch `4c8ef537` (v1.0.0-409).
  **Caveat (found 2026-09-01 by the LUS crawl): `c151cc91` is a KiritoDv
  FORK branch of LUS, not Kenix3 mainline** — branch point `f30fe0ed`
  (1.3.1-463) + 81 fork commits (Vulkan backend, GPU-side T&L,
  postprocessing/multipass shaders, RT64 mipmapping, async texture
  loading, web/emscripten). The ~23 mainline commits after the branch
  point (Context `GetRawInstance` rework, `.meta` priority resolution,
  several audio/texture fixes) are absent from it. The crawl's docs at
  `../../tasks/reference/libultraship/` cover this pin as iteration 18 —
  the **current working-tree state** of that doc set (the crawl's final
  stop), so no git-history digging is needed for this project.
- The events layer is documented upstream in `src/port/events/EVENTS.md`
  — read it before adding cheats; a new cheat is: DEFINE_EVENT (or reuse
  one), CALL_EVENT at the game-code seam, REGISTER_EVENT +
  REGISTER_LISTENER gated on a CVar in
  `src/port/mods/PortEnhancements.cpp`, and a widget in
  `src/port/ui/GhostshipMenuEnhancements.cpp`.
- Sandbox note: building in the runClaudeInContainer sandbox needs
  `mbedtls-devel` (ixwebsocket's cmake configure) and `libshaderc-devel`
  (the new LUS Vulkan backend) installed — neither is in the base image.
- **The Vulkan backend hangs at this pin on the maintainer's GPU**
  (RADV Radeon 610M, 2026-09-01): the game goes silent right after
  "Vulkan device:" in the log, before any window. The game auto-picked
  Vulkan (`Window.Backend.Id = 4` in `runDir/ghostship.cfg.json`); the
  fix is `Id = 2` / `"OpenGL"` (`FAST3D_SDL_OPENGL`, enum in LUS
  `include/fast/Fast3dWindow.h:22`). Upstream/driver issue, not imps'.
- The binary's rpath bakes the absolute build-time path to `libtcc.so`
  (in `Ghostship/libultraship/`) — `run.sh` sets `LD_LIBRARY_PATH` so a
  binary built at one mount path runs at another.

## Podman build (Dockerfile + Makefile)

Created 2026-09-01 per `../../tasks/archive/mario64/2026/09/01/mario64-podman-appimage-build.md`, on
the MajorasMask/BanjoKazooie template. `Dockerfile` mirrors upstream
CI's build-linux job (`.github/workflows/main.yml` at the pin,
`ubuntu-latest` resolved to **24.04**): CI's apt line verbatim
(including the Vulkan set — libvulkan/libshaderc/glslang/spirv-tools),
python deps **`COPY`d from the checkout's
`libultraship/requirements.txt`** (pip `--break-system-packages` for
noble's PEP668; `COPY` not `RUN --mount=type=bind` on purpose — a
build-time bind mount is read by the confined `container_t` RUN process
with the file's on-disk SELinux label, so a `:Z`-poisoned checkout
(sandbox's `c1022,c1023` MCS categories) makes a host-side `podman
build` fail with an MCS-mismatch AVC on `requirements.txt`, and a build
mount has no relabel step; `COPY` is read by buildah as the unconfined
host user, immune to the label — fixed 2026-09-01), SDL 2.30.3 /
tinyxml2 10.0.0 / libzip 1.10.1 from
source. `GeneratePortO2R` runs in-container; the `appimage` target also
copies `build-cmake/.tcc` to `out/.tcc` (CI ships it beside the
AppImage and hard-fails without it — the scripting runtime).

Two fresh-environment gaps surfaced (in the master drift table):
**cmake ≥ 3.30** (LUS's FindVulkan uses policy CMP0159; noble apt ships
3.28; runners pre-provide newer → the Kitware repo block), and a
**shaderc/spirv-tools packaging skew on noble**: LUS prefers
`shaderc_shared`, Ubuntu names the lib plain `libshaderc.so`, so cmake
fell back to `libshaderc_combined.a` — which is ABI-skewed against
noble's newer spirv-tools static libs (undefined `spvtools::` at link).
The Dockerfile adds a `libshaderc_shared.so` compat symlink so LUS
takes its preferred, self-consistent shared path.

Verified nested 2026-09-01: image, `make build` of the patched tree,
and `make appimage` (`out/ghostship.appimage`, 16 MB, + `.tcc`) all
green. The on-host AppImage build was **confirmed 2026-09-01 (William
Emerison Six <billsix@gmail.com>)** — the `COPY` Dockerfile fix cleared
the SELinux block that had stopped host builds (see the Dockerfile
comment); it launches and auto-selects the Vulkan backend, so the RADV
Vulkan-hang caveat above applies — switch to OpenGL if it goes silent
after "Vulkan device:".

## Architecture reference (read to get oriented without re-reading the code)

Deep docs in **`../../tasks/reference/mario64/`** — all authored against the
OLD base (`67e561c6`) and bannered accordingly: the hooks→events
restructure postdates them, so port-layer path claims need verification
against the pinned checkout.

- [`architecture-overview.md`](../../tasks/reference/mario64/architecture-overview.md) —
  read first; the three bodies of code and the seams.
- [`decomp-map.md`](../../tasks/reference/mario64/decomp-map.md) — where X
  lives in the SM64 decomp.
- [`port-layer.md`](../../tasks/reference/mario64/port-layer.md) — `src/port/`
  (most affected by the events restructure — verify).
- [`libultraship-integration.md`](../../tasks/reference/mario64/libultraship-integration.md) —
  the LUS seam (written at 1.3.1-399; pin is 1.3.1-544).
- [`asset-pipeline.md`](../../tasks/reference/mario64/asset-pipeline.md) —
  Torch, sm64.o2r/ghostship.o2r.
- [`frame-interpolation.md`](../../tasks/reference/mario64/frame-interpolation.md) —
  tick/render decoupling (pared down from SoH's).
- [`build-system.md`](../../tasks/reference/mario64/build-system.md) — CMake
  graph.
- [`cheats-and-menu-enhancements-plan.md`](../../tasks/reference/mario64/cheats-and-menu-enhancements-plan.md) —
  the maintainer's cheat roadmap (several items since shipped; see its
  banner).

## Tasks

Migrated cheat-idea stubs from the old fork, all `mario64-`-prefixed under
`../../tasks/`: decomp-rename-and-cleanup, endless-stairs-wallkick-unlock,
infinite-wall-kicks, one-hit-ko, rubber-mario, time-scale-bullet-time.
The archived moon-gravity and ice-everywhere tasks were deliberately left
in the old fork (their code was not ported).

## Conventions

- The decomp is a near-1:1 port — match surrounding style, keep edits
  surgical; implement cheats through the events layer + CVar + menu
  widget, not by hacking decomp logic (the patches above are the worked
  examples).
- C/C++ formatted with the project `.clang-format`.
