=========
Animation
=========

Your course animates by nudging an object with the keyboard — enough to show
motion, not what a game means by animation. Super Mario 64 does the real thing:
keyframed skeletal animation, the technique games have used for decades.

A character is a tree of joints
===============================

You already met the scene graph in :doc:`engine-math`: the world is a tree, and
a child inherits its parent's frame. A character is the same idea at a smaller
scale — a little tree of joints, body then head and limbs, hands off arms. A
**pose** is just an angle at each joint. Rotate the joints and the character
moves; each joint angle is one more rotation composed onto the running transform
as that tree is walked.

An animation is a flip-book of poses
====================================

An animation is a table: for frame 0 the elbow is here, for frame 1 slightly
more bent, and so on — stored compactly, with joints that do not move sharing
storage, plus a note of how the whole body rises and falls. Binding a character
to one sets up that playback:

.. literalinclude:: ../../Ghostship/src/engine/graph_node.c
   :language: c
   :start-after: // doc-region-begin bind_animation
   :end-before: // doc-region-end bind_animation
   :caption: geo_obj_init_animation — start playing an animation

Playing it is a counter: each game step, advance a frame; at the end, loop. As
the renderer walks the joint tree, each joint reads its angle for the current
frame and turns by that much. The game can even advance the counter by a
fractional amount, so an animation plays in slow motion or sped up without extra
frames.

Two kinds of in-between
=======================

One subtlety separates two things students often merge. The flip-book runs at
the game's fixed 30-steps-per-second rate, but the picture is drawn faster. The
game does **not** flip pages faster; it *blends* between this pose and the last
one for the in-between pictures — the smooth-motion trick of the next chapter,
:doc:`frame-interpolation`. So there are two "in-betweens": the animation's own
keyframes, sampled once per step, and the blend that fills up to the display
rate.

.. admonition:: Go deeper
   :class: seealso

   The joint tables, root motion, and playback speed:
   ``tasks/reference/mario64/animation.md`` and its mental model
   ``animation-overview.md``.
