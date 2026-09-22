# PaperBoat ROM import: the whole investigation, the fixes, and how to test a GUI port headless

**Reference document** — the complete account of the 2026-09-21/22 "the ROM won't load" work on
`n64/PaperMario/`: what was reported, every hypothesis and what killed it, the two real bugs, the
three patches that resulted, the headless testing method that proved them, the process-leak
incident, and what is still unverified. Written for re-use on the next HarbourMasters port with the
same shape (libultraship + Torch + an in-app extractor). Written 2026-09-22 by William Emerison Six
<billsix@gmail.com> (agent-assisted). Not a task; update in place. The ROM-specific short form
(sizes, hashes, the trim) is `rom-overdump-and-trimming.md` next to this file.

## 1. The reports, in order

1. 2026-09-21: "the build worked, but the ROM wasn't loading" — PaperBoat showed **"Extraction
   error — No ROM O2R file detected"**. The 09-21 session read the extractor and concluded, by
   reasoning, that the maintainer's `ROMF.z64` (64 MB) could not match the only `config.yml` recipe
   (a whole-file SHA-1 of a 40 MB image) and wrote the "trim to 40 MB" guidance.
2. 2026-09-22, 02:40: the trim was verified from scratch (first 40 MB of the file hash to the
   recipe key; the tail is `00`/`0f`/`ff` padding) and `pm64.z64` written next to the original.
3. 02:42: the maintainer put the trimmed image in place as `ROMF.z64` (originals moved to
   `originalBillRip/`), imported it through PaperBoat's file dialog, and the game **segfaulted
   "near the end"** — crash handler output: `Signal: 11`, `RIP 0xA31347`, no symbols.
4. "Try to build from scratch and import ROMF.z64, make sure the sha1 matches, make importing
   from the command line work; iterate, keep working" — the overnight unit this doc records.

## 2. What the port actually does with a ROM (read from `1.0.1`, `424c220f0`)

- `src/port/Engine.cpp` `RunExtract()` is a state machine driven by ImGui **modal popups**
  (`PaperboatGui::RegisterPopup`, drawn by `PaperboatModals.cpp`, each button a real
  `ImGui::Button`). Flow on Linux, pristine: port archive check → `AnyRomArchiveExists()`
  (`pm64.o2r` in the app dir / next to the binary / cwd) → if absent, popup "No O2R Files —
  Generate one now?" → scan the binary's dir and the app dir for **supported** `.z64` files
  (`FindSupportedRoms`) → popup "ROMs found" → extract; or, if none, the **file dialog**
  (`SelectGameFromUI` → portable-file-dialogs → `zenity`) → `LoadRomFromPath` (no hash check!) →
  extract → popup "Run PaperBoat?" → the game.
- **Supported** means `GetSupportedRomNode()`: SHA-1 over the **entire file**
  (`Companion::CalculateHash`) is a key in `config.yml`. One US key: `3837f44cda784b466c9a2d99df70d77c322b97a0`.
- **Command-line ROM (`Paperboat rom.z64`)**: argv is collected, but the transition to
  `ES_EXTRACT_ARGS` sits inside the **Windows-only** `ES_WINDOWS` branch. On Linux the argument
  was ignored.
- **Torch** (`external/torch`, JeodC `pm64` branch) hashes the same way in `Cartridge::Initialize`;
  on an unknown hash it logs "No config found" and *returns normally*, so `GenerateOTRTo()` reports
  success with no archive written — the origin of the misleading "No ROM O2R" message.
- The app directory on Linux is `SHIP_HOME` if set, else `.` (`NON_PORTABLE` is off). With
  `SHIP_HOME` set, libultraship doubles the config path (`<dir>//<dir>/paperboat.cfg.json`) and
  never reads it — so a headless run that needs a seeded config must use cwd as the app dir.

## 3. The two real bugs

### 3a. The crash "near the end": Vulkan backend built with null Context objects

