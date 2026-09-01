# BanjoKazooie: installdependencies.sh — Fedora dnf install script

**Status:** proposed — needs go-ahead
**Priority:** 3
**Difficulty:** 2

## BLUF

Add `BanjoKazooie/installdependencies.sh`: a Fedora `dnf install` script
derived from the project's own build doc, so `installdependencies.sh` →
`build.sh` → `run.sh` works on a fresh Fedora box. Sibling of the
ocarina task (`ocarina-installdependencies-script.md`) — same shape.

## Context

- **The doc:** `Lighthouse/docs/BUILDING.md`, Fedora section at lines
  ~103-110. **In the PATCHED checkout this already includes the
  maintainer's own fix** — patch 0001 of the series added
  `SDL2_net SDL2_net-devel` to the gcc line — so derive the list from
  the checkout **after `apply.sh`**, not from pristine upstream.
- **Known follow-up the patch didn't cover:** the *clang* dnf line in
  the same section still lacks SDL2_net (noted during the banjo study,
  2026-09-01). The script only needs one toolchain (gcc), but if an
  upstream doc follow-up is ever sent, that line is the candidate.
- Sandbox caveat (from `BanjoKazooie/CLAUDE.md`): environments without
  SDL2_net can build with `-DUSE_NETWORKING=OFF` — worth a one-line
  comment in the script.

## Steps

1. Read `docs/BUILDING.md` (patched) fully; inline the gcc list, cite
   doc + pin + patch 0001.
2. Guard `command -v dnf`, fail loudly on non-dnf hosts.
3. Verify in a fresh `fedora:44` container (nested podman):
   `installdependencies.sh` → `./fetch.sh && ./apply.sh && ./build.sh`.
4. Keep the approach consistent with the ocarina sibling task's choice.

## Open questions

None.
