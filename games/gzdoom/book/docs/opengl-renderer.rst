===================
The OpenGL renderer
===================

The first two chapters got the engine on its feet: it came up, entered its main
loop, and loaded the game's data. Now for the question the whole thing exists to
answer — *how does a room in Doom become pixels on the screen?* This chapter
follows one frame of the 3D view from "render the world now" down to the single
OpenGL call that actually puts triangles on the glass.

One renderer, two graphics cards' worth of API
==============================================

Two ideas have to be separated before any of the code makes sense.

The first is **hardware rendering**. The 1993 engine drew every pixel with the
CPU, one at a time, in software. GZDoom can still do that, but by default it
hands the work to your **graphics card (GPU)** instead: it describes the scene as
lists of triangles and lets the hardware fill them. Everything in this chapter is
that hardware path. (The software renderer is still in the tree; you will see the
engine choose between them in a moment.)

The second is that there is more than one way to *talk* to a GPU. **OpenGL** and
**Vulkan** are two different APIs — two different vocabularies for saying "bind
this texture, draw these triangles." GZDoom supports both. Writing the entire
renderer twice would be madness, so it is split into two halves:

- a **shared hardware renderer** that decides *what* to draw — it walks the map,
  works out what the camera can see, and groups those surfaces into lists; and
- a thin **backend**, one per API, that turns those decisions into *how* — the
  actual OpenGL (or Vulkan) calls.

The happy consequence for you as a reader: most of this chapter is the *shared*
half. When you later meet the Vulkan chapter, only the last two sections change —
you will already understand the rest. So keep a mental note, as we go, of which
side of the line each piece of code sits on. The shared half lives under
``src/rendering/hwrenderer/``; the OpenGL backend lives under
``src/common/rendering/gl/``.

The seam between "what" and "how"
=================================

Start at the line that *is* the boundary. The shared code never mentions OpenGL.
Instead it holds a **render state** — an object that carries the current drawing
settings (color, texture, blend mode, the camera matrices) and exposes a handful
of drawing commands. That object is abstract: it declares *what* commands exist
but supplies no bodies for them.

.. literalinclude:: ../../checkout/gzdoom/src/common/rendering/hwrenderer/data/hw_renderstate.h
   :language: cpp
   :start-after: // doc-region-begin renderstate_draw_api
   :end-before: // doc-region-end renderstate_draw_api
   :caption: the API-neutral draw interface — src/common/rendering/hwrenderer/data/hw_renderstate.h (FRenderState)

The ``= 0`` on each line makes it a *pure virtual* function — C++ for "there is no
implementation here; every concrete render state must provide its own." OpenGL
provides one class, ``FGLRenderState``; Vulkan provides another. When the shared
code calls ``state.Draw(...)``, C++ dispatches to whichever backend is actually
running. That single ``virtual void Draw(...) = 0;`` is the whole GL/Vulkan
seam. Above it, nothing knows which graphics API exists; below it, the two
backends diverge completely.

One term to fix now: a **draw call** is one command to the GPU that says "draw
these ``count`` vertices, starting at this index." A frame is thousands of them.
``Draw`` (a list of vertices) and ``DrawIndexed`` (vertices addressed through an
index buffer, so shared corners are stored once) are the two flavors.

Rendering one viewpoint
=======================

Now back up to where the 3D view begins. Each pass through the main loop from
Chapter 1 eventually calls ``RenderView`` in
``src/rendering/hwrenderer/hw_entrypoint.cpp``. Its very first decision is the
software-versus-hardware fork we mentioned: ``if (!V_IsHardwareRenderer())`` hands
off to the old CPU renderer; otherwise control continues down the hardware path
this chapter follows.

Notice, too, that a single frame is not necessarily a single view. Before the
main view, ``RenderView`` loops over every *camera texture* (a security-monitor
screen, a mirror) and renders each as its own view into a texture. A stereo-3D
mode renders the scene once per eye. The unit of work, then, is not "a frame" but
"a **viewpoint**," and each one runs through ``RenderViewpoint``. Here is its
core:

