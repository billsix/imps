# Endless Stairs "wall-kick unlock" — joke cheat

**Status:** proposed — **investigation DONE (step 1 complete, see Findings).** Feasible; exactly one small
cheat-agnostic decomp edit + two event listeners. **No implementation until Bill reviews these findings,
commits the updated task, and gives the go-ahead.**
**CVar (proposed):** `CVAR_CHEAT("EndlessStairsWallKickUnlock")` — a checkbox.
**Hard requirement:** implement via the port **EventSystem** — a listener gated on the CVar, **not**
inline `CVarGetInteger` in the decomp. Model after the accepted `bills/highjump` / `bills/infiniteJump`
branches (CVar check + event data mutation in `PortEnhancements.cpp`). See `wiki/EventSystem.md` and
`tasks/reference/mario64/port-layer.md`.

## The joke (why this exists)
Setup for a joke video. The castle **Endless Stairs** (the infinite staircase to Bowser in the Sky,
which normally loops you back forever until you have 70 stars) is secretly made **finite** by this
cheat — but the viewer doesn't know that. The bit: the staircase only "**unlocks**" (stops looping)
once the player performs the **"running Z jump into a wall" three times** — i.e. 3 **wall kicks**,
anywhere in the game, not a specific spot. So on camera it looks like a bizarre discovered "tech":
*wall-kick three times → the endless staircase suddenly ends.* It plays off the real **backwards
long jump (BLJ)** that speedrunners use to clip through those stairs. **It does not need to be polished
or lore-accurate — crude is fine** (any 3 wall kicks anywhere counts).

## Design intent (to be confirmed by investigation)
- **Count wall kicks globally.** Each time Mario enters the wall-kick action, bump a counter. At 3, set
  an "unlocked" flag.
- **When unlocked, disable the endless-stairs loop-back** so the staircase becomes climbable/finite.
- Both halves via the EventSystem: an event to observe Mario's action (count wall kicks) and an
  event/hook to cancel or bypass the stairs loop-back when unlocked.

## Investigation plan (step 1 — DO THIS FIRST, findings below)
Answer each before designing. Read `tasks/reference/mario64/decomp-map.md` and the event-system reference first.

1. **How does the Endless Stairs loop-back actually work?** Find the behavior / function in the SM64
   decomp (`src/game/behaviors/*` and/or the castle-area code). Confirm: what condition normally makes
   the stairs finite (expected: total star count ≥ 70, via `save_file_get_total_star_count()`), and
   what code performs the "warp you back down" loop. Note file + function + the exact gating check.
2. **Cleanest bypass mechanism?**
   - **Option A (thematic "unlock"):** make the stairs' own check believe the unlock condition is met
     (e.g. spoof the star-count comparison, or set whatever flag the stairs read) — reuses the game's
     real finish path, lowest risk.
   - **Option B (direct cancel):** a `CALL_CANCELLABLE_EVENT` around the loop-back so the listener
     cancels it when unlocked.
   Recommend one, with the exact hook point.
