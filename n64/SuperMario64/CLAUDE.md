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

## Patches

**Stream order is pinned — `standard-c`, then `cheats`, then `book`**
(`patches/ORDER`, with the rationale inline). `standard-c` is upstream-bound and
touches many decomp files, so it is the base the personal streams sit on (a
conflict then surfaces here, not in a rebase we cannot do); `cheats` and `book`
both touch `src/game/mario.c`, and the markers belong on the cheated tree.
`upstream-candidates` is unlisted (docs only, disjoint) and applies last.

- `patches/standard-c/0001..0046` (46 patches, 2026-09-22; **upstream-bound**) —
  rewrites the decomp's assembly-isms into standard C, one class per patch, per
  directory: `register` removal, matching residue (lone `;`, `do{}while(0)`,
  one-line-to-match), `goto`→`break`/`return`, redundant `else if`, `== TRUE`/
  `!= FALSE` on boolean-valued operands, 16-bit residue (`& 0xFFFF` before s16
  stores, signed `<<` as multiply), `UNUSED` residue + the 321 function-local
  `fillerN[]` arrays, `rawData` indices → field names + behaviour-param masks,
  argN/register-named parameters, boolean `++`/Yoda tests. **Every patch is
  gate-proven: the touched files compile to byte-identical assembly before and
  after** (`../../tools/asmdiff.sh`, over the port's
  own `compile_commands.json`). Rewrites that are behaviour-preserving by
  argument but change codegen (the s32-field `== TRUE`s, `<< 16 >> 16` → `(s16)`,
  memset loops at `-O1`, the spindel `switch`, …) are deliberately NOT in the
  stream — they are the "explained-diff" list in the task. Catalogue, per-batch
  log and the B.11 list: `../../tasks/archive/mario64/2026/09/23/mario64-assembly-isms-to-standard-c.md`;
  the patterns: `../../tasks/reference/mario64/assembly-isms-in-the-decomp.md`.
  Rebuilt on the checkout branch `imps-standard-c` (exported with
  `git format-patch --base=<pin>`); at a pin bump replay AND re-run the gate.
- `patches/cheats/0001-cheat-high-jump.patch` — "Super Jump"
  (`gCheats.SuperJump`): all upward jumps launch 3× higher via a
  `MarioHighJumpLaunch` event in `set_mario_action_airborne`, with a
  `MarioHighJumpFallHeight` event correcting effective fall height so the
  boosted jumps don't cause fall damage / stuck-in-ground.
- `patches/cheats/0002-cheat-infinite-jumps.patch` — "Infinite Air Jumps"
  (`gCheats.InfiniteAirJumps`): pressing A while airborne re-jumps, via a
  cancellable `MarioAirborneActionUpdate` event wrapping
  `mario_execute_airborne_action`.
- `patches/cheats/0003-disable-skybox.patch` — "Disable Skybox"
  (`gEnhancements.DisableSkybox`): a listener cancelling upstream's
  `SkyboxRender` event (already wired into `level_geo.c`) plus the menu widget.
- `patches/upstream-candidates/0001-...libshaderc...` (upstream candidate) —
  adds `libshaderc-devel` to both Fedora dnf lines in `docs/building.md` (the
  LUS Vulkan backend includes `shaderc/shaderc.hpp`; found the hard way,
  2026-09-01). Doc fix to upstream's own file, hence a patch.
- `patches/book/0001-doc-region-markers.patch` — comment-only
  (**gated**: `tools/check_comment_only_streams.sh SuperMario64` proves both
  book streams change nothing the compiler sees; see `../CLAUDE.md`)
  `// doc-region-begin/end <name>` markers so the book's `literalinclude` pulls
  spans by NAME, not line numbers. First region: `euler_zxy_to_matrix`. Grows
  per book chapter (the game-tree doc-region lane).

Cheat-series porting history (the old fork's `highjump`/`infiniteJump`/`noSkybox`
branches linearized across upstream's hooks→events restructure, per-patch port
notes): `../../tasks/reference/imps/game-port-history.md`. How to add a cheat:
DEFINE_EVENT, CALL_EVENT at the game-code seam, REGISTER_EVENT +
REGISTER_LISTENER gated on a CVar in `src/port/mods/PortEnhancements.cpp`, and a
widget in `src/port/ui/GhostshipMenuEnhancements.cpp` (upstream's
`src/port/events/EVENTS.md` documents the layer — read it first).

## Version notes

- Submodules at the pin: **libultraship `c151cc91` (1.3.1-544)** — the newest
  LUS of any imps project — and Torch `4c8ef537` (v1.0.0-409). **Caveat:
  `c151cc91` is a KiritoDv FORK branch of LUS, not Kenix3 mainline** — it lacks
  ~23 mainline commits after its branch point (1.3.1-463) and carries 81 fork
  commits (Vulkan backend, GPU-side T&L, etc.). The crawl's docs at
  `../../tasks/reference/libultraship/` cover this pin as iteration 18 — the
  current working-tree state of that doc set, so no git-history digging is needed
  here. Fork-topology detail: `../../tasks/reference/imps/game-port-history.md`.
