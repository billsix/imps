# MajorasMask: installdependencies.sh — Fedora dnf install script

**Status:** proposed — needs go-ahead
**Priority:** 3
**Difficulty:** 2

## BLUF

Add `MajorasMask/installdependencies.sh`: a Fedora `dnf install` script
derived from the project's own build doc, so `installdependencies.sh` →
`build.sh` → `run.sh` works on a fresh Fedora box. Sibling of the
ocarina task (`ocarina-installdependencies-script.md`) — same shape.

## Context

- **The doc:** `2ship2harkinian/docs/BUILDING.md`, Fedora section at
  lines ~105-112 — gcc dnf line: gcc gcc-c++ git cmake ninja-build
  lsb_release SDL2-devel libpng-devel libzip-devel libzip-tools
  nlohmann-json-devel tinyxml2-devel spdlog-devel.
- Notably **shorter** than the sibling ports' lists (no boost / ogg /
  vorbis / mbedtls) — verify against a real fresh-box build rather than
  trusting the doc; the maintainer's Fedora-44 host built fine, but a
  minimal container may reveal gaps (that is exactly what the
  verification step exists to catch — same class of doc bug as banjo's
  missing SDL2_net and Ghostship's missing libshaderc).

## Steps

1. Read `docs/BUILDING.md` fully; inline the list, cite doc + pin.
2. Guard `command -v dnf`, fail loudly on non-dnf hosts.
3. Verify in a fresh `fedora:44` container (nested podman):
   `installdependencies.sh` → `./fetch.sh && ./apply.sh && ./build.sh`;
   add any packages the doc omitted, each with a comment noting it was
   found missing (candidate upstream doc patch).
4. Keep the approach consistent with the ocarina sibling task's choice.

## Open questions

None.
