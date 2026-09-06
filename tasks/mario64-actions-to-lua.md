# SuperMario64: can character actions move from C to Lua?

**Status:** proposed — VERY LOW priority; a long research + experiment + test
effort, not scheduled. Parked until the maintainer wants to explore it.
**Priority:** 10
**Difficulty:** 9

## BLUF

Investigate whether the game's **character logic that is currently bespoke C** —
Mario's action state machine, and/or the enemies' native behavior loops — could
be **re-expressed in Lua** and the custom C removed, using (or extending) the
port's existing scripting runtime. This is exploratory: the honest likely
outcomes range from "a clean proof of concept for one simple enemy" to "not
worth it for Mario's hot path." Lots of research, experimenting, and testing;
no commitment to ship.

## Context — what's C now, and what scripting already exists

- **Read first — these two reference docs already map exactly what is bespoke C
  vs. data:** `tasks/reference/mario64/hardcoded-vs-data-driven.md` (Mario is
  welded into C: `gMarioState`, special-cased in the object loop, a hand-written
  action state machine) and `object-and-behavior-system.md` (enemies = a
  behavior-script VM + native `CALL_NATIVE` loops leaning on the shared
  `object_helpers.c` library; 533 scripts, 751 `CALL_NATIVE`s). That is the
  precise surface this task would try to move to Lua.
- **A scripting runtime already exists in the port** — `ENABLE_SCRIPTING`
  (`src/port/ui/GhostshipMenu*`), libultraship's `ship/scripting/ScriptLoader.h`,
  and the libtcc-based scripting engine (the `.tcc` runtime the build ships,
  noted in `n64/SuperMario64/CLAUDE.md`). **First question: what language(s)
  does it actually run — Lua, C-via-libtcc, or both — and what can a script
  reach?** The whole feasibility hinges on this.

## Research questions

1. **Runtime:** does the existing scripting layer support Lua (or only libtcc
   C)? If not Lua, is adding a Lua VM realistic, or should "extract to a script"
   mean the runtime that's already there?
2. **The C↔script boundary:** can a script read/write the object fields
   (`o->oAction`, velocities, timers) and call the shared helpers
   (`cur_obj_move_using_vel`, collision, animation)? Those helpers are the real
   dependency — a scripted behavior that can't call them is a rewrite, not an
   extraction.
3. **Hot path / performance:** the per-tick update runs for every object every
   frame (and Mario's action machine every frame). Is a scripted per-tick path
   fast enough, or only viable for cold/rare logic?
4. **Scope:** enemies (semi-data-driven already — the easier target) vs. Mario's
   action machine (huge, hot, and outside the object system — the hard target).

## Suggested phasing (each a stop/decision point)

1. **Survey** the existing scripting runtime and write up answers to Q1-Q2 (a
   `tasks/reference/` doc — this alone is useful knowledge).
2. **Proof of concept:** move ONE simple enemy's native loop (e.g. the Goomba's
   `bhv_goomba_update`) to a script, keeping behavior **identical**; measure the
   per-frame cost against the C version.
3. **Evaluate** whether Mario's action machine is even a candidate given (3);
   possibly a single, cold Mario action as a second PoC.
4. **Decide** — extract, partially extract (cold logic only), or shelve. Record
   why either way.

## Testing

- **Behavior parity:** the scripted version must produce identical object state
  frame-for-frame against the C version on the same inputs (a differential
  trace, per the maintainer's instrumentation-driven method).
- **Performance:** frame-time with N scripted objects vs. C.

## Notes

- Any code changes live as imps patches (the two-lane model), like everything
  else here. A Lua VM addition would be a substantial libultraship-lane change.
- This is deliberately parked at priority 10 — surfaced when the maintainer
  wants a research spike, not part of the book effort.
