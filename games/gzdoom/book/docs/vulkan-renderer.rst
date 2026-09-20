===================
The Vulkan renderer
===================

The last chapter followed one frame down the **OpenGL** backend. This chapter
follows the same frame down the **Vulkan** one — and the good news promised
earlier now pays off: almost everything above the seam is unchanged, so this is
a short chapter about the part that differs.

Recall the shape from the OpenGL chapter. A **shared hardware renderer** walks
the map, decides *what* to draw, and issues its drawing commands through an
abstract **render state** — an object with pure-virtual ``Draw`` / ``DrawIndexed``
commands and no bodies. That abstract object *is* the seam. OpenGL supplied one
concrete implementation, ``FGLRenderState``. Vulkan supplies another,
``VkRenderState``. Everything from ``RenderView`` down to
``FRenderState::Draw`` — the BSP walk, the draw lists, the opaque-before-
translucent pass order — runs exactly as before, naming no graphics API. So we
start at the seam and go down.

One term up front. **Vulkan** is a newer, lower-level graphics API than OpenGL.
Where OpenGL hides the graphics card behind a friendly state machine and a driver
that guesses what you meant, Vulkan hands you the raw machinery and asks you to
drive it yourself: you *record* commands into a buffer, *pre-build* the objects
that describe how to draw, and *synchronize* the GPU by hand. More work, more
control, fewer surprises. That single difference — explicit instead of
implicit — explains every contrast in this chapter.

The same seam, a different servant
==================================

When ``RenderScene`` calls ``state.Draw(...)`` and ``state`` is really a
``VkRenderState``, this is the code that runs:

.. literalinclude:: ../../checkout/gzdoom/src/common/rendering/vulkan/renderer/vk_renderstate.cpp
   :language: cpp
   :start-after: // doc-region-begin vk_draw
   :end-before: // doc-region-end vk_draw
   :caption: VkRenderState::Draw — src/common/rendering/vulkan/renderer/vk_renderstate.cpp

Put it beside the OpenGL version and the shape is identical: reconcile state
(``Apply``), then draw. But look at the last line. OpenGL's ``Draw`` ended in
``glDrawArrays`` — a call that reaches the driver and draws *now*. Vulkan's ends
in ``mCommandBuffer->draw(...)``, which is ``vkCmdDraw`` under the hood, and it
draws **nothing yet**. It *records* "draw these vertices" into a **command
buffer** — a list of GPU instructions being written down for later. The GPU is
not even listening at this moment. This is the heart of the difference: OpenGL
*does*, Vulkan *records*.

Recording, not doing
====================

Where does that command buffer come from? GZDoom opens one lazily, the first
time something needs to be recorded this frame:

.. literalinclude:: ../../checkout/gzdoom/src/common/rendering/vulkan/system/vk_commandbuffer.cpp
   :language: cpp
   :start-after: // doc-region-begin vk_get_draw_commands
   :end-before: // doc-region-end vk_get_draw_commands
   :caption: VkCommandBufferManager::GetDrawCommands — src/common/rendering/vulkan/system/vk_commandbuffer.cpp

``createBuffer()`` allocates a fresh command buffer and ``begin()`` opens it for
recording; every ``draw`` from then on appends to it. Think of the whole frame as
writing a to-do list for the GPU — hundreds or thousands of "bind this, draw
that" entries — which is handed over, all at once, only at the end of the frame.
Nothing on that list executes until then.

Apply, the Vulkan way
=====================

Just like the OpenGL backend, each draw is preceded by an ``Apply`` that makes the
recorded state match what the current surface needs:

.. literalinclude:: ../../checkout/gzdoom/src/common/rendering/vulkan/renderer/vk_renderstate.cpp
   :language: cpp
   :start-after: // doc-region-begin vk_apply
   :end-before: // doc-region-end vk_apply
   :caption: VkRenderState::Apply — src/common/rendering/vulkan/renderer/vk_renderstate.cpp

It reads as a checklist, and most entries have an obvious OpenGL counterpart:
``ApplyMatrices`` and ``ApplyPushConstants`` push the camera math and per-draw
constants; ``ApplyVertexBuffers`` points the draw at its geometry; ``ApplyMaterial``
supplies the textures. The one that has no OpenGL analogue, and carries the whole
Vulkan idea, is ``ApplyRenderPass``.

One object for all the state: the pipeline
==========================================

In OpenGL, ``Apply`` set each piece of fixed-function state with its own call —
``glBlendFunc`` for blending, ``glEnable(GL_POLYGON_OFFSET_FILL)`` for depth bias,
and so on — because OpenGL is a state machine you nudge one knob at a time. Vulkan
refuses that. It requires you to bundle *all* of that state — blend mode, depth
test, stencil, cull mode, which shader, the vertex layout — into a single
immutable object called a **pipeline** (``VkPipeline``), built up front. You do
not tweak a pipeline; you pick the one you want and bind it. So ``ApplyRenderPass``
is not a series of state pokes — it is a *lookup*:

.. literalinclude:: ../../checkout/gzdoom/src/common/rendering/vulkan/renderer/vk_renderstate.cpp
   :language: cpp
   :start-after: // doc-region-begin vk_apply_renderpass
   :end-before: // doc-region-end vk_apply_renderpass
   :caption: VkRenderState::ApplyRenderPass — src/common/rendering/vulkan/renderer/vk_renderstate.cpp

