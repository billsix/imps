========================
Textures
========================

*Model View Projection* draws untextured triangles — it says up front that
texturing is out of scope. Every real game is covered in textures, so this is
pure new ground: what a texture *is*, how a coordinate picks a pixel out of it,
and what happens at the edges.

Formats: small, and oddly packed
=================================

The N64 stored textures in compact formats the port decodes to RGBA before
handing them to the GPU. The common one packs a pixel into 16 bits (five bits
each of red, green, blue, one of alpha). Others are greyscale-plus-alpha, or
**palettized**: the pixels are just indices into a small color table (a
palette), which is how a big image costs very little memory. The port has a
decoder per format; the reference note lists them all.

Coordinates and the edge: wrap, clamp, mirror
==============================================

A vertex carries a **texture coordinate** that says where in the image this
corner samples. The interesting question is what happens when a coordinate runs
off the edge of the image — past 1.0. The tile's addressing mode decides:

.. literalinclude:: ../../Ghostship/libultraship/src/fast/interpreter.cpp
   :language: c
   :start-after: // doc-region-begin tile_wrap_modes
   :end-before: // doc-region-end tile_wrap_modes
   :caption: clamp vs wrap vs mirror, per texture axis

``clamp`` sticks at the edge pixel; the default **wraps** (tiles the image);
``mirror`` flips it back and forth. These map straight onto the GPU sampler's
address modes — the same sampler that also decides whether to blend between
neighboring texels (smooth) or pick the nearest one (blocky), and whether to
blend between mip levels for distant surfaces. (That mip machinery, often
mis-called "RT64 mipmapping," is just texture level-of-detail — there is no ray
tracing here.)

.. graphviz::

   digraph tex {
     rankdir=LR;
     node [shape=box, fontname="sans-serif"];
     n64 [label="N64 texture\n(RGBA16 / CI+palette / IA)"];
     dec [label="decode → RGBA"];
     cache [label="cache\nby key", shape=cylinder];
     samp [label="sampler\n(filter + wrap + mip)"];
     px  [label="texel for\nthis pixel"];
     n64 -> dec -> cache -> samp -> px;
   }

Decoded textures are cached, so each one is converted once, not per frame — the
same "translate once, reuse" instinct as the generated shaders. And a texture
pack "looks great" because the loader will quietly swap a base texture for a
high-resolution one when a matching file exists, decoding the big version on a
background thread. Back on the :doc:`pipeline` map, this is part of what the
Fast3D interpreter box does before it draws.

.. admonition:: Go deeper
   :class: seealso

   Formats, palettes, tiles, sampling, and the HD-asset swap:
   ``tasks/reference/mario64/textures-and-texture-mapping.md``,
   ``sampling-and-mipmapping.md``, ``alternate-and-hd-assets.md``.
