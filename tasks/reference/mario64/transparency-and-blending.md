# Reference: Transparency & blending — render layers and draw order

> **Provenance:** authored 2026-09-06 against Ghostship pin `49c5312a`.
> Anchors in `src/game/rendering_graph_node.c`. Part of the mario64
> graphics set — map at [`README.md`](README.md). Companions:
> `color-combiner-and-surface-shading.md` (the alpha value), `scene-graph-and-data-structures.md`
> (the buckets), `water-and-moving-textures.md` (a big alpha consumer).

## TL;DR

Transparency in SM64 is a **draw-order** problem solved with **render
layers**. The display list is bucketed into layers — opaque,
alpha-tested (decals), and true alpha-blended (transparent) — and the layers
are drawn in a fixed order so transparent things draw last, over the opaque
scene. The per-pixel alpha comes from the color combiner
(`color-combiner-and-surface-shading.md`); the *ordering* comes from the
master-list buckets built in `geo_process_master_list_sub`
(`rendering_graph_node.c:149`). There is no per-object depth sort — the
layer is the material's fixed declaration of "when do I draw."

## 1. Render layers = draw-order buckets

As the geo tree is walked, each display list is appended not to one stream
but to a **per-layer bucket** (`struct DisplayListNode`,
`rendering_graph_node.c:150`; `geo_append_display_list:193`). The layers
(N64 `LAYER_*`) run roughly: **opaque → opaque-decal → alpha-test →
transparent → transparent-decal**. `geo_process_master_list_sub` (`:149`)
then emits the buckets **in layer order**, so:

- opaque geometry lays down the depth buffer first;
- transparent geometry draws afterward, blending over what's there.

A material picks its layer once; that is its whole participation in
transparency ordering. This is the pragmatic answer to "how do I draw glass
over a wall" without sorting every triangle each frame.

## 2. The blend itself

For an alpha-blended layer, the combiner produces an alpha per pixel
(`(A−B)·C+D` on the alpha channel — `color-combiner-and-surface-shading.md`),
and the RDP blender mixes the pixel with the framebuffer by that alpha
(`out = src·a + dst·(1−a)`). Alpha-*test* layers instead use alpha as a
hard cutoff (draw or discard) so they need no ordering care — decals, foliage
edges, HUD icons. So "transparency" is really two mechanisms: **blend**
(needs order) and **test** (doesn't).

## 3. The known failure mode: no per-pixel sort

Because ordering is by fixed layer, two overlapping *transparent* surfaces in
the same layer can draw in the wrong order and show a seam — the classic N64
"transparency sorting" artifact. SM64 avoids it by construction (few
overlapping transparents) rather than by solving it, which is itself a
teaching point about the cost the layer scheme trades away.

## How this relates to the course

- **`modelviewprojection` has no transparency at all** — no `GL_BLEND`, no
  alpha, everything opaque. So the whole idea that *draw order matters once
  things are see-through* is a gap-fill. It pairs naturally with the depth
  buffer the course *does* teach (ch15): the depth buffer handles opaque
  occlusion for free, but transparency defeats it, which is exactly why
  layers/order are needed.
- **A concrete "the pipeline has state and order" lesson:** the course's
  triangles are order-independent; here the render *layer* is a first-class
  material property precisely because blending is not commutative.
- **Gap filled:** alpha blending vs. alpha testing, render layers, draw
  order, and the sorting artifact — the practical machinery of see-through
  surfaces the course omits.

## Candidate doc-region spans (for the later Sphinx pass — not yet added)

- `src/game/rendering_graph_node.c` around `geo_process_master_list_sub`
  (`:149`): region `render_layer_buckets` — emitting buckets in layer order.
- `src/game/rendering_graph_node.c` around `geo_append_display_list`
  (`:193`): region `append_to_layer` — how a DL joins its layer bucket.
