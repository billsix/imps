# Reference: Animation — keyframed skeletal joints, advanced per tick

> **Provenance:** authored 2026-09-06 against Ghostship pin `49c5312a`.
> Anchors in `src/engine/graph_node.c`, `src/game/mario_misc.c`,
> `src/port/importer/AnimationFactory.cpp`. Part of the mario64 graphics set
> — map at [`README.md`](README.md). L1:
> [`animation-overview.md`](animation-overview.md). Companions:
> `scene-graph-and-data-structures.md`, `transformations.md`,
> `frame-interpolation.md`.
>
> **The maintainer flagged animation as barely covered by his course** — a
> priority gap-fill.

## TL;DR

SM64 animates characters with **keyframed skeletal animation**: an
`Animation` is a table of **per-joint rotation values indexed by frame**,
plus a root Y translation. Each game tick the object's `animFrame` advances
(`geo_obj_init_animation:745`), and as the scene graph is walked, each
**animated-part node** reads its joint's angle for the current frame and
builds that joint's transform (`transformations.md`). So a walk cycle is a
few hundred bytes of joint angles over time, applied down the skeleton's tree
every frame — then smoothed to the display rate by the matrix interpolator
(`frame-interpolation.md`).

## 1. The `Animation` data (`graph_node.c:745`)

`geo_obj_init_animation` binds an object to an `Animation`:

```c
struct Animation *anim = segmented_to_virtual(*animSegmented);   // :753
graphNode->animInfo.animFrame = anim->startFrame + ((anim->flags & ANIM_FLAG_FORWARD) ? 1 : -1);
graphNode->animInfo.animYTrans = 0;
```

An `Animation` carries: `startFrame`, a loop/one-shot flag set (`ANIM_FLAG_*`,
e.g. `FORWARD`), a length, the number of joints, and the **indexed value
tables** — a compact scheme where each joint's angle for a given frame is
looked up (`retrieve_animation_index`), sharing storage between joints that
don't change. `animYTrans` is the **root motion** in Y (how the whole
skeleton rises/falls); horizontal root motion is applied by gameplay, not the
anim. `geo_obj_init_animation_accel` (`:766`) is the same but advances the
frame by a fractional **acceleration** so animations can play faster/slower
than one frame per tick.

## 2. Advancing and applying

Each tick `animFrame` steps by ±1 (or by the accel amount), wrapping at the
animation's length for loops. During the scene-graph walk
(`scene-graph-and-data-structures.md`), an **animated-part node** for each
joint calls `retrieve_animation_index` to get that joint's rotation for the
current `animFrame`, builds a `mtxf_rotate_*` transform from it
(`transformations.md`), and composes it onto the matrix stack — so the pose
falls out of the same depth-first traversal that draws everything else. The
skeleton *is* a subtree of the scene graph.

## 3. Interpolated to the display rate

The animation runs at the **30 Hz game tick**, but the game may render at 60+
FPS. It does **not** advance the animation faster; instead the per-joint
matrices are captured and **element-wise lerped** between last tick and this
tick by the frame interpolator (`frame-interpolation.md`) — so animation
looks smooth at high FPS without changing the keyframe rate. This is the same
mechanism that smooths all motion; animation is one of its consumers.

## How this relates to the course

- **The maintainer's course barely covers animation** — only keyboard-nudged
  motion and a frame cap, no keyframes or interpolation. This is the priority
  gap-fill: **keyframed skeletal animation** is the canonical game-animation
  technique, and SM64 is a compact, complete example — joint tables, frame
  advance, root motion, looping, and playback speed.
- **Two distinct interpolations, worth separating:** the *animation* itself
  is keyframes sampled per tick (§2); the *smoothness at high FPS* is the
  matrix lerp (§3). A student conflating "animation" with "interpolation"
  learns here they are different layers.
- **Builds on transforms + scene graph:** a joint angle becomes a
  `mtxf_rotate_*` (`rotation-euler-vs-rotors.md`) composed on the stack
  (`transformations.md`) inside the tree walk
  (`scene-graph-and-data-structures.md`) — animation is those three docs in
  motion.

## Candidate doc-region spans (for the later Sphinx pass — not yet added)

- `src/engine/graph_node.c` around `geo_obj_init_animation` (`:745-759`):
  region `bind_animation` — startFrame, flags, root Y trans.
- `src/engine/graph_node.c` around `geo_obj_init_animation_accel` (`:766`):
  region `animation_accel` — fractional frame advance (playback speed).
