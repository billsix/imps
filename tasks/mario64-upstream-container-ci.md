# SuperMario64: upstream a container-based CI (Dockerfile + workflow patch)

**Status:** proposed — FUTURE, not for the 2026-09-01 batch (maintainer:
"this work is not to happen yet, it is just to keep in mind")
**Priority:** 6
**Difficulty:** 5

## BLUF

Replace Ghostship's upstream Linux CI job with the equivalent container
build: upstream the project Dockerfile plus an updated workflow that
builds inside it, so the CI action is as repeatable/offline as possible
(deps frozen in image layers instead of apt-installed and built from
source on every ephemeral runner) and byte-matches the local podman
build. Both the Dockerfile and the workflow change are **standalone
upstream-bound patches** in this project's series, per the
patch-philosophy section of the master CLAUDE.md — upstreaming them IS
the goal.

## Context

- Upstream CI file: `Ghostship/.github/workflows/main.yml` — the build-linux job runs on ubuntu-latest, cpack -G External. Scope is
  the **Linux job only**; Windows/macOS/Switch jobs stay untouched.
- The imps Dockerfile this would upstream: tasked this same batch (`mario64-podman-appimage-build.md`). This task depends
  on that Dockerfile existing and being verified; sequence after it.
- Design points to settle at execution: where the image lives for CI
  (built in-workflow from the committed Dockerfile — simplest, fully
  self-contained — vs published to GHCR and pulled, faster); GitHub
  Actions `container:` key vs an explicit build+run step; pinning the
  base image by digest for the offline/repeatability goal; keeping the
  artifact-upload steps identical so upstream sees a drop-in change.
- **Acceptance strategy (maintainer, 2026-09-01): maximum fidelity to
  the existing CI job.** Same Ubuntu version as the workflow uses, same
  package list, same from-source library versions and flags, same build
  commands — a reviewer should see a zero-behavior-change refactor, not
  a redesign. The one deliberate deviation IS the pitch: freezing those
  steps into image layers (and pinning what CI leaves floating, like
  `ubuntu-latest`) is what buys reproducibility. Where the imps
  Dockerfile diverges from CI for local reasons (e.g. a newer-distro
  variant), upstream gets the CI-mirror variant — MajorasMask's
  `VARIANT=ci` split is the model.
- CI changes need upstream buy-in — shape the patches as a proposal
  (PR with rationale: reproducibility, dev/CI parity), like the banjo
  series was.

## Open questions

None until execution.
