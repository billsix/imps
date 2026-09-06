# Reference: Matrices & applied linear algebra — two forms, transposed, pooled

> **Provenance:** authored 2026-09-06 against Ghostship pin `49c5312a`.
> Anchors in the decomp (`src/engine/math_util.c`) and the port
> (`src/port/interpolation/matrix.c`, `src/port/Matrix.cpp`). Part of the
> mario64 graphics set — map at [`README.md`](README.md). L1 mental model:
> [`matrices-and-linear-algebra-overview.md`](matrices-and-linear-algebra-overview.md).
> Companions: `vectors-and-vector-math.md`, `transformations.md`,
> `frame-interpolation.md` (why matrices are pooled).

## TL;DR

SM64 keeps every matrix in **two representations**: `Mat4` (`f32[4][4]`, the
float working form) and `Mtx` (the N64 **fixed-point** hardware form).
Math happens in `Mat4`; just before drawing, `mtxf_to_mtx` converts to
`Mtx` via `guMtxF2L`. The storage convention is **transposed relative to
OpenGL/gacalc**: SM64 is row-vector with **translation in the last ROW**
(`m[3]`), not the last column. `mtxf_mul` exploits that by computing only
the affine 3×4 part and hardcoding the last column to `(0,0,0,1)`.
Matrices live in **fixed-size pools at stable addresses** so the frame
interpolator can key on a matrix's pointer across ticks.

## 1. Two representations, and the bridge between them

| Form | Type | Where | Why |
|---|---|---|---|
| Float working matrix | `Mat4` = `f32[4][4]` (`types.h:45`) | all `mtxf_*` math | precision + easy to build |
| N64 fixed-point matrix | `Mtx` (int-pair hi/lo) | what the renderer consumes | the hardware format the RSP used |

The N64's RSP multiplied matrices in a **fixed-point** format that splits
each value into a high (integer) and low (fraction) 16-bit half. The decomp
still produces that format so it byte-matches the ROM; the modern port then
feeds it to Fast3D. The conversion is the one seam:

```c
// mtxf_to_mtx (math_util.c:585)
void mtxf_to_mtx(Mtx *dest, Mat4 src) {
    FrameInterpolation_RecordMatrixMtxFToMtx((MtxF*)src, dest);  // record for interp
    guMtxF2L(src, dest);                                          // float -> fixed-point
}
```

The comment notes it calls `guMtxF2L` **instead of a type-cast** —
casting `Mat4`↔`Mtx` is UB and endian-fragile; `guMtxF2L` does the
split-and-pack correctly on little-endian PCs. `RecordMatrixMtxFToMtx` is
the frame-interpolation hook: because interpolation lerps the *float*
matrices before this conversion, every draw-bound matrix is captured here
(see `frame-interpolation.md` — this is its workhorse recorder).

## 2. The convention: row-vector, translation in the last ROW

`mtxf_mul` (`:501`) reveals the storage convention. Read its structure:

```c
void mtxf_mul(Mat4 dest, Mat4 a, Mat4 b) {
    // for i in 0..2:  temp[i][j] = a[i][0]*b[0][j] + a[i][1]*b[1][j] + a[i][2]*b[2][j]
    // for i == 3:     temp[3][j] = a[3][0]*b[0][j] + ... + b[3][j]   // <-- translation row, + b's translation
    temp[0][3] = temp[1][3] = temp[2][3] = 0;
    temp[3][3] = 1;
    mtxf_copy(dest, temp);
}
```

Three things a reader must see:

- **`a[3]` is the translation.** Row 3 gets the extra `+ b[3][j]` term —
  that is the affine translation, so **SM64 puts translation in the last
  ROW**, the transpose of the OpenGL/gacalc "last column" convention. A
  matrix here is applied as `v' = v · M` (row vector on the left), not
  `M · v`.
- **It's a 3×4 affine multiply, not a full 4×4.** The last column is
  hardcoded to `(0,0,0,1)`; the code never computes a general fourth
  column because SM64 matrices are always affine (no projection lives in
  `Mat4`; projection is set up separately in fixed-point, §4). Multiplying
  two affines and forcing the last column is correct and cheaper.
- **Register-blocked for the N64.** Each row of `a` is read once into
  `entry0/1/2` (`register f32`) and reused across the three output
  columns — a hand-scheduled optimization for the MIPS target, matched by
  the decomp.

