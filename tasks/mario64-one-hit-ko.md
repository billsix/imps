# One-Hit KO (cheat)

**Status:** proposed — needs feasibility research (step 1).
**CVar (proposed):** `CVAR_CHEAT("OneHitKO")` — checkbox. Menu label: "One-Hit KO" (a.k.a. "Fragile
Mario").
**Hard requirement:** implement via the port **EventSystem** — a listener gated on the CVar,
**not** inline `CVarGetInteger` in decomp. See `wiki/EventSystem.md` and
`tasks/reference/mario64/port-layer.md`.

## Goal
**Any damage Mario takes kills him instantly** (confirmed with William Emerison Six <billsix@gmail.com>, 2026-07-31 — this is Mario dying
in one hit, *not* Mario one-shotting enemies). A hardcore/permadeath-style difficulty toggle.

## Plan
1. **Research feasibility & design (do FIRST).** Read the reference docs + `wiki/EventSystem.md` +
   the damage decomp, and write findings + plan back here (then set status `planned`):
   - The **`PlayerHealthChange` event already exists** and already has a listener example in
     `src/port/mods/PortEnhancements.cpp:56` (the `InfiniteHealth` cheat — this is its inverse). A
     listener that, when health *decreases* (damage taken), forces health to 0 / triggers death is
     likely straightforward — **HIGH feasibility, probably no new fire site needed.** Confirm the
     event fires for all damage sources and that its data lets a listener zero the health.
   - Verify the death path: forcing health to 0 should trigger the normal death cutscene/action
     cleanly. Check the environmental killers (fall damage, lava, quicksand, drowning) — some
     already zero health, so make sure the cheat doesn't double-fire or break them.
   - Decide: does *any* health loss kill (including the small chip from e.g. gas/one-off ticks), or
     only "real" hits? Pin the rule in step 1.
2. (Define after step 1: the `PlayerHealthChange` listener that zeroes health on damage; the menu
   checkbox.)
3. Hand to Bill to build/run.

## Feasibility hints (verify in step 1)
- `PlayerHealthChange` is the natural hook and is already wired (`PortEnhancements.cpp:56`,
  `InfiniteHealth`). One-Hit KO is essentially the mirror: instead of clamping health *up*, clamp it
  to 0 whenever it would drop. Same listener shape as the accepted `bills/infiniteJump` cheats, but
  **this one likely needs NO new fire site** — reuse the existing `PlayerHealthChange` event.

## Resolved / open
- **Resolved (William Emerison Six <billsix@gmail.com>, 2026-07-31):** "single hit kills" = **Mario dies from one hit** (not enemies).
