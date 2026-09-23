#!/usr/bin/env bash
# Batch 1 — drop `register` (engine, goddard, game), one commit per directory, gate every file.
set -e
S=$(cd "$(dirname "$0")" && pwd); W=${ASMDIFF_WORK:-$(mktemp -d)}
: "${ASMDIFF_BUILD:?set ASMDIFF_BUILD to the configured Ghostship build tree}"
S=$(cd "$(dirname "$0")" && pwd); W=${ASMDIFF_WORK:-$(mktemp -d)}; IMPS=$(git -C "$S" rev-parse --show-toplevel)
G="$IMPS/n64/SuperMario64/Ghostship"
TOOL="$IMPS/tools"
cd "$G"
git config user.name "William Emerison Six"; git config user.email "billsix@gmail.com"; git config commit.gpgsign false

gate() { # files... -> prints results; fails if any differs
    local ok=1 f r
    for f in "$@"; do
        r=$(cd "$IMPS" && bash "$TOOL/asmdiff.sh" "$f" HEAD | head -1); echo "  $r"
        case "$r" in IDENTICAL*) ;; *) ok=0 ;; esac
    done
    [ "$ok" = 1 ]
}

# ---------- engine (edits already applied in the working tree) ----------
echo "== engine"
ENG="src/engine/math_util.c src/engine/surface_collision.c src/engine/surface_load.c"
gate $ENG
git add $ENG
git commit -q -F - <<'MSG'
engine: drop the `register` storage class (no codegen change)

The decompiler emitted `register` wherever the original held a value in a
MIPS register; the keyword has had no effect on allocation in GCC or Clang
for decades, its only remaining C semantics is forbidding `&x` (no such
variable has its address taken here), and C++17 removed it. Remove the 48
uses in engine/ (math_util.c 28, surface_collision.c 13, surface_load.c 7).

Verified: each file compiles to byte-identical assembly before and after
with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
git log --oneline -1

# ---------- goddard: register + the MIPS register-map comments it carries ----------
echo "== goddard"
GOD=$(grep -l '^\s*register ' src/goddard/*.c)
echo "files: $(echo $GOD | wc -w)"
python3 "$TOOL/standard-c/drop_register.py" --strip-regmap-comments $GOD | grep -E '^#|SKIP' | tail -14
echo "residue:"; grep -rn '\bregister\b' src/goddard | grep -v '://\|/\*\|^\S*:\s*\*' || echo "  no register left"
grep -rn -E '// *(a[0-3]|s[0-7]|t[0-9]|v[01])( \([0-9]+\))? *$' src/goddard | head -5 || true
gate $GOD
git add $GOD
N=$(git diff --cached --numstat | awk '{s+=$2} END{print s}')
git commit -q -F - <<MSG
goddard: drop the \`register\` storage class and its register-map comments (no codegen change)

goddard is the most disassembly-shaped code in the tree: many locals were
declared \`register\` with the MIPS register they lived in as a trailing
comment (\`register s16 *cbufOff; // a0\`). The keyword is ignored by GCC and
Clang, forbids only \`&x\` (never applied to these), and is gone from C++17;
the comments name registers that no longer exist. Remove both — $N lines
across $(echo $GOD | wc -w) files — leaving the declarations themselves untouched.

Verified: every file compiles to byte-identical assembly before and after
with the port's own flags (asmdiff over compile_commands.json).

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
git log --oneline -1

# ---------- game: the single remaining site ----------
echo "== game"
GAME=$(grep -l '^\s*register ' src/game/*.c src/game/behaviors/*.c 2>/dev/null || true)
if [ -n "$GAME" ]; then
    python3 "$TOOL/standard-c/drop_register.py" $GAME | grep -E '^#' | tail -3
    gate $GAME
    git add $GAME
    git commit -q -F - <<'MSG'
game: drop the last `register` (no codegen change)

Same rationale as the engine/ and goddard/ patches: the keyword is a no-op
for modern compilers and removed in C++17; nothing here takes the address
of the variable. Verified byte-identical assembly before and after.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
MSG
    git log --oneline -1
fi
echo "== tree-wide residue (excluding comments):"; grep -rn '^\s*register ' src/game src/engine src/goddard src/audio src/menu || echo "  none"
echo "== branch:"; git log --oneline "$(sed -n 's/^PIN_SHA=//p' ../fetch.sh)"..HEAD
