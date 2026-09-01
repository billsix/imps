# Rubber Mario (cheat)

**Status:** proposed — needs feasibility research (step 1).
**CVar (proposed):** `CVAR_CHEAT("RubberMario")` (checkbox); the 0.8 factor could be a slider later.
**Hard requirement:** implement via the port **EventSystem** — a listener gated on the CVar,
**not** inline `CVarGetInteger` in decomp. See `wiki/EventSystem.md` and
`tasks/reference/mario64/port-layer.md`.

## Goal
On landing, Mario **bounces instead of landing**: reflect the impact with **80% of the impact
velocity**, following the trajectory physics would dictate (preserve horizontal velocity, invert +
scale vertical). Repeated bounces decay by 0.8× each time until he comes to rest.

## Plan
1. **Research feasibility & design (do FIRST).** Read the reference docs + `wiki/EventSystem.md` +
   the landing decomp, and write findings + plan back here:
   - Find where landing is detected: `perform_air_step` returning `AIR_STEP_LANDED` in
     `src/game/mario_step.c`, and the landing action transitions (`act_freefall_land`,
     `act_*_land`, hard-knockback lands) in `mario_actions_airborne.c` / `_moving.c`. Capture the
     **impact vertical speed** at that instant.
   - Determine the hook: there is no existing "landed" event — likely add a `DEFINE_EVENT` +
     `CALL_CANCELLABLE_EVENT` at the air-step land point so a listener can, instead of landing, set
     `vel[1] = +0.8 * |impactSpeed|`, keep `forwardVel`, and force Mario back into an airborne
     action (`ACT_FREEFALL` / a jump action). Alternatively hook `PlayerExecuteAction` on the land
     actions.
   - Feasibility + risks (fall-damage lands, attack lands, ground pounds, min-speed threshold so he
     eventually rests, not bouncing forever on tiny drops).
2. (Define after step 1.)
3. Hand to Bill to build/run.

## Feasibility hints (verify in step 1)
- "Following trajectory physics would dictate" = **keep horizontal velocity**, only reflect the
  vertical component (scaled 0.8). Gravity then produces the natural arc for the next bounce.
- A **minimum impact-speed threshold** is needed so Mario settles (0.8ⁿ decays but never hits 0).
- **Model this after the accepted `bills/infiniteJump` branch.** It shows both shapes you need: a
  data-modifying `CALL_EVENT(EventName, m, &value)` whose listener scales `m->vel[1]`, and a
  `CALL_CANCELLABLE_EVENT(EventName, m) { … }` that lets a listener replace a vanilla block. A bounce
  fits the cancellable shape: a fire site at the air-step landing, a listener that reflects velocity
  (0.8× impact, keep horizontal) and re-enters an airborne action instead of landing.

## Open questions
1. Bounce on **all** landings, or only from a genuine fall above some speed (not walking off a
   1-unit ledge)?
2. Does it apply to hard/attack/ground-pound landings and knockback, or only normal falls?
