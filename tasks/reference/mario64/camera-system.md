# Reference: The camera as a SYSTEM — Lakitu, modes, smoothing, collision

> **Provenance:** authored 2026-09-06 against Ghostship pin `49c5312a`.
> Anchors in the decomp (`src/game/camera.c`, `camera.h`,
> `src/game/rendering_graph_node.c`). Part of the mario64 graphics set —
> map at [`README.md`](README.md). L1:
> [`camera-system-overview.md`](camera-system-overview.md). Companion:
> `field-of-view-and-projection.md`, `matrices-and-linear-algebra.md`.
>
> **The maintainer flagged this as directly relevant to his book** — the
> course teaches the view-transform *math*; SM64 shows the *controller*
> that decides what that transform should be.

## TL;DR

The view matrix is the easy part — one `mtxf_lookat(pos, focus, roll)`
per frame (`rendering_graph_node.c:360`). The hard, interesting part is the
**controller that decides `pos` and `focus`**: a stateful subsystem
personified as **Lakitu** (`gLakituState`) that runs one of ~a dozen
**camera modes** (radial, behind-Mario, close, C-up, water-surface,
cannon, boss, fixed, 8-directions, free-roam…), **smooths** toward its goal
position each frame, is **collision-aware** (it raycasts against floors and
ceilings so it never clips through geometry), and **transitions** between
modes over a frame count. None of that is in a graphics course; the course
stops at "here is the look-at matrix."

## 1. The output: one look-at, on the matrix stack (`:346`)

`geo_process_camera` is small because all the work already happened in the
gameplay update. It reads the camera node's `pos`, `focus`, `roll`, builds
the view transform, and composes it onto the matrix stack like any other
node (see `transformations.md`):

```c
mtxf_rotate_xy(rollMtx, node->rollScreen);            // screen roll -> projection mul
mtxf_lookat(cameraTransform, node->pos, node->focus, node->roll);  // the VIEW matrix
mtxf_mul(gMatStack[i+1], cameraTransform, gMatStack[i]);           // push as parent of the scene
```

`mtxf_lookat` (`math_util.c:196`) is exactly the "camera space = inverse of
placing the camera" transform the course teaches. Everything below is about
where `node->pos`/`node->focus` came from.

## 2. Lakitu — the camera is a character with state (`gLakituState`)

`gLakituState` (`camera.c:176`) is the actual on-screen cameraman. It holds
**goal vs. current** position and focus, per-axis approach speeds
(`posHSpeed`, `focHSpeed`, set per mode at `:498-558`), and smoothing state.
Each frame the gameplay camera code computes a *goal* pos/focus for the
current mode, and Lakitu **eases** its real pos/focus toward that goal
rather than snapping — that easing is what gives SM64 its characteristic
lazy, weighty camera. The `struct Camera *gCamera` (`:180`) is the logical
camera; Lakitu is its smoothed physical realization.

## 3. Modes — a dozen controllers behind one interface (`camera.h:101-115`)

```c
#define CAMERA_MODE_RADIAL            0x01   // default outdoor orbit
#define CAMERA_MODE_BEHIND_MARIO      0x03
#define CAMERA_MODE_CLOSE             0x04   // Inside Castle / Big Boo's
#define CAMERA_MODE_C_UP              0x06   // first-person look
#define CAMERA_MODE_WATER_SURFACE     0x08
#define CAMERA_MODE_INSIDE_CANNON     0x0A
#define CAMERA_MODE_BOSS_FIGHT        0x0B
#define CAMERA_MODE_PARALLEL_TRACKING 0x0C
#define CAMERA_MODE_FIXED             0x0D
#define CAMERA_MODE_8_DIRECTIONS      0x0E   // Bowser / Rainbow Ride
#define CAMERA_MODE_FREE_ROAM         0x10
#define CAMERA_MODE_SPIRAL_STAIRS     0x11
```

Each mode is a function computing a goal pos/focus from Mario's state and
the level. `set_camera_mode(c, mode, frames)` (`:2995`) switches modes and
arms `sModeTransition` (`:178`) with `frames` — so the camera **blends**
from the old mode's result to the new one's over that many frames
(`sModeTransitions[]` table, `:466`), never cutting hard. This is a small
state machine with interpolated edges.

## 4. Collision-aware — the camera raycasts (`find_ceil`/`find_floor`)

The camera calls the same surface-collision routines the player does
(`find_ceil` at `:757`, `:2231`; floor checks throughout) to keep itself
out of walls and below ceilings — e.g. it pulls in when a ceiling would
otherwise clip it. So the camera controller **depends on the collision
system** (`collision-detection.md`); the view transform is downstream of a
physics query. This coupling — camera ↔ collision — is exactly the kind of
system interaction a from-scratch course camera never has.

## How this relates to the course

- **`modelviewprojection` ch10 (camera space = view transform) and ch17
  (moving the camera in 3D)** teach the *math*: the view matrix is the
  inverse of the camera's placement, and you move the camera by changing
  that placement. SM64 agrees completely at the matrix level
  (`mtxf_lookat`, §1) — and then shows the **entire system the course
  omits**: what *decides* the placement. The course's camera is moved by
  the keyboard; SM64's is moved by a mode-driven, smoothed, collision-aware
  controller.
- **`geometricalgebra`/gacalc** has no camera concept at all (it stops at
  the model matrix). So this is a pure gap-fill on the applied side.
- **Gap filled (the one the maintainer wants):** "camera management" as a
  *subsystem* — modes, easing, transitions, and collision avoidance —
  rather than as a single matrix. A reader who knows the view-transform
  math can see here what a shipping game builds on top of it.

## Candidate doc-region spans (for the later Sphinx pass — not yet added)

- `src/game/rendering_graph_node.c` around `geo_process_camera` (`:346-372`):
  region `camera_view_matrix` — the look-at pushed onto the stack.
- `src/game/camera.h` (`:101-115`): region `camera_modes` — the mode list
  as the "one interface, many controllers" catalog.
- `src/game/camera.c` around `set_camera_mode` (`:2995`): region
  `camera_mode_transition` — mode switch with a frame-count blend.
