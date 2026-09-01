# OcarinaOfTime — Ship of Harkinian (OoT PC port), under imps

Shipwright / **SoH** is a PC/console port of *The Legend of Zelda: Ocarina of
Time* — the original "Ship of Harkinian" port (Ghostship, the SM64 port,
derived its approach from this). It combines the **OoT decomp** (`soh/src/`,
zeldaret/oot lineage), a **C++ port layer** (`soh/soh/`, `OTRGlobals` the
central glue), and the **libultraship** runtime (`libultraship/` submodule).

Managed by imps: `Shipwright/` here is a pristine clone of
https://github.com/HarbourMasters/Shipwright, pinned by `fetch.sh` at
`acdbc651d` (9.2.3-421, tip of upstream `develop` as of 2026-09-01), with the
maintainer's patches applied by `apply.sh`. It is not a fork and has no
personal branches — the patch series is the whole delta.

## Scripts

- `./fetch.sh` — clone if missing, checkout the pin, init submodules.
- `./apply.sh` — `git am` the series (refuses unless HEAD is at the pin).
- `./build.sh` — cmake+ninja → `bldInstall/` (fetches first if needed).
- `./run.sh` — launch `bldInstall/soh.elf` with `runDir/` as cwd.

## Patches

- `patches/0001-LLM-generated-renames.patch` — 145-file decomp rename:
  15 address-named `soh/src/code/code_<addr>.c` files and ~206 `func_`/`D_`
  symbols renamed to semantic names, cross-checked against zeldaret/oot.
  Ported 2026-09-01 from a fork based at `988b53665`; one conflict resolved
  in `z_demo_kankyo.c` (upstream's `Audio_PlaySfxGeneral` rename crossing
  the series' `CutsceneCamera_UpdateSpline` rename), and upstream-added
  identifiers were checked for references to renamed-away symbols (none).
  Patched tree build- and run-verified on the maintainer's host 2026-09-01.
  The renaming effort continues in
  [`../tasks/ocarina-decomp-rename-and-cleanup.md`](../tasks/ocarina-decomp-rename-and-cleanup.md);
  method and gotchas in
  [`../tasks/reference/ocarina/decomp-renaming.md`](../tasks/reference/ocarina/decomp-renaming.md).

## Version notes

- **libultraship pinned at `1.3.1-486` (`62e973ae`)**, `torch` at
  `v1.0.0-427`. Upstream replaced the old ZAPDTR/OTRExporter asset pipeline
  with torch (`soh-torch` extractor + `soh-o2r-packer`) between the old fork
  base and this pin — the asset-pipeline and build-system reference docs
  predate that and carry stale-warning banners.
- Archives are **`.o2r` (ZIP)** now, not `.otr` (MPQ) — old "OTR" naming is
  a generation behind.

## Architecture reference (read to get oriented without re-reading the code)

Deep, standing reference docs in **`../tasks/reference/ocarina/`** — start
with the overview, pull the subsystem doc you need. Each carries a
provenance banner (authored at the old base, `988b53665`); spot-check
details against the pinned checkout.

- [`architecture-overview.md`](../tasks/reference/ocarina/architecture-overview.md) —
  **read first.** The three bodies of code, the coroutine frame loop, the
  two seams (`__OTR__`/GbiWrap for graphics+assets, GameInteractor for
  behavior hooks).
- [`decomp-map.md`](../tasks/reference/ocarina/decomp-map.md) — "where does
  X live" in the OoT decomp: GameState, actors-as-overlays (+ `ActorDB`),
  `z_player.c`, collision/camera/scenes.
- [`port-layer.md`](../tasks/reference/ocarina/port-layer.md) — `soh/soh/`:
  `OTRGlobals`, the frame loop, CVars, the resource/OTR glue, SaveManager,
  `stubs.c`.
- [`libultraship-integration.md`](../tasks/reference/ocarina/libultraship-integration.md) —
  how SoH consumes LUS (written at 1.3.1-463; now 1.3.1-486).
- [`asset-pipeline.md`](../tasks/reference/ocarina/asset-pipeline.md) —
  **stale: describes the pre-torch ZAPD/OTRExporter pipeline.**
- [`frame-interpolation.md`](../tasks/reference/ocarina/frame-interpolation.md) —
  how the fixed OoT tick is decoupled from render FPS.
- [`enhancements-gui-rando.md`](../tasks/reference/ocarina/enhancements-gui-rando.md) —
  GameInteractor (hooks + `VB_*` overrides), SohGui, the randomizer.
- [`build-system.md`](../tasks/reference/ocarina/build-system.md) —
  **stale: pre-torch CMake/submodule graph.**
- [`decomp-renaming.md`](../tasks/reference/ocarina/decomp-renaming.md) —
  how to rename `func_/D_` symbols safely; read before touching the
  decomp-rename task.

Upstream human-facing docs live in `Shipwright/docs/` (BUILDING, MODDING,
VERSIONING, CUSTOM_MUSIC).
