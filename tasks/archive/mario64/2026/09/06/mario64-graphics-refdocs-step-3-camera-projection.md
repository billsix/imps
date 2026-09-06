# SM64 refdocs — Step 3: camera, projection & curves

**Status:** done — 2026-09-06 (camera L2+L1+L0, FOV L2+L0, curves L2+L0). Archived same day.
**Priority:** 4
**Difficulty:** 5
**Part of:** `mario64-graphics-refdocs.md` (umbrella)
**Depends on:** `mario64-graphics-refdocs-step-1-foundation.md`
**Next:** `mario64-graphics-refdocs-step-4-pipeline-shaders.md`

## BLUF

Three docs on camera, projection, and curves — the cluster the maintainer
flagged as directly relevant to his book. The courses teach the view- and
projection-transform MATH but have no camera controller and never
implement orthographic projection; SM64's Lakitu camera and its
perspective/ortho set-up fill both gaps.

## Context

Read the umbrella and step 1's template. Bodies: decomp `src/game/`
(camera + projection nodes), with geo-side hooks. Anchors at `49c5312a`.

## Docs & anchors (verify each before writing)

1. **`camera-system.md`** — `src/game/camera.c` (header comment `:37`,
   `gCamera:180`; camera modes, C-button control, triggers, cutscene
   machinery throughout); geo camera node
   `src/game/rendering_graph_node.c:346` `geo_process_camera`; modes in
   `src/game/camera_settings.h`/`camera.h`. *Teaching angle:* a camera as
   a stateful SYSTEM — modes, smoothing, collision-aware follow — vs. the
   course's pure view-transform math (ch10 camera space, ch17 3D camera).
   The maintainer wants this one to speak to his book directly.
2. **`field-of-view-and-projection.md`** — FOV state `camera.c:177`
   `sFOVState` + `set_fov_shake` presets (`:515+`); projection set-up in
   `rendering_graph_node.c`: `geo_process_perspective:259` →
   `guPerspective:275`, `geo_process_ortho_projection:238` →
   `guOrthoInterp:247` (interpolation-aware variants); node types
   `GRAPH_NODE_TYPE_PERSPECTIVE/ORTHO_PROJECTION` in `graph_node.h:33-34`.
   *Teaching angle:* perspective AND orthographic in one engine — the
   course covers perspective (ch18, `perspective.rst`) but only NAMES
   ortho (ch16:80, never implemented). SM64's HUD/ortho path is the
   worked ortho example the book lacks. Note the FOV-shake as an applied
   use of FOV.
3. **`curves-and-splines.md`** — cutscene/credits camera SPLINES only:
   `camera.c:160-163` `sCurCreditsSplinePos/Focus[32]`,
   `sCutsceneSplineSegment/Progress`, `HandheldShakeSpline[4]:118`,
   evaluated by the `move_point_on_spline`-style code in `camera.c`.
   *Teaching angle:* piecewise spline evaluation for camera paths — a
   curves topic absent from both courses. **State plainly that general
   Bezier/NURBS SURFACES are absent** (no parametric-surface code); this
   is the "curves yes, surfaces no" honest scope.

## Verification & done-state

Anchors resolve; each doc carries the banner + course-comparison; the
ortho doc explicitly ties to the book's un-implemented ortho; the curves
doc states the surfaces-absent boundary. Note candidate `doc-region`
spans. Stage the three docs; archive this step on completion.
