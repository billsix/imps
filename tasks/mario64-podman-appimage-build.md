# SuperMario64: podman AppImage build like MajorasMask's and BanjoKazooie's

**Status:** proposed — approved for the 2026-09-01 work-session batch
**Priority:** 4
**Difficulty:** 4

## BLUF

Give `SuperMario64/` a `Dockerfile` + `Makefile` podman build producing an
AppImage, derived from Ghostship's own CI workflow on the same OS version
CI uses — the fourth instance of the now-proven pattern (MajorasMask
shipped it, BanjoKazooie's is verified end to end incl. a host run,
OcarinaOfTime's is tasked in this same batch). Done when `make appimage`
produces `out/ghostship.appimage` from the patched checkout, verified
nested in the sandbox; the host run is the maintainer's closing check.

## Context

- **Templates:** `BanjoKazooie/Dockerfile` + `Makefile` (closest sibling —
  also an ubuntu-latest CI, also GeneratePortO2R done in-container) and
  `MajorasMask/`'s originals. Carry the `USERNS_FLAG` nested-podman
  convention (see `BanjoKazooie/CLAUDE.md` "Podman build").
- **The CI file:** `Ghostship/.github/workflows/main.yml` — the
  build-linux job at ~line 347 runs on **ubuntu-latest** (resolve to the
  concrete LTS, 24.04, with the same reasoning recorded in banjo's
  Dockerfile header) and packages via `cpack -G External` →
  `build-cmake/*.appimage` → `ghostship.appimage` (:430-433). Read the
  job fully: apt list (inline vs a deps file — 2ship had
  `apt-deps.txt`, Lighthouse inlined), any from-source library builds,
  and the o2r generation step.
- **Known dependency lessons from the sandbox builds** (Fedora names;
  find the Ubuntu equivalents in CI's own list): ixwebsocket needs
  mbedTLS at configure, and the LUS Vulkan backend needs shaderc
  headers. CI presumably installs both — if its list lacks either, that
  is a doc/CI gap worth noting like the libshaderc patch (0004).
- cmake configure downloads `gamecontrollerdb.txt` — the container build
  needs network at configure (fine; note it).
- `make build` compiles whatever the checkout holds — pin + applied
  series, per the agent contract.

## Steps

1. Read the build-linux job of `main.yml` fully; derive the Dockerfile
   (FROM ubuntu:24.04, CI's deps, any from-source libs).
2. Makefile from the banjo template: SRC = `Ghostship/`, image
   `ghostship-builder`, GeneratePortO2R in-container, `cpack -G
   External`, `out/ghostship.appimage`, `USERNS_FLAG` +
   `PODMAN_RUN_FLAGS` threading, gitignore entries (`/out/`, image
   tars) — added UP FRONT this time, not after a `git add` accident.
3. Verify nested: `make image` → `make build` (patched tree) →
   `make appimage`.
4. Update `SuperMario64/README.md`/`CLAUDE.md` (podman section like the
   siblings') and the master docs.
5. Maintainer's closing check: `make run` on the host.

## Open questions

None.
