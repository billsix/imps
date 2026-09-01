# libultraship — resource system and archives

> **Pinned:** libultraship **1.3.1-397**
> (`7f2baa104108af3fca9f094754ea974a4973bdeb`, 2026-02-28 —
> MajorasMask's pin; a close cousin of iteration 14's 1.3.1-399,
> not its descendant). Updated 2026-09-01, iteration 15 of the
> reference crawl
> (`../../libultraship-reference-docs.md`). Re-sync check: compare
> `PIN_SHA` in `libultraship/fetch.sh` with the SHA above. This line is
> NEWER than tag 1.4.2 despite the smaller number.

## `.o2r` (zip) is the format now; MPQ is opt-in

The default archive is **zip via libzip** with an `.o2r` extension.
MPQ/`.otr` sits behind `INCLUDE_MPQ_SUPPORT` (**default OFF**,
`CMakeLists.txt:27`) — a stock build has no StormLib and **cannot open
`.otr` files** (they fall through to "unrecognized extension, trying
o2r" and fail). StormLib (v9.25 + local patch) no longer leaks into
consumers: `OtrArchive.h` is wrapped whole in `#ifdef
INCLUDE_MPQ_SUPPORT` and is the only StormLib includer.

## The classes

- **`Ship::Archive`** (`include/ship/resource/archive/Archive.h:20`) —
  now an abstract base (pure-virtual `Open/Close/LoadFile/WriteFile`)
  with three backends:
  - `O2rArchive` (libzip, one `zip_t*`) — **no thread safety**: every
    resource worker calls `zip_fopen_index`/`zip_fread` on the shared
    handle with no mutex (the 1.4.2 per-call StormLib mutex was dropped
    with no replacement). Also `Open` uses `ZIP_CREATE`
    (`O2rArchive.cpp:70`) — a typo'd path silently creates an empty
    archive instead of failing.
  - `OtrArchive` (StormLib, conditional) — **read-only**; `WriteFile`
    logs "use an o2r instead". The `(listfile)` CRC-map code survives
    here, `\r`-trim bug included (`OtrArchive.cpp:90`). `Open`
    null-derefs on a listfile-less MPQ (`:82-86`).
  - `FolderArchive` — a plain directory on disk (replaces the old
    `_DEBUG` `TestData/` override, which is gone).
- **`Ship::ArchiveManager`**
  (`include/ship/resource/archive/ArchiveManager.h:16`) — NEW; owns the
  archives plus global tables `mHashes` (CRC64→path), `mFileToArchive`,
  `mGameVersions`/`mValidGameVersions`.
- **`Ship::ResourceLoader`** — one factory map keyed by
  `ResourceFactoryKey{format, type, version}`
  (`include/ship/resource/ResourceLoader.h:12-28`) + a name→FourCC map.
  Registration rejects conflicts/duplicates; the 1.4.2
  null-insertion-from-worker-threads bug is fixed (lookup is
  `contains()`-then-`[]`).
- **`Ship::ResourceManager`** — cache + `BS::thread_pool` (priority +
  pause enabled via `#define`s before the include). The
  paused-forever-on-failed-archive behavior survives
  (`ResourceManager.cpp:58-61`, comment now explicit) but is normally
  unreachable: `Context::InitResourceManager` fails hard instead
  (`architecture-overview.md`).

## Archive mounting and layering

`Context::InitResourceManager` reads `Game.Main Archive` (default = app
dir) and `Game.Patches Archive` (default `<appdir>/mods`)
(`Context.cpp:206-207`) and passes both as one flat `archivePaths` list
— **no main/patch distinction exists below that point**.

`ArchiveManager::GetArchiveListInPaths` (`ArchiveManager.cpp:208-239`):
each directory contributes its `.otr/.zip/.mpq/.o2r` files; a directory
containing **none** is mounted itself as a `FolderArchive` (`:225-227`).
Extension dispatch in `AddArchive` (`:241-264`): `.o2r`/`.zip` → O2r;
`.otr`/`.mpq` → Otr only if MPQ support; `""` → Folder; unknown → warn
and try O2r.

**Layering is last-writer-wins**, not StormLib patching:
`mFileToArchive[hash] = archive` just overwrites (`:287`). Since
`directory_iterator` order is unspecified (`:215`), **mod precedence
within a directory is filesystem-order dependent** — no deterministic
rule. NEW live-mutation API: `WriteFile`, `RemoveArchive`,
`SetArchives` → `ResetVirtualFileSystem()` (full unload/reload). The
1.4.2 tooling API (`CreateArchive`/`AddFile`/…) is gone. Caveats:
`WriteFile` rebuilds file tables but **not** the resource cache (stale
resources survive); `ResetVirtualFileSystem` re-validates and can
silently drop version-invalid archives.

**Game-version validation:** the `version` member (1 byte endianness +
uint32 hash) is read in `Archive::Load()`; a mismatch warns and unloads
(`Archive.cpp:42-54`). Empty valid-set accepts everything; a missing
`version` member is accepted. **`GameVersions.h` is gone** — valid
hashes are a `std::unordered_set<uint32_t>` the port passes to
`CreateInstance`. Read surface: `GetGameVersions()` → bridge
`ResourceGetGameVersions`.

## Load pipeline (bytes → typed resource)

1. `LoadResource` still routes through the pool
   (`LoadResourceAsync(..., highest).get()`); Fast3D still calls
   `LoadResourceProcess` directly (`src/fast/interpreter.cpp:2513` etc.).
2. **NEW: `.meta` JSON sidecars come first.** `ResourceLoader::
   LoadResource` (`ResourceLoader.cpp:188-231`) tries `<path>.meta` —
   keys `path` (redirect to a different real file!), `format`
   (`"XML"`), `type` (name), `version`. Only without a `.meta` does the
   legacy first-byte sniff run (`'<'` → XML, else 64-byte binary
   header). `.meta` files are hidden from the index (`Archive::
   IndexFile` strips the suffix, `Archive.cpp:109-116`).
3. Binary header: `OTR_HEADER_SIZE 64` now in `Archive.h:15`; the ROM
   CRC/enum reads are commented out; **the header is sliced off the
   buffer before the factory sees it** (`ResourceLoader.cpp:113-116`) —
   factories no longer skip it themselves.
4. XML parses now check `xmlReader->Error()` (the 1.4.2 OTRTODO is
   fixed) — but `ReadResourceInitDataXml` still null-derefs on an
   empty-but-valid doc (`:291-293`).

## Types and factories — LUS registers almost nothing

`Ship::ResourceType` is down to **Blob, Json, Shader**
(`include/ship/resource/ResourceType.h:5-11`).
`RegisterGlobalResourceFactories` registers **Json + Shader only**
(`ResourceLoader.cpp:24-29`) — `Blob`'s factory exists but is
registered by nobody (loading an OBLB fails). GuiTexture (GTEX) and
Font (FONT) register lazily at GUI init. The six graphics types moved
to **`Fast::ResourceType`** — DisplayList, Light (NEW), Matrix,
Texture, Vertex (`include/fast/resource/ResourceType.h`) — classes and
factories ship in-tree but **the port must register them**
(`RegisterResourceFactory` has exactly 3 call sites, all engine-side).
`Array` and the 15 `SOH_*` FourCCs are gone. Vertex AND DisplayList
both have XML paths now.

## Caching and lifetime

- Cache key is no longer a bare string:
  **`ResourceIdentifier{Path, Owner, Parent-archive}`** with a
  precomputed hash (`ResourceManager.h:33-52`) — the same path from two
  archives (or owners) is two entries.
- Still `variant<ResourceLoadError, shared_ptr<IResource>>`, still no
  eviction, failure still memoized (`NotFound`).
- NEW `ResourceFilter{IncludeMasks, ExcludeMasks, Owner, Parent}` for
  bulk ops; `FindLoadedFiles` is gone — `DirtyResources`/
  `UnloadResources` iterate `ArchiveManager::ListFiles` instead.
- Alt assets: `gAltAssetPrefix` is a static on `IResource`; **no
  `gAltAssets` CVar read anywhere** — the port drives
  `ResourceManager::Set/IsAltAssetsEnabled`. Alt tried in both
  `LoadResourceProcess` and `CheckCache`, with a new already-failed-alt
  short-circuit.

## Verified bugs at this pin

- `ResourceClearCache` still declared, never defined
  (`resourcebridge.h:44`) — link error if called.
- **Unlocked cache write on the not-found path**:
  `mResourceCache[identifier] = NotFound` at `ResourceManager.cpp:144`
  with no lock — the old `FindLoadedFiles` race reincarnated.
- `UnloadResource`: TOCTOU (`contains` outside the lock, `:399`) and
  always returns 0 (`ret` never assigned).
- `LoadResourceProcess` still drops `loadExact` on the `__OTR__`-strip
  recursion (`:101`); the async path forwards it.
- `ResourceLoadDirectoryAsync` still discards futures
  (`resourcebridge.cpp:122-124`).
- `use_count() <= 0` dead guard (`ResourceManager.cpp:286`);
  `#undef _DLL` moved into the three archive headers;
  `ReadResourceInitDataPng` declared, never defined;
  `ArchiveManager::AddGameVersion` dead; `Config::mIsNewInstance`
  write-only.
- FIXED since 1.4.2: Texture scalar-`delete` (now `delete[]`,
  `src/fast/resource/type/Texture.cpp:17`); `SFileCheckWildCard`
  redeclaration (glob is `ship/utils/glob.h`); mount logs at ERROR
  severity (now INFO/WARN).
