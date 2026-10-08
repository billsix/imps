# MajorasMask — pin bump to current develop HEAD

**Status:** DONE 2026-10-08 — series replayed onto `e8757c14`, `check_patches_apply` green, derived
artifacts re-verified, pin + patch + docs committed; maintainer built and play-tested (after a clean
rebuild — see below). Archived.
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

## What was done (2026-10-08)

Upstream's `develop` had been force-updated since the 2026-10-07 recon; the current head `e8757c14`
("Update build doc and readme", dated 2026-09-25) is the new pin (develop is unversioned — no tag).

- [x] Replayed the series onto `e8757c14` with `git am --3way`.
- [x] **Resolved the `playback.c` conflict:** upstream had wrapped the `(uintptr_t)parentLayer < 0x7FFFFFFF`
      guard in `#ifndef __WIIU__` (excludes WiiU, leaves it live on desktop — so it does NOT fix our
      non-PIE 64-bit silent-SFX case). Took our side: removed the guard entirely (a superset of upstream's
      WiiU exclusion), keeping the explanatory comment. The other 7 files of patch 0001 auto-merged; verified
      all five fixes landed intact (OSMesg 8-byte receive in `load.c`/`thread.c`, the `uintptr_t` segment in
      `z_scene.c`, the `numSamplesUntilEnd < 0` clamp in `synthesis.c`, `sched.c`, and the port-layer
      `AudioSample*`).
- [x] **Dropped patch 0002** (BUILDING.md audio libs): upstream **absorbed** it — its build-doc update added
      libogg/libvorbis/opus/opusfile to the Ubuntu, Fedora AND Arch dep lists (only a cosmetic ordering
      differs on the Ubuntu lines). Per the sweep rule, an absorbed patch is dropped, not forced.
- [x] Non-textual breakage check: the patch references stable audio symbols (`osRecvMesg`, `OSMesg.data32`);
      nothing it depends on was renamed. Build verification is the maintainer's (below).
- [x] Derived artifacts re-verified: `.github/workflows/apt-deps.txt` and `main.yml` are **unchanged**
      between the pins, so the `Dockerfile` (COPY'd dep list + SDL 2.30.3 / gcc-12 mirror) is still accurate;
      `installdependencies.sh` already lists all four audio libs. Submodules: **libultraship bumped
      `7f2baa10`→`7f9b86a5` (1.3.1-397 → 1.3.1-490)**; ZAPDTR `ee3397a3` and OTRExporter `32e088e2` unchanged.
- [x] Updated `fetch.sh` (`PIN_SHA` → `e8757c14` + comment), regenerated `patches/upstream-candidates/`
      (now 1 patch), refreshed `n64/MajorasMask/CLAUDE.md` (pin, patch list, LUS version) + `n64/CLAUDE.md`
      index. All staged.
- [x] `tools/check_patches_apply.sh MajorasMask` → **green** (1 patch applies cleanly from the pin).
- [x] **Maintainer built + play-tested 2026-10-08.** First rebuild showed garbled textures/fonts from the
      opening scene — this was an **incremental build linking stale libultraship objects against the new
      game code** (the LUS bump 1.3.1-397 → 1.3.1-490 rewrote the fast3d texture path, which made it look
      like an upstream rendering regression). A **clean rebuild fixed it**; the bump and patch are sound.
      Lesson harvested to `tasks/reference/imps/n64-build-gotchas.md` ("After a pin bump that also moves
      libultraship, do a CLEAN rebuild").

## Open questions

None. (For an eventual upstream submission of patch 0001, note that upstream has since WiiU-scoped the
guard — recorded in `n64/MajorasMask/CLAUDE.md` — so the submission should address that rather than present
the guard as unconditional.)
