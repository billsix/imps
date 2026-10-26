#!/usr/bin/env bash
# Phase A of tasks/imps-upstreamable-stream-reorg.md: rename/split patch streams
# into one upstreamable-<slug>/ folder per PR unit. Pure rename+renumber of
# disjoint streams, so the applied tree must be byte-identical afterwards
# (proven by comparing check_patches_apply tree hashes). Re-runnable: each step
# is guarded, so a partial run can simply be re-run. Relative to repo root.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# set_subj <file> <label>  label="" -> [PATCH]; label="n/m" -> [PATCH n/m]
set_subj() {
  local f="$1" label="$2" repl
  if [ -z "$label" ]; then repl="[PATCH]"; else repl="[PATCH $label]"; fi
  sed -i "0,/^Subject: \[PATCH[^]]*\]/s||Subject: ${repl}|" "$f"
}

# mv_dir <src> <dest>  straight folder rename (only if not already done)
mv_dir() { if [ -d "$1" ] && [ ! -e "$2" ]; then git mv "$1" "$2"; fi; }

# move_patch <srcfile> <destdir> <newnum> <label>
move_patch() {
  local src="$1" destdir="$2" newnum="$3" label="$4" base suffix dest
  if [ ! -e "$src" ]; then echo "skip (already moved): $src"; return 0; fi
  base=$(basename "$src"); suffix=${base#[0-9][0-9][0-9][0-9]-}
  mkdir -p "$destdir"; dest="$destdir/${newnum}-${suffix}"
  git mv "$src" "$dest"; set_subj "$dest" "$label"; git add "$dest"
}

# drop_candidates <patchesdir>  remove the emptied upstream-candidates/ (+ its tracked .keep)
drop_candidates() {
  local d="$1/upstream-candidates"
  [ -d "$d" ] || return 0
  if [ -e "$d/.keep" ] && git ls-files --error-unmatch "$d/.keep" >/dev/null 2>&1; then
    git rm -f "$d/.keep" >/dev/null
  fi
  rm -rf "$d"
}

# ---- SuperMario64 ----
P=n64/SuperMario64/patches
mv_dir "$P/standard-c" "$P/upstreamable-standard-c"
move_patch "$P/upstream-candidates/0001-ci-linux-build-the-Linux-AppImage-in-a-reproducible-.patch" "$P/upstreamable-ci-appimage"        0001 ""
move_patch "$P/upstream-candidates/0002-docs-add-libshaderc-devel-to-the-Fedora-build-depend.patch" "$P/upstreamable-fedora-shaderc-deps" 0001 ""
drop_candidates "$P"

# ---- MajorasMask ----
P=n64/MajorasMask/patches
move_patch "$P/upstream-candidates/0001-ci-linux-build-the-Linux-AppImage-in-a-reproducible-.patch"  "$P/upstreamable-ci-appimage" 0001 ""
move_patch "$P/upstream-candidates/0002-Fix-silent-SFX-and-several-64-bit-host-audio-crashes.patch" "$P/upstreamable-audio-64bit"  0001 ""
drop_candidates "$P"

# ---- BanjoKazooie ----  CI = one unit; the 4 JeodC-reviewed patches = one unit (fixonfedora)
P=n64/BanjoKazooie/patches
move_patch "$P/upstream-candidates/0001-ci-linux-build-the-Linux-AppImage-in-a-reproducible-.patch"   "$P/upstreamable-ci-appimage" 0001 ""
move_patch "$P/upstream-candidates/0002-fix-build-dependencies-in-instructions-for-Fedora.patch"       "$P/upstreamable-fixonfedora" 0001 "1/4"
move_patch "$P/upstream-candidates/0003-CMakeLists-stamp-bk.o2r-with-the-project-version-in-.patch"     "$P/upstreamable-fixonfedora" 0002 "2/4"
move_patch "$P/upstream-candidates/0004-core1-graphics_thread-fix-post-import-freeze-from-OS.patch"     "$P/upstreamable-fixonfedora" 0003 "3/4"
move_patch "$P/upstream-candidates/0005-shortened-comments-per-request-from-JeodC.patch"                "$P/upstreamable-fixonfedora" 0004 "4/4"
drop_candidates "$P"

# ---- OcarinaOfTime ----
P=n64/OcarinaOfTime/patches
mv_dir "$P/standard-c" "$P/upstreamable-standard-c"
mv_dir "$P/personal"   "$P/upstreamable-rename-decomp"
if [ ! -f "$P/upstreamable-rename-decomp/DEPENDS" ]; then
  printf 'upstreamable-standard-c\n' > "$P/upstreamable-rename-decomp/DEPENDS"
  git add "$P/upstreamable-rename-decomp/DEPENDS"
fi
move_patch "$P/upstream-candidates/0001-ci-linux-build-the-Linux-AppImage-in-a-reproducible-.patch" "$P/upstreamable-ci-appimage" 0001 ""
drop_candidates "$P"

# ---- PaperMario ----  CI = one unit; the 2 extractor patches = one PaperBoat PR
P=n64/PaperMario/patches
move_patch "$P/upstream-candidates/0001-ci-linux-build-the-Linux-AppImage-in-a-reproducible-.patch"   "$P/upstreamable-ci-appimage"   0001 ""
move_patch "$P/upstream-candidates/0002-extractor-honour-a-ROM-path-on-the-command-line-on-L.patch"    "$P/upstreamable-rom-cli-import" 0001 "1/2"
move_patch "$P/upstream-candidates/0003-extractor-refuse-a-picked-ROM-that-matches-no-config.patch"    "$P/upstreamable-rom-cli-import" 0002 "2/2"
drop_candidates "$P"

echo "=== new stream layout ==="
for g in SuperMario64 MajorasMask BanjoKazooie OcarinaOfTime PaperMario; do
  echo "--- $g ---"
  for s in n64/$g/patches/*/; do printf '  %-32s %s patch(es)%s\n' "$(basename "$s")" "$(ls "$s"*.patch 2>/dev/null | wc -l)" "$([ -f "$s/DEPENDS" ] && echo "  DEPENDS=$(tr '\n' ',' < "$s/DEPENDS")")"; done
done