.. literalinclude:: ../../checkout/gzdoom/src/rendering/hwrenderer/hw_entrypoint.cpp
   :language: cpp
   :start-after: // doc-region-begin render_one_viewpoint
   :end-before: // doc-region-end render_one_viewpoint
   :caption: setting up one viewpoint — src/rendering/hwrenderer/hw_entrypoint.cpp (RenderViewpoint)

Read it as a checklist for one camera. ``StartDrawInfo`` allocates an
``HWDrawInfo`` — think of it as a scratchpad that will collect everything about
drawing this view. ``Set3DViewport`` fixes the rectangle on screen we are drawing
into. Then the two lines that matter most:

- ``VPUniforms.mProjectionMatrix = eye.GetProjection(...)`` computes the
  **projection** — the transformation that squashes the 3D world onto your flat
  2D screen, so that distant things get smaller. It is just a function from world
  space to screen space; the engine will hand it to the GPU later so every vertex
  is transformed the same way.
- ``SetupView`` positions and aims that function at the player's eye.

With the camera set up, ``ProcessScene`` does the actual work. Everything above
was preparation; the drawing happens inside that one call.

One view = build a list, then draw it
=====================================

``ProcessScene`` is short enough to read whole:

.. literalinclude:: ../../checkout/gzdoom/src/rendering/hwrenderer/scene/hw_drawinfo.cpp
   :language: cpp
   :start-after: // doc-region-begin process_scene
   :end-before: // doc-region-end process_scene
   :caption: HWDrawInfo::ProcessScene — src/rendering/hwrenderer/scene/hw_drawinfo.cpp

It works out which section of the map the camera is standing in and calls
``DrawScene``. And ``DrawScene`` is where the single most important structure of
the whole renderer shows itself — **two phases**: first *build* a description of
what to draw, then *submit* it.

.. literalinclude:: ../../checkout/gzdoom/src/rendering/hwrenderer/scene/hw_drawinfo.cpp
   :language: cpp
   :start-after: // doc-region-begin draw_scene
   :end-before: // doc-region-end draw_scene
   :caption: HWDrawInfo::DrawScene — the build/submit split — src/rendering/hwrenderer/scene/hw_drawinfo.cpp

``CreateScene`` is the build phase: it figures out what is visible and files each
surface into a **draw list** — a bucket of similar things to draw (all the plain
walls in one, all the translucent things in another). ``RenderScene`` is the
submit phase: it walks those buckets and issues the draw calls. The portal and
``RenderTranslucent`` lines around them are the same two ideas applied again to
special cases. Hold onto the split — build, then submit — because the next two
sections are simply those two phases in detail.

The build phase: walking the map
================================

.. literalinclude:: ../../checkout/gzdoom/src/rendering/hwrenderer/scene/hw_drawinfo.cpp
   :language: cpp
   :start-after: // doc-region-begin create_scene
   :end-before: // doc-region-end create_scene
   :caption: HWDrawInfo::CreateScene — src/rendering/hwrenderer/scene/hw_drawinfo.cpp

The heart of this is ``RenderBSP(Level->HeadNode(), ...)``. A Doom level is stored
as a **BSP tree** (Binary Space Partition) — a carving of the map, computed ahead
of time, that lets the engine visit exactly the surfaces the camera might see, in
front-to-back order, without ever considering the whole level. As ``RenderBSP``
walks the tree it drops each wall, floor, and sprite into the appropriate draw
list. The rest of the function is honest about reality: after the clean tree walk
come "the crappy hacks that have to be done to avoid rendering anomalies" —
missing textures, deep-water tricks — special cases that a real game accumulates
over thirty years.

