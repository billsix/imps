# Bullet time — time-scale slider (cheat)

**Status:** proposed — needs feasibility research (step 1).
**CVar (proposed):** `CVAR_CHEAT("BulletTime")` — a time-scale **slider**
(`WIDGET_CVAR_SLIDER_FLOAT`, e.g. 0.1–1.0) applied to objects/enemies only.
**Hard requirement:** implement via the port **EventSystem** — a listener gated on the CVar,
**not** inline `CVarGetInteger` in decomp. See `wiki/EventSystem.md` and
`tasks/reference/mario64/port-layer.md`.

## Goal
Slow down objects and enemies (Matrix-style bullet time) **while Mario moves at full speed** — a
configurable time-scale slider.

## Feasibility findings (research, 2026-07-31) — feasible via frame-skip; clean hook

- **The object update loop is `update_objects_starting_at` (`object_list_processor.c:293`)** — a
  `while` loop that calls `cur_obj_update()` on every object (Mario's object included; Mario's update
  runs *through* `cur_obj_update`). Picked over `update_objects_during_time_stop` by
  `update_objects_in_list` based on `gTimeStopState & TIME_STOP_ACTIVE`.
- **SM64 already skips non-Mario object updates during time stop** (`update_objects_during_time_stop`,
  `:318` — freezes objects by not calling `cur_obj_update()`, keeping Mario/doors/unimportant
  unfrozen). Bullet time is the "partial" version: skip non-Mario objects on a *fraction* of frames.
- **Clock + Mario handle both accessible:** `gGlobalTimer` (`game_init.h:54`, per-frame counter),
  `gMarioObject` (`object_list_processor.h:89`).

**Design (frame-skip via a cancellable per-object event):**
- `DEFINE_EVENT(ObjectUpdate, struct Object* obj;)`; wrap the normal loop's update:
  `CALL_CANCELLABLE_EVENT(ObjectUpdate, gCurrentObject) { cur_obj_update(); }` (a cancelled listener
  skips the object's update this frame).
- Listener: `if (!gCheats.BulletTime) return; if (obj == gMarioObject) return; f32 s =
  CVarGetFloat("gCheats.BulletTimeScale",0.5f); if (s>=1) return;` then a **stateless Bresenham** on
  the frame clock — freeze this object this frame iff `(s32)(gGlobalTimer*s) == (s32)((gGlobalTimer-1)
  *s)` (updates `s` fraction of frames, smoothly, and identically for every object in a frame since
  `gGlobalTimer` is constant during a frame). Cancel = freeze.
- Menu: "Bullet Time" checkbox + "Time Scale" slider (0.1–1.0, default 0.5).
- Not reusing `gTimeStopState` (it's binary and the game uses it for cutscenes/Bowser — hijacking it
  risks conflicts). Our hook is in the *normal* loop, so during real time-stop it simply doesn't fire.

**Risks (ice-everywhere lesson):** frame-skip makes objects move in **discrete steps (choppy
slow-mo)**, not smooth — and frame interpolation won't smooth a frozen object (it doesn't move
between skipped frames). True smooth slow-mo (scaling every object's velocity + animation rate) is a
much larger, per-behavior effort that risks breaking object AIs. Also: an object Mario **rides**
(moving platform) freezing on skipped frames could make his ride janky; enemies frozen mid-attack may
look odd. The slider makes it recoverable.

## Plan
1. ~~Research feasibility & design.~~ **Done — see above.** (Pending the questions below.)
2. **Implement** the event + fire site + listener + menu as designed above.
3. **Hand to Bill to build/run.**

## Open questions (confirm before implementing)
1. **Choppy MVP OK?** Frame-skip is easy and correct but looks **steppy** (not smooth); true smooth
   slow-mo is a big per-object effort. Accept the choppy MVP, or not worth it if it can't be smooth?
2. **Exclude only Mario, or also moving platforms / doors?** Mario-only is simplest (everything else
   slows, incl. platforms he might ride → possible jank). Recommend Mario-only for MVP.
3. **Camera** stays full-speed (not in this loop) — you steer Mario + camera normally while the world
   slows (the "Matrix" feel). Assume that's intended?

## Feasibility hints (verify in step 1)
- The `GameFrameUpdate` event exists; a per-object gate likely needs a new fire site in the object
  processor's update loop so a listener can skip non-Mario objects on scaled frames.
- Frame-skipping is the low-effort MVP; smooth slow-mo (scaling velocities/anim rates) is a much
  bigger, per-behavior effort — decide scope in step 1.
- **Model the listener shape after the accepted `bills/infiniteJump` branch** (CVar check +
  `event->cancelled`/data mutation in `PortEnhancements.cpp`). The new part vs those Mario-only
  examples is *where* the fire site goes — the object update loop, not Mario — so a
  `CALL_CANCELLABLE_EVENT` per non-Mario `cur_obj_update` is the likely addition.

## Open questions
1. Does "objects and enemies" include **moving platforms** (Mario rides them — skipping their
   update mid-ride is awkward) and the **camera**?
2. Frame-skip (choppy but easy) or true velocity/animation scaling (smooth but large)? — the
   feasibility research should recommend one.
