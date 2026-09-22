#!/usr/bin/env bash
# One-shot (2026-09-23): promote the reusable assembly-isms tooling from the two task-scoped adhoc
# dirs into tools/, and save the one-shot batch runners (which lived only in the session
# scratchpad) under the adhoc dirs with RELATIVE paths. Idempotent: every move is guarded.
#
#   tools/asmdiff.sh, tools/asmdiff_normalise.py   the codegen gate (was tasks/adhoc/mario64-assembly-isms/)
#   tools/asmdiff_tree.sh                          gate every file that differs between two refs
#   tools/resolve_rename_conflicts.py              mechanical 3-way resolution for a rename stream
#   tools/standard-c/<class>.py                    the per-class rewrite tools (both projects)
#   tasks/adhoc/<slug>/batches/                    the batch runners + patch scripts, paths relativised
#
# usage: bash tasks/adhoc/standard-c-tooling-promotion/promote.sh [<scratchpad-dir>]
set -u
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
SCRATCH=${1:-}
M=tasks/adhoc/mario64-assembly-isms; O=tasks/adhoc/ocarina-assembly-isms
mv_if() { [ -e "$1" ] && ! [ -e "$2" ] && { mkdir -p "$(dirname "$2")"; git mv "$1" "$2"; echo "moved $1 -> $2"; } || true; }

mkdir -p tools/standard-c
mv_if "$M/asmdiff.sh"            tools/asmdiff.sh
mv_if "$M/asmdiff_normalise.py"  tools/asmdiff_normalise.py
mv_if "$O/resolve_rename_conflicts.py" tools/resolve_rename_conflicts.py
for t in drop_register drop_true_false_cmp drop_filler_locals rename_in_function; do mv_if "$M/$t.py" "tools/standard-c/$t.py"; done
for t in drop_empty_if drop_pad_locals fold_return_bool flip_yoda merge_nested_ifs; do mv_if "$O/$t.py" "tools/standard-c/$t.py"; done
# asmdiff.sh: it cd'd to the repo root via ../../.. from tasks/adhoc/<slug>; from tools/ it is ..
sed -i 's|cd "$(dirname "$0")/../../.."                       # repo root|cd "$(dirname "$0")/.."                             # repo root|' tools/asmdiff.sh
sed -i 's|bash tasks/adhoc/mario64-assembly-isms/asmdiff.sh|bash tools/asmdiff.sh|' tools/asmdiff.sh
grep -q 'dirname "$0")/.."' tools/asmdiff.sh || echo "!! asmdiff.sh root cd not rewritten"

