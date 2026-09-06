# Reference: Rotation — SM64 Euler binary angles vs. the course's GA rotors

> **Provenance:** authored 2026-09-06 against Ghostship pin `49c5312a`.
> Anchors in the decomp (`src/engine/math_util.c` + `.h`,
> `include/trig_tables.inc.c`). Part of the mario64 graphics set — map at
> [`README.md`](README.md). L1: [`rotation-euler-vs-rotors-overview.md`](rotation-euler-vs-rotors-overview.md).
> Companions: `matrices-and-linear-algebra.md`, `transformations.md`,
> `frame-interpolation.md` (angle interpolation).
>
> **This doc is the set's showpiece comparison** — the maintainer teaches
> rotation via geometric-algebra rotors, and explicitly wants SM64's very
> different approach set beside it.

## TL;DR

SM64 represents orientation as **three signed 16-bit Euler angles**
(`Vec3s`), in **binary-angle units** where a full turn is `0x10000` so the
`s16` wraps around the circle for free. Sine and cosine are **table
lookups** (`sins`/`coss`), and a rotation is turned into a matrix by a
**hardcoded closed-form product of three axis rotations in a fixed order**
(ZXY or XYZ). The maintainer's course instead builds a rotation as a
**geometric-algebra rotor** — the exponential of a bivector — applied by a
sandwich product and composed by multiplication, with no axis order and no
gimbal lock. Both reach the same rotation in SO(3); the storage, the
composition, the failure modes, and the interpolation all differ.

## 1. Orientation is three `s16` binary angles

An object's orientation is a `Vec3s rotate` — three integers, one per axis
(`mtxf_rotate_zxy_and_translate(dest, translate, Vec3s rotate)`,
`math_util.c:279`). The unit is the **binary angle** ("bam"): the full
`360°` circle is `0x10000` (65536), so:

- **Wraparound is free.** An `s16`/`u16` overflows at `0x10000`, i.e. once
  per revolution, so adding angles never needs an explicit modulo — the
  integer type *is* the circle. `0x4000` = 90°, `0x8000` = 180°.
- The conversion to radians is `angle * M_PI / 0x8000` (seen in `atan2f`,
  `math_util.c:756`), confirming `0x8000` = π.

## 2. Sine and cosine are table lookups (`math_util.h:20-24`)

```c
extern f32 gSineTable[];                       // include/trig_tables.inc.c:1
#define gCosineTable (gSineTable + 0x400)      // cosine = sine shifted 90°
#define sins(x) gSineTable[(u16)(x) >> 4]
#define coss(x) gCosineTable[(u16)(x) >> 4]
```

- `(u16)(x) >> 4` casts the angle unsigned (so it wraps) and drops 4 bits:
  `0x10000 / 16 = 0x1000 = 4096` table entries per revolution.
- **Cosine is the same table read 0x400 entries later** (`0x400 = 1024 =`
  a quarter of 4096 = 90°), because `cos θ = sin(θ + 90°)`.
- The header (`math_util.h:9-12`) notes the two tables **overlap in
  memory** deliberately — `gSineTable` is cut short so cosine reads overflow
  into shared storage; a byte-match quirk, not something to "fix."

So a sine costs an integer shift and one array read — no `sinf` call. This
is the classic speed/precision trade: 4096 samples of resolution, zero
transcendental math per frame.

## 3. Euler angles → matrix: a fixed-order closed form (`:279`)

`mtxf_rotate_zxy_and_translate` bakes the product of three axis rotations
into explicit matrix entries:

```c
f32 sx=sins(rotate[0]), cx=coss(rotate[0]);   // X angle
f32 sy=sins(rotate[1]), cy=coss(rotate[1]);   // Y angle
f32 sz=sins(rotate[2]), cz=coss(rotate[2]);   // Z angle
dest[0][0] = cy*cz + sx*sy*sz;
dest[1][0] = -cy*sz + sx*sy*cz;
dest[2][0] = cx*sy;
// ... dest[2][1] = -sx;  dest[2][2] = cx*cy;  etc.
```

Those nine entries are `R = Rz · Rx · Ry` multiplied out by hand — the
**ZXY** application order. A sibling, `mtxf_rotate_xyz_and_translate`
(`:313`), bakes the **XYZ** order. Two consequences:

- **The axis order is fixed in the function name and cannot be varied at
  runtime.** Different call sites pick ZXY vs XYZ deliberately (object
  transforms use ZXY).
- **Gimbal lock is possible.** When the middle axis reaches ±90° the outer
  two axes align and one rotational degree of freedom is lost — an inherent
  property of any three-Euler-angle scheme. SM64 avoids it by design (most
  objects never tumble freely), not by the math being immune.

## 4. The inverse — extracting angles with `atan2s` (`:713`)

