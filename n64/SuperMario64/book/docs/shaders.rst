=====================================
Shaders you never wrote
=====================================

In *Model View Projection* you write a shader: a little program that runs on
the GPU for every pixel, which you type out and hand to the driver. Super
Mario 64's port does something that sounds impossible at first — **nobody
writes its shaders.** They are manufactured while the game runs. Understanding
why is the clearest window into how old fixed-function hardware meets a modern
GPU.

The N64 had a color combiner, not shaders
=========================================

The N64 could not run arbitrary pixel programs. It had a small fixed unit —
the **color combiner** — that each material *configured*. Per stage it computes
one formula, for the red/green/blue and for the alpha:

.. code-block:: text

    out = (A - B) * C + D

where A, B, C, D are each *selected* from a small menu of inputs: a texture
sample, the per-vertex lit color, a couple of material colors, the constants 0
and 1. That is the whole expressive budget of a 1996 pixel: one multiply-add
over chosen inputs, once or twice.

Turning the combiner into a real shader
=======================================

A modern GPU only runs shader programs, so the port bridges the gap by
**generating** a shader that computes the same formula. The heart of it is a
lookup that turns each combiner input into a GLSL expression:

.. literalinclude:: ../../Ghostship/libultraship/src/fast/backends/gfx_opengl.cpp
   :language: c
   :start-after: // doc-region-begin combiner_input_to_glsl
   :end-before: // doc-region-end combiner_input_to_glsl
   :caption: each combiner input becomes a piece of GLSL

Read it: the constant 0 becomes ``vec3(0.0, 0.0, 0.0)``, a material input
becomes ``uInputs[...]``, and (further down the same table) a texture sample
becomes ``texVal0`` and the per-vertex lit color becomes ``vShade``. The
generator assembles these into the ``(A - B) * C + D`` line, and the material's
whole shader is built, compiled, and **cached** so it is made only once.

.. graphviz::

   digraph shadergen {
     rankdir=LR;
     node [shape=box, fontname="sans-serif"];
     mode [label="combine mode\n(A,B,C,D per stage)"];
     gen  [label="generate GLSL\n(input → expression)"];
     comp [label="compile\nGLSL (GL) / SPIR-V (Vulkan)"];
     cache[label="cache\nby material", shape=cylinder];
     mode -> gen -> comp -> cache;
   }

For OpenGL the generated source is GLSL, compiled by the driver; for Vulkan the
same source is compiled ahead of time to SPIR-V. Same idea, two output forms
for two GPUs — which is why one game runs on both. And notice the division of
labor: the **lighting** was already computed per vertex and arrives as
``vShade`` (that is the next chapter); the generated shader mostly *mixes* that
lit color with textures and tints.

So "the programmable pipeline" you learned by hand-writing shaders has another
answer to *where shaders come from*: a code generator, translating 1996
material settings into modern GPU code. Back to the :doc:`pipeline` map, this is
the inside of the "Fast3D interpreter" box.

.. admonition:: Go deeper
   :class: seealso

   The combiner formula, its inputs, and the generate/compile/cache path in
   full: ``tasks/reference/mario64/color-combiner-and-surface-shading.md`` and
   ``shaders-and-gpu.md``.
