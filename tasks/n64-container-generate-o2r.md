# Follow-up: have the upstream `make appimage` generate the port o2r itself (not accept a CI-supplied one)

**Status:** proposed — needs go-ahead (follow-up to `tasks/n64-upstreamable-appimage-make-target.md`)
**Priority:** 7 **Difficulty:** 5
**Created:** 2026-10-26 (William Emerison Six <billsix@gmail.com>, decision during the appimage-make-target
work: "accept the CI-supplied [o2r] for now, make a follow up task to generate it itself").

## BLUF

The upstreamable `make appimage` target delivered by
`tasks/n64-upstreamable-appimage-make-target.md` **accepts** each port's asset archive (`ghostship.o2r`,
`soh.otr`/`.o2r`, …) as an input — for ports whose CI builds that archive in a **separate** job and
hands it to the Linux build job (SuperMario64's `generate-port-o2r` is the clear case). That keeps the
first patch a minimal, CI-faithful refactor. This follow-up makes `make appimage` **self-contained**:
build the port archive **inside the container** (the relevant CMake target — e.g. `GeneratePortO2R` for
Ghostship, `Generate*Otr` for the others) so one `make appimage` yields a complete AppImage from a bare
checkout, with no cross-job artifact dependency. "Done" = each port's `make appimage` produces its own
asset archive and the Linux CI job can be simplified further (drop the separate generate job + the
download step, or keep the job and let it call `make`), still emitting an identical artifact.

## Context

- **Why deferred:** doing it in the first patch would diverge from the existing CI job structure (which
  splits archive-generation into its own job, often so Windows/macOS/other jobs can reuse the one
  artifact). Accepting the supplied archive keeps the first upstream PR a "zero-behavior-change"
  refactor (the acceptance principle in the parent task). Generating it in-container is a *second*,
  larger change that touches the job graph.
- **The imps-side Makefiles already do this locally** — e.g. `n64/SuperMario64/Makefile`'s `build`
  target runs `cmake --build /src/build-cmake --target GeneratePortO2R` because there is no CI job
  supplying the o2r to a local build. So the mechanism is known; this task is about shaping it for
  upstream and reconciling it with each repo's multi-platform job graph (the generated archive is often
  shared across the Windows/macOS/Linux jobs, so folding it into the Linux `make appimage` must not
  break the others).
- **OcarinaOfTime already satisfies the goal** (found during the 2026-10-27 build verification): its
  `make -C docker build` **self-generated** `build-cmake/soh/soh.o2r` with no injection, so its
  `make appimage` already produces a complete AppImage from a bare checkout. So OoT needs no work here;
  the task is really about SuperMario64 / MajorasMask / BanjoKazooie (the ports whose build verification
  needed the port-o2r injected), and PaperMario already self-generates too. Start by diffing what OoT's
  build does (the `GenerateSohOtr`/equivalent target wired as a build dependency) against the others.
- **Depends on:** `tasks/n64-upstreamable-appimage-make-target.md` landing first (this edits the
  Makefile/CI it adds).

## Open questions

1. Per port: is the asset archive consumed by **other** platform jobs (so a separate generate job still
   earns its place), or only by Linux (so it can fold entirely into `make appimage`)? Decide per repo.
2. Keep the generate job and have it call `make <archive-target>`, or drop it and generate inside
   `make appimage`? (Likely per-port, driven by Q1.)
