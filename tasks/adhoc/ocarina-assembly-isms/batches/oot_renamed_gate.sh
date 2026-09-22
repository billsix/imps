#!/usr/bin/env bash
# Gate the 18 files the rename stream RENAMED (no compile command under their new name): compile
# each on imps-applied vs imps-personal-old using the command recorded for its OLD path.
set -u
export OOT_ANY_BRANCH=1
. "$(dirname "$0")/oot_lib.sh"
P="$IMPS/n64/OcarinaOfTime"
git checkout -q imps-applied
ident=0; diff=0
paste -d' ' <(grep '^rename from' "$P/patches/personal/0001-"*.patch | awk '{print $3}') \
            <(grep '^rename to'   "$P/patches/personal/0001-"*.patch | awk '{print $3}') |
while read -r old new; do
    r=$(cd "$IMPS" && ASMDIFF_CMD_FROM="$old" bash "$TOOL/asmdiff.sh" "$new" imps-personal-old 2>&1 | head -1)
    case "$r" in IDENTICAL*) echo "OK   $new (cmd of $old)";; *) echo "DIFF $new: $r";; esac
done | tee "$W/oot_renamed_gate.txt"
echo "renamed-files gate: $(grep -c '^OK' "$W/oot_renamed_gate.txt") identical, $(grep -c '^DIFF' "$W/oot_renamed_gate.txt") differ"
