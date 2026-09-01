# Reference: The asset pipeline (ROM → `.o2r` → runtime)

> **Provenance:** authored 2026-06/07 against Ghostship around base `67e561c6` — the imps
> pin (`49c5312a`, GitHub develop tip 2026-09-01) is 120+ commits newer and includes a
> restructure of the hook layer (`src/port/hooks/` became `src/port/events/`, with an
> expanded event list and an EVENTS.md). Claims about hooks, file paths under port/, and
> the maintainer's fork/branches are suspect — verify against the pinned checkout.

*Standing reference. How a player's ROM becomes loadable assets, and how the running game
pulls them. Read before touching extraction, `assets/ymls/`, or asset loading. Companions:
[libultraship-integration.md](libultraship-integration.md) (the runtime resource system),
[build-system.md](build-system.md) (the CMake targets), [architecture-overview.md](architecture-overview.md).*

## One correction up front: two extractors, only ONE is live

- **LIVE:** **Torch** + the `assets/ymls/*.yml` descriptors + `config.yml`
  → `sm64.o2r`. This is the whole shipping pipeline.
- **DEAD:** `extract_assets.py` + `assets.json` + `charmap*.txt`. These are the *legacy
  SM64-decomp* extractor, inherited but orphaned. **Verified dead:** nothing tracked
  references `extract_assets.py`/`assets.json` (`git grep` empty), and `extract_assets.py`
  requires a `tools/` dir (`tools/mio0`, `tools/disassemble_sound.py`) that **does not exist
  in the tree** — it cannot run. Don't edit `assets.json` expecting `sm64.o2r` to change.

## What is Torch

`Torch/` submodule (github.com/HarbourMasters/Torch) — a generic N64 asset processor /
OTR-O2R generator ("**T**orch is **O**ur **R**esource **C**onversion **H**elper",
`Torch/README.md:1`). Built **two ways** (see build-system doc): as a linked static lib
*and* as a standalone `torch` executable via `ExternalProject_Add(TorchExternal)`. The
executable is what the asset CMake targets invoke.

- Entry `Torch/src/main.cpp` — subcommands `otr`, `o2r`, `code`, `binary`, `header`,
  `pack`, `modding import/export` (`main.cpp:29-162`).
- Reads a ROM, matches its SHA1 against `config.yml`, and for each asset descriptor invokes
  a **factory** by `type`. Factories in `Torch/src/factories/` (`TextureFactory`,
  `DisplayListFactory`, `VtxFactory`, `LightsFactory`, `GeoLayout`, `BlobFactory`, + game
  subdirs `sm64/`, `mk64`, `sf64`…). Each `type` maps to a FourCC resource type in
  `Torch/src/factories/ResourceType.h` (Texture=`OTEX`, Vertex=`OVTX`, Lights=`LGTS`).

## The `.yml` descriptors (~842 files: 422 US, 420 JP)

`assets/ymls/{us,jp}/…` — one Torch descriptor per asset. Each declares `type`, `offset`
(into a ROM segment or a decompressed MIO0 blob), `size`, format, `symbol`. Examples:
`actors/mario.yml` (lights table), `textures/*.yml` (`type: TEXTURE`, `width/height/format:
RGBA16`), `levels/*.yml`, `texts/*.yml` (`type: SM64:TEXT`). Each opens with a `:config:`
block giving its MIO0 `compression:` offset and `segments:` mapping. Distribution per
region: 128 actor + 33 level + 17 texture + sound/text/skybox.

- **`formatyamls.py`** — maintenance only (uses `ruamel.yaml`): normalizes offsets→hex,
  sorts nodes by `offset`, fixes `segments` formatting; skips `sound/` and `strings.yml`.
  Not part of the build.

## `config.yml` (Torch's config, repo root)

