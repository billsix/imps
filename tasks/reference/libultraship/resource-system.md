# libultraship — resource system and archives

> **Pinned:** libultraship **1.3.1-482**
> (`2917d0f4fe62c579174561dcd34f327c9410bb72`, 2026-07-29 —
> BanjoKazooie's pin; direct descendant of 1.3.1-397, 85 commits).
> Updated 2026-09-01, iteration 16 of the reference crawl
> (`../../libultraship-reference-docs.md`). Re-sync check: compare
> `PIN_SHA` in `libultraship/fetch.sh` with the SHA above. This line is
> NEWER than the 1.4.x tags despite the smaller number.

## `.o2r` (zip) default; MPQ opt-in — unchanged

`INCLUDE_MPQ_SUPPORT` default OFF (`CMakeLists.txt:41`); a stock build
cannot open `.otr`. StormLib confined to the conditional `OtrArchive`.

## The classes

- **`Ship::Archive`** (abstract base, `include/ship/resource/archive/Archive.h:59`)
  with `O2rArchive` / `OtrArchive` (MPQ-gated, read-only) /
  `FolderArchive`.
  - **The O2r thread-safety gap is FIXED (#1050)**: reads check out a
    handle from a mutex-guarded **pool** (`GetZipHandle`/
    `ReleaseZipHandle`, `O2rArchive.cpp:18-35`; `mPoolMutex`/
    `mZipArchivePool`, `O2rArchive.h:79-80`), opening a fresh
    `zip_open(ZIP_RDONLY)` on pool miss; `Close`/`WriteFile` drain the
    pool. Caveat: handles opened while the file changes on disk are
    only invalidated by `WriteFile`'s own drain.
  - `Open` still uses `ZIP_CREATE` (`O2rArchive.cpp:98`, also on
    reopen `:184`) — a typo'd path still silently creates an empty
    archive. OtrArchive still null-derefs on a listfile-less MPQ and
    still has the `\r`-trim off-by-one (`OtrArchive.cpp:82-90`).
  - **NEW: `Archive::Load` parses a `manifest.json`**
    (`Archive.cpp:58-95`): name/author/version/website/description/
    license, `code_version`, `game_version` (also sets+validates the
    game version), `main`, `binaries`, `dependencies`, `checksum`,
    `signature`, `public_key` — exposed via `GetManifest()`,
    `IsSigned()`, `IsChecksumValid()`. Parsing is unconditional; only
    validation is scripting-gated:
  - **NEW: signing/trust chain (`ENABLE_SCRIPTING` only, #1068/#1095).**
    `Archive::Validate()` (`Archive.cpp:183-291`): BLAKE2b-64 checksum
    over sorted `path||bytes` of every file, then ed25519 signature
    check against every **Keystore** key (monocypher). Unknown public
    key → `ArchiveManager`'s `UntrustedArchiveHandler` callback decides
    (typedef `ArchiveManager.h:27`); accepted keys are added to the
    keystore. `Ship::Keystore` (`include/ship/security/`) persists keys
    **inside the config JSON** under a top-level `"Keystore"` node
    (`Keystore.cpp:59-86`). All compiled out in a default build.
- **`Ship::ArchiveManager`** (class now at `ArchiveManager.h:41`) —
  owns archives + the global CRC64 tables. `WriteFile` now only updates
  the tables (`ArchiveManager.cpp:156-159`); the reopen/re-index moved
  into `O2rArchive::WriteFile`. Still does **not** touch the resource
  cache (stale resources survive a write).
- **`Ship::ResourceLoader`** — one factory map keyed
  `{format, type, version}`; registers **Json + Shader only**
  (`ResourceLoader.cpp:25-28`); GTEX lazy at `Gui.cpp:109`, FONT at
  `GameOverlay.cpp:160`; the `Fast::` graphics factories are still the
  **port's** to register; **Blob's factory still registered by
  nobody**.
- **`Ship::ResourceManager`** — cache + thread pool; the
  paused-forever-on-failed-archive behavior survives
  (`ResourceManager.cpp:63-66`), normally unreachable (Context fails
  hard first).

## Mounting, layering, versions — unchanged mechanics

`Game.Main Archive` + `Game.Patches Archive` → one flat path list
(`Context.cpp:234-235`); per-directory archive collection with the
FolderArchive fallback (`ArchiveManager.cpp:205-236`); extension
dispatch (`:238-261`); **layering is last-writer-wins**
(`mFileToArchive[hash] = archive`, `:284`). The doxygen now *claims*
"most recently added takes precedence" (`ArchiveManager.h:33-35`) — but
within one directory the order is still unspecified
`directory_iterator` (`:212`), i.e. **still filesystem-order
dependent**, now with an upstream determinism claim it doesn't have.
Game-version validation unchanged (warn + unload; empty set accepts
all; `ArchiveManager.cpp:295-297`).

## Load pipeline

1. `.meta` JSON sidecars first (redirect/format/type/version,
   `ResourceLoader.cpp:168-203`; suffix hidden from the index,
   `Archive.cpp:174-181`); else legacy sniff (`'<'` → XML, else 64-byte
   binary header, `OTR_HEADER_SIZE` at `Archive.h:16`).
2. **Header slicing replaced by zero-copy offset (#1027)**: `File`
   gained `BufferOffset` (`File.h:61`); `CreateBinaryReader` builds
   `MemoryStream(Buffer, BufferOffset)` (`ResourceLoader.cpp:120-125`).
   Factories still never see the header — same contract, no copy.
3. XML error-checked but `ReadResourceInitDataXml` still null-derefs on
   an empty-but-valid doc (`:288-290`).

## Caching and lifetime

- `ResourceIdentifier{Path, Owner, Parent}` + precomputed hash; move
  constructor added (#1022, `ResourceManager.cpp:29-32`); no eviction;
  failure memoized.
- **NEW `ResourceManager::WriteResource` (#1013)**
  (`ResourceManager.cpp:429-450`): resolves the owning archive, writes
  via `ArchiveManager::WriteFile`, optionally unloads the cached
  resource. C++-only, no bridge.
- **NEW `ResourceManager::CacheExternalResource`**
  (`ResourceManager.cpp:424-427`, locked) — the port injects a resource
  under a path (used by GUI textures).
- **NEW Fast3D-side memoization (#1175)**:
  `Interpreter::ResolveResourceCached` memoizes `LoadResourceProcess`
  hits keyed by display-list pointer, **off by default**
  (`interpreter.h:511`); only hits memoized (so
  `CacheExternalResource` still lands); cleared with the texture cache.
- Alt assets: still `Set/IsAltAssetsEnabled`
  (`ResourceManager.cpp:457-463`), no `gAltAssets` CVar anywhere.
- Perf churn that nets to zero: #989 (cache-lookup change) was fully
  reverted by #1028.

## Verified bugs at this pin

- `ResourceClearCache` **still declared, never defined**
  (`resourcebridge.h:136`) — and now even `API_EXPORT`ed.
- **Unlocked cache write on the not-found path still there**
  (`ResourceManager.cpp:156`, outside the `:168` lock).
- `UnloadResource` TOCTOU + always-returns-0 still there
  (`:410-417`).
- `loadExact` still dropped on the sync `__OTR__`-strip recursion
  (`:106`, now an explicit `false`); the async recursion additionally
  drops `initData` (`:204`).
- `ResourceLoadDirectoryAsync` still discards futures
  (`resourcebridge.cpp:124-126`).
- `use_count() <= 0` dead guard (`:298`); `ReadResourceInitDataPng`
  declared-never-defined (`ResourceLoader.h:150`);
  `ArchiveManager::AddGameVersion` dead (`ArchiveManager.cpp:126`);
  `Config::mIsNewInstance` write-only.
- FIXED since 397: the O2r shared-handle races (#1050, above).
