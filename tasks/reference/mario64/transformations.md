# Reference: Transformations — building and composing down the geo tree

> **Provenance:** authored 2026-09-06 against Ghostship pin `49c5312a`.
> Anchors in the decomp (`src/engine/math_util.c`,
> `src/game/rendering_graph_node.c`). Part of the mario64 graphics set —
> map at [`README.md`](README.md). Depends on `matrices-and-linear-
> algebra.md` (the convention); rotation *math* is in
> `rotation-euler-vs-rotors.md`; the tree *structure* is in
> `scene-graph-and-data-structures.md`.

## TL;DR

A transform is built as a local `Mat4` (translate, scale, or a combined
rotate-and-translate builder) and then **composed onto its parent by
multiplying local × parent**. Composition happens on a **matrix stack**
(`gMatStack[32]`) as the renderer walks the geo tree **depth-first**: each
node pushes `local · parent`, converts the new top to fixed-point, recurses
into its children, and pops. This is the concrete, running form of the
"stack of composed transforms" the course teaches — a scene graph whose
every node contributes one matrix multiply.

## 1. The builders (`math_util.c`) — all row-vector

Each builder writes a `Mat4` in SM64's translation-in-row-3 convention
(see `matrices-and-linear-algebra.md` §2):

- **`mtxf_translate(dest, b)` (`:186`)** — identity with `dest[3] = b`
  (translation in the last row):
  ```c
  mtxf_identity(dest);
  dest[3][0]=b[0]; dest[3][1]=b[1]; dest[3][2]=b[2];
  ```
- **`mtxf_scale_vec3f(dest, mtx, s)` (`:550`)** — scales the three basis
  rows and **preserves the translation row**:
  ```c
  for (i=0;i<4;i++){ dest[0][i]=mtx[0][i]*s[0]; dest[1][i]=mtx[1][i]*s[1];
                     dest[2][i]=mtx[2][i]*s[2]; dest[3][i]=mtx[3][i]; }
  ```
  Row-scaling (not column) because a scale in the row-vector convention
  multiplies the basis rows; row 3 (translation) is copied through.
- **`mtxf_rotate_zxy_and_translate` (`:279`) / `mtxf_rotate_xyz_and_translate`
  (`:313`)** — the workhorses: build rotation-plus-translation in one call.
  The **rotation math** (fixed-point Euler angles, sin/cos LUT, and why ZXY
  vs XYZ order) is `rotation-euler-vs-rotors.md`; here they are just "the
  local transform for a node."

Every builder that a live path uses also fires a `FrameInterpolation_Record*`
(e.g. `RecordMatrixTranslate` at `:188`) so the smooth-framerate system can
interpolate it — see `frame-interpolation.md`.

## 2. Composition = local · parent (order matters, and it's the transpose)

Composition is always `mtxf_mul(out, local, parent)`:

```c
// geo_process_translation_rotation (rendering_graph_node.c:388-390)
mtxf_rotate_zxy_and_translate(mtxf, translation, node->rotation);   // local
mtxf_mul(gMatStack[gMatStackIndex + 1], mtxf, gMatStack[gMatStackIndex]);  // local · parent
gMatStackIndex++;
```

With SM64's **row vectors**, a point is transformed `v' = v · M`, so
`v · (local · parent) = (v · local) · parent` — **local applies first,
then the parent frame**, exactly the child-then-ancestor order a hierarchy
needs. This is the same "order matters" lesson the course dramatizes with a
deliberately-broken rotation (`modelviewprojection` ch08→09), but here the
order is fixed by the row-vector algebra and the multiply argument order,
not by a bug. Note the mirror: a column-vector engine would write
`parent · local`; SM64's `local · parent` is the transpose of that, and
correct for its convention.

## 3. The matrix stack — push, convert, recurse, pop

The renderer keeps two parallel stacks and an index
(`rendering_graph_node.c:53-55`):

```c
s16   gMatStackIndex;
Mat4  gMatStack[32];        // float working matrices
Mtx  *gMatStackFixed[32];   // the fixed-point twin for each level
```

Every transform node processor follows the **same five-step shape**
(shown for translation+rotation, `:388-399`; translation `:416`, scale, and
`geo_process_object` are identical in structure):

1. build `mtxf` (the local transform);
2. `mtxf_mul(gMatStack[i+1], mtxf, gMatStack[i])` — compose onto parent;
3. `gMatStackIndex++` (push);
4. `mtxf_to_mtx(mtx, gMatStack[i])` + `gMatStackFixed[i] = mtx` — make the
   fixed-point twin the renderer will actually draw with;
5. process children, then `gMatStackIndex--` (pop).

So the **float stack** carries the precise composition and the **fixed-point
stack** carries what each node draws. Depth 32 caps hierarchy nesting. This
depth-first push/pop over the geo tree is the transform half of the scene
graph; the tree's *node types and traversal* are
`scene-graph-and-data-structures.md`, and the interpolation `OpenChild`/
`CloseChild` brackets around each push (`:385`, `:399`) are how
`frame-interpolation.md` keeps cross-frame identity.

## How this relates to the course

- **`modelviewprojection` ch08-09 (order of transforms) and ch16 (the
  "lambda stack" of composed functions)** teach composition as function
  composition read top-down/bottom-up. SM64's `gMatStack` **is** that
  lambda stack, made concrete: each geo node is one composed transform,
  pushed as `local · parent` and popped after its subtree. The course's
  abstract "stack of transforms" and this array-of-matrices-with-an-index
  are the same idea at two altitudes — a direct illustration.
- **`geometricalgebra`/gacalc** composes transforms as products of
  `ComposableFunction`s (its `to_matrix` yields the model matrix). SM64
  composes the *matrices* directly on the stack; a gacalc-built transform
  would slot in at step 1 as the local `mtxf` (after transposing for the
  row-vector convention — see the matrices doc).
- **Gap filled:** the course teaches transform composition on a handful of
  objects; SM64 shows it as a **whole-scene depth-first traversal** with a
  bounded stack and a fixed-point twin per level — composition as a
  renderer actually runs it, thousands of nodes per frame.

## Candidate doc-region spans (for the later Sphinx pass — not yet added)

- `src/game/rendering_graph_node.c` around `geo_process_translation_rotation`
  (`:388-399`): region `compose_local_onto_parent` — the five-step
  push/convert/recurse/pop.
- `src/engine/math_util.c` around `mtxf_translate` (`:186-193`): region
  `mtxf_translate_row3` — translation in the last row.
- `src/engine/math_util.c` around `mtxf_scale_vec3f` (`:550-558`): region
  `mtxf_scale_rows` — row-scaling that preserves translation.