# --- the batch runners from the session scratchpad ---------------------------------------------
if [ -n "$SCRATCH" ] && [ -d "$SCRATCH" ]; then
    mkdir -p "$M/batches" "$O/batches"
    for f in batch1_register.sh batch2_matching.sh batch2b.sh batch2b_full.sh batch2c.sh batch3_goto.sh batch4_cond.sh \
             batch5_bool.sh batch6.sh batch7.sh batch8.sh batch9.sh batch10.sh \
             patch_batch2.py patch_batch3.py patch_batch4.py patch_batch6.py patch_batch7.py patch_batch8.py patch_batch10.py \
             sm64_export_and_replay.sh update_progress.py; do
        [ -f "$SCRATCH/$f" ] && cp -n "$SCRATCH/$f" "$M/batches/$f"; done
    for f in oot_lib.sh oot_batch_bool.sh oot_batch_emptyif.sh oot_batch_cf.sh oot_batch_cf2.sh oot_batch_nb.sh oot_batch_nb2.sh \
             oot_batch_nb3_pad.sh oot_batch_fix2.sh oot_batch_sweeps.sh oot_fix_cf.sh oot_check_flaky.sh \
             oot_phase_c.sh oot_phase_c_resume.sh oot_tree_gate.sh oot_renamed_gate.sh \
             patch_oot_cf.py patch_oot_cf2.py patch_oot_bool2.py patch_oot_num.py ladders.py nested_ifs.py classify.py funcslots.py; do
        [ -f "$SCRATCH/$f" ] && cp -n "$SCRATCH/$f" "$O/batches/$f"; done
    # relativise: scripts live beside each other ($S), outputs go to a work dir ($W), the build tree is
    # ASMDIFF_BUILD, the repo root comes from git, the tools from tools/
    for f in "$M"/batches/*.sh "$O"/batches/*.sh; do
        sed -i \
          -e 's|^S=/tmp/claude-0/[^ ]*/scratchpad$|S=$(cd "$(dirname "$0")" \&\& pwd); W=${ASMDIFF_WORK:-$(mktemp -d)}|' \
          -e 's|^\. /tmp/claude-0/[^ ]*/scratchpad/oot_lib.sh$|. "$(dirname "$0")/oot_lib.sh"|' \
          -e 's|export ASMDIFF_BUILD="$S/gs-build"|: "${ASMDIFF_BUILD:?set ASMDIFF_BUILD to the configured Ghostship build tree}"|' \
          -e 's|export ASMDIFF_PROJECT=OcarinaOfTime ASMDIFF_BUILD="$S/soh-build"|export ASMDIFF_PROJECT=OcarinaOfTime; : "${ASMDIFF_BUILD:?set ASMDIFF_BUILD to the configured Shipwright build tree}"|' \
          -e 's|IMPS=/foo/opt/imps;|IMPS=$(git -C "$S" rev-parse --show-toplevel);|' \
          -e 's|TOOL="$IMPS/tasks/adhoc/mario64-assembly-isms"|TOOL="$IMPS/tools"|' \
          -e 's|OOTTOOL="$IMPS/tasks/adhoc/ocarina-assembly-isms"|OOTTOOL="$IMPS/tools/standard-c"|' \
          -e 's|"$TOOL/drop_register.py"|"$TOOL/standard-c/drop_register.py"|g' \
          -e 's|"$TOOL/drop_true_false_cmp.py"|"$TOOL/standard-c/drop_true_false_cmp.py"|g' \
          -e 's|"$TOOL/drop_filler_locals.py"|"$TOOL/standard-c/drop_filler_locals.py"|g' \
          -e 's|"$TOOL/rename_in_function.py"|"$TOOL/standard-c/rename_in_function.py"|g' \
          -e 's|R="$TOOL/rename_in_function.py"|R="$TOOL/standard-c/rename_in_function.py"|' \
          -e 's|"$OOTTOOL/resolve_rename_conflicts.py"|"$IMPS/tools/resolve_rename_conflicts.py"|g' \
          -e 's|"$OOTTOOL/data/|"$IMPS/tasks/adhoc/ocarina-assembly-isms/data/|g' \
          -e 's|"$S/\([A-Za-z0-9_]*\)\.\(txt\|log\|out\)"|"$W/\1.\2"|g' \
          -e "s|'\$S/\([A-Za-z0-9_]*\)\.\(txt\|log\|out\)'|'\$W/\1.\2'|g" \
          -e 's|"$S/m_oot_$1.txt"|"$W/m_oot_$1.txt"|' \
          -e 's|/tmp/claude-0/[^ "]*/scratchpad|$S|g' \
          "$f"
    done
    sed -i 's|^S=/tmp/claude-0/[^ ]*/scratchpad$|S=$(cd "$(dirname "$0")" \&\& pwd); W=${ASMDIFF_WORK:-$(mktemp -d)}|' "$O/batches/oot_lib.sh" 2>/dev/null || true
    chmod +x "$M"/batches/*.sh "$O"/batches/*.sh "$M"/batches/*.py "$O"/batches/*.py
    git add "$M/batches" "$O/batches"
fi
echo "== container-absolute paths left in tools/ and the adhoc dirs (must be none):"
grep -rn "/tmp/claude-0\|/foo/opt" tools "$M" "$O" --include='*.sh' --include='*.py' | grep -v "^tools/check_\|promote.sh" || echo "  none"
