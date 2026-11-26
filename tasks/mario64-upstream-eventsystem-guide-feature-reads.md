# SuperMario64 — wrote the upstream fix to Ghostship's event-system guide (its listener example read a CVar)

**Done 2026-11-26** (agent; William Emerison Six <billsix@gmail.com>, 2026-11-26: "make a task that I intend to upstream to fix [the guide's step 4] … That is a perfect task to make a patch to upstream, with the commit message listing the reasoning and referencing the documents!"). The patch is written and carried; **opening the pull request is the maintainer's and has not been done.**

## What this was

Ghostship's guide for writing events, `wiki/EventSystem.md`, taught a listener that reads its setting with `CVarGetInteger`. Since upstream commit `365df69f` ("Implemented romhack support (#300)") the project's own rule is to read a lockable setting through `Port_FeatureInt`, so that a romhack or mod can disable or force it. Upstream changed its own listeners, including the one the guide says it is based on, and did not change the guide. The maintainer's three cheats had been written from that guide, which is how the mismatch was noticed during the pin bump (`tasks/archive/mario64/2026/11/26/mario64-bump-pin-port-cheats-to-feature-registry.md`).

## Decisions (William Emerison Six <billsix@gmail.com>, 2026-11-26)

1. **Make it an upstream patch**, with the commit message giving the reasoning and citing the documents.
2. **Scope (b): one pull request, two commits.** The agent had found three older differences between the guide's example and the code and offered (a) fixing only the feature-registry read or (b) fixing those too. The maintainer chose (b), split so a reviewer can take the first commit alone.

## What was built

A new upstreamable unit, `n64/SuperMario64/patches/upstreamable-eventsystem-guide/`, two patches against the bare pin `aefb89b8`, touching only `wiki/EventSystem.md` (21 lines added, 11 removed in total):

- **0001 "wiki: read the setting through the feature registry in the event guide".** Step 4's example now reads `Port_FeatureInt("cheats.pause_exit_whenever", 0)`, which is what the real `RenderPauseCourseOptions` listener in `src/port/mods/PortEnhancements.cpp` does. One added paragraph says why (only a read through the registry honours a romhack's or mod's disable and force rules), links the "Feature rules" section of `docs/romhacks/DESIGN.md`, and says a new setting needs its row in `sDefs` in `src/port/features/Features.cpp`. The commit message quotes the rule from `docs/romhacks/DESIGN.md` and cites `docs/scripting.md`, the header comment of `src/port/features/Features.h`, and the listener.
- **0002 "wiki: bring the rest of the event guide's example in line with the code".** The file is named `PortEnhancements.cpp` (the guide said `.c`, three times); `REGISTER_LISTENER` takes the priority second and the callback last (the guide had them reversed); the lambda form the file mostly uses is shown beside the guide's named function; the C++ code fences are marked `cpp`.

The guide's named-function listener was kept, not replaced by a lambda: both forms are in the tree, and keeping it made the second patch smaller.

## Checks

- The claims in the commit messages were checked against the tree at `aefb89b8`: no `REGISTER_LISTENER` call puts the priority last (0 of 52), and 12 calls register a named function.
- `tools/check_upstreamable_applies.sh SuperMario64`: the unit applies on pristine upstream (three units OK).
- `tools/check_patches_apply.sh SuperMario64`: 53 patches applied to the game tree, 1 to libultraship.
- `tools/check_comment_only_streams.sh SuperMario64`: unchanged, both book streams proven.
- No build was made: the unit changes one Markdown file and the pin did not move, so the clean-build rule for syncs (`CLAUDE.md`) did not apply.

## Where things are

- The unit: `n64/SuperMario64/patches/upstreamable-eventsystem-guide/`; it has no `DEPENDS` and is not in `patches/ORDER` (disjoint from every other stream). Listed in `n64/SuperMario64/CLAUDE.md` and `n64/CLAUDE.md`.
- To submit: `tools/apply_unit.sh SuperMario64 upstreamable-eventsystem-guide` puts the checkout on pristine upstream plus this unit, ready to push to a fork branch.
