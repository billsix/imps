# Reference: the asset pipeline (ROM → Torch → `.o2r` → runtime)

> **Provenance:** authored 2026-07-31 against Lighthouse `6d30df9a` — the same commit
> imps pins, so no version gap. Claims about the maintainer's fork/branches predate imps.

*Standing reference. How a ROM becomes runtime assets, and how the decomp's asset references
become archive lookups. Companions: [architecture-overview.md](architecture-overview.md),
[libultraship-integration.md](libultraship-integration.md), [decomp-map.md](decomp-map.md).*

*Banner: Lighthouse at branch `bill`; ships no copyrighted assets — the player supplies a ROM.*

## The two archives

Both are `.o2r` (libultraship's ZIP-based archive format):

- **`bk.o2r`** — ROM-extracted game assets (models, sprites, animations, dialog, maps,
  textures, vertices, display lists, soundfonts), keyed by the `symbol_map` paths from the
  region ymls. Produced by Torch from `baserom.z64`. **Not committed** (`.gitignore`); each user
  regenerates it from their own ROM. Registered as the sole entry of `sRomArchives`
  (`src/port/Engine.cpp:259`).
- **`lighthouse.o2r`** — port-authored assets: fonts (`Inconsolata`, `Montserrat`,
  `PressStart2P`, `Fipps`), the intro lighthouse model + anims (`lighthouse_shrug`,
  `lighthouse_walk`), UI textures, plus Fast3D `shaders/` injected at pack time. **Committed** at
  the repo root (~346 KB). Referenced at `Engine.cpp:154`; its presence gates
  `portArchiveVersionMatch` (`:155`).

There is no combined "game data" file — game data comes only from `bk.o2r`.

## Torch — the one asset tool, used two ways

`Torch/` is a git submodule (its own `CMakeLists.txt`). BK-specific factories live in
`Torch/src/factories/bk64/` (Sprite, Model, Anim, Dialog, Map, DemoInput, GruntyQuestion, …);
resource FourCCs at `Torch/src/factories/ResourceType.h:86-93` (`BKSP`, `BKMO`, `BKAN`, `BKDL`,
`BKMP`, `BKDI`, `BKGQ`, `BKQQ`). Torch is built **twice** (like the siblings): a static `torch`
lib linked into the game (in-app extractor), and a standalone host executable via
`ExternalProject_Add(TorchExternal)` (`CMakeLists.txt:737`) → `${TORCH_EXECUTABLE}` for the
CMake targets. See [build-system.md](build-system.md).

- **CLI path (build targets):**
  - `ExtractAssets` (`CMakeLists.txt:749-755`) runs `${TORCH_EXECUTABLE} o2r baserom.z64`
    (`:753`) → produces **`bk.o2r`**, then copies it into the build dir. **Needs the ROM as
    `baserom.z64` in the source dir.**
  - `GeneratePortO2R` (`CMakeLists.txt:757-766`) wipes `port_staging`, copies the repo `port/`
    dir + LUS `fast/shaders` into it, runs `${TORCH_EXECUTABLE} pack port_staging lighthouse.o2r
    o2r` (`:764`) → produces **`lighthouse.o2r`**.
  - **Both are `add_custom_target` and NOT in any `add_dependencies` — live but manually
    invoked** (`make ExtractAssets` / `make GeneratePortO2R`). A normal build does not re-run
    them; regenerate archives only when the ROM or `port/` changes.
- **Embedded path (in-app extractor):** `src/port/Extractor/GameExtractor.cpp` drives Torch's
  `Companion` class (`GenerateOTR`, `:353`; `ArchiveType::O2R`), reading `config.yml` for the ROM
  hash → region yaml dir (`:245-275`), synthesizing config for unknown hashes via
  `BK64::TrySynthesizeRomConfig` (`:250`). Driven by the boot-time UI flow
  `GameEngine::RunExtract` (`Engine.cpp:423`). This is the "asks for a ROM on first run" path.

## Extraction config

- **`config.yml`** (repo root) maps 4 ROM SHA-1s → per-region yaml dirs + output targets
  (`config.yml:1-59`): US rev0 `1fe1632…`, US rev1 `ded6ee1…`, PAL `bb359a7…`, JP `90726d7…` —
  all output `binary: bk.o2r`, `code: src/assets`, `headers: include/assets`. (`src/assets`/
  `include/assets` are Torch **codegen** for the decomp build, generated, not in-tree.)
- **`assets/yaml/<region>/<rev>/`** — the per-region extraction tables: `assets.yaml` (the asset
  table + `symbol_map` mapping ROM offsets → named paths like `anim/ASSET_3_BSWALK`),
  `soundfont.yaml`, and (US rev0) `hashes.yaml`.
- The container's ROM `ROMF.z64` is US rev0 (`1fe1632…`), the first table.

## Runtime mount order (port → ROM → mods)

In `GameEngine` (`Engine.cpp`):

1. **`lighthouse.o2r`** mounted at construction via `InitResourceManager({ assets_path }, {}, 3,
   true)` (`:160`).
2. **`bk.o2r`** mounted in `FinishInit()` (`:353-359`): `GetArchiveManager()->AddArchive(romPath)`
   (`:357`), resolved via `LocateFileAcrossAppDirs(archive, "bk")`.
3. **Mods / loose dirs / language packs** layered after (`UpdateModFiles`, `LoadLooseModDirectories`,
   `LoadLanguagePacks`; `:367-369`), each `AddArchive`. Later layers override earlier by path —
   the basis for texture packs / HD overrides.

`AnyRomArchiveExists()` (`:261-268`) gates whether the extractor UI must run on launch.

## The runtime asset-load seam — `LOAD_ASSET` / `__OTR__`

`LOAD_ASSET` (`src/port/Engine.h:3-5`): a decomp asset "pointer" is **either** a real in-memory
pointer **or** an `__OTR__`-prefixed archive path, disambiguated at runtime:

```c
#define LOAD_ASSET(path) (path == NULL ? NULL :
    (GameEngine_OTRSigCheck((const char*)path) ? ResourceGetDataByName((const char*)path) : path))
```

- **Signature check** (`Engine.cpp:1522-1528`): `sOtrSignature = "__OTR__"`; `GameEngine_OTRSigCheck`
  is `strncmp(data, "__OTR__", 7) == 0`. This is the Ghostship/Shipwright `OtrSignatureCheck`
  analog (a literal magic-string compare, **unrelated** to any LUS keystore/security signature).
- **Name → archive lookup:** `ResourceGetDataByName` is a LUS bridge fn (body in the submodule,
  `libultraship/src/libultraship/bridge/resourcebridge.cpp:44` — **not in this repo**). Port
  wrappers in `src/port/ResourceHelpers.cpp`: `ResourceMgr_LoadByAssetId` (`:271`, the decomp's
  `assetcache_get` path), `ResourceMgr_LoadGfxByName` (`:345`), `ResourceMgr_LoadVtxByName`/
  `LoadMtxByName` (`:350`/`:354`). A `sResourceRefCache` (`:203`) retains `shared_ptr`s so raw
  pointers don't dangle when LUS evicts; flushed at Destroy (`:359`).
- **GBI-level `__OTR__` resolution:** `src/port/Resource/GfxBridge.c` intercepts GBI macros
  (`gSPDisplayList`, `gSPVertex`) and swaps `__OTR__` names for loaded data.

## Resource factories (registered in the port)

`RegisterResourceFactories(loader)` (`Engine.cpp:271-315`, called from `FinishInit` at `:402`).
Port-authored BK factories live in `src/port/Resource/Importers/` (types in
`src/port/Resource/Type/`): `Sprite` (`BKSprite`), `Model` (`BKModel`), `BKAnimation` (repacks to
a `Ship::Blob`), `BKDialog`, `BKQuizQuestion`, `BKGruntyQuestion`, `BKDemoInput`, `BKMap`. Reused
Fast/LUS factories registered here too: `Fast::ResourceFactoryBinaryTextureV0/V1`, `Vertex`,
`DisplayList`, `Matrix`, and `Ship::ResourceFactoryBinaryBlobV0`. No dedicated AudioBank factory —
soundfonts are handled via `assets/yaml/*/soundfont.yaml` at extract time + `src/port/Audio/
AudioSoundFont.cpp` (loaded as Blobs in `LoadSoundfonts`, `Engine.cpp:1187`).

## HD / alternate assets, mods, language packs

- **Alt (HD) assets** — CVar `Mods.AlternateAssets` → `ResourceManager::SetAltAssetsEnabled`
  (default-on, `Engine.cpp:403-404`); HD assets looked up under the `alt/<path>` prefix. Port alt
  subsystem in `src/port/Resource/Alt/`: `AltSprites.cpp` (BK sprites bake pixels inline, so they
  bypass the normal gfx HD path and redirect to `alt/<path>` via a `ResolveSpriteHdPath` listener,
  `:119`), `AltBoldFont.cpp`, `AltDialogFont.cpp`, `AltPathPool.cpp` (path interning).
- **Mods / `.o2r` overlays** — `src/port/UI/LighthouseModMenuWindow.cpp` discovers `.o2r` under
  `mods/`, categorizes (romhack/shared/scoped/normal), tracks an `EnabledMods` CVar, and
  add/removes archives. `mods/` scaffolding (`~romhacks`, `~lang`, `~shared`) created in
  `Engine.cpp:239-257`. Language packs auto-load from `mods/~lang` (`:339-351`; docs at
  `docs/modding/LANGUAGE PACKS.md`).

## No dead Python extractor

Unlike Ghostship (dead `extract_assets.py` + `assets.json`), Lighthouse has **no `.py` extractor
at all** — a repo-wide search (outside `Torch/`/`libultraship/`) finds zero. Everything is
Torch-driven and live: the CLI targets, and the embedded `Companion`-based extractor. The only
"generated but unused at runtime" artifacts are the `src/assets`/`include/assets` codegen targets
(used by the decomp build, not the runtime, which reads the `.o2r`).
