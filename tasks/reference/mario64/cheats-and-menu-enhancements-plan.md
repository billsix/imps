# Cheats & menu enhancements

> **Provenance:** authored 2026-06/07 against Ghostship around base `67e561c6` — the imps
> pin (`49c5312a`, GitHub develop tip 2026-09-01) is 120+ commits newer and includes a
> restructure of the hook layer (`src/port/hooks/` became `src/port/events/`, with an
> expanded event list and an EVENTS.md). Claims about hooks, file paths under port/, and
> the maintainer's fork/branches are suspect — verify against the pinned checkout.
> **Note:** several cheats this plan proposes have since shipped: always-fly-triple-jump
> was merged upstream, and high jump / infinite air jumps / no skybox are now the imps
> patch series. Moon gravity was deliberately left behind in the old fork.

**Status:** active — rolling log. New toggles get appended to *Upcoming* and
move down to *Shipped* once they land on the `bill` branch.

## Background

Ghostship's menu (the ImGui overlay reachable with Esc, defined in
`src/port/ui/GhostshipMenu*.cpp`) exposes runtime toggles backed by
**CVars**, the libultraship key/value system persisted in
`Ghostship.cfg.json`. Bill is using this fork to add gameplay cheats and
visual toggles, one per session, following a fixed recipe (see
`CLAUDE.md` → "Adding a cheat or enhancement").

All of these widgets land in `src/port/ui/GhostshipMenuEnhancements.cpp`
under the `Enhancements / Graphics` sidebar, grouped by
`WIDGET_SEPARATOR_TEXT` headings (`Rendering`, `Game`, `Cheats`, …).
Cheats use the `gCheats.*` CVar prefix (via `CVAR_CHEAT(...)`); visual
toggles use `gEnhancements.*` (via `CVAR_ENHANCEMENT(...)`).

## Recipe (one feature ≈ one commit)

1. Pick CVar name + prefix (cheat vs. enhancement).
2. Read it at the gameplay site with `CVarGetInteger("gCheats.Name", 0)`.
   Add `#include <libultraship/bridge/consolevariablebridge.h>` to the
   decomp `.c` if it's not already there.
3. Wire the checkbox in `GhostshipMenuEnhancements.cpp`.
4. Build & verify in-game (`bash /mario/build.sh && bash /mario/run.sh`).

The vanilla path must be preserved when the toggle is off — every shipped
toggle below short-circuits via the CVar so `develop`-equivalent behavior
is the default.

## Shipped (on `bill` branch, not yet on `develop`)

In commit order (oldest → newest). Each entry names the CVar, the
gameplay site, and the menu site.

### Always Fly on Triple Jump — `gCheats.AlwaysFlyTripleJump`

Triple-jumping starts the flying triple jump even without the Wing Cap.

- `src/game/mario.c:1041` — `set_jump_from_landing()`: `MARIO_WING_CAP`
  check OR'd with the CVar so a triple-jump landing routes to
  `ACT_FLYING_TRIPLE_JUMP`.
- `src/game/mario_actions_moving.c:149` — `set_triple_jump_action()`:
  same OR pattern so the moving-state triple-jump entry path also routes
  to flying.
- `src/game/mario_actions_airborne.c:1711` — `act_flying()`: vanilla
  forces Mario out of flying when the cap is dropped; CVar suppresses
  that exit so flight persists.
- `GhostshipMenuEnhancements.cpp` — checkbox under *Cheats*.
- Commits: `3c880415 always fly`, `cd9f4528 see if this works` (added
  the missing CVar bridge include in `mario_actions_airborne.c`),
  `b94c0c50 updated` (mirrored the check into
  `mario_actions_moving.c::set_triple_jump_action`).

### Triple Jump High Launch — `gCheats.FlyingTripleJumpHighLaunch`

Flying triple jump launches 3× higher.

- `src/game/mario.c:790` — `set_mario_action_airborne()` /
  `ACT_FLYING_TRIPLE_JUMP` case: `set_mario_y_vel_based_on_fspeed()` Y
  velocity is `246.0f` when the CVar is on, otherwise the vanilla
  `82.0f`.
- Commit: `7865c357 high jump fly`.

### Super Jump — `gCheats.SuperJump`

Every jump (other than the flying triple jump) launches 3× higher, and
the resulting fall doesn't deal damage / get-stuck-in-ground.

- `src/game/mario.c:880` — at the bottom of `set_mario_action_airborne()`,
  multiply `m->vel[1]` by 3 when the CVar is on and the action isn't
  the flying triple jump (which has its own toggle above).
