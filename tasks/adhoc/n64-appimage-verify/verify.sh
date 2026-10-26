#!/usr/bin/env bash
# Nested, from-scratch AppImage build verification for the four unverified N64
# ports (SuperMario64 was verified earlier). For each port: wipe the build dir,
# `make -C docker build` in the CI-mirror container, inject the port-o2r at the
# path cpack expects (copied from the checkout-root canonical copy; PaperMario
# self-generates and needs none), `make -C docker appimage`, then `file` the
# emitted AppImage to confirm it is a real ELF. Sequential (each build uses all
# cores). Relative to the repo root; no hardcoded container-absolute paths.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && git rev-parse --show-toplevel)"
cd "$ROOT"
LOG="$ROOT/tasks/adhoc/n64-appimage-verify/run.log"
: > "$LOG"

log() { printf '%s  %s\n' "$(date +%H:%M:%S)" "$*" | tee -a "$LOG"; }

# port|checkout|builddir(rel checkout)|O2R(rel checkout; empty=self-gen)|root-o2r(rel checkout)
PORTS=(
  "MajorasMask|2ship2harkinian|build-cmake|build-cmake/mm/2ship.o2r|2ship.o2r"
  "BanjoKazooie|Lighthouse|build-cmake|build-cmake/lighthouse.o2r|lighthouse.o2r"
  "OcarinaOfTime|Shipwright|build-cmake|build-cmake/soh/soh.o2r|soh.o2r"
  "PaperMario|PaperBoat|build/ninja-release||"
)

overall=0
for row in "${PORTS[@]}"; do
  IFS='|' read -r port co builddir o2r rooto2r <<<"$row"
  cod="$ROOT/n64/$port/$co"
  dockerd="$cod/docker"
  log "=== START $port ($co) ==="

  rm -rf "$cod/$builddir" "$cod/_packages" "$cod/out" 2>/dev/null

  if [ -n "$o2r" ]; then
    # accept-only: build, inject o2r, then package
    if ! make -C "$dockerd" build >>"$LOG" 2>&1; then
      log "BUILD_FAIL $port"; overall=1; continue
    fi
    if [ ! -f "$cod/$o2r" ]; then
      if [ -f "$cod/$rooto2r" ]; then
        mkdir -p "$(dirname "$cod/$o2r")"
        cp "$cod/$rooto2r" "$cod/$o2r"
        log "injected port-o2r -> $o2r (from $rooto2r)"
      else
        log "O2R_MISSING $port (no $rooto2r to inject)"; overall=1; continue
      fi
    else
      log "port-o2r already present at $o2r"
    fi
  fi

  if ! make -C "$dockerd" appimage >>"$LOG" 2>&1; then
    log "APPIMAGE_FAIL $port"; overall=1; continue
  fi

  shopt -s nullglob
  imgs=("$cod"/out/*.appimage "$cod"/out/*.AppImage)
  shopt -u nullglob
  if [ "${#imgs[@]}" -eq 0 ]; then
    log "NO_ARTIFACT $port"; overall=1; continue
  fi
  img="${imgs[0]}"
  desc="$(file -b "$img")"
  sz="$(du -h "$img" | cut -f1)"
  if printf '%s' "$desc" | grep -q 'ELF'; then
    log "VERIFY_OK $port  $img  ($sz; $desc)"
  else
    log "VERIFY_FAIL $port  $img  (not ELF: $desc)"; overall=1
  fi
done

log "=== DONE overall=$overall ==="
exit "$overall"