Maps each supported ROM **SHA1** (US `9bef11…`, JP `8a20a5…`) to `name`, the `path` to that
region's ymls (`assets/ymls/us`), an output block (`binary: sm64.o2r`, `code: code/us`,
`headers: include/assets`, `modding: mods/assets`), the GBI microcode variant (`gbi: F3D`),
sort order, and the 24 N64 **segment base addresses** (used to resolve segmented pointers in
display lists / geo layouts). `torch o2r` picks the block by hashing the supplied ROM.
(`Torch/config.yml` is just the upstream sample template — not this project's.)

## `sm64.o2r` vs `ghostship.o2r`

| | `sm64.o2r` | `ghostship.o2r` |
|---|---|---|
| Contents | **ROM-derived**: textures, models, geo, level scripts, text, sound banks | **Port-authored**: fonts, shaders, UI/achievement textures |
| Produced by | CMake `ExtractAssets`: `torch o2r baserom.us.z64 -u <ver>` (`CMakeLists.txt:628`) | CMake `GeneratePortO2R`: `torch pack port ghostship.o2r o2r -u <ver>` (`:636`) |
| Source | player's `baserom.us.z64` + `assets/ymls/us/*` | the `port/` dir: `port/fonts/*.{ttf,otf}`, `port/shaders/{opengl,directx,metal}/*`, `port/textures/**/*.png` |
| Copyright | Nintendo IP → **gitignored** (`*.o2r`), never shipped | project's own → safe to ship |
| In tree? | **absent** (needs a ROM) | present (built locally, 359 KB), also gitignored |
| Runtime location | `sm64` app-dir (`LocateFileAcrossAppDirs("sm64.o2r","sm64")`) | app root (`LocateFileAcrossAppDirs("ghostship.o2r")`) |

Both are `copy_if_different` into the build dir and `install`ed; `config.yml` + `assets/`
are installed alongside so the runtime can **re-extract `sm64.o2r`** from the user's ROM
(it can't ship it).

**Neither is in the default build** — a plain `cmake --build` produces a binary that can't
run until `ExtractAssets` (needs your ROM) and `GeneratePortO2R` run. `build.sh` runs them
explicitly.

## The archive format

Both are archive containers (`Torch/src/archive/`):
- **`.o2r` = a plain ZIP** (via `miniz`, `ZWrapper.cpp`). Confirmed: first bytes `50 4b 03 04`
  (`PK\x03\x04`). **You can `unzip ghostship.o2r` to inspect it.** Inner paths are virtual FS
  keys: `textures/icons/g2ShipIcon.png`, `fonts/…`, `sound/banks/*`.
- **`.otr` = an MPQ archive** (Blizzard's format via StormLib, `SWrapper.cpp`). O2R is the
  newer, license-friendlier successor; libultraship reads both.

## Runtime loading (summary — full detail in the LUS doc)

libultraship's ResourceManager/ArchiveManager loads by virtual path. Archives are **layered
port → ROM → mods** (`Engine.cpp:143,225,236-256`), so `mods/*.o2r` or a mod dir overrides
base assets by path — the texture-pack/mod mechanism. Assets requested via
`ResourceGetDataByName(path)` / `LoadResource(path)`; the decomp reaches them through the
`LOAD_ASSET` / `__OTR__` signature redirect (see
[libultraship-integration.md](libultraship-integration.md#2-resource-system--load-an-asset-by-name-from-a-o2r)).

- **Version gating rejects mismatched archives at boot:** the `-u <PROJECT_VERSION>` on both Torch targets is
  embedded in the archive; at boot `DetectOTRVersion("sm64.o2r")` (`Engine.cpp:363`) compares
  it to the build. A stale `sm64.o2r` is **deleted and re-extracted**; a stale/missing
  `ghostship.o2r` raises "Missing/outdated ghostship.o2r" (`Engine.cpp:443`). **Rebuild both
  o2r targets after a version bump** or you get incompatibility dialogs.

## The charmaps (`charmap.txt`, `charmap_menu.txt`)

Decomp-era text-encoding tables (glyph→byte, e.g. `'A' = 0x0A`; JP kana in `charmap_menu.txt`)
for building `text_strings.h`. In the live pipeline, text is instead described by
`assets/ymls/*/texts/*.yml` (`type: SM64:TEXT`). So the charmaps are **legacy** alongside
`extract_assets.py`.

## Newcomer trip-hazards

- `extract_assets.py` / `assets.json` / charmaps are **dead code**; Torch + ymls + config.yml
  is the real pipeline.
- `.o2r` is just a ZIP; `.otr` is MPQ.
- `sm64.o2r` is intentionally absent + gitignored; exists only after building against a
  legally-owned ROM.
- Torch is compiled **twice** (linked lib + ExternalProject executable).
- The `-u <version>` args are not cosmetic — they gate archive acceptance at runtime.
- The `config.yml` `code:`/`headers:` outputs (the `torch code` path that would regenerate
  `include/assets` decomp C) appear **unused** by the shipping build — CMake only calls
  `torch o2r` and `torch pack`.
