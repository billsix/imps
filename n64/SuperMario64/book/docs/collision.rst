===================
Collision detection
===================

Your course has no collision at all. It is the foundation of all game physics,
and Super Mario 64's is a clean, canonical example: triangles, sorted into a
grid so a query only tests what is nearby.

Triangles, in three kinds
=========================

The collidable world is a set of **triangles**, each with a normal and a type.
They are split into three groups — walls, floors, ceilings — because the
questions differ: a floor query wants the highest surface below you facing up; a
ceiling, the lowest above you facing down; a wall, something near-vertical you
push against.

Broad phase then narrow phase
=============================

Testing a point against thousands of triangles every frame would be hopeless, so
at load time each triangle is filed into a cell of a **grid** laid over the
level. A query first hashes its position to a cell, then tests only that cell's
short list:

.. literalinclude:: ../../Ghostship/src/engine/surface_collision.c
   :language: c
   :start-after: // doc-region-begin spatial_partition_lookup
   :end-before: // doc-region-end spatial_partition_lookup
   :caption: find_wall_collisions — hash to a grid cell, then test its list

That two-step shape — a cheap **broad phase** (which cell?) then an exact
**narrow phase** (which triangle?) — is the backbone of every physics engine.
The idea worth carrying away is not the triangle math but the **spatial
partition**: pre-sort geometry by location so queries stay local. It is the same
"don't look at everything, look at what's near" instinct as the texture and
shader caches earlier in this book.

.. graphviz::

   digraph coll {
     rankdir=LR;
     node [shape=box, fontname="sans-serif"];
     pos [label="position (x,z)"];
     cell [label="grid cell\n(broad phase)"];
     list [label="wall/floor/ceil\nlist for the cell"];
     tri [label="per-triangle test\n(narrow phase)"];
     pos -> cell -> list -> tri;
   }

And this system has more than one customer: Mario's movement uses it, and so
does the camera (:doc:`camera`), which raycasts floors and ceilings to avoid
clipping. A subsystem other subsystems depend on — the kind of coupling a
single-purpose demo never has.

.. admonition:: Go deeper
   :class: seealso

   Walls, floors, ceilings, and the partition build:
   ``tasks/reference/mario64/collision-detection.md``.
