# SM64 refdocs — Step 7b: doc-region patch pass (both lanes)

**Status:** carried into the Sphinx-book effort (`tasks/mario64-sphinx-book.md`) — the 39-region worklist below is the seed; doc-region markers get added per-chapter as `literalinclude` needs them, in the two-lane patch model. Setup (signing off both lanes, no cheat overlap, bare-pin checkout) was done 2026-09-06. Archived same day.
**Priority:** 5
**Difficulty:** 5
**Part of:** `mario64-graphics-refdocs.md` (umbrella)
**Depends on:** the content docs (steps 2-7) — their "Candidate doc-region
spans" sections are this pass's worklist.
**Next:** `mario64-graphics-refdocs-step-8-sibling-games.md`

## BLUF

Make the reference set drift-proof and Sphinx-ready: add
`// doc-region-begin <name>` / `// doc-region-end <name>` comment markers
into the source at every span the topic docs identified, **as patches** in
the imps two-lane model, then convert each doc to cite regions **by name**
(keeping `file:line` only as an "as of pin `49c5312a`" aid). Comments only,
so the build must be unaffected. Done when every candidate span has a
marker, the docs reference names, and a build still succeeds.

## Context

- **Why:** line numbers drift (`GfxSpMatrix` moved `:1065`→`:2251` between
  the old docs and this pin); named regions survive edits and are what
  Sphinx `literalinclude` pulls (`:start-after:`/`:end-before:`). The
  maintainer asked (2026-09-06) to pull this forward using patch permission.
- **Worklist:** every topic doc under `tasks/reference/mario64/` ends with a
  "Candidate doc-region spans" section naming the region + span. That is the
  exhaustive list — walk all docs, collect them.
- **Marker syntax:** C/C++ source → `// doc-region-begin <name>` /
  `// doc-region-end <name>` (the maintainer's book uses `# ...` in Python;
  `//` is the C equivalent). Name = the region slug in the doc.

## The two lanes (per `n64/CLAUDE.md`)

- **Game-tree lane** — markers in `Ghostship/src/**` (decomp + port). Commit
  in the Ghostship checkout (signing off — `git config commit.gpgsign
  false`), then `git format-patch` **appended** to the existing
  `n64/SuperMario64/patches/` series (new numbered patches after the cheat
  series; keep them a SEPARATE commit/patch from the cheats — a clean,
  upstream-plausible "add documentation region markers" change).
- **libultraship lane (NEW)** — markers in `Ghostship/libultraship/src/**`.
  The submodule is its own repo: `git config commit.gpgsign false` inside
  it, commit there, then `git format-patch --base=c151cc91` into a NEW
  `n64/SuperMario64/patches-libultraship/` directory (create it with a
  `.keep`). This is the first use of the LUS lane — record its apply step
  in `SuperMario64/CLAUDE.md`.

## Method

1. Collect all candidate spans from the docs (game-tree vs LUS).
2. Add markers, one lane at a time, each region a `begin`/`end` pair
   bracketing exactly the span the doc describes. Do NOT move code.
3. Build-verify (nested podman `make build` or the fedora build) — markers
   are comments, so a failure means a marker landed inside a token/macro;
   fix placement.
4. Regenerate each lane's patch series once, at the end.
5. Convert docs: replace the primary `file:line` citation with "region
   `<name>` (`<file>`)", keeping a parenthetical "as of pin `49c5312a`,
   ~`:NNN`" aid. Update the "Candidate doc-region spans" section to
   "doc-region spans (added)".

## Verification & done-state

Every candidate span has a marker; both patch series regenerate and
`git am`-apply cleanly onto their bases; a build succeeds with markers
present; docs cite names. Update `SuperMario64/CLAUDE.md` (the new LUS lane
+ its apply step) and the map. Archive on completion.

## Worklist — extracted 2026-09-06 (READY TO EXECUTE)

Setup already done: signing disabled in both `Ghostship` and its
`libultraship` submodule; verified the cheat patch series
(`n64/SuperMario64/patches/0001-0004`) touches **none** of these files, so a
doc-region commit on the bare pin is a clean, separate patch. The checkout is
at the bare pin `49c5312a`.

**39 regions — 23 game-tree, 16 libultraship.** Insert each as
`// doc-region-begin <name>` / `// doc-region-end <name>` bracketing the named
span. Prefer **content-anchored** placement (find the function signature; end
at its closing brace) over line numbers — the whole point is drift-proofing.
The `#define`/struct/comment spans (e.g. `sine_lookup`, `camera_modes`,
`movtex_model`, `synth_core`) need a line-range or end-pattern rule instead of
a brace.

