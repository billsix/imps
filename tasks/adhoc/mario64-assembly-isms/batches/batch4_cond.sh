#!/usr/bin/env bash
# Batch 4 — conditionals. Commit a group only when every touched file gates IDENTICAL.
set -u
S=$(cd "$(dirname "$0")" && pwd); W=${ASMDIFF_WORK:-$(mktemp -d)}
: "${ASMDIFF_BUILD:?set ASMDIFF_BUILD to the configured Ghostship build tree}"
IMPS=$(git -C "$S" rev-parse --show-toplevel); G="$IMPS/n64/SuperMario64/Ghostship"; TOOL="$IMPS/tools"
cd "$G"
gate() { local ok=1 f r; for f in "$@"; do r=$(cd "$IMPS" && bash "$TOOL/asmdiff.sh" "$f" HEAD | head -1); echo "  $r"; case "$r" in IDENTICAL*) ;; *) ok=0 ;; esac; done; [ "$ok" = 1 ]; }
run_group() { local grp=$1 msg=$2; shift 2; echo "== $grp"; python3 "$S/patch_batch4.py" "$G" "$grp" || { echo "  patch failed"; return 1; }
    if gate "$@"; then git add "$@"; git commit -q -F "$msg"; git log --oneline -1; else echo "  !! codegen differs — left uncommitted for review: $*"; fi; }

cat > "$W/m4_intro.txt" <<'MSG'
menu: `else` instead of a redundant `else if (state == 1)` in intro_geo.c

Four geo functions test `if (state != 1) … else if (state == 1) …`; the
second condition is the exact complement of the first and `state` is a
parameter the first arm does not modify, so it is a plain `else`.

Verified: intro_geo.c compiles to byte-identical assembly before and after
with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
cat > "$W/m4_spindel.txt" <<'MSG'
game: write the spindel speed ladder as a `switch` with stacked cases

`if (x == 4 || x == 3) … else if (x == 2 || x == 1) … else if (x == 0) …`
over a local with disjoint constant arms is a `switch`; the arms only
assign the discriminant, which a `switch` reads once up front exactly as
the ladder did before any arm ran.

Verified: spindel.inc.c, through the translation unit that includes it,
compiles to an identical instruction stream before and after with the
port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
cat > "$W/m4_file_select.txt" <<'MSG'
menu: one `if/else` for the two complementary tests in print_menu_cursor

`if (t == 0) A; if (t != 0) B;` where neither statement touches `t` is
`if (t == 0) A; else B;`. Braces added while here (the two one-liners had
none).

Verified: file_select.c compiles to byte-identical assembly before and
after with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
cat > "$W/m4_renderer.txt" <<'MSG'
goddard: one condition instead of three nested ifs in gd_dl_load_trg_buf vertex lookup

"the ifs need to be separate to match..." — they no longer do. Three
nested single-statement ifs over side-effect-free struct reads are one
`&&` chain, which short-circuits in the same order the nesting did.

Verified: renderer.c compiles to byte-identical assembly before and after
with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG

run_group intro_geo   "$W/m4_intro.txt"       src/menu/intro_geo.c
run_group spindel     "$W/m4_spindel.txt"     src/game/behaviors/spindel.inc.c
run_group file_select "$W/m4_file_select.txt" src/menu/file_select.c
run_group renderer    "$W/m4_renderer.txt"    src/goddard/renderer.c
echo "== uncommitted:"; git status --short | grep -v "^?? \| libultraship" || echo "  none"
echo "== branch:"; git log --oneline "$(sed -n 's/^PIN_SHA=//p' ../fetch.sh)"..HEAD | head -5