The first two-thirds of the function fills in a ``VkPipelineKey`` — a little struct
that names every piece of state a pipeline bakes in (``DepthTest``, ``StencilOp``,
``ColorMask``, ``CullMode``, the shader ``EffectState``, the vertex format…). That
key is then used to *find* a matching pre-built pipeline:
``mPassSetup->GetPipeline(pipelineKey)``. GZDoom builds these pipelines on demand
and keeps them in a cache keyed by exactly this struct, so the same combination of
state is compiled once and reused for the rest of the run. The two closing lines
do the real work: if the needed pipeline differs from the one already bound
(``changingPipeline``), record a ``bindPipeline`` into the command buffer. That one
bind replaces the whole handful of ``glEnable``/``glBlendFunc`` calls the OpenGL
backend made.

Two supporting ideas ride along, both the Vulkan face of things the OpenGL chapter
already met. A **descriptor set** is Vulkan's way of handing a shader its textures
and buffers — the role OpenGL filled by binding a texture and setting uniforms;
``Apply`` binds those a few lines further down (``ApplyMaterial`` /
``ApplyHWBufferSet``). And **push constants** are a small block of values sent
straight to the shader with the draw — GZDoom uses them for the fast-changing
per-draw data — recorded by ``ApplyPushConstants``. Both are recorded into the
command buffer, like everything else; none of it has run yet.

Ending the frame: submit and present
=====================================

The scene has been *recorded* but not *executed*. Turning the recorded list into
pixels is the frame-end job, and — as in the OpenGL chapter — it hangs off the
framebuffer's ``Update``, called once per turn of ``D_DoomLoop`` from Chapter 1:

.. literalinclude:: ../../checkout/gzdoom/src/common/rendering/vulkan/system/vk_renderdevice.cpp
   :language: cpp
   :start-after: // doc-region-begin vk_frame_update
   :end-before: // doc-region-end vk_frame_update
   :caption: VulkanRenderDevice::Update — src/common/rendering/vulkan/system/vk_renderdevice.cpp

``Draw2D`` records the HUD and menus (still just recording), ``EndRenderPass``
closes the recording, and then ``WaitForCommands(true)`` is where the whole frame
finally reaches the GPU:

.. literalinclude:: ../../checkout/gzdoom/src/common/rendering/vulkan/system/vk_commandbuffer.cpp
   :language: cpp
   :start-after: // doc-region-begin vk_wait_for_commands
   :end-before: // doc-region-end vk_wait_for_commands
   :caption: VkCommandBufferManager::WaitForCommands — src/common/rendering/vulkan/system/vk_commandbuffer.cpp

Three steps, in order:

- ``AcquireImage()`` asks the **swapchain** — Vulkan's set of full-screen images
  that take turns being shown — for the next image to draw into.
- ``FlushCommands(...)`` ends the command buffer and **submits** it to the
  graphics **queue** (``submit.Execute(... GraphicsQueue ...)`` inside it). *This*
  is the moment the recorded list is handed to the GPU and actually executes —
  every ``vkCmdDraw`` from the whole frame, run in one go.
- ``QueuePresent()`` puts the finished image on screen — the Vulkan equivalent of
  OpenGL's buffer swap.

Two Vulkan-only words appear in the submit: **semaphore** and **fence**. Both are
synchronization tools, and Vulkan makes you place them by hand where OpenGL's
driver did it for you. A *semaphore* makes the GPU wait for one step before
starting another (don't present the image until drawing into it has finished); a
*fence* lets the CPU wait for the GPU (``vkWaitForFences`` — don't start reusing a
command buffer the GPU is still running). They are the price of the explicit
control: the driver will not guess the ordering, so the engine states it.

The whole thread
================

Lay it next to the OpenGL diagram and the top half is the *same picture* — the
shared renderer, ending at the seam. Only the bottom, the backend, is Vulkan:

.. graphviz::

   digraph vkrender {
     rankdir=TB;
     node [shape=box, fontname="sans-serif"];

     subgraph cluster_shared {
       label="shared hardware renderer  (unchanged from the OpenGL chapter)";
       style=filled; fillcolor="#f2f2f2"; fontname="sans-serif";
       shared [label="RenderView -> ... -> RenderScene\n(walk BSP, build draw lists,\nsolid -> masked -> translucent)"];
       api    [label="FRenderState::Draw(...)\nthe API-neutral seam", style=filled, fillcolor="#ffe8c0"];
       shared -> api;
     }

     subgraph cluster_vk {
       label="Vulkan backend  (src/common/rendering/vulkan/)";
       style=filled; fillcolor="#e6ffe6"; fontname="sans-serif";
       apply [label="VkRenderState::Apply\nApplyRenderPass: pick + bind a\nprebuilt VkPipeline (by pipeline key)"];
       rec   [label="mCommandBuffer->draw = vkCmdDraw\nRECORD into the command buffer\n(nothing runs yet)", style=filled, fillcolor="#d0ffd0"];
       upd   [label="VulkanRenderDevice::Update\n(end of a D_DoomLoop turn)"];
       wait  [label="WaitForCommands\nAcquireImage -> submit to the queue\n(runs the whole list) -> QueuePresent"];
       apply -> rec -> upd -> wait;
     }

     api -> apply [label="virtual dispatch\n(Vulkan, not GL)"];
   }

The one thing to carry away is the contrast with the last chapter, and it is a
single word: *when*. The OpenGL backend **did** the work at each ``Draw`` —
``glDrawArrays`` drew immediately. The Vulkan backend **records** every ``Draw``
into a command buffer and does nothing until the end of the frame, when
``WaitForCommands`` submits the whole list to the GPU at once and presents the
result. Same scene, same seam, same draw order decided up above — a different
bargain with the hardware underneath.
