# Reference: What's hardcoded — Mario, Bowser, and the data-driven/C spectrum

> **Provenance:** authored 2026-09-06 against Ghostship pin `49c5312a`.
> Anchors in the decomp (`src/game/object_list_processor.c`, `src/game/mario.c`,
> `src/game/behaviors/`, `include/model_ids.h`). Part of the mario64 set — map
> at [`README.md`](README.md).

## TL;DR

Super Mario 64 is a **hybrid**: some things are data-driven (level geometry is
geo-layout bytecode; most objects run a behavior *script*), but a great deal is
**hardcoded C** — and **Mario is the extreme case.** Mario is not a generic
object: he has his own state struct (`gMarioState`), his own global pointer
(`gMarioObject`), **special-casing inside the object-update loop**, and a
dedicated action state machine of hundreds of hand-written actions. Bosses like
**Bowser** each have their own hand-written `behaviors/*.inc.c` file (226 such
files total). Model identity is a **fixed integer** (`MODEL_MARIO = 0x01`)
pointing at geometry. So you can **reskin** (swap what a model ID's geometry is,
the HD-asset path) but you cannot easily **re-behave** or **re-rig** — the
behavior is code and the animations are keyed to a specific skeleton.

## 1. The data-driven half (so "hardcoded" means something)

- **Level geometry** is a *geo layout* — bytecode built into a scene tree by an
  interpreter (`scene-graph-and-data-structures.md`). Not C.
- **Most objects** run a *behavior script* on a small VM, and there is a large
  library of behaviors. So a Goomba is largely data + a shared script.

Against that backdrop, the hardcoded parts stand out.

## 2. Mario is welded into the engine

Mario is **not** an interchangeable entity:

- **A unique struct.** `struct MarioState` (and the global `gMarioState`) is
  Mario's alone — position, velocity, action, held object, and dozens more
  fields no other object has.
- **A special global + special-cased update.** `gMarioObject` is a dedicated
  pointer, and the object loop tests for it directly:
  ```c
  if (gCurrentObject == gMarioObject && !(gTimeStopState & TIME_STOP_MARIO_AND_DOORS))
      unfrozen = TRUE;   // object_list_processor.c
  ```
  Mario gets his own rules (here, an exemption from time-stop). He is a branch
  in the engine, not a row in a table.
- **A dedicated action state machine.** `mario.c` + `mario_actions_*.c` are
  thousands of lines of hand-written C: walking, jumping, wall-kicking,
  swimming — each an action with its own function. None of it is data.
- **Animations keyed to his skeleton.** `set_mario_animation(m, id)` plays an
  animation built for Mario's specific joint hierarchy.

**Consequence:** swap the *model* (geometry at `MODEL_MARIO`) and Mario looks
different — an asset swap, doable (`alternate-and-hd-assets.md`). But a
differently-*rigged* model will animate wrong (the animations assume his
skeleton), and a *different character* with different physics would need the
action machine rewritten. "Replace Mario" is a code project; "reskin Mario" is
an asset.

## 3. Bosses are bespoke C

`MODEL_BOWSER_*` are fixed IDs, and Bowser's behavior lives in hand-written
files — `behaviors/bowser.inc.c`, `bowser_bomb.inc.c`, `bowser_flame.inc.c`,
`bowser_falling_platform.inc.c`, and more. Big set-piece enemies are not
data-driven; they are special code. (Ordinary enemies lean much more on the
shared behavior system.)

## How this relates to the course

- **Neither course has any of this** — a demo has no entities, no data/code
  split. This is a lesson about *engine architecture*: real games sit on a
  spectrum from fully data-driven (modern entity/component/prefab engines) to
  fully hardcoded, and SM64 is a revealing middle — data-driven levels and
  common objects, but a **protagonist and bosses welded into C**. It explains
  *why* fan mods reskin freely but change behavior only with a decomp and a
  compiler.

## Candidate doc-region spans (added to patch 0005)

- `src/game/object_list_processor.c` `mario_is_special` — the object loop
  branching on `gMarioObject`.
