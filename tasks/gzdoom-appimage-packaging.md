# Package the built GZDoom as an AppImage (like the n64 games)

**Status:** proposed — needs go-ahead. Filed 2026-09-20 (William Emerison Six <billsix@gmail.com>), split out
of `tasks/gzdoom-port-and-cli-wad-patch.md` at the maintainer's request ("make the appimage thing a separate
task; keep the Dockerfile and Makefile for now"). Secondary/optional — the native host scripts (that task's
Phase A2) are the main build path; this is a convenience distributable on top.
**Priority:** 7
**Difficulty:** 5 (GZDoom's build does not emit an AppImage — it needs an added packaging step)

## BLUF

Give `games/gzdoom/` a `make appimage` target that produces a single relocatable **`out/gzdoom.appimage`**,
and a `make run` that runs it on the host from `runDir/`, mirroring the n64 games (`n64/OcarinaOfTime/`:
`appimage: build` → `out/soh.appimage`, then `run` executes it from `runDir/`). "Done" = `make appimage`
yields `out/gzdoom.appimage`, and running it on the host (with a CLI-passed WAD) launches GZDoom with no
system-wide install.

## Context (cold-start) — why this is real work, not a flag flip

- **The n64 exemplar copies an AppImage its build already made.** Ship of Harkinian's own CMake emits a
  `*.appimage` artifact; the n64 `Makefile`'s `appimage` target just locates it
  (`/src/build-cmake/*.appimage` or `/src/_packages/*.appimage`) and copies it to `out/soh.appimage`
  (`chmod +x`). `run` then executes `../out/soh.appimage` from `runDir/` on the **host** (it needs a real
  display / GPU / audio).
- **GZDoom's CMake does NOT emit an AppImage.** The Phase-A build produces a plain `install/<type>/bin/gzdoom`
  + `lib64/libzmusic.so*` + the bundled `gzdoom.pk3` resources (see `games/gzdoom/CLAUDE.md`). So an AppImage
  here needs an explicit packaging step that bundles: the `gzdoom` binary, `gzdoom.pk3` (and the other
  bundled `.pk3`s), `libzmusic.so.1`, and the runtime shared libs (SDL2, OpenAL, FluidSynth, libvpx, GL) into
  an AppDir, writes an `AppRun` + `.desktop` + icon, and runs `appimagetool`/`linuxdeploy`.
- **Keep the container build; add to it.** The maintainer wants the existing `Dockerfile` + `Makefile` kept.
  The AppImage build runs in that image (it already has the toolchain + deps); this task only *adds* targets,
  it does not replace the container path.

## Open questions
1. Does upstream GZDoom ship any packaging help at the pin `g4.14.2` (a CPack config, a `dist/` script, a CI
   AppImage recipe) we can reuse, or is this fully hand-rolled? **Investigate first** (grep the checkout for
   `CPack`, `appimage`, `linuxdeploy`; check ZDoom's CI) — the answer sets the difficulty.
2. Tool choice: `linuxdeploy` + its GTK/GL plugins (heavier, resolves libs automatically) vs. a hand-built
   AppDir + `appimagetool` (more control, more manual lib-listing). Recommendation pends Q1.
3. Where does `gzdoom.pk3` live inside the AppImage, and does `-DSYSTEMINSTALL=ON`'s search path still find it
   from inside a mounted AppImage? (The Phase-A resource-half fix must survive relocation — verify the
   packaged binary finds its `.pk3` with no external config.)

## Plan (after go-ahead)
1. Answer Q1 (investigate upstream/CI packaging) and Q2 (pick the tool).
2. Add an `entrypoint/appimage.sh` that builds the AppDir from `install/Release/` and runs the packager;
   wire a `make appimage: build` target (produces `out/gzdoom.appimage`, `chmod +x`) and point `make run` at
   the AppImage from `runDir/` (mirroring the n64 Makefile). Gitignore `out/`.
3. Verify: `make appimage` → `out/gzdoom.appimage`; run it on the host with a CLI WAD → GZDoom launches, and
   it finds `gzdoom.pk3` with no system install (Q3).
4. Document in `games/gzdoom/CLAUDE.md` + `README.md`; note whether the AppImage is a host-run or can smoke
   under Xvfb.

## Related
- Parent task: `tasks/gzdoom-port-and-cli-wad-patch.md` (the port; Phase A2 = the native host scripts).
- Exemplar: `n64/OcarinaOfTime/Makefile` (`appimage`/`run` targets) and `n64/CLAUDE.md` (the podman AppImage
  build). Carrier facts: `games/gzdoom/CLAUDE.md`.
