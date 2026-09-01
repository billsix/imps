# SuperMario64: upstream a container-based CI (Dockerfile + workflow patch)

**Status:** proposed — FUTURE, not for the 2026-09-01 batch (William Emerison Six <billsix@gmail.com>:
"this work is not to happen yet, it is just to keep in mind")
**Priority:** 6
**Difficulty:** 5

## BLUF

Upstream a container-based Linux build for Ghostship as a standalone
patch adding **three in-repo files**: a **Makefile** (the full imps
target set — `image`/`build`/`appimage`/`image-export`/`image-import`/
`shell`/`run`/`clean`, minus the fetch/apply machinery, since the source
now ships in the same tree), the **Dockerfile** it drives, and the Linux
CI job refactored to **just call `make appimage`**. Local dev and CI then
run one identical path, and the build is as repeatable/offline as
possible (deps frozen in image layers instead of apt-installed and built
from source on every ephemeral runner). All three files are **standalone
upstream-bound patches** in this project's series, per the
patch-philosophy section of the master CLAUDE.md — upstreaming them IS
the goal.

## Context

- Upstream CI file: `Ghostship/.github/workflows/main.yml` — the build-linux job runs on ubuntu-latest, cpack -G External. Scope is
  the **Linux job only**; Windows/macOS/Switch jobs stay untouched.
- The imps Dockerfile this would upstream: **shipped and host-verified** (`SuperMario64/Dockerfile`); its build task is archived at `tasks/archive/mario64/2026/09/01/mario64-podman-appimage-build.md`.
- **The patch adds three in-repo files:**
  - a **`Makefile`** — the full imps target set (`image`, `build`,
    `appimage`, `image-export`/`image-import`, `shell`, `run`, `clean`,
    `distclean`) kept verbatim so a contributor gets the maintainer's
    local ergonomics, **minus `fetch.sh`/`apply.sh`**: the build context
    is the repo root (`-f <dir>/Dockerfile .`), not an external checkout,
    and `make appimage` builds the working tree as-is. Derive it from the
    imps `SuperMario64/Makefile` by removing the fetch auto-call and
    re-rooting `$(SRC)`/context to `.`.
  - the **`Dockerfile`** it drives — from the imps `SuperMario64/Dockerfile`
    (now `COPY`-based and host-build-clean as of 2026-09-01).
  - the **CI workflow** — the existing Linux job reduced to
    `checkout → make appimage → upload-artifact`, the upload step kept
    identical so upstream sees a drop-in. This **settles the old
    `container:`-key-vs-build+run design point**: the workflow calls
    `make`, the Makefile drives the container.
- **`CONTAINER_CMD` auto-detects podman→docker** (William Emerison Six <billsix@gmail.com>, 2026-09-01:
  podman on his systems; docker is fine where they use it — GitHub
  runners ship Docker, so `make appimage` runs in CI unchanged). e.g.
  `CONTAINER_CMD ?= $(shell command -v podman >/dev/null 2>&1 && echo podman || echo docker)`.
  imps's own `SuperMario64/Makefile` hardcodes `podman` — the upstreamed
  one must not.
- Design points still open at execution: where the image lives for CI
  (built in-workflow from the committed Dockerfile — simplest, fully
  self-contained — vs published to GHCR and pulled, faster); pinning the
  base image by digest for the offline/repeatability goal; where in the
  tree the Makefile/Dockerfile live (match upstream's conventions). (The
  `container:`-vs-build+run and container-engine choices are settled —
  see above.)
- **Acceptance strategy (William Emerison Six <billsix@gmail.com>, 2026-09-01): maximum fidelity to
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

None block starting. **Settled 2026-09-01:** the CI workflow just calls
`make appimage` (not a bare `container:` job); the Makefile carries the
full imps target set minus fetch/apply; `CONTAINER_CMD` auto-detects
podman→docker. Remaining choices are the execution-time design points in
Context.
