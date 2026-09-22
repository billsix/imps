#!/usr/bin/env bash
# Batch 3 — goto that is a keyword; loops with the exit hoisted into the body. Each group is
# committed only if every touched file gates IDENTICAL; a differing group is left uncommitted
# (its edits stay in the working tree) for review.
set -u
S=$(cd "$(dirname "$0")" && pwd); W=${ASMDIFF_WORK:-$(mktemp -d)}
: "${ASMDIFF_BUILD:?set ASMDIFF_BUILD to the configured Ghostship build tree}"
IMPS=$(git -C "$S" rev-parse --show-toplevel); G="$IMPS/n64/SuperMario64/Ghostship"; TOOL="$IMPS/tools"
cd "$G"
gate() { local ok=1 f r; for f in "$@"; do r=$(cd "$IMPS" && bash "$TOOL/asmdiff.sh" "$f" HEAD | head -1); echo "  $r"; case "$r" in IDENTICAL*) ;; *) ok=0 ;; esac; done; [ "$ok" = 1 ]; }
COPT=src/audio/copt/seq_channel_layer_process_script_copt.inc.c

run_group() { # <group> <msgfile> files...
    local grp=$1 msg=$2; shift 2
    echo "== $grp"
    python3 "$S/patch_batch3.py" "$G" "$grp" || { echo "  patch failed"; return 1; }
    if gate "$@"; then
        git add "$@"; git commit -q -F "$msg"; git log --oneline -1
    else
        echo "  !! codegen differs — left uncommitted for review: $*"
    fi
}

cat > "$W/m3_copt.txt" <<'MSG'
audio: replace goto-as-break in the copt sequence-layer script with `break`

The US/JP sequence-layer interpreter (copt/…_copt.inc.c) jumps out of
three `switch` statements with `goto l1090` / `goto l1138` / `goto l13cc`
— labels named after ROM offsets — where the label is the statement that
immediately follows the `switch`. `break` transfers control to exactly the
same point with no intervening statement, so the eight gotos become
`break` and the three labels go away.

Verified: the including translation unit (seqplayer.c) compiles to
byte-identical assembly before and after with the port's own flags
(asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
cat > "$W/m3_load.txt" <<'MSG'
audio: use `break` instead of `goto out1`/`goto out2` in the sample-DMA init loops

Both loops already say `break` in their EU arm; the JP/US arm used a
`goto` to a label placed immediately after the loop, which is the same
control transfer. Use `break` unconditionally and drop the two
version-guarded labels.

Verified: load.c compiles to byte-identical assembly before and after with
the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
cat > "$W/m3_koopa.txt" <<'MSG'
game: `return` instead of `goto end` at the end of koopa_shelled_act_lying

The label `end:;` is the last statement of a void function, so the goto
is a return; write it as one and drop the label (and the `:;` that C89
needed to place a label before `}`).

Verified: koopa.inc.c, through the translation unit that includes it,
compiles to byte-identical assembly before and after with the port's own
flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
cat > "$W/m3_gdmath.txt" <<'MSG'
goddard: invert the guard in gd_broken_quat_to_vec3f instead of jumping over its body

`if (run < 0) goto end;` skipped a body whose only writes are to UNUSED
locals; the three stores after the label run on both paths. Nest the body
under `if (run >= 0)` and drop the label.

Verified: gd_math.c compiles to byte-identical assembly before and after
with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
cat > "$W/m3_loops.txt" <<'MSG'
game: write two search loops with their exit condition in the loop header

print.c's digit counter and macro_special_objects.c's two preset lookups
were `while (TRUE)` loops whose real test sat in the body behind a `break`.
Move the test into the header. In the first preset lookup an empty-bodied
`if (preset_id == 0xFF) { }` — a bounds check whose body was optimised
away — is deleted; the read it performed had no effect.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG

run_group copt   "$W/m3_copt.txt"   "$COPT"
run_group load   "$W/m3_load.txt"   src/audio/load.c
run_group koopa  "$W/m3_koopa.txt"  src/game/behaviors/koopa.inc.c
run_group gdmath "$W/m3_gdmath.txt" src/goddard/gd_math.c
run_group loops  "$W/m3_loops.txt"  src/game/print.c src/game/macro_special_objects.c
echo "== residue: live gotos outside VERSION_EU/SH:"; grep -n "goto " src/audio/load.c src/game/behaviors/koopa.inc.c src/goddard/gd_math.c "$COPT" || echo "  none"
echo "== uncommitted:"; git status --short | grep -v "^?? \| libultraship" || echo "  none"
echo "== branch:"; git log --oneline "$(sed -n 's/^PIN_SHA=//p' ../fetch.sh)"..HEAD | head -6
