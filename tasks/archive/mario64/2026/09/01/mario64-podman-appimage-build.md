# SuperMario64: podman AppImage build like MajorasMask's and BanjoKazooie's

**Status:** DONE — host-confirmed 2026-09-01 (William Emerison Six
<billsix@gmail.com>): `make appimage` produces `out/ghostship.appimage`
(verified nested) and the on-host build succeeds; it launches on the
Vulkan backend (RADV Vulkan-hang caveat → `SuperMario64/CLAUDE.md`).
The first host attempt failed at the requirements.txt bind-mount step
under SELinux — the sandbox's `:Z` EXTRA_MOUNTS relabel
(`container_file_t:c1022,c1023`) poisoning the repo. The **durable fix**
was switching that Dockerfile step from `RUN --mount=type=bind` to
`COPY` (read by buildah unconfined), applied across all four Dockerfiles
(master CLAUDE.md drift table + the `SuperMario64/Dockerfile` comment);
an earlier host `restorecon -R` + `:z` launcher change was a stopgap.
Separately, the install-script verification's fedora
container had left Fedora-built LUS artifacts INSIDE
`Ghostship/libultraship/` (LUS 482+/fork builds into its source dir),
which broke the next nested build with a monocypher PIE link error —
submodule `git clean -fdx` + `git checkout -- src/generate_keys_header`
+ `build-cmake/` wipe, then a from-scratch nested `make appimage` went
green (909 steps, fresh out/ghostship.appimage). Gotcha recorded in the
master CLAUDE.md agent contract. Both hurdles are cleared. Outcome
details in
`SuperMario64/CLAUDE.md` ("Podman build") incl. two gaps found: Kitware
cmake (CMP0159 needs >= 3.30, noble ships 3.28) and the noble
shaderc/spirv-tools ABI skew solved with a libshaderc_shared.so compat
symlink.
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
