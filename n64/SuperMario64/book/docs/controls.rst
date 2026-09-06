========
Controls
========

*Model View Projection* reads the keyboard directly: a key-press callback nudges
a paddle. That is all a first demo needs. A real game has a whole input layer
between the physical button and the thing that happens on screen, and Super
Mario 64's is a small masterclass — partly because the port slid a modern
gamepad in under **unmodified 1996 code**.

The game still thinks it is an N64
==================================

The decomp reads the controller with the original N64 function, exactly as on
hardware:

.. literalinclude:: ../../Ghostship/src/game/game_init.c
   :language: c
   :start-after: // doc-region-begin read_controller
   :end-before: // doc-region-end read_controller
   :caption: read_controller_inputs — the N64 read, unchanged

There is **no port code here** — the game calls ``osContGetReadData`` believing
it talks to N64 hardware. libultraship *provides* that function and feeds it from
an SDL gamepad through its controller layer. So a real controller (or keyboard,
or the touch controls) is slid in underneath the same API the cartridge used.
This is the same trick you saw with graphics: reimplement the old interface, and
the old code runs unchanged (:doc:`pipeline`).

.. graphviz::

   digraph input {
     rankdir=LR;
     node [shape=box, fontname="sans-serif"];
     sdl [label="SDL gamepad"];
     cd  [label="ControlDeck\n(libultraship)"];
     os  [label="osContGetReadData\n(N64 API)"];
     ctl [label="gControllers\n(struct Controller)"];
     inp [label="m->input flags"];
     act [label="Mario action\n(jump, …)"];
     sdl -> cd -> os -> ctl -> inp -> act;
   }

Held versus just-pressed
========================

The single most important idea in input handling is the difference between a
button being **held** and being **newly pressed** this frame. The controller
struct carries both — ``buttonDown`` (the level) and ``buttonPressed`` (the
edge) — and the game folds them into an abstract input-flag set:

.. literalinclude:: ../../Ghostship/src/game/mario.c
   :language: c
   :start-after: // doc-region-begin button_to_input
   :end-before: // doc-region-end button_to_input
   :caption: a button becomes an abstract input flag

Jump fires on the **edge** (``buttonPressed``); holding A to jump higher reads
the **level** (``buttonDown``). Then notice the indirection: the code does not
act on ``A_BUTTON`` directly — it sets ``INPUT_A_PRESSED``, and the action state
machine acts on *that*. Hardware button → abstract flag → action. That one extra
hop is what lets the same jump respond to a gamepad, a keyboard, or touch, and
what lets the game be re-mapped without touching gameplay code.

.. admonition:: Try breaking it
   :class: caution

   Change ``buttonPressed`` to ``buttonDown`` in the A-button line above.
   Rebuild and hold A: Mario now tries to jump **every frame** the button is
   down, not once per press — a stuttering, un-releasable jump. You have swapped
   an edge for a level, and felt exactly why input code cares about the
   difference.

.. admonition:: Go deeper
   :class: seealso

   The full input path, the touch/rumble wiring, and the ControlDeck:
   ``tasks/reference/mario64/controls-and-input.md`` and
   ``libultraship-integration.md`` (§5).
