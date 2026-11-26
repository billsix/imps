# SuperMario64 — upstream a fix to Ghostship's event-system guide (its listener example still reads a CVar)

**Status:** ready — scope decided 2026-11-26; the pin bump it depended on is done
**Priority:** 5
**Difficulty:** 2 (one Markdown file; the work is a reviewer-ready commit message)
**Depends on:** `tasks/archive/mario64/2026/11/26/mario64-bump-pin-port-cheats-to-feature-registry.md` (the patch is written against the new pin, where the mismatch exists; that bump was done on 2026-11-26, pin `aefb89b8`)
**Created:** 2026-11-26 (William Emerison Six <billsix@gmail.com>: "make a task that I intend to upstream to fix [the guide's step 4] … That is a perfect task to make a patch to upstream, with the commit message listing the reasoning and referencing the documents!").

## BLUF

Ghostship's guide for writing events, `wiki/EventSystem.md`, teaches a listener that reads its setting with `CVarGetInteger`. Since upstream commit `365df69f` ("Implemented romhack support (#300)") the project's own rule is to read a lockable setting through `Port_FeatureInt`, and upstream changed its own listeners but not the guide. This task writes a documentation patch that brings the guide in line, carried as its own upstreamable unit for the maintainer to submit as a pull request. Done means `n64/SuperMario64/patches/upstreamable-eventsystem-guide/` holds the patch, it applies on the bare pin, and the commit message gives the reasoning and cites the documents.

## Context

**Read first:** `CLAUDE.md` ("Patch philosophy": an upstreamable unit is one PR's worth in its own `upstreamable-<slug>/` stream, depends only on pristine upstream, reviewer-facing commits) and `n64/CLAUDE.md` (streams, `tools/apply_unit.sh`, `tools/check_upstreamable_applies.sh`). Paths below are inside the Ghostship checkout, `n64/SuperMario64/Ghostship/`, at upstream `aefb89b8`.

**The mismatch, verified at `aefb89b8`:**

- `wiki/EventSystem.md`, step 4 ("Create the Listener"), shows:
  ```c
  if (CVarGetInteger("gPauseExitWhenever", 0) == 0) {
      return;
  }
  ```
  and introduces it with "This is usually where you check for CVars or custom mod logic."
- The code the guide says it is based on, the `RenderPauseCourseOptions` listener in `src/port/mods/PortEnhancements.cpp`, now reads:
  ```cpp
  if (Port_FeatureInt("cheats.pause_exit_whenever", 0) == 0) {
      return;
  }
  ```
- The rule is stated in `docs/romhacks/DESIGN.md`, section "Feature rules": "Code reads a lockable setting through the registry instead of `CVarGet*`", and "To make another setting lockable, add it to `sDefs` in Features.cpp with its vanilla value, and change every read of its CVar outside the menus to `Port_FeatureInt`." The same is said in `docs/scripting.md` ("From C, read a lockable setting through the registry rather than its console variable") and in the header comment of `src/port/features/Features.h`.
- `wiki/EventSystem.md` is byte-identical at `40eef138` and `aefb89b8`: `365df69f` changed the listeners and added the design doc, and did not touch the guide. A contributor who follows the guide today writes a cheat that a romhack cannot disable, which is the case the feature registry exists for. (That is how the maintainer's own three cheats were written, from this guide.)

**Three older differences between the guide and the code**, present before `365df69f` too:

- The guide names the file `src/port/mods/PortEnhancements.c`; it is `PortEnhancements.cpp`.
- The guide registers a named function, `REGISTER_LISTENER(RenderPauseCourseOptions, OnRenderPauseCourseOptions, EVENT_PRIORITY_NORMAL)`. The code and `src/port/events/EVENTS.md` put the priority second and pass a lambda: `REGISTER_LISTENER(RenderPauseCourseOptions, EVENT_PRIORITY_NORMAL, [](IEvent* event) { … })`.
- The guide's setting name `gPauseExitWhenever` was never the real one (`gCheats.PauseExitWhenever`, feature id `cheats.pause_exit_whenever`).

## Plan

1. After the pin bump, branch at the bare pin in the checkout and edit `wiki/EventSystem.md`: step 4 reads the setting with `Port_FeatureInt`, its lead-in sentence mentions the feature registry, and one added sentence (or short step) says a new setting needs its row in `sDefs`, linking `docs/romhacks/DESIGN.md#feature-rules`. That is commit 1. Commit 2 fixes the three older differences listed above (the `.cpp` file name, the `REGISTER_LISTENER` form with the priority second and a lambda, the real setting name), so the whole example matches the code.
2. Write each commit message for a reviewer; for commit 1: what the guide showed, what the code does since `365df69f`, why it matters (a listener written from the guide ignores `disable`/`force` rules), and the documents it relies on (`docs/romhacks/DESIGN.md` "Feature rules", `docs/scripting.md`, `src/port/features/Features.h`, the `RenderPauseCourseOptions` listener in `src/port/mods/PortEnhancements.cpp`). Match upstream's commit style (`git log` in the checkout).
3. `git format-patch --no-cover-letter --base=<pin>` into `n64/SuperMario64/patches/upstreamable-eventsystem-guide/`; no `DEPENDS` (it stands on the bare pin and touches only the guide).
4. Gates: `tools/check_upstreamable_applies.sh SuperMario64`, `tools/check_patches_apply.sh SuperMario64`. A Markdown-only patch needs no codegen or comment-only proof.
5. List the unit in `n64/SuperMario64/CLAUDE.md` and `n64/CLAUDE.md` as an upstream candidate. Stage; the maintainer commits and opens the pull request.

## Decision (William Emerison Six <billsix@gmail.com>, 2026-11-26)

Scope (b): one pull request with two commits. The first fixes the feature-registry read in step 4 and explains it; the second brings the rest of the example in line with the code. A reviewer can take the first alone.

## Open questions

None.
