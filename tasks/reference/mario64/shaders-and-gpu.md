# Reference: Shaders & the GPU — generated, not written; GL and Vulkan

> **Provenance:** authored 2026-09-06 against LUS submodule `c151cc91`
> (1.3.1-544 fork). Anchors in `libultraship/src/fast/`. Part of the mario64
> graphics set — map at [`README.md`](README.md). L1:
> [`shaders-and-gpu-overview.md`](shaders-and-gpu-overview.md). Reads
> `color-combiner-and-surface-shading.md` (the source of the shader) and
> `graphics-pipeline.md` (where this sits).

## TL;DR

SM64's shaders are **manufactured at runtime from the N64 color combiner**,
not hand-written. When the interpreter meets a material it doesn't have a
shader for, `LookupOrCreateColorCombiner` (`interpreter.cpp:632`) calls
`GenerateCC` (`:361`) to decode the combiner, and the active GPU **backend**
turns that into shader source: the OpenGL backend emits **GLSL** directly
(`shader_item_to_str`, `gfx_opengl.cpp:170`), and the Vulkan backend emits
GLSL and compiles it to **SPIR-V via shaderc** (`gfx_vulkan.cpp:293-298`).
Programs are **cached** by combiner key, so each distinct material compiles
its shader once. This is "how graphics hardware is used by OpenGL/Vulkan"
for this game: generated programs, one per material, driving a modern GPU.

## 1. Each combiner input becomes a GLSL expression (`shader_item_to_str`)

The generated fragment shader implements the combiner's `(A − B)·C + D` by
substituting each slot with a GLSL expression. The GL backend's mapping
(`gfx_opengl.cpp:170`):

```c
case SHADER_0:        return "vec3(0.0, 0.0, 0.0)";      // constant 0
case SHADER_1:        return "vec3(1.0, 1.0, 1.0)";      // constant 1
case SHADER_INPUT_1:  return "uInputs[0].rgb";           // primitive/env/... uniforms
...
case SHADER_INPUT_7:  return "vShade.rgb";               // per-vertex shade = lighting
case SHADER_TEXEL0:   return "texVal0.rgb";              // sampled texture 0
case SHADER_TEXEL0A:  return "texVal0.a";                // its alpha
```

So texture samples become `texVal0`, the lit vertex color becomes `vShade`,
material constants become `uInputs[]` uniforms, and the combiner formula is
assembled from these into one `(A-B)*C+D` GLSL line per cycle. The N64's
"select an input" becomes "reference this GLSL variable."

## 2. Generate → compile → cache

- **Generate** — `GenerateCC` (`:361`) decodes the `combine_mode` into the
  set of inputs and a shader id (see the combiner doc). The backend's
  shader-source builder walks those inputs via `shader_item_to_str`.
- **Compile** — per backend:
  - **OpenGL** (`gfx_opengl.cpp`): build a GLSL vertex+fragment program from
    a template (`fast/shaders/opengl/default.shader.glsl`) plus the
    generated combiner body, then `glCompileShader`/link.
  - **Vulkan** (`gfx_vulkan.cpp:293`): the fork uses a **"prism" template →
    Vulkan GLSL → SPIR-V** path (`gfx_vulkan.cpp:51`), compiling with
    `shaderc::Compiler::CompileGlslToSpv` (`:298`) at
    `shaderc_optimization_level_performance`. This is why the build needs
    `libshaderc-devel` (see `SuperMario64/CLAUDE.md`).
- **Cache** — `LookupOrCreateColorCombiner` (`:632`) keys programs by the
  combiner key, so a material's shader is generated and compiled **once**
  and reused every draw. `CreateAndLoadNewShader` (`gfx_vulkan.cpp:1171`)
  is the "miss" path.

## 3. The vertex side and the uniforms

Lighting and texgen are done in the **vertex** stage (see
`lighting-illumination-reflection.md`): the interpreter computes each
vertex's `shade` color and passes it as `vShade`, which the fragment shader
reads as combiner input 7. Per-draw constants (primitive/env colors, LOD
fraction) are latched as the `uInputs[]` uniforms in `LatchCombinerUniforms`
(`:197`). So a draw = a cached program + its vertex buffer (with shade) +
its latched uniforms + its bound textures.

## How this relates to the course

- **`modelviewprojection` ch20-21** teach you to *write* a vertex and a
  fragment shader and hand them to the GPU. This engine instead **writes
  them for you**, mechanically, from a compact material description — the
  same endpoint (a compiled GPU program) reached by code generation rather
  than authoring. It is a vivid answer to "where do shaders come from?"
  other than "a person typed them."
- **Two backends, one source of truth:** the course targets one API; here
  the *same* combiner drives GLSL for OpenGL and GLSL→SPIR-V for Vulkan,
  showing the backend-abstraction the course never needs. "How the GPU is
  used" differs per API below a shared front end.
- **Gap filled:** runtime shader generation, a shader cache keyed by
  material, and the GLSL-vs-SPIR-V compile paths are all absent from the
  course. This is the concrete machinery behind the abstract "programmable
  pipeline" ch20-21 name.

## Candidate doc-region spans (for the later Sphinx pass — not yet added)

- `libultraship/src/fast/backends/gfx_opengl.cpp` around `shader_item_to_str`
  (`:170-210`): region `combiner_input_to_glsl` — the input→GLSL mapping.
- `libultraship/src/fast/backends/gfx_vulkan.cpp` around the shaderc compile
  (`:293-300`): region `glsl_to_spirv` — GLSL→SPIR-V via shaderc.
- `libultraship/src/fast/interpreter.cpp` around
  `LookupOrCreateColorCombiner` (`:632-642`): region `shader_cache` — the
  generate-once-per-material cache.
