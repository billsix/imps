# Reference: The graphics pipeline — one triangle's journey, N64 list → GPU

> **Provenance:** authored 2026-09-06 against Ghostship pin `49c5312a`,
> libultraship submodule `c151cc91` (1.3.1-544 fork). Anchors in the port
> (`src/port/`) and the pinned LUS (`libultraship/src/fast/`). Part of the
> mario64 graphics set — map at [`README.md`](README.md). L1:
> [`graphics-pipeline-overview.md`](graphics-pipeline-overview.md). This
> doc **stitches** the existing `frame-interpolation.md` and
> `libultraship-integration.md` with the shader/texture docs — it is the
> map, they are the detail.

## TL;DR

The decomp emits N64 **display lists** exactly as on hardware. The port's
`exec_display_list` (`Game.cpp:26`) diverts them to
`GameEngine::ProcessGfxCommands` (`Engine.cpp:1387`), which **replays the
same list N times** with interpolated matrices (the smooth-framerate trick),
each pass calling `RunCommands` (`:1352`) → the Fast3D `Interpreter::Run`
(`interpreter.cpp:6644`). The interpreter **translates** N64 graphics
commands into vertex batches and, per material, looks up or **generates a
shader** from the N64 color combiner, then calls
`DrawTriangles` (`:146`) on a **GPU backend** (OpenGL / Vulkan / DX11 /
Metal). So one N64 triangle flows: display list → interpreter → generated
shader + vertex buffer → GPU backend → pixels.

## 1. The stages, end to end

```
decomp  (src/game/rendering_graph_node.c)
   │  walks the geo tree, emits ONE N64 display list (Gfx*) per frame
   ▼
exec_display_list (Game.cpp:26)  ──diverts──►  GameEngine::ProcessGfxCommands (Engine.cpp:1387)
   │  computes N interpolated matrix sets for the target FPS (frame-interpolation.md)
   ▼
RunCommands (Engine.cpp:1352)  ──per interpolation sub-frame──►
   ▼
Fast::Interpreter::Run (interpreter.cpp:6644)   ← the Fast3D command translator
   │  • decodes F3D/F3DEX commands (matrices, vertices, textures, combine modes)
   │  • per material: LookupOrCreateColorCombiner (:632) → generated shader (shaders-and-gpu.md)
   │  • uploads textures (textures-and-texture-mapping.md), builds vertex batches
   ▼
mRapi->DrawTriangles (interpreter.cpp:146)   ← hand to the backend
   ▼
GPU backend  (gfx_opengl.cpp / gfx_vulkan.cpp / gfx_d3d11 / gfx_metal)  →  pixels
```

Two properties a newcomer must internalize:

- **The list is replayed, not rebuilt, per rendered frame.** One game tick
  builds one display list; `ProcessGfxCommands` draws it several times with
  different interpolated matrices to hit 60/120/… FPS. Details:
  `frame-interpolation.md`.
- **The N64 command stream is translated, not emulated cycle-accurately.**
  Fast3D reads F3D/F3DEX macros and re-expresses them as modern GPU draws;
  it is a *translator* with a shader cache, not an RSP simulator.

## 2. What the interpreter does per command (the middle box)

`Interpreter::Run` walks the command list; the ones that matter for the
pipeline:

- **Matrix commands** (`GfxSpMatrix`, `interpreter.cpp:2251`) — load/mul a
  matrix; the frame-interpolator substitutes an interpolated `Mtx` here via
  the `unordered_map<Mtx*, MtxF>` passed into `Run` (see
  `frame-interpolation.md`).
- **Vertex commands** (`GfxSpVertex`, `:2353`) — transform + light vertices
  into an internal buffer (lighting is done here in the vertex path —
  `lighting-illumination-reflection.md`).
- **Texture/tile commands** (`GfxDpSetTile`, `GfxDpLoadTlut`, …) — configure
  and upload textures (`textures-and-texture-mapping.md`).
- **Combine mode** (`GfxDpSetCombineMode`, `:3677`) — set the N64 color
  combiner, which selects/generates the shader
  (`color-combiner-and-surface-shading.md`, `shaders-and-gpu.md`).
- **Triangle commands** — accumulate vertices; when the batch flushes,
  `DrawTriangles` (`:146`) hands `(vbo, len, numTris)` to the backend.

## 3. The backend boundary (`GfxRenderingAPI`)

The interpreter never calls OpenGL or Vulkan directly. It calls a
`GfxRenderingAPI` interface (`mRapi`), implemented per platform in
`libultraship/src/fast/backends/gfx_opengl.cpp`, `gfx_vulkan.cpp`,
`gfx_d3d11.cpp`, `gfx_metal.*`. The chosen backend (OpenGL vs Vulkan on
Linux — see `SuperMario64/CLAUDE.md`) does the actual GPU work: compile the
generated shader, upload the vertex buffer, issue the draw. This clean
"translate once, target many GPUs" seam is the whole reason one N64 game
runs on four graphics APIs.

## How this relates to the course

- **`modelviewprojection` ch20-21 (the programmable pipeline, vertex →
  fragment)** teach the *modern* pipeline abstractly, with hand-written
  shaders. This doc shows a **real, running** pipeline whose front half is
  a 1996 N64 command stream and whose back half is that same modern GPU
  pipeline — with a **translator** in between that the course never needs.
  Seeing both ends bolted together makes the course's "stages" concrete.
- **Gap filled:** the course has no notion of a *command-list translator*,
  a *shader cache*, or a *multi-backend boundary* — all central to how a
  shipping cross-platform port renders. This is the spine the rest of the
  set's GPU-side docs hang from.

## Candidate doc-region spans (for the later Sphinx pass — not yet added)

- `src/port/Game.cpp` (`:26-27`): region `graphics_seam` — the one
  `exec_display_list` handoff.
- `src/port/Engine.cpp` around `ProcessGfxCommands`/`RunCommands`
  (`:1387`, `:1352`): region `replay_loop` — the N-times replay.
- `libultraship/src/fast/interpreter.cpp` around `DrawTriangles` (`:146`):
  region `draw_batch` — the interpreter→backend boundary.
