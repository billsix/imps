# libultraship render-backend selection — why every Linux port's `run.sh` seeds OpenGL

**Reference document** — how a libultraship port chooses its renderer at startup, the config keys,
the ids, and the two independent reasons (Ghostship 2026-09-01, PaperBoat 2026-09-22) the imps
`run.sh` scripts pin OpenGL on first launch. Written 2026-09-22 by William Emerison Six
<billsix@gmail.com> (agent-assisted). Update in place; re-verify at a libultraship pin bump.

## The mechanism (read at PaperBoat's LUS fork `7aa03b6c`, same shape on mainline)

- `Fast3dWindow.cpp` registers the available backends **in this order**: DX11 (Windows), Metal
  (macOS), **Vulkan** (if `ENABLE_VULKAN` and `Vulkan_IsSupported()`), then **OpenGL**.
- `Window::GetSavedWindowBackend()` reads **`Window.Backend.Id`** from the app's config
  (`<app>.cfg.json` in the app directory); if that id is not available it falls back to **the front
  of the list** — so with no config, a Linux box with any Vulkan driver starts on Vulkan.
- The chosen backend is written back to the config on startup (`SetWindowBackend` →
  `Window.Backend.Id` + `.Name`), so **a config created by a previous run pins whatever that run
  picked**; seeding only matters when the file does not exist yet.
- Ids (`WindowBackend` enum, `include/fast/Fast3dWindow.h`): `FAST3D_SDL_OPENGL = 2`,
  `FAST3D_SDL_METAL = 3`, `FAST3D_SDL_VULKAN = 4` (DX11 on Windows). The `Name` string is informational.
- In-menu switching (the port's settings) writes the same keys, so a seed is overridden by the
  user's later choice and stays out of the way.

## Why OpenGL is seeded

- **Ghostship (SuperMario64), 2026-09-01:** Vulkan on the maintainer's RADV driver hung/crashed;
  `n64/SuperMario64/run.sh` seeds `Window.Backend.Id = 2` when no config exists.
- **PaperBoat (PaperMario), 2026-09-22:** the JeodC libultraship fork constructs the Vulkan backend
  with its default null arguments (`new GfxRenderingAPIVK()`), so the first shader build and the
  first draw dereference a null resource manager / console-variable store — a segfault on the
  first frame after ROM extraction on **every** Vulkan-capable Linux box. Fixed on the LUS lane
  (`n64/PaperMario/patches-libultraship/upstream-candidates/0001`), and `run.sh` still seeds
  OpenGL as the proven backend.

The seed pattern (both `run.sh`s):

```sh
cd runDir
if [ ! -f <app>.cfg.json ]; then
    cat > <app>.cfg.json <<'JSON'
{ "Window": { "Backend": { "Id": 2, "Name": "OpenGL" } } }
JSON
fi
```

Caveat for an existing `runDir`: a config from an earlier run already holds an id; delete the file
(or edit `Id` to 2) to get the seed. Caveat for headless tests: `SHIP_HOME` makes this LUS double
the config path, so seeds are only honoured with cwd as the app dir.

## Symptoms that mean "you are on the wrong backend"

- Crash on the first frame right after extraction, `RIP` in `ResourceManager::LoadResource` or
  `ConsoleVariable::Get`, backtrace through `BuildVulkanShader` / `GfxRenderingAPIVK::DrawTriangles`
  → the PaperBoat null-Context bug (fixed by the LUS patch; OpenGL avoids it).
- Black window / hang at startup on RADV → the Ghostship case; seed OpenGL.
- Confirm which backend ran by reading `runDir/<app>.cfg.json` (`Window.Backend.Id`); the log does
  not name it.
