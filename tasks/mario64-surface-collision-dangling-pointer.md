# SuperMario64: `find_floor_from_list` returns the address of a local (frame-interpolation path)

**Status:** proposed — needs go-ahead
**Priority:** 3 · **Difficulty:** 2 (one static per function; the hard part is deciding the
lifetime the callers need)
**Project key:** mario64
**Found by:** the assembly-isms survey (`tasks/archive/mario64/2026/09/23/mario64-assembly-isms-to-standard-c.md`, "Out of
scope but found: a real bug"), 2026-09-22. Not a decomp artefact — it is in Ghostship's own
port-authored interpolation code, so it is an **upstream bug**, to be shaped as an
`upstream-candidates` patch, not part of the `standard-c` stream.

## BLUF

`Ghostship/src/engine/surface_collision.c` `find_floor_from_list` (definition at the
`struct Surface *find_floor_from_list(` line; the `if (interpolate)` block near the end of its
loop) builds a `struct Surface s` on the stack and `return &s;` — a dangling pointer every caller
then dereferences (`floor->normal.y`, `floor->type`, …). Done = the interpolated surface lives
somewhere that outlives the call (a `static struct Surface` per function, or a caller-provided
out-parameter), the same fix mirrored in `find_ceil_from_list` if it has the same shape, the
behaviour checked in-game with frame interpolation on, and the patch filed under
`patches/upstream-candidates/`.

## Context

- The block (current text at the pin, unchanged by the `standard-c` stream):
  ```c
  *pheight = height;
  if (interpolate) {
      struct Surface s;
      s.type = surf->type;
      s.normal.x = nx;
      s.normal.y = ny;
      s.normal.z = nz;
      s.originOffset = oo;
      return &s;
  }
  ```
  `interpolate = gInterpolatingSurfaces && surf->modifiedTimestamp == gGlobalTimer` — so it only
  fires on surfaces modified this frame while interpolation is on (moving platforms), which is
  why it "works": the stack slot usually still holds the values when the caller reads them.
  GCC warns (`-Wreturn-local-addr`) and at higher optimisation levels may return NULL instead
  (it is allowed to), which would turn the platform floor into "no floor".
- Callers: `find_floor` (dynamic then static surface lists) and, through it, every
  floor query in the game loop; check `find_ceil_from_list` for the same idiom before fixing.
- Why not a `standard-c` patch: the stream's rule is codegen-identical, and this is a semantic
  fix. It also stands a much better chance upstream on its own (a bug, with a warning to quote).

## Plan

- [ ] Confirm the warning: compile `surface_collision.c` with the port's flags + `-Wall` and
      quote `-Wreturn-local-addr`; check `find_ceil_from_list`.
- [ ] Fix: `static struct Surface sInterpolatedFloor;` (and `sInterpolatedCeil` if needed), fill
      and return `&sInterpolatedFloor`. Note in the message that only one interpolated result is
      live at a time (the caller consumes it before the next query) — verify that claim by
      reading `find_floor`'s two calls (dynamic result is compared with the static one: **two
      results may be live at once**, so the dynamic and static paths may need separate statics,
      or `find_floor` must copy the first before the second call).
- [ ] Build, run with interpolation on, stand on a moving platform (BitFS elevators, the tilting
      pyramids) — the maintainer's host check.
- [ ] Commit on a scratch branch at the pin, export to `patches/upstream-candidates/0002-…`,
      `tools/check_patches_apply.sh SuperMario64`, list it in `n64/SuperMario64/CLAUDE.md`.

## Notes / decisions

## Open questions

1. Fix shape: per-function statics (smallest diff) or an out-parameter the callers own (cleaner
   lifetime, touches every caller)? Recommendation: statics, with the two-results-live caveat
   handled by giving the dynamic and static lookups separate slots.
