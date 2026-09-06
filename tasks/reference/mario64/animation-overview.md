# Orientation (L1): Animation — the mental model

> **Provenance:** Ghostship pin `49c5312a`, 2026-09-06. **L1**
> (understand-without-code). Capsule (L0) in [`README.md`](README.md);
> full mechanism (L2) in [`animation.md`](animation.md).

The maintainer's course animates by nudging an object with the keyboard —
enough to show motion, but not what a game means by "animation." SM64 does
the real thing, and it is worth seeing because the technique is the standard
one games have used for decades.

Start with the skeleton. A character like Mario is a small hierarchy of
joints — body, then head and limbs hanging off it, hands off arms — arranged
exactly as a tree, the same tree the scene graph already uses to place things.
A **pose** is nothing more than an angle at each joint: how far the elbow is
bent, how the head is turned. Change those angles and the character moves;
this is why a joint angle in this engine is just another rotation composed
onto the running transform as the tree is walked.

An **animation**, then, is a flip-book of poses: a table that says, for frame
0 the elbow is here, for frame 1 slightly more bent, and so on. SM64 stores
this compactly — angles indexed by frame, with joints that don't move sharing
storage — plus a note of how the whole body rises and falls (a walk cycle
bobs up and down; that vertical "root motion" is part of the animation, while
walking *forward* is handled by the gameplay code, not the flip-book).

Playing it is a counter. Each game step, advance to the next frame; when you
reach the end, loop back to the start. As the renderer walks the character's
joint tree, each joint reads its angle for the current frame and turns by
that much. There's a small refinement: the game can advance the counter by a
fractional amount, so an animation can play in slow motion or sped up without
needing more frames.

One subtlety separates two things students often merge. The flip-book runs at
the game's fixed 30-steps-per-second rate. But the picture is drawn faster
than that — 60 or more times a second. The game does **not** flip pages
faster; instead it *blends* between the current pose and the previous one for
the in-between pictures, so motion looks smooth at any framerate. So there are
two kinds of "in-between" here: the animation's own keyframes (sampled once
per game step) and the smoothing blend that fills the gap up to the display
rate. They are different layers doing different jobs.

The whole model, in a sentence: a character is a tree of joints, an animation
is a table of joint angles over time, playing it advances a frame counter and
each joint turns to its listed angle during the normal scene walk, and a
separate blend makes it smooth on screen. That is keyframed skeletal
animation — the thing the course leaves out and nearly every game relies on.
