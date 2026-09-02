#!/usr/bin/env bash
# Fix relative references to the shared tasks/ tree after the five N64 project
# folders moved one level deeper (imps/<Project>/ -> imps/n64/<Project>/).
#
# Every project doc (CLAUDE.md and README.md) references the UNMOVED tasks/
# tree with `../tasks/...` — both as markdown links `](../tasks/...)` and as
# backtick prose `` `../tasks/...` ``. One extra directory level means each such
# reference needs one more `../`:  ../tasks/...  ->  ../../tasks/...
#
# What is intentionally NOT touched:
#   * sibling cross-links like `../OcarinaOfTime/CLAUDE.md` — the projects moved
#     together, so a sibling `../<Project>/` still resolves correctly under n64/;
#   * upstream-checkout-internal paths (e.g. `Ghostship/libultraship/`,
#     `libultraship/requirements.txt`) — those live inside a checkout, not imps;
#   * root-relative command examples (`git log -- tasks/reference/...`) that
#     assume cwd = the imps root and carry no `../`.
#
# Idempotent by construction: the Python regex rewrites `../tasks/` only when it
# is NOT already preceded by `../` (negative lookbehind), so an already-fixed
# `../../tasks/` is left alone and a second run changes nothing.
#
# Run from the imps repo root:
#   bash tasks/adhoc/imps-family-folder-restructure/fix-project-doc-links.sh
set -euo pipefail

python3 - <<'PY'
import re, glob
# (?<!\.\./) — do not match a ../tasks/ that already sits behind a ../, so the
# rewrite is safe to run repeatedly.
pat = re.compile(r'(?<!\.\./)\.\./tasks/')
for f in glob.glob("n64/*/CLAUDE.md") + glob.glob("n64/*/README.md"):
    src = open(f).read()
    out = pat.sub("../../tasks/", src)
    if out != src:
        open(f, "w").write(out)
        print(f"fixed: {f}")
PY
echo "done"
