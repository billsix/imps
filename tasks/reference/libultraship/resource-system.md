# libultraship — resource system and OTR archives

> **Pinned:** libultraship tag **1.3.0**
> (`317edd72cc317387f8ac010a9ec772d4bfdfdbb6`, 2023-10-02). Authored
> 2026-09-01, iteration 1 of the reference crawl
> (`../../libultraship-reference-docs.md`). Re-sync check: compare
> `PIN_SHA` in `libultraship/fetch.sh` with the SHA above.

## OTR = MPQ at this tag

Archives are **StormLib MPQ files** with an `.otr` extension (the
`.o2r`/ZIP era comes much later). StormLib 9.24 is vendored and linked
**PUBLIC**, and `src/resource/Archive.h:14` includes `<StormLib.h>`
directly, so StormLib's `HANDLE`/`DWORD` types leak to every consumer
via `include/libultraship/classes.h`.

## The classes

- **`LUS::Archive`** (`src/resource/Archive.h:20`) — owns the MPQ
  handles, serves raw bytes. One `std::mutex` taken around *each
  individual* StormLib call (`Archive.cpp:93-135`) — serializes StormLib
  but open→read→close is not atomic as a sequence; `mHashes`/
  `mMpqHandles` are mutated without the lock (construction-time only).
- **`LUS::File`** (`src/resource/File.h:10`) — `Parent`
  (`shared_ptr<Archive>`), `Path`, `Buffer`, `IsLoaded`.
- **`LUS::IResource` / `Resource<T>`** (`src/resource/Resource.h:19`,
  `:38`) — typed payload holder + `ResourceInitData` (path, endianness,
  type FourCC, version, id, isCustom). `gAltAssetPrefix = "alt/"` at
  `Resource.h:21`.
- **`LUS::ResourceLoader`** (`src/resource/ResourceLoader.h:12`) —
  factory registry (three parallel maps; **no mutex**, and
  `mFactories[type]` on the load path inserts null entries for unknown
  types from worker threads — an unsynchronized mutation).
- **`LUS::ResourceManager`** (`src/resource/ResourceManager.h:19`) —
  cache + `BS::thread_pool` (`hardware_concurrency − reserved − 1`,
  min 1; hard 1 on Switch/WiiU). If the archive failed to load, the pool
  is **paused forever** (`ResourceManager.cpp:92`) and blocking loads
  hang.

## Archive mounting and layering

`Archive::LoadMainMPQ` (`Archive.cpp:411`): scan `mMainPath` for
`*.otr` (or take an explicit list) → first candidate whose `version`
member validates becomes the main MPQ → every remaining candidate is
layered as a patch. `LoadPatchMPQs` (`:357`) then scans the patches dir
(default `<appdir>/mods`, `src/Context.cpp:188`) for `.otr` **and**
`.mpq`. Layering is StormLib-native `SFileOpenPatchArchive`
(`Archive.cpp:525`) — patched files shadow base files transparently;
precedence is application order. A patch with no `version` member is
applied anyway (INFO log only, `:518`).

The `version` member: 1 byte endianness + uint32 game-version hash,
checked against `validHashes` (`ProcessOtrVersion`). Known hashes are
**OoT ROM CRCs** in `GameVersions.h` — SoH residue. Since 1.3.0 an
empty `validHashes` list skips the version-file check entirely (an
archive with no `version` member is then accepted), while game-version
tracking still records whatever versions it finds.

**Name lookup:** MPQ paths are the keys; `GenerateCrcMap` (`:377`) reads
the `(listfile)` and stores `~CRC64(line)` → path. **Bug:** it
unconditionally strips the last character of every line "to trim `\r`"
(`:386`) — LF-only or final lines lose a real character and hash wrong.

**Debug override:** under `_DEBUG`, `TestData/<path>` on disk shadows
the archive (`Archive.cpp:80-91`).

## Load pipeline (bytes → typed resource)

