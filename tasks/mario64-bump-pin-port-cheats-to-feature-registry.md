# SuperMario64 — bump the pin to Ghostship `aefb89b8`, porting the cheats to upstream's feature registry

**Status:** ready — decision recorded 2026-11-26; starts on the maintainer's word
**Priority:** 4
**Difficulty:** 5 (the replay is mostly done and understood; the cheats need a small port to a new upstream API, and the build files changed a lot)
**Created:** 2026-11-26 (agent, third upstream sweep; stopped and logged under the sweep contract in `tasks/imps-check-upstreams-and-rebase-patches.md`. Filed as its own task because a sync item that does not resolve gets a task: `CLAUDE.md`, "Staying current with upstream").

## BLUF

The third sweep did not bump SuperMario64: upstream Ghostship rewrote how cheats and enhancements are configured, and the three `cheats/` patches cannot be replayed onto it mechanically. The pin stays at `40eef138` and the checkout is back on the full series there (`tools/check_patches_apply.sh SuperMario64` green). Done means the pin is `aefb89b8` (or the head at that time), all streams apply, the standard-c stream is proven codegen-identical at the new pin, the book stream is proven comment-only, and the derived build files match upstream's.

## Context

**Read first:** `n64/SuperMario64/CLAUDE.md`, `n64/CLAUDE.md` (streams, `ORDER`, the two lanes), `tasks/reference/imps/standard-c-tooling.md` (the asmdiff gate) and `tasks/reference/imps/derived-artifact-drift.md`.

**Upstream moved** `40eef138` → `aefb89b8` (11 commits, 211 files, +18058 −1603; head dated 2026-10-27). The commit that matters is `365df69f` "Implemented romhack support (#300)". The libultraship gitlink moved `93a1a417` → `37daaa66` and Torch `106621f0` → `f83dfb3b`.

**What the trial replay found (2026-11-26, in the checkout on a scratch branch, then discarded):**

| Stream | Patches | Result at `aefb89b8` |
|---|---|---|
| `upstreamable-standard-c` | 46 | 45 apply as they are. Patch 0030 (remove `UNUSED u8 filler[]` padding) conflicts in `src/game/behaviors/piranha_bubbles.inc.c`: upstream changed the line above the one the patch deletes (`curAnim->loopEnd` became `obj_cur_anim(parent)->loopEnd`). Resolution: keep upstream's line, delete the padding line. |
| `cheats` | 3 | **Does not replay.** All three touch `src/port/mods/PortEnhancements.cpp`, which upstream rewrote (below). |
| `book` | 1 (see "Duplicate file") | One marker pair needs re-anchoring: `sine_lookup` in `src/engine/math_util.h`, where upstream changed `sins`/`coss` to cast through `s32`. The markers go around the new lines. The book text that quotes the old macros needs the same update. |
| `upstreamable-ci-appimage` | 1 | Conflicts in `.github/workflows/main.yml`, not examined further. On MajorasMask and BanjoKazooie the same patch conflicted because upstream edited next to the block the patch deletes. |
| `upstreamable-fedora-shaderc-deps` | 1 | Not reached. |
| `patches-libultraship/book` | 1 | Not tried; it is keyed to the libultraship gitlink, which moved. |

**The cheats and the feature registry.** At the old pin a cheat read its setting with `CVarGetInteger("gCheats.AlwaysFlyTripleJump", 0)`. At the new pin upstream reads it with `Port_FeatureInt("cheats.always_fly_triple_jump", 0)`, and a table in `src/port/features/Features.cpp` maps each feature id to its CVar (`{ "cheats.always_fly_triple_jump", CVAR_CHEAT("AlwaysFlyTripleJump"), Kind::Toggle, 0 }`). The menu in `src/port/ui/GhostshipMenuEnhancements.cpp` still binds widgets to CVars. The maintainer's three patches (high jump, infinite jumps, disable skybox) add listeners that call `CVarGetInteger("gCheats.SuperJump", …)` and the like, and add menu widgets.

**The event system itself did not change.** The guide the cheats were written from, `wiki/EventSystem.md` in Ghostship ("Implementing New Events in the Event System": `DEFINE_EVENT`, `REGISTER_EVENT`, `CALL_CANCELLABLE_EVENT`, a listener, `REGISTER_LISTENER`), is byte-identical at `40eef138` and `aefb89b8`. Its companion `src/port/events/EVENTS.md` only gained 68 lines (the "Game Data" and "Net" events). The feature registry is a second layer beside the events, documented in Ghostship's `docs/romhacks/DESIGN.md` ("Feature rules") and `src/port/features/Features.h`. Its rule, quoted from the design doc: "To make another setting lockable, add it to `sDefs` in Features.cpp with its vanilla value, and change every read of its CVar outside the menus to `Port_FeatureInt`." Upstream has not added any of the three cheats itself (no `MarioHighJump`, `MarioAirborneActionUpdate`, `SuperJump`, `InfiniteAirJumps` or `DisableSkybox` at `aefb89b8`). The guide's step 4 still shows a listener reading `CVarGetInteger`; fixing that upstream is `tasks/mario64-upstream-eventsystem-guide-feature-reads.md`.

