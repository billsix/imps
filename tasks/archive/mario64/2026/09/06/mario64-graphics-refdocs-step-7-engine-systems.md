# SM64 refdocs — Step 7: engine systems (collision, animation, scene graph, sound)

**Status:** done — 2026-09-06 (scene-graph & animation L2+L1+L0; collision & sound L2+L0). Archived same day.
**Priority:** 4
**Difficulty:** 6
**Part of:** `mario64-graphics-refdocs.md` (umbrella)
**Depends on:** `mario64-graphics-refdocs-step-1-foundation.md`
**Next:** `mario64-graphics-refdocs-step-8-sibling-games.md`

## BLUF

Four docs on the non-surface engine systems: collision detection,
animation, the scene-graph data structures, and sound. Collision and
animation are absent/thin in the courses (the maintainer said he "barely
covers" animation); the scene-graph doc gives the data-structure backbone
the other docs reference; sound is absent from both courses.

## Context

Read the umbrella and step 1's template. Bodies: decomp
`src/engine/`/`src/game/`/`src/audio/` with port importers and the LUS
audio player. Anchors at Ghostship `49c5312a` / LUS `c151cc91`.

## Docs & anchors (verify each before writing)

1. **`collision-detection.md`** — `src/engine/surface_collision.c`: walls
   `find_wall_collisions:185` / `find_wall_collisions_from_list:20` /
   `f32_find_wall_collision:160`, ceilings `find_ceil:307` /
   `find_ceil_from_list:227`, floors `find_floor` (same file); surface
   partition build `src/engine/surface_load.c`. *Teaching angle:*
   triangle-surface collision + spatial partition (cells) — the collision
   topic absent from the course. A canonical worked example.
2. **`animation.md`** — skeletal/geo animation in `src/engine/graph_node.c`
   (`geo_obj_init_animation:745`, `geo_obj_init_animation_accel:766`,
   `retrieve_animation_index:788`, part animation `:865-877`); Mario mesh/
   anim glue `src/game/mario_misc.c`; anim data format loaded by
   `src/port/importer/AnimationFactory.cpp`. *Teaching angle:* keyframed
   skeletal animation — indexed joint angles applied down the geo tree,
   advanced per tick and interpolated for render (tie to
   `frame-interpolation.md`). This is the animation depth the course
   lacks; give it room (maintainer flagged it).
3. **`scene-graph-and-data-structures.md`** — geo layout bytecode → graph
   node tree: `src/engine/geo_layout.c` (`GeoLayoutJumpTable:13`, node
   cmds `:22-28`), node structs/types `src/engine/graph_node.h:26-39`,
   tree build `graph_node.c`; traversal + DL emission
   `src/game/rendering_graph_node.c` (`geo_process_node_and_siblings:33`,
   master-list buckets `geo_process_master_list_sub:149`,
   `struct DisplayListNode:150`, `geo_append_display_list:193`); port geo
   parsing `src/port/game/GeoLayoutParser.cpp`. *Teaching angle:* a real
   scene graph + per-layer display-list buckets — the data structures
   the course (transform stacks only) doesn't cover. This doc underpins
   the transformations, camera, and appearance docs — write it as the
   structural reference they point back to.
4. **`sound-processing.md`** — decomp software synth `src/audio/synthesis.c`
   (`synthesis_execute:271`, `final_resample`, `process_envelope`, reverb
   `synthesis_resample_and_mix_reverb:368`), sequence playback
   `src/audio/seqplayer.c`, mixing `src/audio/mixer.c`; output/device
   layer LUS `libultraship/src/ship/audio/` (`AudioPlayer.cpp:10` `Init`,
   backends `SDLAudioPlayer.cpp`/`WasapiAudioPlayer.cpp`/
   `CoreAudioAudioPlayer.cpp`, surround `SoundMatrixDecoder.cpp`); port
   glue `src/port/ModAudio.cpp`. *Teaching angle:* software audio
   synthesis (envelopes, resampling, reverb, mixing) → a modern device
   backend — sound is absent from both courses; note it's a DSP topic,
   adjacent to but distinct from the graphics thread.

## Verification & done-state

Anchors resolve at the pin (LUS anchors against the pinned submodule);
each doc has the banner + course-comparison; the scene-graph doc is
written as the structural reference the visual docs cite. Note candidate
`doc-region` spans. Stage the four docs; archive this step on completion.
