# Reference: The asset pipeline (ROM → OTR/O2R → runtime)

> **Provenance:** authored 2026-07 against Shipwright `988b53665` (9.2.3-320, the old
> fork base) — 101 commits behind the current imps pin `acdbc651d` (9.2.3-421). Spot-check
> details against the pinned checkout before trusting them.
> **Largely stale at the current pin:** this doc describes the ZAPDTR/OTRExporter asset
> pipeline, which upstream has replaced with the `torch` submodule (`soh-torch` extractor +
> `soh-o2r-packer`). Treat as historical until re-verified.

*Standing reference. How an OoT ROM becomes loadable assets and how the game pulls them. Read
before touching ZAPD, `soh/assets/`, or asset loading. Companions:
[libultraship-integration.md](libultraship-integration.md) (the runtime resource system),
[build-system.md](build-system.md), [architecture-overview.md](architecture-overview.md).*

## One correction up front: it's `.o2r` (ZIP) now, not `.otr` (MPQ)

The code, names, and old docs all say "OTR," but the live archive format is **`.o2r` (ZIP)**.
`oot.otr`/`soh.otr` are legacy names; the pipeline emits **`oot.o2r`, `oot-mq.o2r`, `soh.o2r`**.
MPQ/`.otr` survives only for *reading* old archives (`INCLUDE_MPQ_SUPPORT` ON, forced by SoH).
"OTR" now means the resource system generically (`__OTR__` prefix, `OTRGlobals`, `ExtractAssets`),
not the file format.

## ZAPD and OTRExporter

- **ZAPD** (`ZAPDTR/`, "Zelda Asset Processor for Decomp") is the classic OoT-decomp extractor: given
  an XML descriptor + a baserom, it reads N64 asset data at declared offsets. Built as the standalone
  `ZAPD` exe **and** as `ZAPDLib`, which is **linked directly into `soh`** (so the in-app extractor
  runs it in-process).
- **OTRExporter** (`OTRExporter/OTRExporter/`) is a set of per-asset-type exporters
  (`TextureExporter`, `RoomExporter`, `SkeletonExporter`, `AnimationExporter`, `CollisionExporter`,
  `DisplayListExporter`, `AudioExporter`, …) that hook ZAPD's parse pass and, instead of emitting C,
  serialize each parsed resource into the game's **runtime binary format** and write it into an
  archive. It turns "ZAPD parsed the ROM" into "an `.o2r` the game loads."
- **The ~7697 XML files** (`soh/assets/xml/<VERSION>/…`) are ZAPD extraction descriptors, one dir
  tree per ROM version (`N64_NTSC_10`, `GC_MQ_NTSC_U`, `GC_NMQ_PAL_F`, …). They declare *what lives
  where in that ROM's segments*: `objects/` (actor `<Skeleton>`/`<Animation>`/`<Collision>`/
  `<Texture>`/`<DisplayList>`), `scenes/` (`<Scene>`+`<Room>`), `textures/`, `code/`, `audio/`.
  `AddedByScript="true"` marks auto-discovered entries.

## The three archives

| Archive | Contents | Produced by | Provenance |
|---|---|---|---|
| `oot.o2r` | all ROM-extracted assets (non-MQ) | `extract_assets.py BuildOTR` → ZAPD `ed` mode | **ROM-derived** (copyrighted; never shipped) |
| `oot-mq.o2r` | same, Master Quest ROM | same, MQ xml set | **ROM-derived** |
| `soh.o2r` | port-authored: fonts, shaders, custom scenes/objects/textures, presets, accessibility JSON, lang | `extract_assets.py BuildCustomOtr` (`--norom`, ZAPD `botr` mode) over `soh/assets/custom/` | **Port-authored** (ships legally) |

- **`soh.o2r` in the tree is a gitignored build artifact** (`.gitignore:416` `*.o2r`). What's committed
  is its *source*: `soh/assets/custom/` + the XML + LUS shaders. `oot*.o2r` are never in the repo.
- **Shaders are injected at extract time**: `ExtractAssets`/`GenerateSohOtr` copy
  `libultraship/src/fast/shaders/` into `soh/assets/custom/shaders/` right before packing
  (`CMakeLists.txt:227-229`) — that dir is generated/transient, not authored.

## Build glue (`CMakeLists.txt:220-262`) — manual, not default

**None of these are `ALL` and `soh` depends on none of them → asset extraction is a manual step**
(a plain build makes the exe but no playable game). See [build-system.md](build-system.md).

