# Reference: Curves & splines — cubic B-splines for cutscene cameras (surfaces: absent)

> **Provenance:** authored 2026-09-06 against Ghostship pin `49c5312a`.
> Anchors in the decomp (`src/game/camera.c`). Part of the mario64 graphics
> set — map at [`README.md`](README.md). Companion: `camera-system.md`,
> `rotation-euler-vs-rotors.md` (`atan2s`).

## TL;DR

The only real curve math in SM64 is a **uniform cubic B-spline**, used to
fly the **cutscene and credits camera** along a smooth path.
`evaluate_cubic_spline(u, Q, a0..a3)` (`camera.c:3784`) blends four control
points with the cubic B-spline basis; `move_point_along_spline` (`:3839`)
walks a `CutsceneSplinePoint[]` array segment by segment at a per-point
speed. There are **no parametric surfaces, no Bezier/NURBS, no tessellation
anywhere** — all in-game geometry is explicit polygon meshes
(`scene-graph-and-data-structures.md`).

## 1. The evaluator is a cubic B-spline (`:3784`)

```c
void evaluate_cubic_spline(f32 u, Vec3f Q, Vec3f a0, Vec3f a1, Vec3f a2, Vec3f a3) {
    f32 B[4];
    if (u > 1.f) u = 1.f;
    B[0] = (1.f - u)*(1.f - u)*(1.f - u) / 6.f;
    B[1] =  u*u*u/2.f - u*u + 0.6666667f;
    B[2] = -u*u*u/2.f + u*u/2.f + u/2.f + 0.16666667f;
    B[3] =  u*u*u/6.f;
    Q[i] = B[0]*a0[i] + B[1]*a1[i] + B[2]*a2[i] + B[3]*a3[i];   // i = 0,1,2
}
```

Those four `B[k]` are the **uniform cubic B-spline basis functions** (they
sum to 1 and are non-negative). Key property: a B-spline is an
**approximating** curve — it does **not** pass through its control points
(unlike a Catmull-Rom or a Bezier's endpoints); it stays inside their convex
hull and is C²-continuous across segments. That smoothness is exactly why it
suits a camera path — no kinks at the joints.

The function also contains a second, **unused** basis (`:3806-3818`)
computing the curve's **derivative** (tangent) and turning it into
`unusedSplinePitch`/`unusedSplineYaw` via `atan2s` — dead code that would
have aimed the camera *along* its motion. Worth noting as dead (per the
verify-and-mark-absence rule): the tangent-facing feature exists in shape
but has no live effect.

## 2. Walking the path (`move_point_along_spline:3839`)

A cutscene path is a `CutsceneSplinePoint[]` (each a point + a speed;
`sCurCreditsSplinePos[32]`/`Focus[32]`, `:187-192`). `move_point_along_spline`
tracks `sCutsceneSplineSegment` and `sCutsceneSplineSegmentProgress`,
advancing `progress` each frame by the segment's speed and rolling over to
the next four-point window when it passes 1.0. The header comment derives the
frame-count recurrence (`p(n+1) = (s2 - s1 + 1)·p(n) + s1`) — a nice touch,
but the takeaway is: **position and focus each ride their own B-spline**, so
the camera glides and looks along smooth curves during cutscenes and the
credits.

## 3. What is NOT here

- **No surfaces.** No parametric/NURBS/Bezier *surface* code exists; curved
  *looking* geometry (hills, Mario) is low-poly mesh, not a math surface.
- **No general curve library.** The B-spline is special-purpose camera code
  in `camera.c`, not a reusable primitive. Gameplay motion uses linear
  `approach_*` easing, not splines.

## How this relates to the course

- **Neither course covers curves or splines**, so this is a pure gap-fill on
  the "how do you move something along a smooth path" question. The B-spline
  here is a compact, real example of parametric curve evaluation — basis
  functions blending control points — that a course could lift directly.
- **Contrast with the course's rotation-by-rotor / transform math:** those
  are exact algebraic transforms; a spline is *sampled interpolation* of
  positions over a parameter `u`. Different tool, different job — transforms
  place things, splines route them over time.
- **Surfaces stay a gap** even after this doc — SM64 has none to show, so
  parametric surfaces remain something the courses and this engine both
  lack (stated so nobody hunts for it — see `absent-topics.md` for the
  policy).

## Candidate doc-region spans (for the later Sphinx pass — not yet added)

- `src/game/camera.c` around `evaluate_cubic_spline` (`:3784-3803`): region
  `cubic_bspline_eval` — the basis functions + the blend (skip the dead
  derivative half).
- `src/game/camera.c` around `move_point_along_spline` (`:3839`): region
  `spline_walk` — advancing progress through segments.
