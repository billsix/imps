# Reference: The scene graph — geo bytecode → typed node tree → layer buckets

> **Provenance:** authored 2026-09-06 against Ghostship pin `49c5312a`.
> Anchors in `src/engine/geo_layout.c`, `src/engine/graph_node.h`,
> `src/game/rendering_graph_node.c`. Part of the mario64 graphics set — map
> at [`README.md`](README.md). L1:
> [`scene-graph-and-data-structures-overview.md`](scene-graph-and-data-structures-overview.md).
> This is the **structural backbone** the `transformations.md`,
> `camera-system.md`, and `field-of-view-and-projection.md` docs all point
> back to.

## TL;DR

SM64's scene is a **tree of typed graph nodes** built by a **bytecode
interpreter**. A level/actor's layout is a "geo layout" program; a jump
table of command procs (`GeoLayoutJumpTable`, `geo_layout.c:13`) executes it
to construct the node tree (open/close-node commands nest it). Each node has
a **type** (camera, perspective, ortho, translation-rotation, scale, object,
display-list…) — `graph_node.h`. Each frame the renderer walks the tree
depth-first (`geo_process_node_and_siblings`) and, for drawable nodes,
appends their display lists into **per-layer buckets** emitted in order
(`geo_process_master_list_sub:149`). So: **bytecode builds the tree once;
the tree is traversed every frame into a bucketed display list.**

## 1. The geo-layout bytecode (`geo_layout.c:13`)

A geo layout is a little program; `GeoLayoutJumpTable[]` maps each opcode to
a handler:

```c
GeoLayoutCommandProc GeoLayoutJumpTable[] = {
    geo_layout_cmd_branch_and_link, geo_layout_cmd_end, geo_layout_cmd_branch,
    geo_layout_cmd_return, geo_layout_cmd_open_node, geo_layout_cmd_close_node,
    geo_layout_cmd_node_root, ...
};
```

`open_node`/`close_node` (`:18-19`) are the structural pair — they push/pop
the current parent, so the *nesting* of commands becomes the *nesting* of the
tree. This is one of **three bytecode VMs** in SM64 (the others drive levels
and behaviors — see `decomp-map.md`); this one builds the render tree.

## 2. Typed nodes (`graph_node.h`)

The tree is not homogeneous — each node is a **struct with a type tag**
(`GRAPH_NODE_TYPE_*`): camera, perspective, ortho-projection,
translation-rotation, scale, animated-part, billboard, display-list, switch,
and more. The renderer's traversal is a **dispatch on that type**: a
perspective node sets up projection (`field-of-view-and-projection.md`), a
transform node pushes onto the matrix stack (`transformations.md`), a
display-list node emits geometry. The node type *is* the scene-graph
vocabulary.

## 3. Traversal → layer buckets (`rendering_graph_node.c`)

`geo_process_node_and_siblings` (`:33`) walks the tree depth-first,
processing each node by type and recursing into children. Drawable nodes call
`geo_append_display_list` (`:193`), which files their display list into a
**`DisplayListNode` bucket per render layer** (`:150`). After the walk,
`geo_process_master_list_sub` (`:149`) emits the buckets in layer order (the
draw-order mechanism of `transparency-and-blending.md`). So the tree walk
*sorts* geometry into layers as a side effect of traversal.

## How this relates to the course

- **`modelviewprojection` has transform stacks but no scene graph** — its
  handful of objects are placed by explicit code, not organized into a
  traversable data structure. SM64 shows the real thing: a **typed tree** an
  engine builds and walks, where transforms, cameras, projections, and
  geometry are all *nodes*. This is the data-structure backbone the course's
  ad-hoc placement never needs but every engine has.
- **Two ideas the course lacks, both here:** (1) a **bytecode/VM** that
  *constructs* scene data (declarative layout compiled to a tree), and (2)
  **type-dispatched traversal** producing a bucketed, ordered command stream.
  Together they answer "how is a whole level organized for rendering?"
- **Backbone for the rest of the set:** transformations push on the stack
  *during this walk*; the camera and projection are *nodes in this tree*;
  transparency layers are *filled by this traversal*. Read this doc to see
  how those pieces are one structure.

## Candidate doc-region spans (for the later Sphinx pass — not yet added)

- `src/engine/geo_layout.c` around `GeoLayoutJumpTable` (`:13-28`): region
  `geo_layout_opcodes` — the bytecode → node-builder dispatch.
- `src/game/rendering_graph_node.c` around `geo_process_node_and_siblings`
  (`:33`): region `scene_graph_traversal` — depth-first type dispatch.
- `src/game/rendering_graph_node.c` around `geo_append_display_list`
  (`:193`) and `geo_process_master_list_sub` (`:149`): region
  `layer_bucketing` — traversal sorting geometry into layers.
