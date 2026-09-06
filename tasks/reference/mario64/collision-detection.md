# Reference: Collision detection — triangle surfaces in a grid partition

> **Provenance:** authored 2026-09-06 against Ghostship pin `49c5312a`.
> Anchors in `src/engine/surface_collision.c`, `src/engine/surface_load.c`.
> Part of the mario64 graphics set — map at [`README.md`](README.md).
> Companions: `scene-graph-and-data-structures.md`, `camera-system.md`
> (the camera is a collision client).

## TL;DR

The world's collision is a set of **triangles** (`struct Surface`), sorted
at load time into a **uniform grid of cells** (a spatial partition) so a query
only tests the few triangles near a point, not all of them. The triangles are
split into **three kinds** — walls, floors, ceilings — each in its own list
per cell, because the tests differ. `find_wall_collisions` (`:185`),
`find_floor`, and `find_ceil` (`:307`) hash a position to its cell and walk
that cell's list. This is classic broad-phase (grid) + narrow-phase
(per-triangle) collision — the standard structure, at 1996 scale.

## 1. The data: triangle surfaces, three kinds

Every collidable surface is a `struct Surface` triangle with a normal and a
type. At load, `surface_load.c` bins each triangle into a **cell** of a 2D
grid over the level (by X/Z) and into one of three per-cell lists:
`SPATIAL_PARTITION_WALLS`, `_FLOORS`, `_CEILS` (`surface_collision.c:211`).
Why three: a **floor** query wants the highest surface below you whose normal
points up; a **ceiling** wants the lowest above you pointing down; a **wall**
wants near-vertical surfaces you'd push against. Different geometry, different
test, so different lists.

## 2. The broad phase: hash position → cell (`:203`)

```c
cellX = ((x + LEVEL_BOUNDARY_MAX) / CELL_SIZE) & NUM_CELLS_INDEX;
cellZ = ((z + LEVEL_BOUNDARY_MAX) / CELL_SIZE) & NUM_CELLS_INDEX;
node = gStaticSurfacePartition[cellZ][cellX][SPATIAL_PARTITION_WALLS].next;
```

A position maps to a grid cell by integer division (the `& NUM_CELLS_INDEX`
wraps/masks to the grid size). The query then only walks **that cell's** list
— turning "test against thousands of triangles" into "test against the handful
in this cell." There are static (level) and dynamic (moving platform)
partitions, checked in turn (`:208-212`).

## 3. The narrow phase: per-triangle tests (`find_*_from_list`)

`find_wall_collisions_from_list` (`:20`), `find_floor_from_list`,
`find_ceil_from_list` (`:227`) do the actual geometry: for each triangle in
the cell, is the point inside the triangle's projection, and on the correct
side of its plane? Walls push the point out along the surface normal by a
radius; floors/ceilings return the surface height at (x,z). The result feeds
gameplay (Mario's movement) **and** the camera (`camera-system.md` raycasts
`find_ceil`/`find_floor` to avoid clipping).

## How this relates to the course

- **Neither course covers collision at all** (`modelviewprojection` ch01's
  "collision" is a pun). So this is a clean, canonical gap-fill: the
  **broad-phase/narrow-phase** split, a **uniform-grid spatial partition**,
  and **triangle-vs-point** tests are the foundation of all game physics.
- **A data-structures lesson as much as geometry:** the key idea is *not*
  the triangle math but the **spatial partition** — pre-sorting geometry by
  location so queries are local. That "don't test everything, test what's
  near" principle generalizes far beyond collision (it's the same instinct as
  the texture/shader caches elsewhere in this set).
- **Cross-system:** collision is consumed by movement *and* by the camera, so
  it shows a subsystem other subsystems depend on — the kind of coupling a
  single-purpose course example never has.

## Candidate doc-region spans (for the later Sphinx pass — not yet added)

- `src/engine/surface_collision.c` around the cell hash in
  `find_wall_collisions` (`:203-212`): region `spatial_partition_lookup` —
  position → grid cell → surface list.
- `src/engine/surface_collision.c` around `find_ceil` (`:307`) /
  `find_ceil_from_list` (`:227`): region `narrow_phase_ceiling` — the
  per-triangle test.
