========================================
One frame's journey (the big picture)
========================================

This chapter is the map the rest of the book fills in. It follows a **single
frame** from the game's logic all the way to pixels, at arm's length — a black
box. Each stage links to the chapter that opens it up. Read this to hold the
whole shape in your head; click through when you want the inside of a box.

The whole path
==============

.. graphviz::

   digraph frame {
     rankdir=TB;
     node [shape=box, fontname="sans-serif"];
     logic  [label="game logic (30 Hz)\nwalks the scene tree"];
     dl     [label="one N64 display list\n(Gfx commands)"];
     seam   [label="exec_display_list\n→ ProcessGfxCommands"];
     replay [label="replay N times\nwith interpolated matrices"];
     interp [label="Fast3D interpreter\ndecodes commands"];
     gpu    [label="GPU backend\n(OpenGL / Vulkan)"];
     pixels [label="pixels"];
     logic -> dl -> seam -> replay -> interp -> gpu -> pixels;
   }

Stage by stage (black box)
==========================

**Game logic builds one display list.** Thirty times a second the game walks
its scene tree, and each node contributes drawing commands — set this matrix,
draw these triangles — in the exact format the 1996 hardware expected. The tree
walk, the transforms it composes, the camera and projection nodes it sets up:
that is :doc:`engine-math`, :doc:`camera`, and :doc:`projection`.

**The port intercepts the list at one seam.** The decomp still calls the N64
function ``exec_display_list``; the port redefines it to forward the list to its
own renderer. This single function is the entire N64-to-PC handoff:

.. literalinclude:: ../../Ghostship/src/port/Game.cpp
   :language: c
   :start-after: // doc-region-begin graphics_seam
   :end-before: // doc-region-end graphics_seam
   :caption: exec_display_list — the one seam

.. admonition:: Try breaking it
   :class: caution

   Comment out the one line inside ``exec_display_list`` — the
   ``ProcessGfxCommands`` call above. Rebuild and run. The game still works:
   logic ticks, music plays, the controller responds. But the screen is
   **black**, because nothing is ever handed to the renderer. You just did to
   the graphics what commenting out the ``exec`` system call does to a shell —
   everything is set up and ready, and then nothing is actually handed off to
   happen. One line is the whole difference between "a running game" and "a
   running game you can see."

**The list is replayed several times per frame.** The game thinks at 30 Hz, but
we want 60 or more. Rather than run the game faster, the port draws the *same*
list several times with matrices blended between the last frame and this one:

.. literalinclude:: ../../Ghostship/src/port/Engine.cpp
   :language: c
   :start-after: // doc-region-begin replay_loop
   :end-before: // doc-region-end replay_loop
   :caption: ProcessGfxCommands — draw the frame N times, interpolated

That smooth-motion trick gets its own chapter later; for now, note only that one
game tick becomes several rendered frames.

**The interpreter translates, and the GPU draws.** Each replay runs the Fast3D
interpreter, which reads the N64 commands and re-expresses them for a modern
graphics card — transforming and lighting vertices, preparing textures, and
**generating a shader** for each material — then hands triangles to a per-GPU
backend (OpenGL or Vulkan). Those boxes open up in the chapters on shaders,
textures, and lighting.

Why a translator, not an emulator
=================================

Fast3D does not pretend to be the N64 chip cycle by cycle. It **translates**
the intent of the old commands into modern GPU work, caching what it can (shaders
by material, decoded textures). That one idea — translate once, target many GPUs
— is why a single 1996 game runs on four graphics APIs. The chapters ahead are
just the insides of these boxes.

.. admonition:: Go deeper
   :class: seealso

   The exhaustive pipeline walk and the frame-interpolation mechanism:
   ``tasks/reference/mario64/graphics-pipeline.md`` and
   ``frame-interpolation.md``.
