============
Introduction
============

What this book is
=================

A game engine is easiest to understand from the outside in: what does the
program *do*, in order, from the moment you launch it? Before GZDoom can render
a room in *Doom*, two problems have to be solved. First, the program has to come
up — parse its command line, initialize its subsystems — and reach the **main
loop**, the single ``for(;;)`` that will run until you quit. Second, it has to
figure out **which game you are playing and where its data lives**: *Doom* ships
its content in ``.wad`` files, and the engine has to identify one, then load its
thousands of named chunks (called *lumps*) into memory.

The first two chapters follow exactly those two problems; the next two then
follow one frame through the renderer, once the world is loaded and it is time to
draw:

- **Chapter 1 — From launch to the main loop.** The top-level entry point, the
  handoff into the game, and the loop itself (``src/d_main.cpp``).
- **Chapter 2 — IWADs, PWADs, and the lump filesystem.** How the engine
  recognizes a WAD by its contents, when it has to ask you which one to use, and
  how every WAD gets merged into one virtual filesystem
  (``src/d_iwad.cpp`` and ``src/common/filesystem/source/filesystem.cpp``).
- **Chapter 3 — The OpenGL renderer.** One 3D frame, from "render the world now"
  down to the single OpenGL draw call, and the shared-vs-backend split that
  decides *what* to draw vs *how*
  (``src/rendering/hwrenderer/`` + ``src/common/rendering/gl/``).
- **Chapter 4 — The Vulkan renderer.** The same frame down the other backend —
  recorded into a command buffer and submitted to the GPU — reusing Chapter 3's
  shared half (``src/common/rendering/vulkan/``).

A little vocabulary
===================

You will meet three terms constantly, so here they are up front:

**WAD**
    *Where's All the Data.* A single file bundling many named resources. Doom's
    maps, textures, sounds, and menus all live inside WADs.

**Lump**
    One named chunk inside a WAD — a texture, a sound, a map's geometry. The
    engine addresses everything by lump name, and the filesystem in Chapter 2 is
    what turns a name into bytes.

**IWAD vs PWAD**
    An **IWAD** (*internal* WAD) is a complete base game — ``doom2.wad``,
    ``heretic.wad``. A **PWAD** (*patch* WAD) is an add-on layered on top of an
    IWAD: a custom map, a mod. Exactly one IWAD, then any number of PWADs — the
    load order in Chapter 2 is what makes a PWAD *override* the base game.

How to read the code excerpts
=============================

Each excerpt is the actual GZDoom source at the pinned commit, spliced in by a
named region. When the text says *"see the loop below,"* the code below it is
that loop, verbatim from ``src/d_main.cpp`` — not a paraphrase. If GZDoom's
source moves, the excerpt moves with it, because the region is matched by name.