- `src/game/mario.c:43` — two file-scope state vars for the
  fall-damage compensation: `gSuperJumpActive`, `gSuperJumpStartHeight`.
- `src/game/mario_actions_airborne.c:5` — `extern` the two vars.
- `src/game/mario_actions_airborne.c:69` — `check_fall_damage()`:
  back-compute a "natural" peak height (`startHeight +
  (peakHeight - startHeight) / 9`, derived from a 3× velocity giving
  ~9× height) and use that as the fall distance, then reset
  `gSuperJumpActive`.
- `src/game/mario_actions_airborne.c:132` — `should_get_stuck_in_ground()`:
  same correction so 1000-unit-fall snow/sand stuck-in-ground doesn't
  fire on a super-jump descent.
- Commits: `f3dbae2b high jump` (the multiplier),
  `27d1c40f don't get hurt from super jump` (the fall-damage
  compensation).

### Disable Skybox — `gEnhancements.DisableSkybox`

Skips the background skybox render so only the level geometry draws.

- `src/game/level_geo.c:72` — `geo_skybox_main()`: gate the
  `GEO_CONTEXT_RENDER` branch on `!CVarGetInteger(...)`.
- Menu: lives under a new *Rendering* `WIDGET_SEPARATOR_TEXT` group
  (first non-Mods item under Graphics).
- Commit: `f1433693 don't show background skybox`.

### Infinite Air Jumps — `gCheats.InfiniteAirJumps`

Pressing A while airborne re-enters `ACT_JUMP`. Holding Z suppresses
the re-jump (so ground-pound and Z-aimed actions still work).

- `src/game/mario_actions_airborne.c:2061` — at the tail of
  `mario_execute_airborne_action()`, after the action dispatch, check
  `INPUT_A_PRESSED` + `!INPUT_Z_DOWN` + not-invulnerable +
  not-swimming/flying + not-ground-pound + not-flying-triple-jump,
  and re-`set_mario_action(m, ACT_JUMP, 0)`. The function returns
  `FALSE` after the re-action so the rest of the airborne tick is
  short-circuited cleanly.
- Commits: `99f26b94 infinite jump` (initial wiring — returned `TRUE`
  at first, which broke subsequent ticks), `2fd2eb71 see if this fixes`
  (returns `FALSE` after re-action), `c94b89d2 try for z jump` (Z-down
  suppression for ground pound).

### Mario Size dropdown — `gCheats.MarioSize` (Tiny / Regular / Giant)

A `WIDGET_CVAR_COMBOBOX` letting the player pick Tiny / Regular /
Giant in any level. Most of the work landed in a single session
(2026-04-28) on top of vanilla Mario; one open task list at the end.

**Two helpers in `src/game/mario.c`** (declared in `mario.h`):

- `mario_size_factor()` — *visual* scale: Tiny=0.25, Regular=1.0,
  Giant=4.5. Used everywhere a *physical extent* needs to track size
  (model, hitbox, ledge-grab, camera distance, animation overrides).
- `mario_size_speed_factor()` — *speed* scale: Tiny=3.0, Regular=1.0,
  Giant=0.5. **Intentionally inverted** from the visual factor —
  Bill's call: "Tiny zooms, Giant lumbers." Used for forward velocity
  caps, accel curves, walk-anim cadence, and speed gates that need
  to track the cap.

When dialing the dropdown, only these two functions change.

**What's wired up:**

- **Visual model** — `squish_mario_model` (`mario.c:1230`) reads
  `mario_size_factor()` for the idle scale, and all five vanilla
  `gfx.scale` write sites (squish recovery, pancake, fall-into-pit
  shrink, ceiling-crush squish, ceiling-crush pancake) multiply
  through it so animations play at the right size.
- **Hitbox** — per-frame `hitboxHeight` (`mario.c:1692`) and
  `hitboxRadius` (newly set per-frame instead of left at the spawn-
  time 50) scale by visual factor. Hurtbox left at 0 (no hurtbox in
  vanilla).
- **Walk/run speed** — `update_walking_speed` (`mario_actions_moving
  .c:436`) scales target speed, accel deltas, and the 48 cap by
  speed factor. The `vel/43` taper is *divided* by the scale to
  preserve the curve shape (time-to-cap stays constant in frames).
- **Walk anim cadence** — `anim_and_audio_for_walk` multiplies
  `val14` by speed factor at all four anim sites (start-tiptoe,
  tiptoe, walking, running). Bypasses the vanilla
  `val04 = max(intendedMag, forwardVel)` quirk where joystick
  magnitude (~32) dominates and would otherwise leave Giant's legs
  cycling at Regular's rate.
