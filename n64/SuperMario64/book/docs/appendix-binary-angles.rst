==================================
Appendix B: The binary-angle table
==================================

Chapter :doc:`rotation` said sine and cosine come from a lookup table indexed by
a 16-bit angle. Here is the trick in full — it is a small marvel of packing.

.. literalinclude:: ../../Ghostship/src/engine/math_util.h
   :language: c
   :start-after: // doc-region-begin sine_lookup
   :end-before: // doc-region-end sine_lookup
   :caption: math_util.h — sine/cosine as table reads

Three things to notice. The angle is cast **unsigned** and shifted right by four
bits, so a full turn (``0x10000``) indexes ``0x1000`` = 4096 entries — and
because it is unsigned, an angle that runs past the end wraps to the start for
free. Cosine is the **same table** read ``0x400`` entries later, because
``cos θ = sin(θ + 90°)`` and 90° is a quarter of 4096. And the two tables
deliberately **overlap in memory** — the sine table is cut short and cosine's
reads spill into shared storage — a byte-exact quirk carried from the ROM. A
sine now costs one shift and one array read, no transcendental math at all.

Full detail: ``tasks/reference/mario64/rotation-euler-vs-rotors.md``.
