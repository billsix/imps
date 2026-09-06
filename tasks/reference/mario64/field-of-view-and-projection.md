# Reference: Field of view & projection — perspective, ortho, and the FOV system

> **Provenance:** authored 2026-09-06 against Ghostship pin `49c5312a`.
> Anchors in the decomp (`src/game/rendering_graph_node.c`,
> `src/game/camera.c`). Part of the mario64 graphics set — map at
> [`README.md`](README.md). Companions: `matrices-and-linear-algebra.md`
> (matrices are fixed-point), `camera-system.md`.

## TL;DR

SM64 builds **both** projection kinds the geo tree needs:
`geo_process_perspective` calls `guPerspective(fov, aspect, near, far)` for
the 3D world (`rendering_graph_node.c:275`), and `geo_process_ortho_projection`
calls `guOrthoInterp(...)` for the 2D HUD/menus (`:247`). The **field of
view is a live, animated quantity**: `sFOVState.fov` (default 45°) plus a
`fovOffset` and a **shake** (amplitude/phase) that the game drives for
impact and cutscene effects. Both projection matrices are built directly in
N64 **fixed-point**, separate from the `Mat4` model/view math.

## 1. Perspective (`geo_process_perspective:259`)

```c
f32 aspect = (f32)gCurGraphNodeRoot->width / (f32)gCurGraphNodeRoot->height;  // EU: *1.1
guPerspective(mtx, &perspNorm, node->fov, aspect, node->near, node->far, 1.0f);
gSPPerspNormalize(gDisplayListHead++, perspNorm);
gSPMatrix(gDisplayListHead++, ..., G_MTX_PROJECTION | G_MTX_LOAD | G_MTX_NOPUSH);
```

- **`guPerspective`** is the N64's `gluPerspective` analogue: vertical
  `fov`, `aspect`, and `near`/`far` planes → a fixed-point projection
  matrix. It is the exact frustum construction the course derives, done in
  hardware format.
- **`gSPPerspNormalize(perspNorm)`** is N64-specific: the RSP needs a scalar
  to keep fixed-point W-values in range, output by `guPerspective`. It has
  no course analogue — a fixed-point artifact.
- The FOV comes from the camera's FOV system (§3), not a constant.
- After projection, an optional **mirror-mode** transform flips X (`:281`).

## 2. Orthographic (`geo_process_ortho_projection:238`) — the gap-filler

```c
guOrthoInterp(mtx, left, right, bottom, top, -2.0f, 2.0f, 1.0f);
```

The HUD, menus, and 2D overlays render under an **orthographic** projection
built by `guOrtho`/`guOrthoInterp` — a box, no perspective divide, so screen
pixels map 1:1 and depth doesn't shrink things. (`guOrthoInterp` is the
frame-interpolation-aware variant; see `frame-interpolation.md`.) This is
the projection the maintainer's book *names but never implements* — SM64 is
a live, working example of it, side by side with perspective in the same
frame (world in perspective, HUD in ortho).

## 3. FOV is a system, not a constant (`sFOVState`, `camera.c`)

`sFOVState` (`camera.c:177`) makes field of view dynamic:

```c
sFOVState.fov = 45.f;          // :3476 default; 37.f in some contexts (:7661)
sFOVState.fovOffset;           // additive adjustment
sFOVState.shakeAmplitude; sFOVState.shakePhase;   // FOV shake
```

`set_fov_shake(amplitude, decay, phase)` (`:515`, many call sites) wobbles
the FOV for landing thumps, damage, and cutscene punch; the per-frame FOV
handed to `guPerspective` is `fov + fovOffset + shake(phase)`. So **FOV is
animated** — a lens that breathes — which is why big impacts feel like the
world lurches. The course treats FOV as a fixed parameter of the frustum;
here it is a live signal.

## How this relates to the course

- **`modelviewprojection` ch18 (perspective, frustum, vertical FOV) +
  `perspective.rst`** derive the perspective matrix the course is built
  around; SM64's `guPerspective` is the same construction in fixed-point,
  with the extra `gSPPerspNormalize` scalar the N64 needs. Direct match,
  plus one console wrinkle.
- **Orthographic projection is the clean gap-fill:** the book (ch16:80)
  says implementing ortho "would require a lot of code changes" and never
  does it; SM64 ships it for every HUD element via `guOrtho`. This doc is
  the worked ortho example the course lacks.
- **FOV-as-a-system** is a second gap: the course's FOV is a constant; SM64
  animates it (offset + shake). A small but vivid "the parameter you
  thought was fixed is actually a signal" lesson.
- **`geometricalgebra`/gacalc explicitly refuses perspective** (its
  `to_matrix` raises on the non-linear projective step). So this doc is
  precisely the stage *past* where gacalc stops — the perspective divide it
  cannot express, done concretely.

## Candidate doc-region spans (for the later Sphinx pass — not yet added)

- `src/game/rendering_graph_node.c` around `geo_process_perspective`
  (`:275-278`): region `guPerspective_setup` — frustum + perspective
  normalize.
- `src/game/rendering_graph_node.c` around `geo_process_ortho_projection`
  (`:247`): region `guOrtho_hud` — the orthographic HUD projection (the
  book's missing example).
- `src/game/camera.c` around `sFOVState` init + `set_fov_shake` (`:3476`,
  `:515`): region `fov_system` — FOV as offset + shake.