- **Long jump (Z+A)** — trigger gate (`mario_actions_moving.c:1466`),
  forward-velocity cap (`mario.c:884`), and isSlow threshold
  (`mario.c:879`) all scaled by speed factor. Dive distance
  proportional to size. Fixed Bill's "z jump forward not registering"
  for Tiny when speeds were originally inverted.
- **Ledge grab** — `check_ledge_grab` (`mario_step.c:368`) scales
  the three magic numbers (60 lateral, 160 search start, 100
  minimum gap) by visual factor.
- **Camera** — `focus_on_mario` (`camera.c:709`), the bottleneck
  every camera mode routes through, scales `dist`, `posYOff`,
  `focYOff` by visual factor. Cascades to all modes (radial,
  8-direction, cannon, Bowser-fight, splash, etc).
- **Tiny walks/runs on water** — three coordinated sites
  (`mario_step.c:281` ground qstep, `:425` air qstep,
  `mario.c:1364` `update_mario_geometry_inputs`) swap `m->floor`
  to a new `gTinyWaterSurfacePseudoFloor` (a `SURFACE_DEFAULT`
  sibling of the `SURFACE_VERY_SLIPPERY` shell-surfing pseudo-floor)
  and set `floorHeight = waterLevel + 5` so feet sit visibly above
  the surface. Override gated on `fabsf(forwardVel) >= 4.0f` — when
  Tiny stops, the override drops, vanilla's `INPUT_IN_WATER` →
  `set_water_plunge_action` flow kicks in, Tiny plunges and swims.
  Splash + ripple via `m->particleFlags |= PARTICLE_IDLE_WATER_WAVE
  | PARTICLE_WATER_SPLASH` (self-throttled by `oActiveParticleFlags`).

**Open subtasks (deferred — Bill's call to revisit):**

- [ ] **Step / ceiling-clearance constants don't scale.** ~6
  magic-number sites in `mario_step.c` (160 / 150 / 100 / 30) still
  use vanilla values. Giant's body collision is fine but his step-
  up, ceiling-clearance, and ground-snap assume vanilla proportions —
  he bonks ceilings sooner than his model implies.
- [ ] **Jump heights / Y-velocity don't scale.**
  `set_mario_action_airborne` (`mario.c:790+`) hardcodes Y velocities
  per jump action. Giant currently jumps at vanilla absolute heights
  (looks like a tiny relative-to-his-body hop).
- [ ] **Speed-gated thresholds besides long-jump don't scale.** Slide-
  kick (`mario_actions_moving.c:1473`), the high-vel triple-jump
  branch (`mario.c:1064`), and ~7 other `forwardVel > 10|16|20` gates
  still use vanilla constants. Means Giant (slow) can't slide-kick or
  trigger the high-vel triple-jump branch. Note-only per Bill.
- [ ] **Tiny's running anim flips upside-down at full water-running
  speed.** Walking and slow running on water look correct after the
  +5 lift; the flip only shows up at top speed. Likely candidates:
  `tilt_body_running` math overflow into 180°, the
  `sFloorTiltMario*` body-state knobs, or the running anim's
  per-frame tilt accumulator interacting with `m->faceAngle[0]`
  resets. Don't touch yet.

**Phase C (runtime world scale) deferred** — see CLAUDE.md's
"Codebase notes" for the THI investigation that would gate it.

## Notes / follow-ups

- **Decomp-vs-port boundary.** Every cheat above pokes a CVar read
  directly into a decomp `.c` file. That's how upstream Ghostship does
  it — there's no "patch in port code only" abstraction. Match the
  pattern; don't try to reroute through a hook unless Bill asks.
- **Menu grouping.** All cheat checkboxes currently live in the same
  *Cheats* `WIDGET_SEPARATOR_TEXT` block. If the list grows past ~6–8,
  consider splitting into sub-groups (Mario / Camera / Enemies / …)
  with extra separators — but ask first.
- **Naming.** CVar names are `PascalCase`, no abbreviations
  (`AlwaysFlyTripleJump`, not `AFTJ`). Tooltips are full sentences with a
  trailing period.
- **`develop` rebase.** The shipped commits are `bill`-branch only and
  haven't been PR'd upstream. If/when Bill wants to upstream, expect to
  squash these into one cheat-per-commit history; the "see if this
  works" / "updated" / "try for z jump" intermediates won't survive.