The host's `RIP 0xA31347` symbolized on an identical-toolchain sandbox build (same Fedora 44 gcc,
same flags) to `Ship::ResourceManager::LoadResource`; a headless reproduction under gdb gave the
full chain: `Fast::BuildVulkanShader → GfxRenderingAPIVK::CreateAndLoadNewShader →
Interpreter::GfxSpTri1 → … → GameEngine::ProcessGfxCommands → main`, i.e. **the game's first
frame after extraction**. In the libultraship fork (`external/libultraship`, JeodC
`lus-converge` @ `7aa03b6c`), `Fast3dWindow.cpp` does `new GfxRenderingAPIVK()` — the constructor
takes `(consoleVariable = nullptr, resourceManager = nullptr)` and keeps both; the first shader
build dereferences the resource manager, and once that is fixed the first draw dereferences the
console-variable store (`DrawTriangles → ConsoleVariable::GetInteger`, found by the second gdb
run). The OpenGL backend reads both through `Ship::Context::GetRawInstance()` instead, which is
why OpenGL works. libultraship registers Vulkan before OpenGL on Linux and picks the front of that
list when no config exists, so **every Linux machine with a Vulkan driver crashed identically**
(RADV on the maintainer's host, lavapipe under Xvfb).

### 3b. Unsupported ROMs handled silently or not at all

Through the scan, a file that is not exactly the recipe image is simply never offered; through
the dialog it is accepted, "extracted" to nothing, and reported as "No ROM O2R". And on Linux the
command line was dead. The 64 MB over-dump exercised all three.

## 4. The patches (imps `n64/PaperMario/`, all upstream candidates)

Game-tree lane, `patches/upstream-candidates/` (only `src/port/Engine.cpp`,
`src/port/extractor/GameExtractor.cpp`):

- `0001` — take the `args → ES_EXTRACT_ARGS` branch on non-Windows too. `Paperboat <rom>` then
  goes straight to `RunStandalone` (hash-checked) → extraction → "Run PaperBoat?".
- `0002` — `LoadRomFromPath` refuses a file matching no recipe, records the reason in
  `sLastError` (size, byte order, "a padded dump must be trimmed"), and the picker callback shows
  it as a "PaperBoat ROM Error" popup; a plain cancel is unchanged.

libultraship lane, `patches-libultraship/upstream-candidates/`:

- `0001` — `gfx_vulkan.cpp`: resolve the resource manager and the console-variable store
  through the Context when none was injected (a `VKResourceManager()` helper and a
  `ConsoleVariables()` method), so the backend no longer depends on constructor injection that
  `Fast3dWindow` never performs.

Around them: `apply.sh` (the family's two-lane stream machinery), and `run.sh [ROM]` — verifies
the file's SHA-1 against the recipes in the *built* `config.yml` (so a pin bump adding a version
needs no edit), auto-trims a longer file whose first 40 MB match into `runDir/pm64.z64`, refuses
anything else printing the expected hash and the usual causes, passes the accepted path on the
command line, and seeds `Window.Backend.Id = 2` (OpenGL) into `runDir/paperboat.cfg.json` on
first launch — the proven backend, and the same defence Ghostship's `run.sh` uses.

## 5. Will it work on the host? (the honest forecast)

**Answered 2026-09-22: it works** — the maintainer built with the series and played from
`run.sh` on the host ("building and using run.sh works as is now"). The forecast as written the
night before, kept for the record: **expected yes.** Everything my changes touch is proven in the sandbox: extraction through both
paths, the ROM refusal, the trim, and — the part that actually crashed you — the game running
past its first frame on Vulkan (lavapipe) and on OpenGL (llvmpipe) for 30 s each with audio
initialized. What the sandbox cannot show is a picture or sound, so "the title screen appears and
plays" is the one claim still owed to a real display. Two safety nets if something on your GPU
differs: `run.sh` starts on OpenGL regardless of the Vulkan patch, and a wrong ROM is refused
before the app even launches. If it still fails, the first thing to read is
`runDir/logs/Paperboat.log` and the crash handler's `RIP`, which this build can be symbolized
against (`addr2line -e PaperBoat/build/ninja-release/Paperboat -f -C <addr>`).

## 6. How the proofs were run (re-usable for any HarbourMasters port)

`tasks/adhoc/papermario-rom-import/test_paperboat.sh` (+ `zenity-shim/`, `patch_autoclick.py`,
`patch_trace.py`). The method, because each piece cost real time to find:

- **Display:** `Xvfb :99` + `LIBGL_ALWAYS_SOFTWARE=1`. Vulkan resolves to lavapipe, OpenGL to
  llvmpipe — both real enough to exercise the crash and the fix.
- **Popups cannot be clicked.** The GL window's contents are not capturable under Xvfb (every
  screenshot is black), so `xdotool` has nothing to aim at, and ImGui buttons need a real click.
  Answer: a throwaway commit adding `PAPERBOAT_AUTOCLICK=1` → every modal takes its first button
  immediately (`PaperboatModals.cpp`). Never exported as a patch; lives on the checkout's
  `imps-test` branch (= `imps-work` + instrumentation).