- Sandbox note: building in the runClaudeInContainer sandbox needs
  `mbedtls-devel` (ixwebsocket's cmake configure) and `libshaderc-devel`
  (the new LUS Vulkan backend) installed — neither is in the base image.
- **The Vulkan backend hangs at this pin on the maintainer's GPU**
  (RADV Radeon 610M, 2026-09-01): the game goes silent right after
  "Vulkan device:" in the log, before any window. The cause is that
  libultraship registers Vulkan before OpenGL on Linux and defaults to the
  front of that list (`GetSavedWindowBackend` returns
  `mAvailableWindowBackends->front()` in
  `libultraship/src/ship/window/Window.cpp`), so a first run with no config
  auto-picks Vulkan (`Window.Backend.Id = 4`). **`run.sh` now seeds
  `runDir/ghostship.cfg.json` with `Id = 2` / `"OpenGL"`
  (`FAST3D_SDL_OPENGL`) when the config is absent**, so a fresh `runDir/`
  starts on OpenGL; switch to Vulkan in the menu if a machine wants it (the
  choice persists, and the seed never overwrites an existing config).
  Vulkan stays compiled in — this changes only the default. Task:
  `../../tasks/archive/mario64/2026/09/06/mario64-default-to-opengl-backend.md`.
  Upstream/driver issue, not imps'.
- The binary's rpath bakes the absolute build-time path to `libtcc.so`
  (in `Ghostship/libultraship/`) — `run.sh` sets `LD_LIBRARY_PATH` so a
  binary built at one mount path runs at another.

## Podman build (Dockerfile + Makefile)

`Dockerfile` mirrors upstream CI's build-linux job
(`.github/workflows/main.yml` at the pin, `ubuntu-latest` → **24.04**): CI's apt
line verbatim (including the Vulkan set), python deps `COPY`d from the checkout's
`libultraship/requirements.txt` (`COPY` not `RUN --mount=type=bind` — see the
drift table), SDL 2.30.3 / tinyxml2 10.0.0 / libzip 1.10.1 from source.
`GeneratePortO2R` runs in-container; the `appimage` target also copies
`build-cmake/.tcc` to `out/.tcc` (the scripting runtime — the AppImage
hard-fails without it). The Dockerfile adds a `libshaderc_shared.so` compat
symlink for a **shaderc/spirv-tools packaging skew on noble** (LUS prefers
`shaderc_shared`; Ubuntu names it plain `libshaderc.so`, so cmake would fall
back to the ABI-skewed `libshaderc_combined.a` — undefined `spvtools::` at link).
Other fresh-environment gaps (cmake ≥ 3.30 via the Kitware block) are in the
drift table. `make image/build/appimage/run`.

**The OpenGL-default seed lives in `run.sh`, not in the AppImage** — an AppImage
launched directly (not via `run.sh`) still auto-picks Vulkan on first run, so the
RADV Vulkan-hang caveat applies to it: switch to OpenGL in the menu if it goes
silent after "Vulkan device:". The maintainer's own play path is a from-source
build run via `run.sh`, which is seeded. Build/run verification history:
`../../tasks/reference/imps/game-port-history.md`.

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
infinite-wall-kicks, one-hit-ko, rubber-mario, time-scale-bullet-time. Plus
(2026-09-22) `mario64-assembly-isms-to-standard-c` — the upstream-first
`patches/standard-c/` stream that rewrites the decomp's assembly-isms into
standard C, proved with an assembly-diff gate; its patterns reference is
`../../tasks/reference/mario64/assembly-isms-in-the-decomp.md`.
The archived moon-gravity and ice-everywhere tasks were deliberately left
in the old fork (their code was not ported).

## Conventions

- The decomp is a near-1:1 port — match surrounding style, keep edits
  surgical; implement cheats through the events layer + CVar + menu
  widget, not by hacking decomp logic (the patches above are the worked
  examples).
- C/C++ formatted with the project `.clang-format`.

## The book (student-facing docs)

`book/` is the Sphinx book *How a Production Game Is Built* (HTML/EPUB/PDF via
its own Dockerfile+Makefile), teaching a reader who has done `modelviewprojection`
how a real game is made, `literalinclude`-ing this source by doc-region. It
draws its detail from `../../tasks/reference/mario64/`. Design + status:
`../../tasks/mario64-sphinx-book.md`.

### libultraship doc-region lane (`patches-libultraship/`)

The book also `literalinclude`s libultraship code, so a SECOND patch lane
lives in `patches-libultraship/` (streamed the same way — `patches-libultraship/book/`) (base = the submodule pin `c151cc91`),
applied INSIDE `Ghostship/libultraship/`. `patches-libultraship/book/0001-...` adds comment-only
doc-region markers (currently `combiner_input_to_glsl`, `set_combine_mode`,
`light_dir_to_normal_space`, `tile_wrap_modes`), verified to `git am` clean onto
the pin. **`apply.sh` applies BOTH lanes** (2026-09-06): after `fetch.sh`'s
`git submodule update` checks out libultraship at its pin, `apply.sh` applies
`patches-libultraship/*` inside the submodule (signing off, guarded on the
submodule being at its pristine gitlink SHA). So a fresh `fetch.sh && apply.sh`
gives a checkout with both the game-tree and the LUS doc-region markers.