### Game-tree lane (commit in `Ghostship/`, patch → `n64/SuperMario64/patches/0005-...`)
  - `src/audio/synthesis.c` (~`:54`) → region `synth_core` — from `sound-processing.md`
  - `src/engine/graph_node.c` (~`:745`) → region `bind_animation` — from `animation.md`
  - `src/engine/graph_node.c` (~`:766`) → region `animation_accel` — from `animation.md`
  - `src/engine/math_util.c` (~`:279`) → region `euler_zxy_to_matrix` — from `rotation-euler-vs-rotors.md`
  - `src/engine/math_util.c` (~`:639`) → region `angles_from_vector` — from `rotation-euler-vs-rotors.md`
  - `src/engine/math_util.h` (~`:20`) → region `sine_lookup` — from `rotation-euler-vs-rotors.md`
  - `src/engine/surface_collision.c` (~`:203`) → region `spatial_partition_lookup` — from `collision-detection.md`
  - `src/engine/surface_collision.c` (~`:307`) → region `narrow_phase_ceiling` — from `collision-detection.md`
  - `src/game/camera.c` (~`:3476`) → region `fov_system` — from `field-of-view-and-projection.md`
  - `src/game/camera.h` (~`:101`) → region `camera_modes` — from `camera-system.md`
  - `src/game/moving_texture.c` (~`:20`) → region `movtex_model` — from `water-and-moving-textures.md`
  - `src/game/moving_texture.c` (~`:103`) → region `movtex_vertex_alpha` — from `water-and-moving-textures.md`
  - `src/game/paintings.c` (~`:614`) → region `ripple_traveling_wave` — from `painting-wobble.md`
  - `src/game/paintings.c` (~`:712`) → region `recompute_normals` — from `painting-wobble.md`
  - `src/game/rendering_graph_node.c` (~`:33`) → region `scene_graph_traversal` — from `scene-graph-and-data-structures.md`
  - `src/game/rendering_graph_node.c` (~`:149`) → region `render_layer_buckets` — from `transparency-and-blending.md`
  - `src/game/rendering_graph_node.c` (~`:193`) → region `append_to_layer` — from `transparency-and-blending.md`
  - `src/game/rendering_graph_node.c` (~`:247`) → region `guOrtho_hud` — from `field-of-view-and-projection.md`
  - `src/game/rendering_graph_node.c` (~`:275`) → region `guPerspective_setup` — from `field-of-view-and-projection.md`
  - `src/game/rendering_graph_node.c` (~`:346`) → region `camera_view_matrix` — from `camera-system.md`
  - `src/game/rendering_graph_node.c` (~`:388`) → region `compose_local_onto_parent` — from `transformations.md`
  - `src/port/Engine.cpp` (~`:1387`) → region `replay_loop` — from `graphics-pipeline.md`
  - `src/port/Game.cpp` (~`:26`) → region `graphics_seam` — from `graphics-pipeline.md`

### libultraship lane (commit in `Ghostship/libultraship/`, patch → NEW `n64/SuperMario64/patches-libultraship/0001-...`)
  - `libultraship/src/fast/backends/gfx_opengl.cpp` (~`:170`) → region `combiner_input_to_glsl` — from `shaders-and-gpu.md`
  - `libultraship/src/fast/backends/gfx_vulkan.cpp` (~`:293`) → region `glsl_to_spirv` — from `shaders-and-gpu.md`
  - `libultraship/src/fast/backends/gfx_vulkan.cpp` (~`:532`) → region `sampler_selection` — from `sampling-and-mipmapping.md`
  - `libultraship/src/fast/interpreter.cpp` (~`:146`) → region `draw_batch` — from `graphics-pipeline.md`
  - `libultraship/src/fast/interpreter.cpp` (~`:370`) → region `combiner_decode` — from `color-combiner-and-surface-shading.md`
  - `libultraship/src/fast/interpreter.cpp` (~`:632`) → region `shader_cache` — from `shaders-and-gpu.md`
  - `libultraship/src/fast/interpreter.cpp` (~`:747`) → region `alt_asset_resolution` — from `alternate-and-hd-assets.md`
  - `libultraship/src/fast/interpreter.cpp` (~`:916`) → region `decode_rgba16` — from `textures-and-texture-mapping.md`
  - `libultraship/src/fast/interpreter.cpp` (~`:947`) → region `tile_wrap_modes` — from `textures-and-texture-mapping.md`
  - `libultraship/src/fast/interpreter.cpp` (~`:1950`) → region `build_mip_chain` — from `sampling-and-mipmapping.md`
  - `libultraship/src/fast/interpreter.cpp` (~`:1985`) → region `texture_format_dispatch` — from `textures-and-texture-mapping.md`
  - `libultraship/src/fast/interpreter.cpp` (~`:2243`) → region `light_dir_to_normal_space` — from `lighting-illumination-reflection.md`
  - `libultraship/src/fast/interpreter.cpp` (~`:2383`) → region `apply_vertex_lighting` — from `lighting-illumination-reflection.md`
  - `libultraship/src/fast/interpreter.cpp` (~`:3677`) → region `set_combine_mode` — from `color-combiner-and-surface-shading.md`
  - `libultraship/src/ship/audio/AudioPlayer.cpp` (~`:10`) → region `audio_device` — from `sound-processing.md`
  - `libultraship/src/ship/resource/ResourceManager.cpp` (~`:452`) → region `alt_assets_gate` — from `alternate-and-hd-assets.md`

### After insertion
1. Build-verify (markers are comments — a failure means one landed inside a
   token/macro; fix placement).
2. `git format-patch` each lane (game-tree: `--base=49c5312a`; LUS:
   `--base=c151cc91`).
3. Update each doc's "Candidate doc-region spans" → "doc-region spans (added)"
   and, where useful, cite regions by name in prose (keep `file:line` as an
   "as of pin" aid).
4. Record the new LUS lane + its apply step in `n64/SuperMario64/CLAUDE.md`.
