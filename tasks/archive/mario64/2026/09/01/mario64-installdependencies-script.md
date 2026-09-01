# SuperMario64: installdependencies.sh — Fedora dnf install script

**Status:** done — verified 2026-09-01: a fresh fedora:44 container ran
installdependencies.sh then full configure + GeneratePortO2R + complete
build, all green on the first run (shaderc-devel and the other
sandbox-discovered deps were already in the list; the libshaderc doc gap
is patch 0004 of the series). Archived same day.
**Priority:** 3
**Difficulty:** 2

## BLUF

Add `SuperMario64/installdependencies.sh`: a Fedora `dnf install` script
derived from the project's own build doc, so `installdependencies.sh` →
`build.sh` → `run.sh` works on a fresh Fedora box. Sibling of the
ocarina task (`ocarina-installdependencies-script.md`) — same shape.

## Context

- **The doc:** `Ghostship/docs/building.md` (lowercase name), Fedora
  section at lines ~102-109 — a ready gcc dnf line: gcc gcc-c++ git
  cmake ninja-build lsb_release SDL2-devel libpng-devel libzip-devel
  libzip-tools nlohmann-json-devel tinyxml2-devel spdlog-devel
  boost-devel libogg-devel libvorbis-devel mbedtls-devel.
- **Known gap in the doc (found building in the sandbox 2026-09-01):**
  the list was missing **`libshaderc-devel`** — the pin's libultraship
  (1.3.1-544) has a Vulkan backend that includes `shaderc/shaderc.hpp`
  and the build fails without it. **Already fixed as patch 0004 of the
  series** (`0004-docs-add-libshaderc-devel-...patch`, maintainer
  request 2026-09-01) — so the patched checkout's `docs/building.md`
  Fedora lines are complete, and the install script derives from the
  post-`apply.sh` doc, like banjo's does.
- Configure also needs network (`gamecontrollerdb.txt` download) — not a
  package matter, but the verification step must allow it.

## Steps

1. Read `docs/building.md` fully; inline the package list in the script
   with a comment citing the doc and the pin, plus `libshaderc-devel`
   with its own comment.
2. Guard `command -v dnf`, fail loudly on non-dnf hosts.
3. Verify in a fresh `fedora:44` container (nested podman):
   `installdependencies.sh` → `./fetch.sh && ./apply.sh && ./build.sh`.
4. Keep the approach consistent with whatever the ocarina sibling task
   decides (inline list recommended there too).

## Open questions

None.
