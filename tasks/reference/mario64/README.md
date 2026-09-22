# Mario 64 (Ghostship) graphics & math reference set — the map (L0)

> **Provenance:** Ghostship pin `49c5312a`, libultraship submodule
> `c151cc91` (1.3.1-544 fork). Built by the initiative
> `tasks/mario64-graphics-refdocs.md`.

This is the **top level-of-detail (L0)** for a teaching-oriented reference
set: it shows the Super Mario 64 PC port (Ghostship) as a worked source of
graphics and applied-math examples for the topics the maintainer's courses
(`modelviewprojection`, `geometricalgebra`) don't cover, or cover thinly —
**each topic compared to how he teaches it.**

## How to read this set — levels of detail

Each topic is a **column of docs at decreasing detail**. Start at the
capsule here; descend as far as you need:

- **L0 — capsule:** the paragraph in the table below. The whole topic in a
  breath.
- **L1 — orientation** (`<topic>-overview.md`, when present): ~1 page, no
  code, the mental model.
- **L2 — mechanism** (`<topic>.md`): the full `file:line`-anchored
  algorithm and data flow.
- **L3 — source:** the code itself; the later Sphinx pass adds
  `doc-region` markers so a book can `literalinclude` the exact spans.

Docs are written deepest-first (L2), then summarized upward (each level
~half the lines of the one below). The scheme is evolvable — see the
umbrella's deviations log for changes.

## Code-quality reference (not a topic capsule)

- `assembly-isms-in-the-decomp.md` — the 20 patterns the matching-era decomp left in the C
  (`goto`-as-`break`, `register`, stack-slot names, `== TRUE`, `& 0xFFFF` before an `s16`
  store, double literals, …), why each exists, the rewrite, and the semantic rule that decides
  whether the rewrite is behaviour-preserving; plus the assembly-diff proof gate and the
  upstream posture. Companion to `tasks/mario64-assembly-isms-to-standard-c.md`. The gate and
  the per-class rewrite tools now live in `tools/` — map: `tasks/reference/imps/standard-c-tooling.md`;
  the OoT twin's findings: `tasks/reference/ocarina/assembly-isms-in-soh.md`.

## Architecture docs (orientation — "where does X live")

These predate this set and map the code, not the concepts. Read the
relevant one alongside a topic doc: `architecture-overview.md`,
`decomp-map.md`, `port-layer.md`, `libultraship-integration.md`,
`asset-pipeline.md`, `frame-interpolation.md`, `build-system.md`.

## Topics — capsules and status

Status: ⬜ not started · 🟡 L2 drafted · ✅ L2+L0 (+L1) done. Capsules are
filled as each topic's L2 completes (the capsule is the halved summary of
its L2).