- **`ExtractAssets`** (`:223`) — full extraction *from a ROM*: rm old o2r, copy shaders, run
  `extract_assets.py … --port-ver <version>`, then `copy-existing-otrs.cmake`. Produces `oot*.o2r`
  **and** `soh.o2r`. `DEPENDS ZAPD`.
- **`GenerateSohOtr`** (`:249`) — ROM-less (`--norom` → ZAPD `botr`), builds **only `soh.o2r`**. Used
  by CI/docs.
- **`ExtractAssetHeaders`** (`:240`) — `--gen-headers`, regenerates asset C headers.

`extract_assets.py` (`OTRExporter/`) drives ZAPD; `rom_info.py` maps the ROM's CRC → filelist +
`xml_ver`. `--port-ver <CMAKE_PROJECT_VERSION>` stamps a version file into the archive (read back at
runtime — see version handshake below).

## Runtime asset loading

Game code references assets by string with an **`__OTR__`** prefix, e.g.
`"__OTR__objects/object_link_boy/gLinkAdultHeadDL"`.

1. **`OTRGlobals`** (`soh/soh/OTRGlobals.cpp`) inits the LUS `Context`/`ResourceManager` and mounts
   archives: `AddArchive(oot-mq.o2r)`, `AddArchive(oot.o2r)` (`:792-796`), `soh.o2r` via
   `InitResourceManager` (`:303`). Located with `Context::LocateFileAcrossAppDirs`.
2. **`ResourceManagerHelpers.cpp`** provides the `extern "C" ResourceMgr_Load*ByName(path)` bridges
   the decomp C calls — they strip the 7-char `__OTR__` prefix, optionally prepend the alt-assets
   prefix (`IResource::gAltAssetPrefix`, Tab-toggle HD packs), then load by name.
3. **`ArchiveManager`** hashes the path with **CRC64**; `mFileToArchive[hash]` picks the owning
   archive → an archive is effectively a `CRC64(path) → blob` map.
4. **`ResourceManager::LoadResource*` → `ResourceLoader`** dispatches on the resource's type header to
   a registered **`ResourceFactory`** (SoH's live in `soh/soh/resource/importer/`) that deserializes
   the OTRExporter blob into a runtime struct. Cached; async variants use a thread pool. Details:
   [libultraship-integration.md](libultraship-integration.md).

The `__OTR__` string is the stable public name; CRC64 of the suffix is the physical key.

## ROM prep & verification

- **`soh/fixbaserom.py`** — prep of the **Debug ROM** specifically (strip overdump, byte/word-swap to
  big-endian `.z64`, gate on MD5 `9c1d7954…`).
- **ROM identification is by internal CRC**, kept in two synced places: `OTRExporter/rom_info.py:5-27`
  (build-time) and `soh/soh/Extractor/Extract.cpp:54-103` (runtime in-app extractor). Supported: many
  OoT versions (N64 1.0/1.1/1.2, PAL, all GC/MQ/Debug revisions). Users verify SHA1 against
  `docs/supportedHashes.json`.
- **Two extraction entry points**: the developer CMake `ExtractAssets` target (ROM staged in `soh/`),
  and the **end-user in-app extractor** (`Extract.cpp` → `Extractor::CallZapd`, `OTRGlobals.cpp:596`,
  using linked `ZAPDLib`) that prompts for the ROM on first run and writes `oot*.o2r` to the app-data
  dir (the "Processing OTR" flow).

## Newcomer trip-hazards

- **`.o2r` not `.otr`** — older SoH tutorials referencing `oot.otr` are stale here.
- **`soh.o2r` is gitignored** — edit `soh/assets/custom/` and rebuild `GenerateSohOtr`.
- **You supply the ROM**; extraction picks the XML set by CRC. Wrong `xml_ver` → garbage offsets.
- **Version handshake**: `--portVer` stamps the SoH version; at boot `ReadPortVersionFromOTR`/
  `CheckSoHVersion` (`OTRGlobals.cpp:1484-1516`) compares major versions and **deletes** `oot*.o2r`
  (`:450`) forcing re-extraction if incompatible — new devs see "archives outdated" and blame the ROM.
- **Master Quest is a separate archive** (`oot-mq.o2r`), selected by ROM CRC; `mq_asset_hacks.h`
  patches specific MQ paths.
- **ZAPD is both a library and an exe** — the in-app extractor uses `ZAPDLib` in-process.
