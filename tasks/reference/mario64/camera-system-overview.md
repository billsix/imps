# Orientation (L1): The camera as a system — the idea

> **Provenance:** Ghostship pin `49c5312a`, 2026-09-06. **L1**
> (understand-without-code). Capsule (L0) in [`README.md`](README.md);
> full mechanism (L2) in [`camera-system.md`](camera-system.md).

A graphics course teaches you the camera's *matrix*: given where the camera
sits and what it looks at, you can write the transform that turns the world
into what the camera sees. That matrix is genuinely the easy part, and SM64
computes it in one line. Everything memorable about the SM64 camera lives in
the part the course never reaches: the machinery that *decides where the
camera should sit and look* every single frame.

Think of it as a character, not a matrix. SM64 literally personifies the
camera as Lakitu, a cameraman who has a **goal** (where he'd like to be) and
a **current** position, and who **eases** from current toward goal instead of
teleporting. That easing is why the camera feels heavy and lazy rather than
rigidly glued to Mario — it is a deliberate, tunable lag, not a side effect.

Behind Lakitu sits a small **library of modes**: a normal outdoor orbit, a
behind-the-back mode, a tight indoor mode, a first-person look, a
water-surface mode, a cannon-aiming mode, a boss mode, and more. Each mode
is just a different rule for computing "where should the camera want to be,
given where Mario is and what level this is." Switching modes doesn't cut
abruptly; the system **blends** from the old mode's answer to the new one's
over a set number of frames, so the transition is smooth.

Finally, the camera is **aware of the world's geometry**. It asks the same
collision system the player uses — "is there a ceiling here? a floor there?"
— and pulls itself in or up so it never pokes through a wall or clips into
the ground. That means the camera isn't an independent observer; it depends
on the physics system, and its final position is the result of a smoothing
rule *and* a collision query.

So "the camera" in SM64 is four things a course leaves out: a smoothed
follower, a menu of behavioral modes, blended transitions between them, and
a collision-aware placement. The view matrix the course teaches is only the
last, trivial step that turns all of that into something the renderer can
use. This is the sense in which a game "manages" a camera, and it is exactly
the layer worth seeing once you already understand the underlying transform.
