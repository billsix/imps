# Orientation (L1): Matrices in SM64 — the mental model

> **Provenance:** Ghostship pin `49c5312a`, 2026-09-06. This is the **L1**
> (understand-without-code) level. Capsule (L0) is in
> [`README.md`](README.md); full mechanism with anchors (L2) in
> [`matrices-and-linear-algebra.md`](matrices-and-linear-algebra.md).

Read this to *get* how SM64 handles matrices without reading the code.
Three ideas carry the whole subject.

**1. A matrix exists in two forms.** While the engine is doing math — building
a transform, composing it with a parent's — a matrix is an ordinary float
4×4. But the renderer wants the format the original N64 hardware used: a
**fixed-point** form that splits every number into an integer half and a
fraction half. So each matrix leads a double life: it is computed as
floats, then, just before it is drawn, converted once to fixed-point. The
conversion is a single well-defined step, not a cast, because reinterpreting
the bytes would be wrong on a modern PC. This dual life is pure console
heritage — a from-scratch renderer would use floats end to end — and it is
the first thing that surprises someone coming from a graphics course, where
a matrix is just a matrix.

**2. The convention is the transpose of what a graphics course teaches.**
OpenGL, and the maintainer's course, store a matrix so that translation
sits in the last **column** and a point is transformed by putting the
matrix on the **left** (`M · v`). SM64 does the mirror image: translation
lives in the last **row**, and a point is a **row vector** transformed on
the **right** (`v · M`). It is the same rotation and the same translation —
the same linear map — laid out transposed. Because of this, the engine's
matrix multiply only ever computes the affine part (a 3×3 rotation plus a
translation row) and simply stamps the last column as "no projection here."
Projection is not part of this math at all; it is built separately, later,
directly in the fixed-point form.

**3. Matrices live at fixed addresses, on purpose.** Rather than allocate a
matrix wherever there is room, the port keeps them in fixed-size arrays and
reuses the same slots every frame. The reason is the smooth-framerate trick
(see the frame-interpolation doc): to blend a matrix between last frame and
this frame, the engine has to recognize "this is the same matrix as last
time," and it does that by its **memory address**. Stable addresses make
that recognition free. So matrix storage is not just a container — its
*lifetime and location* are load-bearing for how the game renders at
120 Hz from 30 Hz logic.

Put together: a matrix in SM64 is a float 4×4 during computation, stored
transposed from the textbook convention, converted to a fixed-point twin
for drawing, and pinned to a stable address so it can be recognized frame
to frame. None of those three facts is something a graphics course needs to
teach, which is exactly why they are worth seeing here.
