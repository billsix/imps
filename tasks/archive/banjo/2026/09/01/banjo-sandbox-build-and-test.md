# BanjoKazooie: build and test in the sandbox

**Status:** dropped 2026-09-01 (maintainer decision) — superseded, not
completed. Its purpose (prove the patched BanjoKazooie builds and runs)
was satisfied by other means the same day: the podman container build
compiled the patched tree, and the maintainer ran the resulting AppImage
on his host. The only remaining unique deliverable (a headless
Xvfb-and-screenshots run in the sandbox) verifies nothing new. Archived
for the record so the idea is not re-proposed from scratch; if a
sandbox-run harness is ever wanted, this doc still holds the recipe
(ROM-symlink ExtractAssets path, Xvfb/pixel-judging steps).
**Priority:** 3
**Difficulty:** 4

## BLUF

Build BanjoKazooie from imps (fetch → apply → build) **inside this
sandbox** and prove it actually runs: launch it headless under Xvfb,
screenshot it, and judge pixels — not exit codes. Done when the patched
tree compiles clean and the game boots and renders real frames (title
screen or in-game), closing BanjoKazooie's one open verification gate.

## Context

- `BanjoKazooie/CLAUDE.md` — unlike the heavier ports, this sandbox CAN
  build and run Lighthouse (Xvfb + Mesa software GL + gdb + the full
  toolchain). Read its Version notes first.
- Build gotchas: `tasks/reference/banjo/build-system.md` (banner caveats
  apply). Known sandbox constraint from the old fork's notes:
  **`-DUSE_NETWORKING=OFF`** — the sandbox has no SDL2_net. `build.sh`
  doesn't pass extra cmake flags; either run the configure step by hand
  mirroring build.sh, or (small, worthwhile) teach build.sh a
  `CMAKE_EXTRA_FLAGS` pass-through — decide in-task.
- If it hangs: `tasks/reference/banjo/os-emulation-threading.md` has the
  freeze-debugging playbook (ThreadWatchdog dump in `logs/Lighthouse.log`);
  `freeze-after-rom-import.md` is the prior art. A hang after ROM import
  would suggest patch 0003 isn't doing its job — that's signal, not noise.
- Configure-time network: the build downloads `sse2neon.h` (unpinned) and
  FetchContent's `dr_libs` — the sandbox has network, so this works; just
  expect it.

## Getting bk.o2r without GUI clicking (machine-local, never committed)

The in-app ROM extraction needs interactive clicks — wrong for a headless
test. Two options, both using the maintainer's local ROM store
(`/foo/opt/n64/n64roms/BanjoKazooie/ROMF.z64` — machine-local path, `.z64`
byte order; the sibling `ROM.n64` is byte-swapped and won't work):

1. **Preferred — exercises patch 0002:** symlink the ROM as
   `Lighthouse/baserom.z64` and build the `ExtractAssets` target. With the
   series applied, `torch o2r` now runs with `-u ${PROJECT_VERSION}`, so
   the generated `bk.o2r` must pass `VerifyArchiveVersion()` — booting
   without the "Outdated/incompatible ROM archives" re-extract loop IS the
   patch-0002 test. Put the result in `runDir/`. Remove the symlink after.
2. Fallback: copy the old fork's already-extracted
   `/foo/opt/n64/banjo/Lighthouse/build-cmake/bk.o2r` (24 MB, made in-app
   at 1.0.0) into `runDir/` — quicker, but tests less.

## Test plan

1. `./fetch.sh && ./apply.sh`, then build with `-DUSE_NETWORKING=OFF`
   (see above); `build.sh`'s tail copies `lighthouse.o2r` into `runDir/`.
2. Provide `bk.o2r` (above).
3. `Xvfb :99 -screen 0 1280x800x24 &`, then run the game with
   `DISPLAY=:99` from `runDir/` under `timeout N` (a long-running game has
   no meaningful exit code — rc=124 means "ran the full duration"). If
   audio init fails headless, `SDL_AUDIODRIVER=dummy`.
4. Screenshot with `import -display :99 -window root shot.png`; check
   unique-color count / non-black fraction, and LOOK at the PNG. Capture
   at a couple of time offsets (boot logo vs title).
5. Check `runDir/logs/Lighthouse.log` for the ThreadWatchdog being quiet.
6. Report: build warnings/errors, boot outcome, screenshots, whether
   patches 0002/0003 demonstrably did their jobs.

## Notes

- ROM paths above are machine-local test inputs — imps' ROM-agnostic rule
  is about what gets committed, and nothing ROM-derived is committed here.
- GLFW-based rendering works under Xvfb+Mesa in this sandbox; if
  Lighthouse turns out to use a path that doesn't (the GLUT-under-Xvfb
  failure from the sandbox capability map), fall back to reporting build +
  boot-to-log-output and flag the render check for the maintainer's host.

## Open questions

None.
