# Infinite wall kicks (cheat)

**Status:** proposed — needs feasibility research (step 1).
**CVar (proposed):** `CVAR_CHEAT("InfiniteWallKicks")` (checkbox).
**Hard requirement:** implement via the port **EventSystem** — a listener gated on the CVar,
**not** inline `CVarGetInteger` in decomp. See `wiki/EventSystem.md` and
`tasks/reference/mario64/port-layer.md`.

## Goal
Remove the limit on wall kicks so Mario can wall-kick freely with no timing/height cap (climb a
single wall indefinitely).

## Plan
1. **Research feasibility & design (do FIRST).** Read the reference docs + `wiki/EventSystem.md` +
   the wall-kick decomp, and write findings + plan back here:
   - Find the wall-kick mechanism: `m->wallKickTimer` in `MarioState`, the air-hit-wall action
     (`act_air_hit_wall`) and wall-kick trigger (`check_wall_kick` in `src/game/mario.c`,
     `src/game/mario_actions_airborne.c`). Determine exactly what "limits" a wall kick (the short
     `wallKickTimer` window, and/or losing speed each kick).
   - Decide the semantics (see open question) and the hook: `PlayerExecuteAction` (fires per
     action) is a candidate; otherwise add a `DEFINE_EVENT` + `CALL_CANCELLABLE_EVENT` around the
     wall-kick gate so a listener can keep the window open / re-arm the kick.
   - Feasibility + risks (does freely re-kicking the same wall gain unbounded height? intended?).
2. (Define after step 1.)
3. Hand to the maintainer (William Emerison Six <billsix@gmail.com>) to build/run.

## Feasibility hints (verify in step 1)
- SM64 doesn't cap the *count* of wall kicks directly; the gate is the **`wallKickTimer` window**
  (a few frames after touching a wall) plus speed loss per kick. "No limit" most likely means
  keeping that window always satisfiable.
- `PlayerExecuteAction` can observe/redirect Mario's action each frame — good place to force the
  wall-kick opportunity.
- **Model this after the accepted `bills/infiniteJump` branch — the canonical event-system template.**
  Its infinite-air-jump cheat: a `CALL_CANCELLABLE_EVENT(MarioAirborneActionUpdate, m)` fire site in
  `mario_actions_airborne.c` (passing `struct MarioState* m`), a `DEFINE_EVENT(MarioAirborneActionUpdate,
  struct MarioState* m;)` in `hooks/list/PlayerEvent.h`, and the whole cheat in a `PortEnhancements.cpp`
  listener that checks `gCheats.InfiniteAirJumps` and, on the right input,
  `set_mario_action(m, ACT_JUMP, 0); event->cancelled = true;`. **The wall-kick is dispatched from the
  same `mario_execute_airborne_action`** — do the same: a fire site around the wall-kick decision, a
  listener that forces the wall-kick when `gCheats.InfiniteWallKicks` is set. (The `bill` branch has an
  older *inline* version — ignore it; the `bills/*` branch versions are the accepted model.)

## Open questions
1. "No limit" = the **timing window never closes** (you can always wall-kick when near a wall), or
   **re-kick the same wall repeatedly** for unbounded height, or both?
