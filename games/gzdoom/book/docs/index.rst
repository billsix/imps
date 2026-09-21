########################
How a Doom Engine Works
########################

*Reading GZDoom's source to learn how a real game engine starts up, finds its
data, and runs.*

`GZDoom <https://github.com/ZDoom/gzdoom>`_ is the widely-used open-source
source port of *Doom* (the ZDoom family): it runs the original id games and the
enormous ecosystem of add-on WADs, with a modern renderer and a scripting
language on top of the 1993 engine's bones. It is a large, living C++ codebase —
a good place to see how the pieces of a shipping game engine actually fit
together, rather than a toy.

This book reads that source directly. Every piece of code shown is pulled from
the real GZDoom tree with ``literalinclude`` (never pasted, so it cannot drift),
selected by **named doc-region markers** rather than line numbers. It opens with
the two things an engine must do before it can draw a single frame — **come up
and enter its main loop**, and **find and load the game's data** — and then turns
to the renderer: how a room in *Doom* becomes pixels through the **OpenGL**
backend, and then how the **Vulkan** backend renders the same frame a different
way. Later chapters (the tic/sim model, scripting, sound) build on these.

This is a teaching book maintained inside `imps <https://github.com/billsix>`_,
which carries the GZDoom source at a pinned commit (tag ``g4.14.2``) plus a
comment-only patch that adds the doc-region markers these chapters cite.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   intro
   launch-to-loop
   iwads-and-lumps
   opengl-renderer
   vulkan-renderer
