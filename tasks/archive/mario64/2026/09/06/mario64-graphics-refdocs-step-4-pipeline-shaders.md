# SM64 refdocs — Step 4: pipeline, shaders & surface shading

**Status:** done — 2026-09-06 (pipeline L2+L1+L0, shaders L2+L1+L0, combiner L2+L0). Archived same day.
**Priority:** 4
**Difficulty:** 6
**Part of:** `mario64-graphics-refdocs.md` (umbrella)
**Depends on:** `mario64-graphics-refdocs-step-1-foundation.md` (needs the re-anchored LUS docs)
**Next:** `mario64-graphics-refdocs-step-5-textures-assets.md`

## BLUF

Three docs on how N64 rendering reaches modern GPU hardware: the full
pipeline (display list → Fast3D → backend), the color-combiner →
generated-shader path, and combiner/surface-shading semantics. This is
the "what actually happens on the GPU" layer the courses gesture at
(ch20-21 shaders) but never show for a real title. Heavy libultraship
work — study the pinned fork submodule.

## Context

Read the umbrella and the RE-ANCHORED `libultraship-integration.md` +
`frame-interpolation.md` from step 1 (they carry the pipeline spine — do
not re-derive it, extend it). Bodies: port `src/port/` + LUS
`Ghostship/libultraship/src/fast/`. Anchors at Ghostship `49c5312a` / LUS
`c151cc91`.

## Docs & anchors (verify each before writing)

1. **`graphics-pipeline.md`** — the end-to-end seam:
   `src/port/Game.cpp:26` `exec_display_list` →
   `GameEngine::ProcessGfxCommands` (`src/port/Engine.cpp:1387`) →
   `RunCommands:1352` → `Fast::Interpreter::Run`
   (`libultraship/src/fast/interpreter.cpp:6644`) → `DrawTriangles:146` →
   GPU backend. DL build in `src/game/rendering_graph_node.c`.
   *Approach:* this doc is the map that stitches the existing
   `frame-interpolation.md` (the replay/interp side) and the shader/
   texture docs together — a single "one triangle's journey" narrative.
   *Course link:* ch20-21 pipeline stages, but concrete and N64-flavored.
2. **`shaders-and-gpu.md`** — the color-combiner → shader generation:
   `interpreter.cpp:361` `GenerateCC`, `LookupOrCreateColorCombiner:632`;
   GL backend generates GLSL from the CC in
   `libultraship/src/fast/backends/gfx_opengl.cpp` (`shader_item_to_str:170`,
   template `:418`); Vulkan backend generates GLSL→SPIR-V via shaderc in
   `gfx_vulkan.cpp:51-301` (`shaderc::Compiler:293`); templates in
   `libultraship/src/fast/shaders/{opengl,vulkan,metal,directx}/default.shader.glsl`.
   *Teaching angle:* shaders are GENERATED per material from the N64
   combiner state, not hand-written — a striking contrast with the
   course's hand-authored vert/frag shaders (ch20-21). This is "how
   graphics hardware is used by OpenGL/Vulkan" the maintainer asked about.
3. **`color-combiner-and-surface-shading.md`** — CC mux decoding &
   per-cycle input selection: `interpreter.cpp:197` `LatchCombinerUniforms`,
   `GenerateCC:361` (mux enum strings `:336-355`), combine-mode set
   `GfxDpSetCombineMode:3677`. *Teaching angle:* the N64 color combiner as
   a tiny fixed-function shading language, and how "surface shading" is
   expressed as combiner cycles before the backend turns it into a shader.
   Feeds `lighting-illumination-reflection.md` (step 6).

## Verification & done-state

Anchors resolve at the pin (LUS anchors against the pinned submodule);
each doc has the banner + course-comparison; the pipeline doc links (not
duplicates) the frame-interp and integration docs. Note candidate
`doc-region` spans (the shader templates are prime `literalinclude`
targets). Stage the three docs; archive this step on completion.