3. **Wall-kick detection.** Which Mario action constant is the "running Z jump into a wall" / wall kick
   (candidates: `ACT_WALL_KICK_AIR`, and the wall-slide that precedes it)? Where is the cleanest place
   to observe entering it — is there an existing action-change / `set_mario_action` event in the port's
   GameInteractor, or does a new fire site need adding (like bullet-time's per-object hook)? Note the
   file/line.
4. **State + lifecycle.** Where to keep the wall-kick counter and the unlocked flag (a small cheat
   state struct vs statics). Does it reset on level reload / save load, or persist for the session?
   For the joke, session-persistent + reset on cheat-toggle-off is probably fine — confirm.
5. **Event-system feasibility.** Confirm the two hooks (observe wall kick; bypass stairs loop) are both
   expressible as events the way `bills/infiniteJump` does it, and whether either needs a **new** fire
   site added to the decomp (and where). Flag if anything can't be done purely as a listener.

## Findings (investigation done — 2026-07-31)
**Verdict: feasible, and cleanly event-system-shaped.** Exactly ONE small decomp edit needed (a
cheat-agnostic fire site); everything else is listeners in `PortEnhancements.cpp`.

1. **Endless Stairs loop-back mechanism + gate.** `check_instant_warp()` —
   `src/game/level_update.c:533-568`. The finite/infinite decision is the early-return at
   **`level_update.c:537-539`**: `if (gCurrLevelNum == LEVEL_CASTLE && save_file_get_total_star_count(...)
   >= 70) return;` (≥70 stars → no warp-back → stairs finite). With <70 it falls through to the warp-back
   body at **`level_update.c:542-567`**: on a `SURFACE_INSTANT_WARP_1B`-family floor
   (`include/surface_terrains.h:20`) it adds `warp->displacement` to Mario's pos and `change_area()`,
   teleporting him back down. Driven once/frame from `play_mode_normal()` (`level_update.c:982`). Cosmetic
   secondary gate: looping music at `sound_init.c:212` also keys off `numStars < 70` (flip too if you want
   the music to stop).
2. **Bypass — recommend Option B (cancellable event), NOT A.** Option A (spoof the star count) is worse:
   `save_file_get_total_star_count()` is read inline at :538 and shared by ~4 unrelated call sites
   (`interaction.c:815,1002,1058`, `mario_actions_stationary.c:1056`) — faking it corrupts door unlocks /
   star HUD. Option B is self-contained: wrap the warp body (:542-567) in a new
   `CALL_CANCELLABLE_EVENT(EndlessStairsWarp, gMarioState)` at **`level_update.c:542`**; the listener sets
   `event->cancelled = true` when unlocked → warp skipped → stairs finite, reusing the game's real
   no-warp-back outcome. **Scope the fire site to `LEVEL_CASTLE`** (WDW also uses instant warps — otherwise
   an unlocked cheat breaks WDW's inter-area warps).
3. **Wall-kick detection — pure listener, no new fire site.** Action constant
   **`ACT_WALL_KICK_AIR = 0x03000886`** (`include/sm64.h:274`), entered via `set_mario_action(...)` in
   `mario_actions_airborne.c:1149,1317`. `set_mario_action` **already** fires
   `CALL_CANCELLABLE_EVENT(PlayerExecuteAction, m, action, actionArg)` at **`mario.c:1001`** — a listener
   checks `action == ACT_WALL_KICK_AIR` and increments (session-wide), zero decomp change. Same shape as the
   existing `PlayerExecuteAction`/`PlayerHealthChange` listeners (`PortEnhancements.cpp:56,64`). **Observe
   only — must NOT cancel it.**
4. **State + lifecycle.** Two file-scope statics in `src/port/mods/PortEnhancements.cpp` (`sWallKicks`,
   `sStairsUnlocked`), like the existing statics there (:15,20). A raw static persists the whole process
   session and does not reset on level/save load — matches the joke (earn 3 anywhere, stays unlocked).
   Optional per-file reset hook exists: `LevelInitFromSaveFile` (`level_update.c:1287`, listener already at
   `PortEnhancements.cpp:81`). Also reset the counter to 0 when the CVar toggles off.
5. **Event-system feasibility.** Wall-kick observer = fully a pure listener (reuse `mario.c:1001`). Stairs
   bypass = needs **one new fire site**: `DEFINE_EVENT(EndlessStairsWarp, struct MarioState* m;)` in
   `hooks/list/PlayerEvent.h`, `REGISTER_EVENT(EndlessStairsWarp)` in `PortEnhancements_Register`
   (`PortEnhancements.cpp:~124`), and the `CALL_CANCELLABLE_EVENT` wrapper at `level_update.c:542` — the same
   "add a cheat-agnostic fire site, all logic in the listener" pattern the recipe blesses.

**Recommended design (for implementation, after go-ahead):** two listeners in `PortEnhancements.cpp`, both
gated on `CVAR_CHEAT("EndlessStairsWallKickUnlock")`: (a) on `PlayerExecuteAction`,
`if (action == ACT_WALL_KICK_AIR && ++sWallKicks >= 3) sStairsUnlocked = true;` (pure listener); (b) on the
new cancellable `EndlessStairsWarp`, `if (sStairsUnlocked) event->cancelled = true;`. Plus the one fire site
at `level_update.c:542` (scoped to `LEVEL_CASTLE`), the `DEFINE_EVENT`/`REGISTER_EVENT`, and a checkbox in
`GhostshipMenuEnhancements.cpp`.

**Risks:** (1) the stairs fire site is the ONLY decomp edit — keep it cheat-agnostic so vanilla is untouched
when off; (2) without the `LEVEL_CASTLE` scope, WDW warps break; (3) the ≥70-star path never reaches the
event (already finite — harmless).

## Plan (after go-ahead)
1. ~~Investigate feasibility & mechanism (step 1).~~ — findings above.
2. **Implement**: the wall-kick-count event/listener + the stairs-bypass event/listener + a
   "Endless Stairs Wall-Kick Unlock" checkbox in the cheats menu.
3. **Hand to Bill to build + run** (Bill runs the game; verify the staircase both loops before 3
   wall kicks and becomes finite after).

## Open questions (for Bill, after investigation)
1. **Count scope:** any 3 wall kicks *anywhere/anytime* in the session (crude, easiest — recommended
   for the joke), or only while in the castle / on/near the stairs? Recommend anywhere.
2. **Persistence:** does the "unlocked" state persist for the whole session once earned, or reset each
   time you re-enter the stairs area? Recommend persist-for-session.
3. **Wall kick vs wall slide:** count the actual **wall kick** (jump off the wall) specifically, or any
   wall contact? Recommend the wall-kick action so it matches the "running Z jump into a wall" framing.
