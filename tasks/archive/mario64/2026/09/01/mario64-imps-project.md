# SuperMario64: add the Ghostship project to imps

**Status:** done — verified 2026-09-01: the maintainer built and ran on
his host; the three cheats are present in the menu. Two run-time issues
were found and fixed on the way (Vulkan-backend hang on RADV → OpenGL
forced in config; libtcc.so rpath → LD_LIBRARY_PATH in run.sh) — both
recorded in SuperMario64/CLAUDE.md. A 4th patch (libshaderc-devel doc
fix) joined the series post-creation. Archived same day.
**Priority:** 3
**Difficulty:** 6

## BLUF

Create `SuperMario64/` in imps like the other three projects — fetch.sh /
apply.sh / build.sh / run.sh / README / CLAUDE.md / patches — with a
3-patch cheat series (high jump, infinite jumps, no skybox) rebased onto a
modern upstream develop pin, and the maintainer's Ghostship reference-doc
set migrated to `tasks/reference/mario64/` ("absolutely" wanted —
maintainer, 2026-09-01). The old fork's messy `bill` branch history (moon
gravity, experiments, task churn) is explicitly NOT ported. Done when
fetch→apply→build→run works on the maintainer's host with the three
cheats in the menu.

## Facts established in-session (2026-09-01) — don't re-derive

- **Upstream:** `https://github.com/HarbourMasters/Ghostship.git` exists
  and serves the pi mirror's commits (verified by shallow SHA fetch of
  `fdb6ac1342d5923038f4fba96e31b93a283fa820`). GitHub `develop` was at
  `49c5312a0f3c0a28e1974be1923babd4f869f719` — **ahead of the maintainer's
  pi-mirror clone**, so resolve the pin from GitHub at execution time, not
  from the local mirror.
- **The triple-jump-fly cheat is already merged upstream**, restructured:
  `src/port/events/list/PlayerEvent.h` defines `SetTripleJumpAction` /
  `FlyingTripleJumpLaunch`, and `PortEnhancements.cpp` registers the
  listener under `gCheats.AlwaysFlyTripleJump`. So the old topic branches'
  shared base commit (`463df670` "cheat - always fly on triple jump")
  produces NO patch — it drops from the series, as the maintainer hoped.
- **The other three cheats are NOT upstream** (verified by symbol grep for
  HighJump/InfiniteJump/Skybox in develop's `src/port/`).
- **Upstream renamed the hook layer**: the cheats were written against
  `src/port/hooks/`; develop uses `src/port/events/`. Rebasing the three
  commits is therefore a real port, not a mechanical `git am` — and the
  merged fly cheat is the worked example of exactly how a cheat lands in
  the new events/ shape. Follow it.
- **The series** (from the old fork's topic branches, all in
  `/foo/opt/n64/mario64/Ghostship` — machine-local):
  1. `69c176ec` "cheat - high jump"
  2. `110b8065` "cheat - infinite jumps" (already stacks on high jump)
  3. `7399ea50` "cheat - disable skybox" (was based beside, not on, the
     other two; all three touch `PortEnhancements.cpp` +
     `GhostshipMenuEnhancements.cpp`, so linearizing it last will hit
     small mechanical menu-entry conflicts)

## Steps

1. Resolve the pin: GitHub `develop` tip at execution time. Fetch it,
   port the three cheats onto it (events/ shape, series order above),
   verify each compiles, then `format-patch` with `--base`.
2. Scripts per the per-project contract (master `CLAUDE.md`), adapting
   the old host scripts at `/foo/opt/n64/mario64/build.sh` + `run.sh`
   (machine-local): configure `-HGhostship -Bbuild-cmake -GNinja`, build
   `GeneratePortO2R` (port assets, no ROM) — **skip `ExtractAssets`**
   (wants `baserom.us.z64` in the source root; the shipped flow is
   run-the-binary-and-pick-a-ROM) — then build + install. `run.sh` runs
   `build-cmake/Ghostship` from `runDir/` (install doesn't install the
   binary; the maintainer's old `runDir/` with `sm64.o2r` and saves can be
   copied over to skip re-extraction). Caveat for containers later:
   cmake `curl`s `gamecontrollerdb.txt` at configure time.
3. **Migrate the doc set from the old fork's `bill` branch** (wanted
   absolutely): the fork's `tasks/reference/*.md` → imps `tasks/reference/mario64/`
   with provenance banners — banner STRONGLY: they were authored around
   base `67e561c6`, and develop has moved 118+ commits since, including
   the hooks→events restructure, so hook-layer claims are suspect. Also
   migrate `docs/plans/cheats-and-menu-enhancements.md` as reference, and
   rewrite the fork's `CLAUDE.md` into the tier-2 `SuperMario64/CLAUDE.md`
   (fixing fork-era claims). Enumerate the exact doc list from the `bill`
   tree at execution.
4. The `bill` branch's cheat-idea task stubs (ice-everywhere, one-hit-ko,
   rubber-mario, bullet-time, infinite-wall-kicks,
   endless-stairs-wallkick-unlock, time-scale, decomp-rename) — migrate as
   `mario64-`-prefixed `proposed` tasks in imps so the ideas survive the
   fork's retirement (cheap; see open question 2).
5. Master CLAUDE.md/README project entries; stage everything.
6. Verification: maintainer builds and runs on the host (per the other
   projects); the three cheats appear in the menu and work.

## Decisions (William Emerison Six <billsix@gmail.com>, 2026-09-01)

- **Pin = GitHub develop tip at execution time** (the fly cheat is
  upstream there; the pi mirror lags).
- **Migrate the cheat-idea task stubs** as `mario64-`-prefixed `proposed`
  imps tasks; skip only the archived moon-gravity one (its code is
  deliberately not ported).

## Open questions

None.
