==================================
Appendix A: Fixed-point matrices
==================================

Chapters :doc:`engine-math` and :doc:`projection` mentioned that matrices live
in two forms — a float working form and a fixed-point form the renderer draws
with — and glossed the bridge. Here is the next level.

The N64's graphics coprocessor multiplied matrices in **fixed point**: each
number split into an integer half and a fractional half, stored as two 16-bit
pieces. It is fast on integer hardware and has no floating-point rounding, but a
narrow range. The decomp still produces exactly that format, so it byte-matches
the original game.

The conversion from the float form (``Mat4``) to the fixed-point form (``Mtx``)
is a single, deliberate step — **not** a reinterpret-the-bytes cast, which would
be undefined and would break on a little-endian PC. The engine calls the N64's
own ``guMtxF2L`` helper, which splits and packs each value correctly. That one
call is also where the smooth-motion system records the matrix (see
:doc:`frame-interpolation`), because interpolation happens on the *float* form
just before this conversion.

Full detail: ``tasks/reference/mario64/matrices-and-linear-algebra.md``.