1. `ResourceManager::LoadResource(path)` → `LoadResourceAsync(...).get()`
   (`ResourceManager.cpp:189-190`); async submits `LoadResourceProcess`
   to the pool (priority jobs use `submit_front`). Fast3D calls
   `LoadResourceProcess` directly for synchronous loads
   (`gfx_pc.cpp:2396` etc.).
2. `LoadResourceProcess` (`:71`): strip `"__OTR__"` prefix; if CVar
   `gAltAssets` is set and not already alt, try `"alt/" + path` first
   (the HD-texture-pack mechanism); consult the cache; else
   `Archive::LoadFile` for raw bytes.
3. `ResourceLoader::LoadResource` (`ResourceLoader.cpp:46`) reads byte 0:
   - `'<'` → **XML resource**: tinyxml2 parse (no error checking —
     `:75` OTRTODO; malformed doc null-derefs), root element name picks
     the factory, always `IsCustom = true`.
   - else → **64-byte OTR binary header**: endianness(1) + isCustom(1) +
     pad(2) + type FourCC(4) + version(4) + id(8) + unnamed(4) +
     ROM CRC(8, discarded) + ROM enum(4, discarded) + reserved to 64.
4. Factory dispatches on version to a `ResourceVersionFactory` whose
   `ParseFileBinary` fills the typed payload.
5. Result (or `NotFound`) lands in the cache.

## Types and factories at this tag

`ResourceType` (`src/resource/ResourceType.h`) declares 6 generic types
with factories — **Texture (V0+V1), Vertex (the only one with an XML
path), DisplayList, Matrix, Array, Blob** — registered in
`ResourceLoader.cpp:25-32`; plus 15 `SOH_*` FourCCs with **no factories
in LUS** (games register their own) and an explicitly `(UNUSED)`
`Archive` type. DisplayList's binary parser understands the 128-bit OTR
opcodes (`G_SETTIMG_OTR_HASH` etc., `DisplayListFactory.cpp:68-74`);
its XML parser is ~900 lines of GBI command names (1.0.1 added
`Grayscale`/`SetGrayscaleColor`).

## Caching and lifetime

- Cache = `unordered_map<string, variant<ResourceLoadError,
  shared_ptr<IResource>>>` — **everything loads forever**; the header
  comment says so ("the entire ROM is 64MB"). No eviction. Negative
  results are cached and never invalidated.
- Resources do **not** keep the Archive alive (the `File` is dropped
  after parsing).
- Dirty flag = soft invalidation: next load re-parses and replaces the
  entry. `UnloadResource` erases outside the destructor to avoid
  deadlock (destructors may load resources, `:321-323`).
- Alt (`alt/…`) and base occupy separate cache keys.
- Archive write APIs (`CreateArchive`/`AddFile`/`RemoveFile`/
  `RenameFile`) exist for external tooling, have zero in-repo callers,
  and do NOT invalidate the resource cache (TODOs at `:229`, `:245`).

## Verified dead code and bugs (1.0.0)

- `ResourceClearCache` — declared (`resourcebridge.h:47`), **never
  defined**: calling it fails to link.
- `Texture` payload allocated `new uint8_t[n]`, freed with scalar
  `delete` (`type/Texture.cpp:17`) — UB.
- `FindLoadedFiles` iterates the cache with no lock
  (`ResourceManager.cpp:277`) — races worker inserts;
  `DirtyDirectory`/`UnloadDirectory` ride on it.
- `LoadResourceProcess` drops `loadExact` when recursing after
  `__OTR__` strip (`:75`); the async path forwards it — the two
  disagree.
- `ResourceLoadDirectoryAsync` discards its futures
  (`resourcebridge.cpp:154`).
- Listfile `\r` trim bug (above); `SFileCheckWildCard` hand-redeclared
  (`ResourceManager.cpp:13`); `#undef _DLL` at the top of the public
  `Archive.h`; informational logs at `SPDLOG_ERROR` severity
  (`Archive.cpp:365`, `:418`); `use_count() <= 0` guard that can never
  fire (`ResourceManager.cpp:229`).
