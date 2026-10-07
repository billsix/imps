# MajorasMask — pin bump to current develop HEAD

**Status:** proposed — todo (filed 2026-10-08 from the upstream sweep's findings).
**Priority:** 5
**Difficulty:** 5 (2 patches, but the audio-crash fix collides with reworked upstream code)
**Created:** 2026-10-08 (William Emerison Six <billsix@gmail.com>: "yes, write it as a todo")
**Part of:** `tasks/imps-check-upstreams-and-rebase-patches.md` (the 2026-10-07 upstream sweep).

## BLUF

Bump `n64/MajorasMask`'s pin from `04a1a43197…` to 2ship2harkinian's current develop HEAD
`e8757c14a0fc8701461b0458c9ed72c118bcfc67`, replaying the 2 `upstream-candidates` patches. The sweep's
rebase probe found **patch 0001 ("Fix silent SFX and several 64-bit-host audio crashes") conflicts** in
`mm/src/audio/lib/playback.c` — upstream reworked the audio lib. Done = the series re-applies onto the new
head (conflict resolved), derived artifacts re-verified, pin + patches + docs updated and staged, and the
maintainer has built + play-tested.

## Context

- **The rebase probe (2026-10-07):** `git am --3way` of `patches/upstream-candidates/*.patch` onto
  `e8757c14` applied some hunks then conflicted at `mm/src/audio/lib/playback.c` (also auto-merged
  `AudioSampleFactory.cpp`, `load.c`, `thread.c`). So the audio-crash-fix patch needs its hunks
  re-placed against the reworked upstream audio code — a real code-merge, not a clean replay.
- **The pin-bump operation** is defined in the master `CLAUDE.md` agent contract; **MM is a single-lane**
  game here (only `upstream-candidates`, no standard-c / personal / LUS lane in `patches/`).
- **Re-verify derived artifacts** at the bump (`tasks/reference/imps/derived-artifact-drift.md`): MM's
  `Dockerfile` (from the upstream `main.yml` build-linux job + `apt-deps.txt`), `installdependencies.sh`
  (from `docs/BUILDING.md` Fedora section — note the audio libs ogg/vorbis/opus/opusfile come from MM's
  own patch 0002 per the drift table), `build.sh`/Makefile target names (`Generate2ShipOtr`), and
  `run.sh`.
- Current checkout default state = pin + applied series; probe left it restored to the old applied HEAD
  (`176e3f628`), pin unchanged.

## Plan

- [ ] Fetch `e8757c14`, branch at it, `git am --3way` the 2 `upstream-candidates` patches; **resolve the
      `playback.c` conflict** by re-placing the audio-crash-fix hunks against the reworked upstream (read
      the new `playback.c`/`load.c`/`thread.c` first — a wrong merge reintroduces the crash).
- [ ] Check for **non-textual breakage** (upstream symbols the patch references that were renamed/moved).
- [ ] Re-verify the derived artifacts (above) against the new upstream; update any that drifted.
- [ ] Update `PIN_SHA` + pin comment in `fetch.sh`, regenerate the series
      (`git format-patch --no-cover-letter --base=e8757c14 e8757c14..HEAD -o patches/upstream-candidates/`),
      refresh the per-project `CLAUDE.md` pin facts, **stage**.
- [ ] Run `tools/check_patches_apply.sh MajorasMask` (resets to the new pin, replays, confirms).
- [ ] **Maintainer:** build + play-test; then the bump is trusted and this task archives.

## Open questions

None — the decision to do the bump is made; the only judgment is the mechanical `playback.c` conflict
resolution, which is this task's work.