Two lines bracket the walk and deserve a name. ``screen->mVertexData->Map()`` and
its matching ``Unmap()`` open and close a window directly into GPU memory. A
**vertex buffer** is a slab of memory on the graphics card holding the raw
triangle corners; ``Map`` hands the CPU a pointer into it, the walk writes each
surface's vertices straight in, and ``Unmap`` gives it back to the GPU. So the
build phase is not just making a to-do list — it is streaming the actual geometry
onto the card, ready to be drawn.

Nothing has been drawn yet. ``CreateScene`` only *decides and records*.

The submit phase: replaying the lists
=====================================

.. literalinclude:: ../../checkout/gzdoom/src/rendering/hwrenderer/scene/hw_drawinfo.cpp
   :language: cpp
   :start-after: // doc-region-begin render_scene
   :end-before: // doc-region-end render_scene
   :caption: HWDrawInfo::RenderScene — src/rendering/hwrenderer/scene/hw_drawinfo.cpp

Now the buckets get drawn, and the *order* is deliberate. Solid geometry goes
first (``GLDL_PLAINWALLS``, ``GLDL_PLAINFLATS``), then **masked** geometry —
textures with see-through holes, like a chain-link fence, where an alpha test
keeps or discards each pixel — then models, then decals. Solid-before-transparent
is not an aesthetic choice: drawing the opaque world first fills the **depth
buffer** (the GPU's per-pixel record of how far away the nearest thing drawn so
far is), which lets the hardware cheaply throw away pixels that are hidden behind
walls. Genuinely translucent surfaces, which must *blend* with whatever is behind
them, are held back to a later pass (``RenderTranslucent``) precisely because they
need the rest of the scene already sitting in the frame.

The line to watch is the type of ``state``: every ``DrawWalls`` /  ``DrawFlats`` /
``Draw`` call takes an ``FRenderState &`` — the abstract interface from the second
section. This whole function issues drawing commands *without knowing whether it
is driving OpenGL or Vulkan*. This is the shared half doing its last useful work
before the seam. The next section is where we cross it.

Crossing into OpenGL
====================

When ``RenderScene`` calls ``state.Draw(...)`` and ``state`` is really an
``FGLRenderState``, this is the code that runs:

.. literalinclude:: ../../checkout/gzdoom/src/common/rendering/gl/gl_renderstate.cpp
   :language: cpp
   :start-after: // doc-region-begin gl_draw
   :end-before: // doc-region-end gl_draw
   :caption: FGLRenderState::Draw — src/common/rendering/gl/gl_renderstate.cpp

There it is — ``glDrawArrays``, a real OpenGL function, the moment the triangles
are handed to the driver. ``dt2gl`` is a tiny translation table turning GZDoom's
notion of a primitive ("triangle fan", "triangle strip") into the matching GL
constant. Everything this book has built toward funnels through this one line,
thousands of times a frame.

But look at what happens *first*: ``Apply()``.

.. literalinclude:: ../../checkout/gzdoom/src/common/rendering/gl/gl_renderstate.cpp
   :language: cpp
   :start-after: // doc-region-begin gl_apply
   :end-before: // doc-region-end gl_apply
   :caption: FGLRenderState::Apply — src/common/rendering/gl/gl_renderstate.cpp

OpenGL is a **state machine**: it has exactly one "current texture," one "current
blend mode," one "current shader program" at a time. You do not pass those to a
draw call; you *set* the machine's state, then draw, and the draw uses whatever
the state currently is. So before each draw ``Apply`` reconciles three groups of
state to match what the current surface wants:

- ``ApplyState`` turns GZDoom's render style into real GL switches —
  ``glBlendFunc``, ``glEnable(GL_POLYGON_OFFSET_FILL)``, depth settings.
- ``ApplyBuffers`` binds the vertex buffer that the *build* phase filled, so the
  draw pulls from the right geometry.
- ``ApplyShader`` chooses and binds the GPU program and uploads its inputs.

