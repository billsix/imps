# SuperMario64 — bumped the pin to Ghostship `aefb89b8`, with the cheats ported to upstream's feature registry

**Done 2026-11-26** (agent; William Emerison Six <billsix@gmail.com>, 2026-11-26: "put them in the feature table", then "start the SuperMario64 bump"). The maintainer committed the bump, then the clean build and the CI-patch fix it led to. The play-test was left to the maintainer; the cheats in particular need one.

## Why it was its own task

The third upstream sweep (`tasks/imps-check-upstreams-and-rebase-patches.md`) stopped at SuperMario64. Upstream Ghostship had moved `40eef138` → `aefb89b8` (11 commits, 211 files; head dated 2026-10-27), and commit `365df69f` "Implemented romhack support (#300)" reorganised `src/port/mods/PortEnhancements.cpp`, the file all three cheat patches edit. A fuzz retry of the conflicted hunks placed one listener block inside another listener's lambda without complaint, so the replay was discarded and the bump was filed here. The lesson is in `tasks/reference/imps/replaying-a-series-onto-a-new-pin.md`.

## Decisions, in the order they were made (William Emerison Six <billsix@gmail.com>, 2026-11-26)

1. **Port the cheats, do not just re-place them.** The agent offered (a) upstream's feature registry or (b) the smallest change that keeps the direct CVar reads; the maintainer chose to port.
2. **Find the event-system document the cheats were written from, before deciding the form.** It is `wiki/EventSystem.md` in Ghostship, and it is byte-identical at both pins: the event system did not change. Upstream added a second layer beside it, the feature registry (`docs/romhacks/DESIGN.md`, "Feature rules"; `src/port/features/Features.h`), whose rule is: add the setting to `sDefs` in `Features.cpp` with its vanilla value, and change every read of its CVar outside the menus to `Port_FeatureInt`.
3. **The cheats go into the feature table**, so a romhack or mod can disable or force them like upstream's own cheats. The alternative, leaving them outside the table so they always work, was declined.
4. **The guide's stale listener example gets an upstream patch**: `tasks/mario64-upstream-eventsystem-guide-feature-reads.md` (a separate task; it stands on this pin).

5. **Every sync or rebase ends with a clean build made by the agent.** Ruled after the bump was committed (`CLAUDE.md`, "Every sync or rebase ends with a clean build"). It is why this record has a build section, and it found the defect described there.

Choices the agent made during the work:

6. **The cheats' rows were also added to the id table in `docs/romhacks/DESIGN.md`**, because upstream keeps that table in step with `sDefs`.
7. **The fedora-shaderc-deps docs patch was dropped.** Its reason was that the build failed on Fedora without `libshaderc-devel`. Upstream commit `15e73cbe` now documents `vulkan-loader-devel vulkan-headers libshaderc-devel` as optional packages for the Vulkan renderer and builds without that renderer when they are missing, so the patch had nothing left to fix.
8. **`installdependencies.sh` gained `vulkan-loader-devel vulkan-headers`**, to follow upstream's new optional line and keep the Vulkan renderer in the maintainer's builds.

## What was done, per stream

| Stream | Patches | Result at `aefb89b8` |
|---|---|---|
| `upstreamable-standard-c` | 46 | 45 replayed as they were. Patch 0030 conflicted in `src/game/behaviors/piranha_bubbles.inc.c` (upstream changed the line above the padding line the patch deletes); resolved by hand: upstream's line kept, the padding line deleted. |
| `cheats` | 3 | Ported, one commit each, authorship and dates kept. Events, `CALL_…EVENT` sites and menu widgets replayed unchanged. In `PortEnhancements.cpp` each listener was placed at a named anchor and reads `Port_FeatureInt("cheats.super_jump" / "cheats.infinite_air_jumps" / "enhancements.disable_skybox", 0)`. Each cheat has its row in `sDefs` and in the design doc's table. Patch 0001 no longer adds the stray conflict-marker lines it used to carry (0002 used to remove them), so each patch now compiles on its own. |
| `book` | 1 | Replayed; the `sine_lookup` markers in `src/engine/math_util.h` were re-anchored around upstream's changed `sins`/`coss` macros (they now cast through `s32`). The stale duplicate file `0001-doc-region-markers.patch` was removed, so the stream is one file for its one commit. `book/docs/appendix-binary-angles.rst` gained a sentence about the new cast. |
| `upstreamable-ci-appimage` | 1 | Conflicted in `.github/workflows/main.yml`: upstream added two lines (`max-size`, `save`) to the ccache step inside the block the patch deletes. Resolved the standard way: the deletion stands, upstream's edits elsewhere are kept. Changed again after the clean build (below). |
| `upstreamable-fedora-shaderc-deps` | 1 → 0 | Dropped (decision 7); the stream folder is gone. |
| `patches-libultraship/book` | 1 | Replayed with no conflict onto libultraship `37daaa66`; regenerated under its subject's file name, the old short-named file removed. |