- **The port swallows stdout.** `printf` instrumentation vanished for an hour; `fprintf(stderr, …)`
  (or spdlog) works. The `[trace]` lines (every `RegisterPopup`, `LoadRomFromPath`,
  `RunStandalone`, `GenerateOTRTo` with byte count and paths, and `RunExtract`'s inputs) are what
  finally showed the real control flow instead of the reconstructed one.
- **The file dialog:** portable-file-dialogs finds `zenity` with `which` and reads the chosen
  path from its stdout, so a `zenity` shim first on `PATH` that prints `$FAKE_ZENITY_PICK` drives
  the exact picker path.
- **Crashes:** run under `gdb -q --batch -ex run -ex "bt 8"`; the app's own crash handler prints
  registers but no symbols.
- **Termination:** the game **ignores SIGTERM**; `timeout -s KILL` on every launch, plus an EXIT
  trap that `pkill -9`s the binary, plus a `ps` audit — see §8.
- **App dir = cwd**, not `SHIP_HOME` (§2), or seeded configs are never read.
- **Check the input file's identity at every step.** The "64 MB" runs after 02:42 were reading a
  40 MB file; for an hour the evidence looked like Torch normalized over-dumps. It does not.

Verification record (2026-09-22, sandbox): six scenarios, 20/20 checks; `apply.sh` from the bare
pins reproduces the work trees byte-identically (game tree `fe12e9dc…`, LUS `38867d0c…`).

## 7. What the maintainer changed, and what that did

Renaming the trimmed image over `ROMF.z64` was the right move and broke nothing — it is exactly
what the port wants. Its only side effect was on the *investigation*: several sandbox runs labelled
"64 MB" read the new file. Nothing in imps or the checkout depends on the ROM's name or location.

## 8. Incident: leaked test processes swapped the host

Over the night, headless runs left `Paperboat` instances behind: the game ignores SIGTERM (so a
plain `timeout` and `kill` did nothing), gdb-wrapped runs orphaned the inferior when gdb was
killed, `pkill -x Paperboat` did not match a copy I had renamed to `Paperboat.pristine`, and no
`ps` audit was run between experiments. Two of those renamed copies, stuck in the pristine popup
loop, grew to **~19 GB RSS each** over 8 hours; the host went into swap and was "borderline
unusable for 10 minutes" in the morning. Killed by pid at 08:12; memory went from 45 GB used /
6.3 GB swap to 6 GB / 2.2 GB. Rules now in the harness and in memory: hard timeouts only, an EXIT
trap that reaps the binary, never a renamed copy, a `ps` audit before moving on and before ending
a session, and the audit result stated in the report.

## 9. Still open

- ~~Host gameplay verify~~ — done 2026-09-22 (built and played on the maintainer's host).
- Whether to submit the three patches upstream (PaperBoat ×2, JeodC/libultraship ×1).
- Why the pristine binary's popup loop leaks memory (~40 MB/s judging by 19 GB in 8 h) — a
  separate upstream bug worth a report, not investigated.
- The libultraship reference crawl does not cover the JeodC fork; the LUS-lane patch was made
  from a direct read of two functions, not the crawl.

## Related

- `rom-overdump-and-trimming.md` — the ROM sizes/hashes/trim, and the evidence chain for the over-dump.
- `n64/PaperMario/CLAUDE.md` — the operational facts (scripts, patches, version notes).
- `tasks/archive/papermario/2026/09/22/papermario-add-port.md` — the port task (archived 2026-09-22: host-verified). Upstream submission: `tasks/papermario-upstream-patches.md`.
- `n64/SuperMario64/run.sh` — the OpenGL-seed precedent (Ghostship's Vulkan-on-RADV hang).
