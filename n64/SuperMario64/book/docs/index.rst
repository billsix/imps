###############################
How a Production Game Is Built
###############################

*Reading Super Mario 64's source to learn how a real 3D game is made.*

This book is for a reader who has worked through *Model View Projection*
(https://github.com/billsix/modelviewprojection) and wants to see how the
math there — vectors, matrices, transforms, projection, rotation via
geometric-algebra rotors — actually shows up in a shipping 3D game, plus all
the parts a linear-algebra course leaves out: lighting, textures, cameras,
animation, collision, sound, and the pipeline that ties them together.

The game is **Super Mario 64**, read through the *Ghostship* PC port. Every
piece of code shown is pulled directly from the real source with
``literalinclude`` (never pasted, so it cannot drift), and the deeper reference
notes behind each chapter live in the imps ``tasks/reference/mario64/`` set.

We gloss over detail early to keep the story moving, and push depth into later
chapters and appendices you can follow when you want more.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   intro
   rotation
   engine-math
   camera
   projection
   pipeline
   shaders
   textures
   lighting
   animation
   collision
   effects
   frame-interpolation
   sound

.. toctree::
   :maxdepth: 1
   :caption: Appendices

   appendix-fixed-point
   appendix-binary-angles
   appendix-geo-bytecode
   appendix-curves
   appendix-reference-set
