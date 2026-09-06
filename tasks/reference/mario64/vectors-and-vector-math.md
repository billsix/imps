# Reference: Vectors & vector math in SM64 — arrays, in place, dest-first

> **Provenance:** authored 2026-09-06 against Ghostship pin `49c5312a`.
> All anchors are in the decomp (`src/engine/math_util.c`, `include/
> types.h`); no libultraship involved. Part of the mario64 graphics set —
> map at [`README.md`](README.md). Companion: `matrices-and-linear-
> algebra.md`, `transformations.md`.

## TL;DR

A vector in SM64 is a **bare C array** — `Vec3f` is `f32[3]`, `Vec3s` is
`s16[3]` — not a struct and not an object. Every operation **mutates a
`dest` argument in place** and takes `dest` first (`vec3f_sum(dest, a,
b)`), C's answer to "no return-by-value for aggregates cheaply." There is
**no named float dot product and no float subtract**; where the engine
needs them it writes the arithmetic inline. `vec3f_cross` and
`vec3f_normalize` exist; normalize has no divide-by-zero guard. Each
function ends `return &dest;` with a standing decomp warning — a matching
artifact, not a value anyone uses.

## 1. The types (`include/types.h`)

```c
typedef f32 Vec3f[3];    // :39  — X, Y, Z, where Y is up
typedef s16 Vec3s[3];    // :40  — 16-bit integer components
typedef u16 Vec3su[3];   // :77  — unsigned variant
typedef f32 Mat4[4][4];  // :45  — float 4x4 (matrices doc)
```

Three consequences that shape every call below:

- **A `Vec3f` decays to a pointer** when passed, so a function receives
  the caller's storage and writes through it — there is no copy, and no
  way to return a vector by value. Hence the **dest-first, mutate-in-place**
  convention.
- **`Vec3s` is integer** (`s16`, range ±32767). Positions, normals, and
  especially **angles** are frequently stored as `Vec3s`; converting to
  `Vec3f` for arithmetic and back is a recurring pattern (§3).
- **`Y is up`** is a documented axis convention baked into the type
  comment — worth stating because the course and gacalc are axis-agnostic.

## 2. The float operations (`math_util.c:33-157`)

The whole block sits inside a `#pragma GCC diagnostic push/pop`
(`:157` pops) that silences one warning the decomp deliberately keeps
(§4). Live functions:

| Function | Line | Does |
|---|---|---|
| `vec3f_copy(dest, src)` | `:33` | `dest = src`, componentwise |
| `vec3f_set(dest, x,y,z)` | `:41` | `dest = (x,y,z)` |
| `vec3f_add(dest, a)` | `:49` | `dest += a` (accumulate) |
| `vec3f_sum(dest, a, b)` | `:57` | `dest = a + b` |
| `vec3f_cross(dest, a, b)` | `:137` | `dest = a × b` |
| `vec3f_normalize(dest)` | `:145` | scale `dest` to unit length |
| `find_vector_perpendicular_to_plane(dest,a,b,c)` | `:126` | triangle normal (fused cross) |
| `vec3f_to_vec3s(dest, a)` | `:116` | round float→short |

**Note what is missing.** There is **no `vec3f_sub` and no `vec3f_dot`.**
`vec3s` has a `_sub` (`:98`) but `vec3f` does not; the dot product is
never a named function. Both are instead written **inline at call sites**
— e.g. the length term inside normalize is a hand-written dot:

```c
// vec3f_normalize (:145-147)
f32 invsqrt = 1.0f / sqrtf(dest[0]*dest[0] + dest[1]*dest[1] + dest[2]*dest[2]);
```

and the billboard/relative-position math writes three inline dot products
against matrix columns (`:616-625`). This is deliberate 1996-era
hand-optimization: a named `dot` would cost a call and an array read the
compiler couldn't always inline on the N64's MIPS target, so the decomp
matches the ROM by inlining. **Teaching point:** the dot product is
everywhere in this engine, but never as a *word* — it hides inside
normalize, projection, and the lighting/billboard code.

### Cross product (`:137`)

The textbook formula, no abstraction:

```c
dest[0] = a[1]*b[2] - b[1]*a[2];
dest[1] = a[2]*b[0] - b[2]*a[0];
dest[2] = a[0]*b[1] - b[0]*a[1];
```

`find_vector_perpendicular_to_plane` (`:126`) is a **fused variant**: it
computes `(b−a) × (c−b)` for a triangle's face normal in one pass without
materializing the two edge vectors — used by surface/lighting code that
needs the normal, not the edges.

### Normalize (`:145`) — and its two hazards

```c
f32 invsqrt = 1.0f / sqrtf(dest[0]*dest[0] + dest[1]*dest[1] + dest[2]*dest[2]);
dest[0] *= invsqrt; dest[1] *= invsqrt; dest[2] *= invsqrt;
```

Two decomp comments mark real hazards left in for ROM-accuracy:
`//! Possible division by zero` (a zero-length vector yields `inf`/`NaN`,
unguarded) and the block-wide return quirk (§4). A teaching library would
guard the zero case; the engine relies on callers never normalizing a zero
vector.

## 3. `Vec3s` ↔ `Vec3f` conversion (`:106`, `:116`)

`vec3s_to_vec3f` widens directly. `vec3f_to_vec3s` **rounds to nearest**
rather than truncating, by nudging ±0.5 before the implicit cast:

```c
dest[0] = a[0] + ((a[0] > 0) ? 0.5f : -0.5f);   // then cast to s16
```

This matters because integer `Vec3s` is the storage form for positions and
angles; every frame, float math results are rounded back to `s16`, so
sub-integer motion is quantized. (Angles as `Vec3s` are the subject of
`rotation-euler-vs-rotors.md`.)

## 4. The `return &dest` quirk — a matching artifact, not an API

Every function ends:

```c
return &dest;   //! warning: function returns address of local variable
```

`dest` is a parameter (a pointer, since the array decayed), so `&dest` is
the address of a **local copy of that pointer** — dangling the instant the
function returns. The return value is **never used**; callers rely on the
in-place mutation. It is reproduced faithfully because the original ROM did
it, and the decomp's job is byte-matching, not cleanup — hence the
`#pragma GCC diagnostic push/pop` wrapping the block to keep the build
quiet. **Do not "fix" it**; it is load-bearing for the match, not for
behavior.

## How this relates to the course

- **`modelviewprojection` ch05 / mathhomework1** introduce vectors as a
  `Vector` class with methods and operator overloading, returning **new,
  immutable** vectors (`a + b` yields a fresh object). SM64 is the
  opposite pole: **mutable arrays, dest-first, no operators, no
  return-by-value.** Same linear algebra, but the ergonomics the course
  teaches are exactly what a cache- and cycle-constrained console gives
  up. Showing both side by side makes the course's abstraction *visible*
  as a choice, not a given.
- **`geometricalgebra`/gacalc** models a vector as a grade-1 multivector
  and derives the **cross product as the dual of the wedge**
  (`vectorcalc.py`), with dot/wedge as first-class operations. SM64 has
  **no wedge and no named dot** — the cross product is a hand-written
  determinant and the dot is inlined arithmetic. This is the clean
  contrast: gacalc names and generalizes the products; the engine spends
  them as raw coordinate arithmetic and never names them. A reader who
  knows the GA story will recognize `find_vector_perpendicular_to_plane`
  as a wedge-then-dual computed the coordinate way.
- **Gap filled:** neither course covers the *engineering* of vectors —
  in-place mutation, integer storage with rounding, hand-inlined dot,
  unguarded normalize. That is the "how a shipping engine actually does
  it" layer the courses omit.

## Candidate doc-region spans (for the later Sphinx pass — not yet added)

- `src/engine/math_util.c` around `vec3f_cross` (`:137-143`): region
  `vec3f_cross` — the textbook cross product with no abstraction.
- `src/engine/math_util.c` around `vec3f_normalize` (`:145-153`): region
  `vec3f_normalize` — shows the inlined dot and the divide-by-zero note.
- `src/engine/math_util.c` around `vec3f_to_vec3s` (`:116-123`): region
  `round_float_to_short` — the ±0.5 rounding idiom.