Going from a direction *to* angles is where Euler shines. `atan2s(y, x)`
returns an `s16` binary angle via an arctangent table lookup, and
`vec3f_find_yaw`/pitch (`:639-640`) read a facing straight off a vector:

```c
*pitch = atan2s(sqrtf(x*x + z*z), y);
*yaw   = atan2s(z, x);
```

Aiming, camera-follow, and "turn toward" logic all use this — trivial in
Euler angles, awkward with rotors (you would extract the rotation plane and
angle). This ease is a real reason a game engine likes Euler.

## 5. Interpolation — angle lerp, with a wrap fix (`frame-interpolation.md`)

The smooth-framerate system does **not** interpolate angles directly for
the workhorse path (it interpolates final matrices — see
`frame-interpolation.md` §1). But where angles *are* interpolated, the
binary-angle representation needs care: lerping `0xF000`→`0x1000` naively
sweeps the long way around. The interpolator works in `u16` and picks the
`±0x10000` wrap that **minimizes** the difference
(`FrameInterpolation.cpp` binary-angle path, ~`:367-392`), i.e. "take the
short way." This is angle-space lerp: cheap, but it can take a
non-geodesic path through orientation space and wobble near gimbal
configurations — exactly what the rotor's slerp avoids.

## 6. How this relates to the course — Euler angles vs. GA rotors

The maintainer teaches rotation in `modelviewprojection` ch07/ch14 and
`geometricalgebra` via **rotors**: a rotation is `R = exp(-B·θ/2)` where
`B` is the unit bivector naming the **plane** of rotation, applied by the
**sandwich** `v' = R v R̃`, and composed by **multiplying rotors**. Set the
two approaches side by side:

| Aspect | SM64 Euler binary angles | Course GA rotor |
|---|---|---|
| **Representation** | 3 × `s16` angles (6 bytes) | a rotor (even-grade multivector; 4 floats, like a quaternion) |
| **What it names** | angle about each of 3 fixed axes | the **plane** of rotation + half-angle |
| **Angle unit** | binary (`0x10000` = full turn; wraps for free) | radians |
| **Trig** | table lookup (`sins`/`coss`) | computed (`exp`, `cos`/`sin` of half-angle) |
| **Compose two rotations** | multiply the matrices, in a fixed axis order | multiply the rotors (order-free framing, associative) |
| **Gimbal lock** | possible (middle axis at ±90°) | **none** — a rotor is a single planar rotation |
| **Normalization drift** | none (angles are exact integers) | a rotor/quaternion drifts and needs renormalizing |
| **Interpolate** | lerp angles (short-way wrap); can wobble | **slerp** — constant-speed geodesic on SO(3) |
| **Extract from a vector** | trivial (`atan2s` → yaw/pitch) | awkward (recover plane + angle) |

**Where they agree:** both produce the *same element of SO(3)* — SM64's
nine matrix entries in §3 are exactly the rotation a rotor's sandwich would
apply; a reader can build the rotor for `(rotate[0],rotate[1],rotate[2])`
in ZXY order and get the same matrix (transposed for the row-vector
convention — see `matrices-and-linear-algebra.md`).

**Where they differ, and why the engine chose Euler:** a 1996 console
valued the three things Euler wins on — **tiny storage** (6 bytes vs 16),
**no normalization drift** (integers can't denormalize the way a
float quaternion does), and **trivial angle extraction** (`atan2s` for
aiming and cameras). It paid for that with **gimbal lock** and
**non-geodesic interpolation**, both of which it dodges by design (objects
rarely tumble freely; the matrix-level interpolation sidesteps angle
wobble). The rotor's advantages — clean composition, no gimbal, geodesic
slerp — are exactly what the course teaches *because* they are the right
default when you are *not* constrained to 6 bytes and a lookup table. So
this is the cleanest possible worked contrast: **the same rotation, chosen
two ways, each optimal for its constraints.**

**Gap filled / connection made:** the course never shows Euler angles,
binary-angle arithmetic, sine tables, gimbal lock, or angle-lerp — all
staples of real-time engines. Seeing them next to the rotor makes the
rotor's coordinate-free virtues concrete (you can point at the gimbal case
the rotor removes) and shows the reader *why* an engine might still reach
for the "worse" representation.

## Candidate doc-region spans (for the later Sphinx pass — not yet added)

- `src/engine/math_util.h` (`:20-24`): region `sine_lookup` — the LUT
  macros and the cosine-as-shifted-sine trick.
- `src/engine/math_util.c` around `mtxf_rotate_zxy_and_translate`
  (`:279-308`): region `euler_zxy_to_matrix` — the hand-multiplied
  closed form; the centerpiece for the Euler-vs-rotor comparison.
- `src/engine/math_util.c` around `atan2s`/`vec3f_find_yaw` (`:639`,
  `:713`): region `angles_from_vector` — the easy inverse.