| Topic (L2 doc) | Course gap | Status | Capsule (L0) |
|---|---|---|---|
| `vectors-and-vector-math.md` | vs mvp Vector class | ✅ | A vector is a bare mutable C array (`Vec3f`=`f32[3]`), operated on in place with a dest-first convention. No named dot product or float subtract (both inlined for speed); `cross` and `normalize` exist, normalize unguarded against zero; every function ends with an unused `return &dest` kept only for ROM-matching. The coordinate-arithmetic pole opposite the course's immutable `Vector` class and gacalc's grade-1 multivectors. |
| `matrices-and-linear-algebra.md` (+ `-overview.md` L1) | fixed-point matrices | ✅ | Every matrix has two forms: a float `Mat4` for math and an N64 fixed-point `Mtx` for drawing, bridged by `mtxf_to_mtx`/`guMtxF2L`. Storage is transposed from OpenGL/gacalc — row-vector, translation in the last ROW — so `mtxf_mul` computes only the affine 3×4 part. Matrices live in fixed-size pools at stable addresses so the frame interpolator can key on their pointers. Projection is built separately in fixed-point, never in `Mat4`. |
| `transformations.md` | transform composition | ✅ | Transforms are built as local `Mat4`s (translate/scale/rotate-and-translate) and composed as `local · parent` on a matrix stack (`gMatStack[32]`) walked depth-first over the geo tree: each node pushes, makes a fixed-point twin, recurses, pops. Row-vector algebra fixes the child-then-parent order. It's the course's "lambda stack" of composed transforms made concrete over a whole scene. (L1 skipped — the mental model lives in the scene-graph doc.) |
| `rotation-euler-vs-rotors.md` (+ `-overview.md` L1) | Euler angles vs GA rotors | ✅ | **The showpiece.** SM64 stores orientation as three `s16` Euler binary angles (full turn = `0x10000`, wraps for free), takes sine/cosine from a lookup table, and bakes a fixed-axis-order (ZXY/XYZ) closed form into the rotation matrix; `atan2s` reads yaw/pitch off a vector. The course uses GA rotors (exp of a bivector, sandwich product, rotor multiply): no axis order, no gimbal lock, geodesic slerp. Same SO(3) rotation; Euler wins on size/speed/drift/extraction, the rotor on composition/gimbal/interpolation — each optimal for its constraints. |
| `camera-system.md` (+ `-overview.md` L1) | camera as a system | ✅ | The view matrix is one `mtxf_lookat` per frame; the interesting part is the controller that decides `pos`/`focus`: Lakitu (`gLakituState`), a stateful cameraman running one of ~a dozen modes, easing toward a goal, blending across mode transitions, and raycasting floors/ceilings so it never clips. The course teaches the view-transform math; this is the system on top of it (maintainer-flagged). |
| `field-of-view-and-projection.md` | FOV, ortho gap | ✅ | `guPerspective(fov,aspect,near,far)` for the 3D world and `guOrtho` for the HUD, both built in fixed-point with a `gSPPerspNormalize` scalar the N64 needs. FOV is a live signal (`sFOVState` = 45° default + offset + shake), not a constant. Ortho is the projection the book names but never implements; perspective is exactly where gacalc stops. |
| `curves-and-splines.md` | splines; surfaces absent | ✅ | One uniform cubic B-spline (`evaluate_cubic_spline`) flies the cutscene/credits camera along a smooth, approximating (not interpolating) C² path; `move_point_along_spline` walks it segment by segment. A dead tangent-facing branch exists. No parametric surfaces, Bezier/NURBS, or tessellation anywhere — all geometry is explicit mesh. |
| `graphics-pipeline.md` (+ `-overview.md` L1) | DL→Fast3D→GPU | ✅ | The decomp emits an N64 display list; `exec_display_list`→`ProcessGfxCommands` replays it N times with interpolated matrices; each pass runs the Fast3D `Interpreter`, which translates F3D commands, generates/looks up a shader per material, uploads textures/vertices, and calls `DrawTriangles` on a GPU backend (GL/Vulkan/DX11/Metal). A command-list translator with a shader cache and a multi-backend seam — the whole conveyor the course's ch20-21 pipeline sits at the end of. |
| `shaders-and-gpu.md` (+ `-overview.md` L1) | generated shaders | ✅ | Shaders are manufactured at runtime from the N64 color combiner, not written: `GenerateCC` decodes the material, `shader_item_to_str` maps each combiner input to a GLSL expression, and the backend compiles it — GLSL for OpenGL, GLSL→SPIR-V via shaderc for Vulkan — cached one program per material. Lighting arrives pre-baked as the per-vertex `vShade`; the generated shader mostly mixes. The course teaches writing shaders; here a code generator produces them. |
| `color-combiner-and-surface-shading.md` | combiner semantics | ✅ | The N64 shades each pixel with a two-cycle combiner computing `(A−B)·C+D` for RGB and alpha, where A/B/C/D are selected from a menu (texel0/1, prim, env, per-vertex shade, constants) via a `combine_mode` bitfield. `GenerateCC` decodes and constant-folds it. This is fixed-function shading — configure, not program — the ancestor of the course's free-form fragment shader; lighting enters pre-baked as `shade`, so the combiner just mixes. |
| `textures-and-texture-mapping.md` | textures/UV/TLUT | ✅ | `ImportTexture` decodes N64 formats (RGBA16 5551, RGBA32, IA, and palettized CI indexing a TLUT) and uploads to the GPU; a tile descriptor carries format/size and the `cms`/`cmt` wrap/clamp/mirror modes; results are cached like shaders. The whole texturing path the course explicitly excludes — texels, coordinates, palettes, edge addressing. |
| `sampling-and-mipmapping.md` | filtering/mips | ✅ | The GPU sampler decides nearest vs bilinear filtering, wrap/clamp/mirror from the tile, and (in the fork) trilinear blending across an auto-generated mip chain (`GetSampler(linear,cms,cmt,autoMipmap)`, `UploadMipChain`). This — not ray tracing — is what "RT64 mipmapping" means. Sampling is the texel-space twin of the course's vertex-attribute interpolation. |
| `alternate-and-hd-assets.md` | HD asset swap | ✅ | Why texture packs look great: a request for `name` is transparently redirected to `alt/name` when alt assets are enabled, with graceful fallback for partial packs and async off-thread HD decode. HD textures are clamped to the region the original occupied so they stay aligned. A naming-convention + runtime-lookup + async pattern; extends the asset pipeline. |
| `lighting-illumination-reflection.md` (+ `-overview.md` L1) | lighting (the #1 gap) | ✅ | Per-vertex diffuse (Gouraud): dot each vertex normal with directional lights → a shade color, interpolated across the triangle and handed to the combiner as `vShade`. No per-pixel Phong/specular. Lighting runs in the generated vertex shader; the combiner only mixes. Reflection is faked via env-mapping (normal→texcoord, the shiny paintings) and projected blob shadows. The course omits lighting entirely — this is the set's #1 gap-fill. |
| `transparency-and-blending.md` | alpha blending | ✅ | Transparency is a draw-order problem solved with render layers: the display list is bucketed (opaque → alpha-test → transparent) and emitted in layer order so transparent things draw last over the opaque scene. Per-pixel alpha comes from the combiner; a material picks its layer once. No per-pixel sort (the classic N64 seam). Alpha-test (cutoff) vs alpha-blend (needs order) are two mechanisms. Pairs with the depth buffer the course does teach. |
| `skyboxes.md` | skybox | ✅ | Not a cube — a flat 8-row grid of textured tiles drawn behind everything, scrolled horizontally by the camera's yaw (`scaledX ≈ (360/fov)·(yaw/65536)·width`, fov pinned 90°). Only yaw matters, so it reads as infinitely distant. A camera-locked 2D backdrop, cheaper than a cube map; a neat use of the binary-angle yaw as a coordinate. |
| `water-and-moving-textures.md` | water/movtex | ✅ | Water is scrolling, alpha-blended textured geometry — the general 'movtex' system shared with sand/haze/mist/treadmills. Each frame the texture coordinates scroll over static geometry (animate the UVs, not the vertices); per-vertex alpha makes it translucent. No refraction shader (verified) — the 'bent underwater' look is tint + scroll + the world showing through. Effects are cheaper than they look. |
| `painting-wobble.md` | vertex-deform + envmap | ✅ | The paintings ripple because the game moves their mesh vertices on the CPU each frame by a radial traveling wave (`rippleMag·cos(rippleRate·2π·(time−distance))`) and then recomputes the normals, so the env-mapped surface glints as it undulates. A small state machine decides when/where ripples start. Vertex animation + normal-recompute — both absent from the course; the contrast to water (UV-scroll) is the lesson. |
| `collision-detection.md` | surface collision | ✅ | The world's collision is a set of triangles (`struct Surface`) pre-sorted at load into a uniform grid of cells (spatial partition), split into wall/floor/ceiling lists since each test differs. A query hashes a position to its cell and walks only that cell's list: broad-phase (grid) + narrow-phase (per-triangle). Consumed by movement AND the camera. The broad/narrow split and spatial partition are the canonical physics data structures, absent from both courses. |
| `animation.md` (+ `-overview.md` L1) | skeletal animation | ✅ | Keyframed skeletal animation: an `Animation` is per-joint rotation values indexed by frame plus a root Y translation. Each tick `animFrame` advances (±1 or a fractional accel for playback speed); during the scene-graph walk each joint reads its angle and composes a rotation onto the stack. The 30 Hz keyframes are then matrix-lerped to the display rate — two distinct interpolations. The maintainer's flagged gap; built on transforms + scene graph. |
| `scene-graph-and-data-structures.md` (+ `-overview.md` L1) | scene graph | ✅ | The scene is a tree of typed nodes (camera/perspective/transform/geometry/…) built by a geo-layout bytecode interpreter (open/close-node commands nest it). Each frame the renderer walks it depth-first, dispatching on node type, and files drawable nodes into per-layer buckets emitted in draw order. Bytecode builds the tree once; traversal turns it into a bucketed display list. The structural backbone the transform/camera/projection/transparency docs all point back to. |
| `sound-processing.md` | audio DSP | ✅ | SM64 synthesizes audio in software then LUS plays it. A sequence player reads MIDI-like scores → active notes; the synthesizer resamples an instrument sample to pitch and applies an ADSR envelope; the mixer sums notes and adds reverb → a buffer, handed to a per-OS `AudioPlayer` (SDL/WASAPI/CoreAudio). A complete DSP pipeline. `final_resample` is the audio twin of texture sampling; the per-OS backend split mirrors the GPU backends. |
| `controls-and-input.md` | input path (new) | ✅ | The decomp still calls the N64 `osContGetReadData`; libultraship provides it, fed SDL → ControlDeck → osCont → `gControllers`. The game reads a `Controller` with `buttonDown` (held) vs `buttonPressed` (edge) plus an analog stick, and folds buttons into an abstract `m->input` flag set the action machine consumes. Device-independent input with an edge/level model and a hardware→flag→action indirection the course's direct keyboard read never needs. |
| `object-and-behavior-system.md` | object/entity system (new) | ✅ | Ordinary enemies (Goomba, Bob-omb, Koopa) aren't hardcoded like Mario: each is a behavior SCRIPT (bytecode in `data/behavior_data.c`, run by a VM) carrying its object list, flags, physics params, and animations as DATA, that `CALL_NATIVE`s a hand-written update loop leaning on a big shared `cur_obj_*` helper library. 533 scripts, 751 CALL_NATIVEs. Semi-data-driven: configured by data, bespoke-but-helper-heavy C for logic. The behavior VM is the third of SM64's three bytecode VMs. |
| `hardcoded-vs-data-driven.md` | engine architecture (new) | ✅ | A hybrid engine: levels are geo-layout bytecode and most objects run a behavior script, but Mario is welded into C — his own `gMarioState` struct, a `gMarioObject` global the update loop special-cases, a hand-written action state machine, and animations keyed to his skeleton. Bosses (Bowser) each have bespoke `behaviors/*.inc.c`. Models are fixed IDs, so you can reskin (asset swap) but not easily re-behave or re-rig. Answers 'why can't Mario/Bowser be swapped easily?' |
| `extracting-behaviors-to-scripts.md` | scripting feasibility (new) | ✅ | Can character logic move to Lua? The port has NO Lua — its scripting runtime is libtcc (runtime-compiled C linked against the game's `-export-dynamic` symbols; mods hook via the events system + `RegisterShipInitFunc`). So extracting a behavior to the port's own C-scripting is feasible incrementally (enemies first; the `CALL_NATIVE` pointer is baked so it needs runtime redirection), while Lua specifically means a new VM + bindings + per-tick marshalling on the hot path. Recommends a Goomba-in-a-C-mod PoC. Backs `tasks/mario64-actions-to-lua.md`. |
| `absent-topics.md` | what's NOT here | ✅ | Ray tracing and implicit modeling are absent; the fork's "RT64 mipmapping" is auto-mipmap + trilinear sampling, not a tracer. |
