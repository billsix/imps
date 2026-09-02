#!/usr/bin/env bash
# Add the n64/ family segment to project-FOLDER path references in the task docs
# after the five projects moved to imps/n64/<Project>/.
#
# Only the four CamelCase folder names are rewritten, and only where they are a
# path (immediately followed by `/`):
#   OcarinaOfTime/  MajorasMask/  SuperMario64/  BanjoKazooie/  ->  n64/<same>/
# The regex requires the name to be preceded by a non-word, non-slash character,
# which:
#   * leaves bare proper-noun mentions alone (no trailing slash to match anyway);
#   * never double-prefixes (`n64/OcarinaOfTime/` ends in `/` before the name);
#   * never touches the short reference/archive keys (ocarina, mm, banjo,
#     mario64, libultraship) used under tasks/reference/ and tasks/archive/.
# libultraship is deliberately excluded — it is both a folder name and a short
# reference key, and the task docs only ever reference it via tasks/…/libultraship/.
#
# The restructure spec (imps-family-folder-restructure.md) is skipped: it shows
# intentional before/after path examples that must stay as written.
#
# Idempotent (the lookbehind blocks an already-prefixed name).
# Run from the imps repo root.
set -euo pipefail

python3 - <<'PY'
import re, glob, os
pat = re.compile(r'(?<![\w/])(OcarinaOfTime|MajorasMask|SuperMario64|BanjoKazooie)/')
for f in glob.glob("tasks/*.md"):
    if os.path.basename(f) == "imps-family-folder-restructure.md":
        continue
    src = open(f).read()
    out = pat.sub(r'n64/\1/', src)
    if out != src:
        open(f, "w").write(out)
        print(f"fixed: {f}")
PY
echo "done"
