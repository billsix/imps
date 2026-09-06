==============================
Appendix D: Curves and splines
==============================

The main chapters never needed a curve, but Super Mario 64 has exactly one place
that does: the **cutscene and credits camera**, which glides along a smooth path.
The path is a **uniform cubic B-spline** — four control points blended by cubic
basis functions to produce a point that moves smoothly as a parameter runs from
0 to 1. A B-spline *approximates* its control points (it does not pass through
them) and joins its segments smoothly, which is exactly what a camera path wants:
no kinks.

There are **no curved surfaces** anywhere — every curved-looking shape in the
game is low-polygon mesh, not a mathematical surface. So "curves" in this engine
means one special-purpose camera spline, and nothing more.

Full detail: ``tasks/reference/mario64/curves-and-splines.md``.
