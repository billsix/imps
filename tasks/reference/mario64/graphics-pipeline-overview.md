# Orientation (L1): The graphics pipeline — the mental model

> **Provenance:** Ghostship pin `49c5312a` / LUS `c151cc91`, 2026-09-06.
> **L1** (understand-without-code). Capsule (L0) in [`README.md`](README.md);
> full mechanism (L2) in [`graphics-pipeline.md`](graphics-pipeline.md).

Here is what happens to a frame, without any code.

The original game still speaks the N64's graphics language. Every frame, the
game code walks its scene and produces a **display list** — a sequence of
low-level drawing commands ("load this matrix," "here are these vertices,"
"use this texture," "combine colors this way," "draw these triangles") in
exactly the format the 1996 hardware expected. That is the front of the
pipeline, and it is unchanged from the cartridge.

The port intercepts that display list at a single well-known point and hands
it to a **translator** — the part called Fast3D. The translator's job is to
read the old N64 commands and re-express them in terms a modern graphics card
understands. It is not pretending to be the N64 chip cycle by cycle; it is
*translating* the intent. As it reads the list, it transforms and lights the
vertices, prepares the textures, and — the interesting part — decides which
**shader** to use.

That shader is not written by a person. The N64 had a little configurable
color-mixing unit (the "color combiner") that each material sets up
differently. The translator reads that configuration and **generates** a
matching shader program on the fly, caching it so the same material reuses
it. So where a graphics course hands you a vertex and a fragment shader you
typed yourself, this engine *manufactures* shaders from the old hardware's
mixing settings.

Finally, the translator doesn't talk to OpenGL or Vulkan directly. It talks
to a thin **backend interface**, and there is one implementation per graphics
API — OpenGL, Vulkan, Direct3D, Metal. That backend compiles the generated
shader, uploads the vertices, and issues the actual draw call to the GPU.
This one seam is why a single N64 game can run on four completely different
graphics systems: translate the old commands once, then let a small
per-API backend do the platform-specific work.

The whole journey, then, is: **old game speaks N64 → a translator converts
the commands and manufactures shaders → a per-GPU backend draws them.** And
because of the smooth-framerate trick (its own doc), that translated list is
actually drawn several times per game tick with slightly blended positions,
which is what turns 30-per-second game logic into a 60-or-more-per-second
picture. A course teaches the last third of this — the modern GPU pipeline —
in isolation; here you see the whole conveyor belt it sits at the end of.
