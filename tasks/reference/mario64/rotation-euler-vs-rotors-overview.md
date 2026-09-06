# Orientation (L1): Rotation — Euler angles vs. rotors, the idea

> **Provenance:** Ghostship pin `49c5312a`, 2026-09-06. This is the **L1**
> (understand-without-code) level. Capsule (L0) in [`README.md`](README.md);
> full mechanism with anchors (L2) in
> [`rotation-euler-vs-rotors.md`](rotation-euler-vs-rotors.md).

The maintainer's course teaches rotation one way; SM64 does it another.
Both spin things correctly — they land on the same rotation — but they
*think about* rotation differently, and the differences are exactly the
lessons worth drawing out.

**How SM64 thinks about a rotation.** An orientation is three numbers: how
much to turn about X, about Y, and about Z, applied in a fixed order. Each
number is a whole integer on a clever scale where one full turn is exactly
65536 units, so an angle that runs off the end of the number simply wraps
back to the start — the counter *is* the circle, and adding angles never
needs a "keep it in range" step. To turn those three angles into something
the renderer can use, the engine looks up their sines and cosines in a
precomputed table (no live trig) and drops them into a fixed formula that
produces the rotation matrix. This is compact (three small integers),
fast (table lookups), and drift-free (integers can't slowly lose
precision). It also makes "which way is this thing facing?" easy to answer:
a small table-based arctangent reads a yaw and pitch straight off a
direction vector, which is why cameras and aiming love it.

**How the course thinks about a rotation.** A rotation is named not by
three axis angles but by the **plane** you rotate in and the amount you
rotate — packaged as a single object called a rotor (close cousin of the
quaternion). You apply it with a symmetric "sandwich" operation, and you
combine two rotations just by multiplying their rotors. Nothing here refers
to X, Y, Z axes or an order to apply them in, so two failure modes of the
three-angle scheme simply don't exist: there is no "gimbal lock" (the
situation where two of the three axes line up and you lose the ability to
turn in one direction), and blending smoothly from one orientation to
another follows the natural shortest arc rather than a wobble.

**The trade, in one breath.** SM64's three-angle scheme is smaller, faster,
drift-free, and trivial to read a facing out of — but it has a fixed axis
order, can gimbal-lock, and blends orientations along a slightly unnatural
path. The rotor is a little larger and needs occasional cleanup, but it
composes cleanly, never gimbal-locks, and interpolates along the true
shortest turn. **They produce the same rotation**; each is the right choice
under different pressures. A 1996 cartridge chose the three angles because
six bytes and a lookup table mattered and gimbal lock could be designed
around. A modern course teaches the rotor because, freed of those limits,
its cleaner behavior is simply the better default.

The value of putting them side by side is that each explains the other: the
rotor's "no gimbal lock" is abstract until you can point at the exact
three-angle configuration where SM64 *would* lock, and SM64's cleverness
(the wrapping integer angle, the sine table) is invisible until you contrast
it with the course's from-scratch radians and computed trig.