(The `// TODO: FrameInterpolation is broken` commented-out
`FrameInterpolation_RecordMatrixMult` at `:502` is dead — matrix *products*
are not recorded; only the final `mtxf_to_mtx` outputs are. See
`frame-interpolation.md` §1 on which recorders are live.)

Identity and the builders (`mtxf_identity:171`, `mtxf_translate:186`, the
rotate-and-translate builders, `mtxf_scale_vec3f:550`) all follow the same
row-translation convention and are covered as *transforms* in
`transformations.md`.

## 3. Matrix pools — stable addresses for the interpolator

The port keeps matrices in fixed-size arrays, not the heap
(`src/port/interpolation/matrix.c`):

```c
Mtx     gMainMatrixStack[0x480];   // :20  — 1152 fixed-point matrices
Matrix  sGfxMatrixStack[0x20];     // float working stack
Matrix  sCalcMatrixStack[0x20];    // float scratch stack
```

`Matrix` is the port's own float 4×4 (`{ f32 mf[4][4]; }`), initialized
from `gIdentityMatrix`. The pools matter for **frame interpolation**: the
interpolator keys its replacement map on the **destination `Mtx*`
pointer** (`unordered_map<Mtx*, MtxF>`), so a given logical matrix must
occupy the **same address every tick**. Pooling in a stable array
guarantees that; heap-allocating per frame would break the key. This is
the coupling `frame-interpolation.md` §7 warns not to disturb — the two
docs meet here.

## 4. Projection is fixed-point and separate (`Matrix_InitPerspective`)

Projection never enters `Mat4` math. `Matrix_InitPerspective` (`matrix.c`)
builds it straight in fixed-point with the libultra helpers:

```c
guPerspective(gGfxMtx, &norm, fov=45.0f, 320.0f/240.0f, near=10.0f, far=12800.0f, 1.0f);
gSPPerspNormalize(...norm);                 // the perspective-normalize scalar
gSPMatrix(..., G_MTX_LOAD | G_MTX_PROJECTION);
guLookAt(gGfxMtx, eye, at, up);             // view, multiplied onto projection
```

So the model/view/world transforms flow through `Mat4` (§1-2) and land on
the modelview matrix stack, while **projection is a separate fixed-point
matrix** set once per frame. FOV, near/far, and `guPerspective` belong to
`field-of-view-and-projection.md`; noted here only to bound what `Mat4`
math does and does not include.

## How this relates to the course

- **`modelviewprojection` ch19 (`gluPerspective`, matrix stacks) +
  `perspective.rst`** teach OpenGL's convention: **column-major** storage,
  **translation in the last column**, applied as `M · v`. SM64 is the
  **transpose**: row-vector, **translation in the last row**, applied as
  `v · M`. Same linear map, mirrored storage — a perfect worked example of
  why "which convention" is a real decision, not cosmetics. Put the two
  matrices side by side and the transpose is visible.
- **`geometricalgebra`/gacalc `to_matrix`** emits a homogeneous 4×4 with
  translation in the **last column** (the mvp/OpenGL convention) and
  refuses anything non-linear. SM64 agrees it's affine-only in `Mat4`
  (projection is elsewhere), but stores it transposed — so a gacalc-built
  model matrix would need transposing to feed SM64's `mtxf_mul`.
- **Gap filled:** neither course has the **dual float/fixed-point
  representation** or the **stable-pool-for-interpolation** idea. The
  fixed-point form is pure console heritage; the pooling is the concrete
  reason the frame-interpolation trick (which the course also lacks) can
  key on pointers. This doc is where "a matrix" stops being one clean
  object and becomes two representations with a conversion and a lifetime.

## Candidate doc-region spans (for the later Sphinx pass — not yet added)

- `src/engine/math_util.c` around `mtxf_mul` (`:501-544`): region
  `mtxf_mul_affine` — the 3×4 affine multiply with translation in row 3.
- `src/engine/math_util.c` around `mtxf_to_mtx` (`:585-591`): region
  `float_to_fixed_matrix` — the `guMtxF2L` bridge + interp hook.
- `src/port/interpolation/matrix.c` around the pool decls (`:20`): region
  `matrix_pools` — stable addresses for interpolation keying.
