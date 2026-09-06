# SuperMario64: default run.sh to the OpenGL renderer

**Status:** done — implemented + verified 2026-09-06; archived same day.
**Priority:** 2
**Difficulty:** 2

## BLUF

`./run.sh` for SuperMario64 (Ghostship) launched with the **Vulkan**
backend on first run, which hangs or crashes on some GPUs/drivers — the
maintainer hit it on a second machine. Fix: `run.sh` seeds
`runDir/ghostship.cfg.json` with OpenGL (Backend Id 2) **only when the
config does not exist yet**, so a first launch picks OpenGL and a later
in-menu switch to Vulkan (written back as Id 4) is preserved. All
backends stay compiled in; only the default changes. No build change and
no upstream patch — the seed lives in imps' own `run.sh`. Done when
`run.sh` on a fresh `runDir/` starts on OpenGL.

## Context

- **Read first:** `n64/SuperMario64/CLAUDE.md` (already records the
  RADV Vulkan hang and the `Id = 2` fix), `n64/SuperMario64/run.sh`.
- **Why the default is Vulkan (runtime, not build):** libultraship picks
  the front of its registered-backend list when no config exists
  (`Ghostship/libultraship/src/ship/window/Window.cpp` —
  `GetSavedWindowBackend` returns `mAvailableWindowBackends->front()`).
  On Linux the `Fast3dWindow` constructor
  (`Ghostship/libultraship/src/fast/Fast3dWindow.cpp`) adds Vulkan
  **before** OpenGL, so the built-in default is Vulkan whenever Vulkan
  was found at build time.
- **The build already builds "all backends available."** Ghostship always
  compiles OpenGL in on non-iOS (`Ghostship/CMakeLists.txt`,
  `ENABLE_OPENGL=1`); libultraship compiles Vulkan in when
  `find_package(Vulkan)` succeeds (`LUS_ENABLE_VULKAN`). So only the
  runtime default needed changing.
- **Config mechanics (verified in `Config.cpp`):** the file is
  `ghostship.cfg.json` (app id set in `src/port/Engine.cpp`), stored as
  **nested** JSON, dot-keys mapped via flatten/unflatten. `Window.Backend.Id`
  = 2 selects `FAST3D_SDL_OPENGL` (enum in
  `libultraship/include/fast/Fast3dWindow.h`). A partial, version-less
  seed is safe: `RunVersionUpdates` treats a missing `ConfigVersion` as 0,
  runs its updaters, and fills every other key from defaults — nothing is
  rejected or renamed to `.bak`.

### Decisions made with the maintainer (2026-09-06)

- **Seed in `run.sh`, not a code patch.** imps-native, needs no rebuild,
  keeps Vulkan fully available, zero rebase cost across pin bumps. A patch
  reordering backend registration was considered and rejected (touches
  upstream code, permanent personal-patch rebase cost, same effect).
- **Default to OpenGL universally, not per-machine.** OpenGL works
  everywhere; Vulkan is the fragile one and the maintainer's own GPU
  (RADV Radeon 610M) also hangs on it. Anyone who wants Vulkan flips it in
  the menu and the choice persists.

## The AppImage gap — noted, deliberately NOT fixed

The seed lives in `run.sh`. The podman `appimage` target packages only the
binary, so **an AppImage launched directly (not via `run.sh`) still picks
Vulkan on first run.** This is accepted, not a bug to fix: the maintainer
builds from source and runs via `run.sh` for his own play; the podman
AppImage exists **only to stay consistent with upstream's CI/CD** (mirror
the `main.yml` build-linux job), not as his run path. If a future need
arises to make the AppImage default to OpenGL too, the seed would have to
move into the packaged runtime (e.g. an AppRun wrapper), which is out of
scope here.

## SuperMario64-only

Ghostship is the only imps game whose libultraship (the `1.3.1-544`
KiritoDv fork) registers a Vulkan backend at all. Ocarina, Majora's Mask,
and Banjo run on older LUS (1.3.1-397/-482/-486) that never registers
Vulkan, so they already default to OpenGL. No change needed there.

## Done-state

- `n64/SuperMario64/run.sh` seeds `ghostship.cfg.json` with Id 2 / "OpenGL"
  when absent, before launching, and leaves an existing config untouched.
- The seed's shape matches what libultraship writes on save (nested
  `Window.Backend.{Id,Name}`).
- `SuperMario64/CLAUDE.md` updated to point at the seed instead of "switch
  to OpenGL by hand if it goes silent."

## Verification

Seed is a shell `[ -f ] ||` heredoc guard — verified by inspection and by
generating the file into a scratch dir and confirming it is valid JSON
with `Window.Backend.Id == 2`. A full on-hardware run is the maintainer's
own build-from-source launch; the code path (front-of-list default vs a
present Id-2 config) is settled by the source reading above.
