# OcarinaOfTime: podman AppImage build like MajorasMask's

**Status:** implemented — verified nested through `make appimage`
(out/soh.appimage, 32 MB, patched tree); awaiting the maintainer's
on-host run. Note (2026-09-01 evening): his first HOST build of the
sibling mario64 project failed on the sandbox's `:Z`-poisoned SELinux
labels (see that task) — fixed host-wide via `restorecon -R` + a `:z`
launcher, so this project's host run should be unaffected now. Ocarina's
checkout has NO submodule build-pollution (its older LUS doesn't build
into the source tree — checked). Archive when the host run passes. Outcome details in
`OcarinaOfTime/CLAUDE.md` ("Podman build") incl. three
runner-pre-provides gaps found: Kitware cmake (jammy 3.22 < 3.26),
python3, imagemagick (configure-time AppImage icon).
**Priority:** 4
**Difficulty:** 4

## BLUF

Give `OcarinaOfTime/` a `Dockerfile` + `Makefile` podman build producing an
AppImage, the way `MajorasMask/` has one — derived from the project's own
CI workflow, **on the same OS version CI uses**. Done when
`make appimage` in `OcarinaOfTime/` produces a runnable `out/soh.appimage`
from the patched checkout.

## Context

Read first:

- **The template:** `MajorasMask/Dockerfile` + `MajorasMask/Makefile` — the
  maintainer's proven pattern: base image mirroring the CI job's OS, apt
  list bind-mounted from the checkout's own CI deps file where one exists,
  from-source builds of the libs CI builds from source, `PODMAN_RUN_FLAGS`
  threaded into runs, `--userns=keep-id`, per-variant image tags,
  `make image/build/appimage/run/image-export/import`. Provenance notes in
  `MajorasMask/CLAUDE.md` ("Podman build").
- **The CI file to derive from:**
  `Shipwright/.github/workflows/generate-builds.yml` — its Linux job runs
  on **ubuntu-22.04** (line 113; there is a second 22.04 job at line 11 —
  identify which builds the Linux artifact). Also look at
  `test-builds-on-distros.yml` for per-distro dependency lists.
- The checkout is at the imps pin (`acdbc651d`, torch-based asset
  pipeline); `make build` should compile whatever the checkout holds
  (pin + applied patches), per the agent contract in the master
  `CLAUDE.md`.

## Steps

1. Read the Linux job of `generate-builds.yml`: base OS, compiler pins,
   apt packages, from-source library builds, the cpack/AppImage step, and
   whether a deps list file exists in-repo (MM had
   `.github/workflows/apt-deps.txt`; Shipwright may inline its list —
   then the Dockerfile inlines it too, with a comment citing the workflow
   file and pin).
2. Write `OcarinaOfTime/Dockerfile` (FROM the CI job's ubuntu version) +
   `Makefile` adapted from MajorasMask's (SRC = `Shipwright/`, image
   context = the checkout, `soh`-named image/artifacts).
3. Wire the AppImage step the way CI does it (SoH generates
   `appimage-generate.cmake` in the build dir; MM used `cpack -G External`).
4. Verify: `make appimage` from the patched checkout; run the AppImage on
   the host from `runDir/`.
5. Update `OcarinaOfTime/README.md`/`CLAUDE.md` (podman section, like MM's)
   and the master docs.

## Open questions

1. None yet — variant split (CI-mirror vs modern-OS, like MM's
   `VARIANT=2604`) can come later; start with the CI-mirror only.