The pin is `aefb89b85e7b78daff62b491ebb2669d2d9270f0`. Submodules moved with it: libultraship `93a1a417` → `37daaa66` (URL unchanged, Kenix3) and Torch `106621f0` → `f83dfb3b`.

## Checks

- **`tools/check_patches_apply.sh SuperMario64`:** 51 patches applied to the game tree, 1 to libultraship.
- **`tools/check_upstreamable_applies.sh SuperMario64`:** both units (ci-appimage 1, standard-c 46) apply on pristine upstream.
- **`tools/check_comment_only_streams.sh SuperMario64`:** both book streams proven comment-only.
- **standard-c codegen, the check pending since sweep two: 104 of 104 touched files compile to identical assembly.** `tools/asmdiff_tree.sh <pin> <standard-c tip>` reported 47 identical and 57 skipped; the 57 are `*.inc.c` files, which the tree gate skips because they have no compile command of their own. Each was then run through `tools/asmdiff.sh`, which handles included files, and all 57 were identical. The cmake tree was configured in a sandbox-only directory, after `git submodule update` to the new gitlinks and installing `mbedtls-devel` in the sandbox.
- **Compile check of the ported cheats:** `PortEnhancements.cpp`, `Features.cpp`, `GhostshipMenuEnhancements.cpp`, `mario.c`, `mario_actions_airborne.c` and `skybox.c` pass `-fsyntax-only` with their recorded flags at the cheats tip; `PortEnhancements.cpp`, `mario.c` and `mario_actions_airborne.c` also pass at each of the two earlier cheat commits, so each patch stands on its own. This is a syntax and type check, not a link or a run.
- **Not done:** any play-test.

## The clean build, and the defect it found

`tools/verify_appimage_builds.sh SuperMario64` built the image and the game from scratch (decision 5).

- **First run:** all 696 build steps compiled and linked, the ported cheats included, and `cpack` then failed: `file INSTALL cannot find "/src/build-cmake/ghostship.o2r"`.
- **Cause:** the `upstreamable-ci-appimage` patch, not the bump. Unlike the other ports' patches, SuperMario64's moved the CI download of `ghostship.o2r` to the repo root and defaulted `O2R` there, while upstream's `CMakeLists.txt` installs the archive from the build directory, at the old pin as at the new one.
- **Fix:** the patch keeps upstream's `path: ./build-cmake` and defaults `O2R` to `build-cmake/ghostship.o2r`; its commit message was corrected; the verifier's SuperMario64 row injects the archive there, as it does for the other accept-only ports. `tools/check_patches_apply.sh` and `tools/check_upstreamable_applies.sh` were rerun and stayed green.
- **Second run:** a valid AppImage (15 MB, x86-64 ELF).
- **Limit:** the bundled `ghostship.o2r` was the checkout-root copy from 2026-10-26, not regenerated at this pin (`tasks/n64-container-generate-o2r.md`).

## Derived artifacts

- `Dockerfile`: upstream's build-linux apt list did not change between the pins; only the pin named in the header comment was updated.
- `build.sh` and the `Makefile`: the targets they use (`GeneratePortO2R`, `cpack -G External`, the `.tcc` directory) still exist; `CMakeLists.txt` changed by 308 lines, mostly new platforms (Xbox UWP, iOS caching) and options.
- `installdependencies.sh`: decision 8. Upstream's `docs/building.md` changed (the optional Vulkan line, an Xbox section, `sf64.o2r` corrected to `sm64.o2r`); the stopped trial had reported it unchanged because it looked for `docs/BUILDING.md`, which is not this project's file name.
- Docs refreshed: `n64/SuperMario64/CLAUDE.md` (pin, streams, cheats, submodules, how to add a cheat), `n64/CLAUDE.md` (the family index and the list of upstreamable units), the pin comment in `fetch.sh`.

## Where things are

- Script: a one-shot `port_cheats.py` replayed the three cheat patches with their `PortEnhancements.cpp` hunks excluded and inserted the listeners, `REGISTER_EVENT` lines and feature rows at anchors that each had to occur exactly once. It was tied to this pin and was removed at archive; it is in git history under `tasks/adhoc/mario64-bump-pin-port-cheats-to-feature-registry/`.
- The libultraship reference crawl (`tasks/reference/libultraship/`) still describes engine commit `c151cc91`; a re-crawl at `37daaa66` remains a future task, as before.