That last one is where **shaders** enter. A shader is a small program that runs on
the GPU — one (the *vertex* shader) transforms each corner, another (the
*fragment* shader) colors each pixel. GZDoom's are written in GLSL and live in the
tree at ``wadsrc/static/shaders/glsl/main.vp`` and ``main.fp``; they are compiled
and linked when the renderer starts (``src/common/rendering/gl/gl_shader.cpp``).
``ApplyShader`` (in this same file) picks the right compiled program, binds it
with ``glUseProgram``, and pushes the current render state into its **uniforms** —
its read-only inputs: the fog color, the light level, and the projection and model
matrices computed all the way back in ``RenderViewpoint``. That is how the camera
math from the third section finally reaches the GPU.

So a single item's draw is really: *make OpenGL's state describe this surface,
then fire one* ``glDrawArrays``. Repeat for every wall, floor, and sprite in every
list.

Ending the frame
================

The scene has been drawn — but not to anything the player can see yet. It went to
a hidden *back buffer*. Closing out the frame is the backend's last job:

.. literalinclude:: ../../checkout/gzdoom/src/common/rendering/gl/gl_framebuffer.cpp
   :language: cpp
   :start-after: // doc-region-begin gl_frame_update
   :end-before: // doc-region-end gl_frame_update
   :caption: OpenGLFrameBuffer::Update — src/common/rendering/gl/gl_framebuffer.cpp

``GLRenderer->Flush()`` pushes out any remaining queued 2D drawing (the HUD, the
menus), and ``Swap()`` performs the **buffer swap**: the GPU keeps two full-screen
images, a front one being displayed and a back one being drawn, and the swap flips
them in a single instant. The player therefore never sees a half-drawn frame — the
picture appears complete or not at all. This ``Update`` is called once per turn of
the ``D_DoomLoop`` from Chapter 1; it is the far end of that loop's ``D_Display``
step.

The whole thread
================

Put it together and one frame of the 3D view is a straight line from the loop to
the glass:

.. graphviz::

   digraph render {
     rankdir=TB;
     node [shape=box, fontname="sans-serif"];

     subgraph cluster_shared {
       label="shared hardware renderer  (also feeds Vulkan)";
       style=filled; fillcolor="#f2f2f2"; fontname="sans-serif";
       loop  [label="D_DoomLoop -> D_Display\n(Chapter 1)"];
       rv    [label="RenderView\n(software-vs-hardware fork,\ncamera textures, eyes)"];
       rvp   [label="RenderViewpoint\n(projection matrix, camera)"];
       proc  [label="ProcessScene -> DrawScene"];
       build [label="CreateScene  (BUILD)\nwalk the BSP -> fill draw lists,\nstream vertices into the GPU buffer"];
       sub   [label="RenderScene  (SUBMIT)\nsolid -> masked -> models -> translucent"];
       api   [label="FRenderState::Draw(...)\nthe API-neutral seam", style=filled, fillcolor="#ffe8c0"];
       loop -> rv -> rvp -> proc -> build -> sub -> api;
     }

     subgraph cluster_gl {
       label="OpenGL backend  (src/common/rendering/gl/)";
       style=filled; fillcolor="#e6f0ff"; fontname="sans-serif";
       apply [label="FGLRenderState::Apply\nreconcile GL state:\nblend, buffers, shader+uniforms"];
       draw  [label="glDrawArrays", style=filled, fillcolor="#d0ffd0"];
       swap  [label="OpenGLFrameBuffer::Update\nFlush 2D -> Swap (buffer swap)"];
       apply -> draw -> swap;
     }

     api -> apply [label="virtual dispatch\n(GL, not Vulkan)"];
   }

The one thing to carry away is the seam. Everything from ``RenderView`` down to
``FRenderState::Draw`` is shared: it decides *what* to draw and never names a
graphics API. Only the blue box — ``Apply``, ``glDrawArrays``, the buffer swap —
is OpenGL. Swap OpenGL for Vulkan and the top of the diagram does not change; only
the bottom does. That is the whole reason the renderer is built in two halves, and
it is why the next chapter, on the Vulkan backend, can start most of the way up
this same picture.
