# Paper Mario ROM: the 64 MB over-dump, how it was found, and how it was trimmed

**Reference document** — why PaperBoat rejected the maintainer's Paper Mario dump, the evidence
chain that found it, the one-line fix, and the proofs. Not a task; update in place. Written
2026-09-22 by William Emerison Six <billsix@gmail.com> (agent-assisted); first diagnosed 2026-09-21
(`../../../n64/PaperMario/CLAUDE.md` "ROM requirements"), re-verified from scratch and proven both
ways 2026-09-22. ROMs stay out of imps' scope — this doc is guidance about a file the repo never
contains.

## The symptom

`./build.sh` succeeded, but on launch PaperBoat showed **"Extraction Error — No ROM O2R file
detected. Please generate a ROM O2R and relaunch."** — with no extraction ever visibly running, and
no `pm64.o2r` appearing in the run directory. The ROM given to it was
`/foo/opt/n64/n64roms/PaperMario/ROMF.z64` (container path; the maintainer's ROM set).

## What PaperBoat actually checks

Read from the pinned source (`1.0.1`, `424c220f0`):

- `src/port/extractor/GameExtractor.cpp` `GetSupportedRomNode()` reads the **whole file** into
  memory, hashes **all of it** with SHA-1 (Torch's `Companion::CalculateHash`), and looks the digest
  up as a **key in `config.yml`**. No header sniffing, no size heuristics, no truncation.
- `config.yml` has exactly one US key: **`3837f44cda784b466c9a2d99df70d77c322b97a0`**.
- Every path into extraction goes through that lookup: `FindSupportedRoms()` (the scan of the
  binary's directory and the app directory for `.z64` files — only *supported* ones are offered),
  `RunStandalone()` (a path handed in), and `ValidateChecksum()`/`DetectVersion()`. A file whose
  whole-file hash is not a key is simply *not a ROM* as far as the extractor is concerned, so the
  state machine in `src/port/Engine.cpp` `RunExtract()` reaches `ES_VERIFY` with no archive and
  shows the generic "No ROM O2R" popup. The misleading part is that the message reads like a
  post-extraction failure; the extractor never ran.

## The evidence chain

1. **The file is the wrong size.** `ROMF.z64` is **67,108,864 bytes (64 MB)**. The sidecar
   `CartTest.txt` from the dumper says `Romsize - 64MB` and `CIC - Failed 6103`: the cart tester
   could not identify the CIC, fell back to the maximum size, and read the whole 64 MB address
   space. Paper Mario is a 320 Mbit cart = **41,943,040 bytes (40 MB)**.
2. **The header is right.** `xxd -l 64 ROMF.z64` starts `80 37 12 40` (big-endian `.z64`) and carries
   the title `PAPER MARIO` and ID `NMQE` (US). So it *is* the right game in the right byte order —
   only the length is wrong. (The sibling `ROM.n64` is the same dump byte-swapped: `37 80 40 12`,
   `APEP RAMIR O` — a `.n64`/`.v64` hashes differently again and is not what the port wants.
   `ROMF.flash` / `ROM.fla` are 128 KB FlashRAM save images — `Mario Story 006` — not ROMs.)
3. **The first 40 MB hash to the recipe key.** This is the decisive test:
   ```sh
   head -c 41943040 ROMF.z64 | sha1sum      # → 3837f44cda784b466c9a2d99df70d77c322b97a0
   ```
   exactly the `config.yml` key.
4. **The trailing 24 MB is padding.** A byte histogram of a sample of the tail is almost entirely
   `00`, `0f` and `ff` — open-bus / unprogrammed flash, not game data. Nothing is lost by cutting it.

Whole-file SHA-1 of the 64 MB file is `5f10c5423fdfe611ee1345ff70e79a97bf1891d0` — matches nothing,
so the extractor's lookup misses. That is the entire bug.

## The fix — trim, don't re-dump

```sh
# [ANY] next to the original; nothing is overwritten
head -c 41943040 ROMF.z64 > pm64.z64
sha1sum pm64.z64        # must print 3837f44cda784b466c9a2d99df70d77c322b97a0
```

Done 2026-09-22: `/foo/opt/n64/n64roms/PaperMario/pm64.z64` (40 MB, hash verified). The cart dump
itself is fine; re-dumping would only reproduce the 64 MB file unless the dumper is told the size.

Feed `pm64.z64` to PaperBoat by putting it in the binary's directory or the app directory (the
"ROMs found" prompt then offers it), or pick it in the file dialog. With `run.sh`, the app directory
is the run directory (`runDir/`).

## Proof, both ways (sandbox, headless, 2026-09-22)

Pristine `1.0.1` build (`./build.sh`, Fedora 44), run under `Xvfb :99` with `LIBGL_ALWAYS_SOFTWARE=1`
and `SHIP_HOME=<run dir>` (on Linux `Ship::Context::GetAppDirectoryPath()` honours `SHIP_HOME`, so the
run dir is the app directory):

- **Trimmed 40 MB `pm64.z64` in the app dir → extraction ran unattended and succeeded.** The log
  shows Torch's banner (`Hash: 3837f44c…`, `Country: [us]`, `Assets: …/assets/yaml/us`), then
  `Done! Took 27073ms`; **`pm64.o2r` = 40,095,335 bytes** appeared in the app dir. No popup needed
  clicking in this run.
- **The 64 MB `ROMF.z64` in the same place → nothing.** No Torch banner in the log, no `pm64.o2r`,
  the app fell through to the "no ROM" path and exited — the maintainer's symptom, reproduced.

The maintainer then reported the trimmed file working on the host the same day.

## What happened next (same night): "it crashed near the end" was not the ROM

After the trim the maintainer replaced `ROMF.z64` with the 40 MB image (the originals moved to
`originalBillRip/`), imported it through the file dialog, and PaperBoat segfaulted "near the end"
— i.e. after a *successful* extraction, on the game's first frame. Symbolized against an
identical-toolchain sandbox build, the host's `RIP` landed in `Ship::ResourceManager::LoadResource`,
and a headless reproduction under gdb gave the full chain: `Fast::BuildVulkanShader →
GfxRenderingAPIVK::CreateAndLoadNewShader → … → main`. Cause: `Fast3dWindow` constructs the Vulkan
backend with its default arguments (`new GfxRenderingAPIVK()`), so the resource manager it loads
shader templates through and the console-variable store it reads CVARs from are both null; the
first shader build dereferences one, the first draw the other; libultraship prefers Vulkan on Linux whenever
`Vulkan_IsSupported()`, so every Linux box with a Vulkan driver (RADV on the host, lavapipe under
Xvfb) crashed identically. Fixed on the libultraship lane (resolve both through the Context on use,
as the OpenGL backend does) and worked around in `run.sh` (seed OpenGL) — see
`n64/PaperMario/CLAUDE.md` "Patches" / "Vulkan crash".

Two investigation lessons worth keeping: (1) **check the input file's identity at every step** — for
an hour the "64 MB" runs were reading a file that had silently become 40 MB, which made Torch look
like it normalized over-dumps (it does not; `CalculateHash` is a plain whole-file SHA-1); (2) the
port swallows `stdout`, so instrumentation must go to stderr or spdlog, and ImGui popups cannot be
clicked under Xvfb (the GL window is uncapturable) — an env-gated auto-click hook on a throwaway
branch is the way to drive the prompt flow headlessly.

## Gotchas met on the way (sandbox-side, not the ROM)

- **`libshaderc-devel` must be installed BEFORE `cmake` configures.** Missing it, the build fails
  late — at the final link, on `shaderc_*` undefined references (`gfx_vulkan.cpp`); installing it
  after configure does not help until `cmake --preset ninja-release` runs again (build.sh does).
  `n64/PaperMario/installdependencies.sh` lists it; it was added to the runClaudeInContainer and
  runCrushInContainer base package lists 2026-09-22 so fresh sandboxes have it.
- **Passing the ROM on the command line did nothing on Linux (pristine).** In `RunExtract()` the
  `args → ES_EXTRACT_ARGS` transition sat inside the Windows-only `ES_WINDOWS` branch; on Linux the
  flow was scan-the-app-dir → prompt → extract, or the file dialog. imps game-tree patch `0001`
  takes the same branch on Linux/macOS, which is what `run.sh <ROM>` uses.
- **The `.o2r` lands in the app directory** (`GetAppDirectoryPath("boat")`), which is `SHIP_HOME` if
  set, else the SDL pref path or `.`. With absolute `SHIP_HOME`, libultraship logs a few harmless
  `Could not open "<SHIP_HOME>//<SHIP_HOME>/…"` config errors (a doubled-path quirk) — cosmetic.

## Related

- `rom-import-investigation.md` — the full investigation (both bugs, the patches, the headless method, the process-leak incident).
- `n64/PaperMario/CLAUDE.md` — the port's operational facts (pin, scripts, dependency deltas); its
  "ROM requirements" section is the short form of this doc.
- `tasks/archive/papermario/2026/09/22/papermario-add-port.md` — the port task (archived 2026-09-22: host-verified).
- Source anchors: `src/port/Engine.cpp` `RunExtract`, `src/port/extractor/GameExtractor.cpp`
  `GetSupportedRomNode` / `FindSupportedRoms` / `RunStandalone`, `config.yml`, Torch
  `Companion::CalculateHash`.
