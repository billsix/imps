#!/usr/bin/env bash
# Export the SuperMario64 standard-c stream from imps-standard-c into imps, then replay the WHOLE
# series (all streams, in ORDER) from the bare pin with the project's own apply.sh — the Phase C
# check that the personal streams (cheats, book) still apply on top. Proves the standard-c part is
# byte-identical to the branch, then returns the checkout to imps-standard-c.
set -e
SM=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)/n64/SuperMario64
cd "$SM/Ghostship"
PIN=$(sed -n 's/^PIN_SHA=//p' ../fetch.sh)
N=$(git rev-list --count "$PIN"..imps-standard-c)
echo "pin $PIN ; standard-c commits: $N"

# --- export ---
rm -f ../patches/standard-c/*.patch
git format-patch --no-cover-letter --base="$PIN" "$PIN"..imps-standard-c -o ../patches/standard-c/ >/dev/null
ls ../patches/standard-c/ | wc -l

# --- replay: bare pin + apply.sh (all streams) ---
WORK_TREE=$(git rev-parse imps-standard-c^{tree})
git checkout -q --detach "$PIN"
( cd "$SM" && ./apply.sh ) 2>&1 | tail -8
# the first N commits above the pin are the standard-c stream; their tree must equal the branch
STDC_HEAD=$(git rev-list --reverse "$PIN"..HEAD | sed -n "${N}p")
APPLIED_TREE=$(git rev-parse "$STDC_HEAD"^{tree})
echo "standard-c tree: branch $WORK_TREE applied $APPLIED_TREE"
[ "$WORK_TREE" = "$APPLIED_TREE" ] && echo "BYTE-IDENTICAL: standard-c replays exactly" || { echo "MISMATCH"; exit 1; }
echo "series on top of pin: $(git rev-list --count "$PIN"..HEAD) commits"
git log --oneline "$PIN"..HEAD | tail -n +1 | head -40

# --- back to the work branch ---
git checkout -q imps-standard-c
git status --short | grep -v '^?? \| libultraship' || echo "clean"
