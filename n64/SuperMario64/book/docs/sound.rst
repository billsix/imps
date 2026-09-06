=====
Sound
=====

Neither of the maintainer's books covers sound, so this chapter is a short tour
of the piece students most often find missing. Super Mario 64 **synthesizes**
its audio in software and lets the modern host **play** it — a small but complete
digital-signal-processing pipeline.

From a score to samples
=======================

Music is stored as a compact, MIDI-like **sequence** of note and tempo events. A
sequence player reads it each audio frame and decides which notes should sound.
Each note is then turned into actual samples two ways:

- **Resampling** — an instrument's recorded sample is read faster or slower to
  shift it to the note's pitch. This is the exact same idea as texture sampling
  (:doc:`textures`): reconstruct a signal and re-sample it at a new rate. Here
  the signal is a sound and the axis is time.
- **An envelope** — the note's volume is shaped over time (a swell in, a fade
  out) so it does not click on and off.

.. graphviz::

   digraph audio {
     rankdir=LR;
     node [shape=box, fontname="sans-serif"];
     seq  [label="sequence\n(MIDI-like score)"];
     note [label="active notes"];
     synth[label="resample + envelope"];
     mix  [label="mix + reverb"];
     dev  [label="device\n(SDL / WASAPI / CoreAudio)"];
     seq -> note -> synth -> mix -> dev;
   }

All the notes are summed by a mixer, a little reverb is folded in for a sense of
space, and the finished buffer is handed to a per-operating-system player. That
last split — synthesize once, play through a thin per-OS device layer — is the
same shape as the graphics backends in :doc:`shaders`: portable work in the
middle, a small platform-specific edge. On the original console this ran on
dedicated audio hardware; here it is plain code on the CPU.

.. admonition:: Go deeper
   :class: seealso

   ``tasks/reference/mario64/sound-processing.md``.
