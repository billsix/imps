#!/usr/bin/env bash
#
# verify_appimage_builds.sh -- nested, from-scratch build of each N64 port's Linux
# AppImage via its upstreamable `make -C docker appimage`, proving the
# `upstreamable-ci-appimage` unit actually produces a valid AppImage.
#
# WHEN TO RUN
#   After a pin bump (the derived-artifact-drift rule, n64/CLAUDE.md), or when the
#   docker/ Dockerfile/Makefile of any port changes. Promoted from the one-shot
#   tasks/adhoc/n64-appimage-verify/ harness after the 2026-10-27 verification.
#
# WHAT IT DOES, per port
#   Wipes the build dir, `make -C <checkout>/docker build`, injects the port asset
#   o2r at the path cpack expects (from the checkout-root copy) for the accept-only
#   ports, `make -C <checkout>/docker appimage`, then `file`s the output to confirm
#   a real ELF. OcarinaOfTime's build self-generates its o2r (no injection) and
#   PaperMario self-generates paperboat.o2r in-build.
#
# O2R PREREQUISITE
#   Like `make appimage` itself, the accept-only ports (SuperMario64, MajorasMask,
#   BanjoKazooie) consume a supplied port-o2r; this injects the checkout-root copy
#   if present, else reports O2R_MISSING. Generating it in-container is the
#   follow-up tasks/n64-container-generate-o2r.md (OoT already does).
#
# USAGE
#   tools/verify_appimage_builds.sh [Project ...]     # default: all five ports
#
# Requires nested podman (NESTED_PODMAN=1 is exported by the sandbox). LONG: each
# image builds SDL2/tinyxml2/libzip from source. Per-port logs: /tmp/verify-appimage-<Port>.log.
# Never touches runDir/ (a sibling of the checkout). Exits non-zero if any port fails.
set -uo pipefail
cd "$(dirname "$0")/.."
ROOT=$PWD

# Project|checkout|builddir(rel checkout)|O2R(rel checkout; empty=self-gen)|root-o2r(rel checkout)
ALL=(
  "SuperMario64|Ghostship|build-cmake|ghostship.o2r|ghostship.o2r"
  "MajorasMask|2ship2harkinian|build-cmake|build-cmake/mm/2ship.o2r|2ship.o2r"
  "BanjoKazooie|Lighthouse|build-cmake|build-cmake/lighthouse.o2r|lighthouse.o2r"
  "OcarinaOfTime|Shipwright|build-cmake|build-cmake/soh/soh.o2r|soh.o2r"
  "PaperMario|PaperBoat|build/ninja-release||"
)

want=("$@")
overall=0
for row in "${ALL[@]}"; do
  IFS='|' read -r port co builddir o2r rooto2r <<<"$row"
  if [ "${#want[@]}" -gt 0 ]; then
    skip=1; for w in "${want[@]}"; do [ "$w" = "$port" ] && skip=0; done
    [ "$skip" -eq 1 ] && continue
  fi
  cod="$ROOT/n64/$port/$co"
  dockerd="$cod/docker"
  log="/tmp/verify-appimage-$port.log"
  echo "=== $port ($co) -> $log ==="
  [ -d "$dockerd" ] || { echo "  SKIP $port (no $dockerd -- run ./fetch.sh && ./apply.sh)"; continue; }
  rm -rf "$cod/$builddir" "$cod/_packages" "$cod/out" 2>/dev/null

  if [ -n "$o2r" ]; then
    if ! make -C "$dockerd" build >"$log" 2>&1; then echo "  BUILD_FAIL $port (see $log)"; overall=1; continue; fi
    if [ ! -f "$cod/$o2r" ]; then
      if [ -f "$cod/$rooto2r" ]; then
        mkdir -p "$(dirname "$cod/$o2r")"; cp "$cod/$rooto2r" "$cod/$o2r"
        echo "  injected port-o2r -> $o2r (from $rooto2r)"
      else
        echo "  O2R_MISSING $port (no $rooto2r to inject; supply O2R= or generate it)"; overall=1; continue
      fi
    fi
  fi

  if ! make -C "$dockerd" appimage >>"$log" 2>&1; then echo "  APPIMAGE_FAIL $port (see $log)"; overall=1; continue; fi

  shopt -s nullglob
  imgs=("$cod"/out/*.appimage "$cod"/out/*.AppImage)
  shopt -u nullglob
  if [ "${#imgs[@]}" -eq 0 ]; then echo "  NO_ARTIFACT $port"; overall=1; continue; fi
  desc="$(file -b "${imgs[0]}")"
  if printf '%s' "$desc" | grep -q ELF; then
    echo "  OK $port  ${imgs[0]}  ($(du -h "${imgs[0]}" | cut -f1); $desc)"
  else
    echo "  VERIFY_FAIL $port  ${imgs[0]}  (not ELF: $desc)"; overall=1
  fi
done

echo "=== overall=$overall ==="
exit "$overall"