**A trap found on the way:** retrying the conflicted cheat hunks with `patch -F3` placed the high-jump listener block inside another listener's lambda (before its closing `});`). It applied without complaint and would not have compiled. The cheats must be placed by hand. The fuzz-retry script was deleted, and the rule is in `tasks/reference/imps/replaying-a-series-onto-a-new-pin.md`: a conflicted hunk in code is resolved by reading it.

**Two things already wrong at the current pin** (found during the trial, independent of the bump):

- *Duplicate file.* `n64/SuperMario64/patches/book/` holds two files numbered 0001 with the same subject and the same markers: `0001-doc-region-markers.patch` and `0001-docs-add-doc-region-markers-for-the-book-s-literalin.patch`. `git am --3way` applies the first and finds the second already applied, so the stream is one commit, not two. The 2026-10-08 bump regenerated the patch under the longer name and left the old file. Regenerating the stream at the bump removes the stale one.
- *Conflict markers inside a patch.* `patches/cheats/0001-cheat-high-jump.patch` adds the literal lines `=======` and `>>>>>>> 69c176ec (cheat - high jump)` to `PortEnhancements.cpp`, plus a second copy of two `REGISTER_EVENT` lines; `0002-cheat-infinite-jumps.patch` removes them again. The tree with the whole series applied is fine, but patch 0001 alone does not compile. Porting the cheats is the moment to fix it.

**Derived artifacts that need a re-check at the bump:** `CMakeLists.txt` changed by 308 lines and `.github/workflows/main.yml` by 80, so `n64/SuperMario64/Dockerfile`, `build.sh`, the `Makefile` targets and `installdependencies.sh` must be compared with upstream's; `docs/BUILDING.md` did not change.

## Plan

1. Replay `upstreamable-standard-c` (the one hand resolution above), then prove it at the new pin: `tools/asmdiff_tree.sh <new pin> <new pin + standard-c>` against a configured tree in a sandbox-only build directory (never the bind-mounted `build-cmake/`).
2. Port the three cheats onto the feature registry (see Decision), fixing the conflict-marker lines in patch 0001:
   - Keep each cheat's events and listeners (`DEFINE_EVENT`, `REGISTER_EVENT`, the `CALL_…EVENT` sites, `REGISTER_LISTENER`); place the listener blocks by hand in the reorganised `src/port/mods/PortEnhancements.cpp`.
   - Add three rows to `sDefs` in `src/port/features/Features.cpp`, each `Kind::Toggle` with vanilla value 0: `cheats.super_jump` (`CVAR_CHEAT("SuperJump")`), `cheats.infinite_air_jumps` (`CVAR_CHEAT("InfiniteAirJumps")`), `enhancements.disable_skybox` (`CVAR_ENHANCEMENT("DisableSkybox")`). Confirm each CVar name against the patch's menu widget.
   - Change each listener's `CVarGetInteger("gCheats.…", 0)` to `Port_FeatureInt("<feature id>", 0)`.
   - Leave the menu widgets in `src/port/ui/GhostshipMenuEnhancements.cpp` bound to their CVars; the menu greys a locked widget by itself.
   - Compile-check `Features.cpp` and `PortEnhancements.cpp` against the configured tree from step 1 before regenerating the patches.
3. Replay `book` with the `sine_lookup` markers re-anchored; run `tools/check_comment_only_streams.sh SuperMario64`; update the book chapter that quotes `sins`/`coss`.
4. Replay `upstreamable-ci-appimage` and `upstreamable-fedora-shaderc-deps` on the bare pin; run `tools/check_upstreamable_applies.sh SuperMario64`.
5. Replay `patches-libultraship/book` onto libultraship `37daaa66`.
6. Regenerate every stream, set `PIN_SHA`, run `tools/check_patches_apply.sh SuperMario64`.
7. Re-derive the build files (Dockerfile, `build.sh`, Makefile, `installdependencies.sh`) from upstream's; refresh `n64/SuperMario64/CLAUDE.md`, `n64/CLAUDE.md`, the pin comment in `fetch.sh`, and the libultraship crawl note if the engine pin matters to it.
8. Stage as one unit. Build and play-test are the maintainer's; the cheats in particular need a play-test.

## Decision (William Emerison Six <billsix@gmail.com>, 2026-11-26)

"port them … put them in the feature table": the three cheats go into upstream's feature registry, so a romhack or mod can disable or force them like upstream's own cheats. The alternative, leaving them outside the table with direct CVar reads so they always work, was declined.

## Open questions

None.
