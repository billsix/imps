=================
What's hardcoded
=================

A natural question once you start reading a real game: how much of it is
*data* — geometry, tables, scripts you could edit without a compiler — and how
much is *code*, welded in so hard that changing it means changing the program?
Super Mario 64 sits in a revealing middle, and the answer explains why fans can
reskin the game freely but can only change how it *plays* with a decompiler.

The data-driven half
====================

A lot of the game is data. **Levels** are not C — each is a *geo layout*, a
compact program interpreted into a scene tree (:doc:`engine-math`). **Most
objects** — a Goomba, a coin — run a small **behavior script** on a little
virtual machine, drawing on a big shared library of behaviors. Reskinning and
even re-arranging levels lives here, in data.

Mario is the opposite: welded into the engine
=============================================

Mario is **not** an interchangeable object. He has his own state structure that
no other object shares, his own global pointer, and — the giveaway — the object
update loop **checks for him by name**:

.. literalinclude:: ../../Ghostship/src/game/object_list_processor.c
   :language: c
   :start-after: // doc-region-begin mario_is_special
   :end-before: // doc-region-end mario_is_special
   :caption: the engine branches on "is this Mario?"

Mario gets his own rules (here, an exemption from time-stop). Beyond this, his
entire moveset — walking, jumping, wall-kicking, swimming — is a **hand-written
state machine** of hundreds of C functions, and his animations are built for
**his specific skeleton**. None of that is data you can edit.

So there are three different questions hiding inside "can I replace Mario?":

- **Reskin him** (a new model)? Yes — a model is a fixed ID pointing at
  geometry, and swapping that geometry is an asset swap (:doc:`textures` covers
  the same replacement machinery). He will *look* different.
- **Re-rig him** (a differently-boned model)? No, not easily — the animations
  assume his skeleton, so a differently-jointed model animates wrong.
- **Re-behave him** (different physics, a different character)? That is a code
  project: the action state machine would have to be rewritten.

Bosses are bespoke code too
===========================

The big set-piece enemies are the same story. Bowser's behavior is not a shared
script; it is hand-written C — ``behaviors/bowser.inc.c`` and its siblings
(``bowser_bomb``, ``bowser_flame``, and more), with fixed ``MODEL_BOWSER_*``
IDs. There are **226** hand-written behavior files in all. Ordinary enemies lean
on the shared behavior system; the memorable ones are special code.

The takeaway
============

Real engines sit on a spectrum from fully **data-driven** (modern
entity/component/prefab systems, where a "character" is data) to fully
**hardcoded**. Super Mario 64 is an instructive middle: data-driven levels and
common objects, a **protagonist and bosses welded into C**. That single fact
explains what a mod can and cannot do without a compiler — and it is the kind of
architectural trade every game makes and no course demo ever shows.

.. admonition:: Go deeper
   :class: seealso

   The full breakdown — the behavior VM, Mario's action machine, and the model-
   ID indirection — is in
   ``tasks/reference/mario64/hardcoded-vs-data-driven.md`` (and, for reskinning,
   ``alternate-and-hd-assets.md``).
