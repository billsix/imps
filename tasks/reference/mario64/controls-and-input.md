# Reference: Controls & input — SDL → the N64 osCont API → Mario

> **Provenance:** authored 2026-09-06 against Ghostship pin `49c5312a`.
> Anchors in the decomp (`src/game/game_init.c`, `src/game/mario.c`,
> `include/types.h`) and libultraship (the ControlDeck). Part of the mario64
> graphics set — map at [`README.md`](README.md). Companion:
> `libultraship-integration.md` (§5, the controller crossing).

## TL;DR

The decomp still speaks the **N64 controller API** — `osContGetReadData` —
exactly as on hardware. libultraship *provides* those symbols, fed from an
SDL gamepad through its ControlDeck, so the chain is **SDL → ControlDeck →
osCont → the decomp's `gControllers`**. Each frame `read_controller_inputs`
(`game_init.c:564`) reads the pad; the game then reads a `struct Controller`
with `buttonDown` (held this frame) and `buttonPressed` (newly pressed this
frame) plus an analog stick. A button becomes gameplay by a bitmask test —
`buttonPressed & A_BUTTON` sets `INPUT_A_PRESSED`, which the action state
machine turns into a jump.

## 1. The N64 API, reimplemented (`read_controller_inputs:564`)

```c
osContGetReadData(&gControllerPads[0]);   // the N64 read; LUS supplies the symbol
```

The decomp calls `osContGetReadData` believing it talks to N64 hardware.
There is **no port shim in the game code** — libultraship implements the
`osCont*` functions (`libultraship/.../libultra/`) and drives them from
`LUS::ControlDeck`, which reads an SDL gamepad. So the game is unmodified N64
input code; the port slid a modern gamepad in underneath the same API.

## 2. `buttonDown` vs `buttonPressed` (`types.h:18`)

```c
struct Controller {
    float stickX, stickY, stickMag;   // analog, [-64,64]
    u16   buttonDown;                 // held THIS frame
    u16   buttonPressed;              // newly pressed THIS frame (edge)
};
```

The distinction is the crux of responsive controls: **`buttonDown`** is the
level (is A held?), **`buttonPressed`** is the edge (was A pressed just now?).
Jump triggers on the edge; holding A longer jumps higher reads the level. A
game that confuses the two double-jumps or misses inputs.

## 3. A button becomes an action (`mario.c` `update_mario_button_inputs`)

```c
if (m->controller->buttonPressed & A_BUTTON) m->input |= INPUT_A_PRESSED;
if (m->controller->buttonDown    & A_BUTTON) m->input |= INPUT_A_DOWN;
```

The raw button bits are folded into an abstract `m->input` flag set, which the
Mario action state machine consumes. That indirection — hardware button →
abstract input flag → action — is what lets the same jump respond to a
controller, a keyboard, or the touch controls the port also wires in.

## How this relates to the course

- **`modelviewprojection` reads the keyboard directly** through GLFW (ch04:
  key callbacks nudging the paddles). SM64 shows the fuller picture: a
  *device-independent* input layer (the N64 API) with an SDL gamepad behind it,
  an **edge-vs-level** button model, and an **abstract input-flag** indirection
  between hardware and gameplay — none of which a first input demo needs but
  every real game has.
- **Gap filled:** the pressed-vs-down distinction, the reimplemented-hardware-
  API trick, and the button→flag→action indirection.

## Candidate doc-region spans (added to patch 0005)

- `src/game/game_init.c` `read_controller` — the `osContGetReadData` read.
- `src/game/mario.c` `button_to_input` — button bits → abstract input flags.
