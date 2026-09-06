# Orientation (L1): The scene graph — the mental model

> **Provenance:** Ghostship pin `49c5312a`, 2026-09-06. **L1**
> (understand-without-code). Capsule (L0) in [`README.md`](README.md);
> full mechanism (L2) in
> [`scene-graph-and-data-structures.md`](scene-graph-and-data-structures.md).

In a graphics course you place a few objects by writing a little code for
each: push a transform, draw a paddle, pop. That works for a handful of
things. A whole game level — hundreds of pieces, cameras, projections, nested
moving parts — needs a *data structure*, and SM64's is a **tree**.

Picture the scene as an outline. At the top is the root; under it hang
branches; under those, more branches, down to the leaves that are actual
geometry. Each entry in the outline is a **node with a kind**: this one is the
camera, this one sets up the perspective view, this one is a transform that
moves everything beneath it, this one is a piece of geometry to draw. The
tree's *shape* encodes the scene's *hierarchy*: a node's children are drawn in
the coordinate frame that node establishes, so putting Mario's hat under
Mario's head under Mario's body means the hat automatically follows.

That tree isn't typed in by hand. Each object and level ships a compact
**recipe** — a little program in a tiny instruction set — that says "open a
node here, add a transform, open a child, add this geometry, close, close."
An interpreter runs the recipe and builds the tree. This is the same idea as
a scene file or a prefab in a modern engine, just expressed as bytecode. (It
is one of three such little languages in SM64; the others script levels and
object behavior.)

Once the tree exists, rendering a frame is a **walk**. The renderer visits
each node in order, top to bottom, and does what the node's *kind* says: a
camera node establishes the view, a transform node composes onto the running
stack, a geometry node hands its triangles off to be drawn. Because the walk
follows the tree's nesting, transforms accumulate exactly along the hierarchy
— which is why the transform-composition doc and this one describe the same
motion from two angles.

One more thing happens during that walk. Rather than drawing geometry the
instant it's visited, the renderer *files* each piece into a **bucket by
render layer** — opaque here, transparent there — and draws the buckets in a
fixed order afterward. So the single tree walk does three jobs at once: it
applies the hierarchy of transforms, it sets up cameras and projections, and
it sorts everything into the right draw order.

The takeaway that reframes the course: placing objects with per-object code is
fine for a demo, but a real scene is a **typed tree built from a recipe and
traversed every frame**, and that traversal is where transforms, cameras,
and draw-order all actually happen. Almost every other doc in this set is
really describing one kind of node, or one thing that happens during this
walk.
