#!/usr/bin/env bash
# Add the n64/ family segment to imps-project-FOLDER path references inside the
# LIVING reference docs (tasks/reference/**). Reference docs are living knowledge
# updated in place as they drift (per the maintainer's conventions); the folder
# move is exactly such drift, so a `libultraship/fetch.sh` or `OcarinaOfTime/…`
# prose reference must gain the n64/ segment to keep pointing at the real file.
#
# What is rewritten (all unambiguously imps project folders — the upstream
# checkouts are named Shipwright/Ghostship/Lighthouse/2ship2harkinian, never the
# game name, so a CamelCase-name path is always the imps folder):
#   OcarinaOfTime/  MajorasMask/  SuperMario64/  BanjoKazooie/  ->  n64/<same>/
#   libultraship/fetch.sh                                       ->  n64/libultraship/fetch.sh
#
# Deliberately NOT rewritten:
#   * tasks/archive/**  — frozen historical work logs (the convention keeps
#     archives as a record of what was done at the time; not touched here);
#   * checkout-INTERNAL engine paths — `libultraship/src`, `libultraship/bridge`,
#     `libultraship/cmake`, `libultraship/include`, `libultraship/requirements.txt`,
#     `libultraship/libultra*.h`, etc. — these describe the upstream engine's own
#     layout, so only the exact `libultraship/fetch.sh` (the imps script) is touched;
#   * absolute host paths like `/foo/opt/n64/n64roms/BanjoKazooie/` — the
#     (?<![\w/]) lookbehind blocks a name preceded by `/`.
#
# Idempotent (the lookbehind blocks an already-`n64/`-prefixed name).
# Run from the imps repo root.
set -euo pipefail

python3 - <<'PY'
import re, glob, os
camel = re.compile(r'(?<![\w/])(OcarinaOfTime|MajorasMask|SuperMario64|BanjoKazooie)/')
lus   = re.compile(r'(?<![\w/])libultraship/fetch\.sh')
for f in glob.glob("tasks/reference/**/*.md", recursive=True):
    if f.startswith("tasks/archive/"):   # belt-and-braces; reference glob excludes it anyway
        continue
    src = open(f).read()
    out = lus.sub("n64/libultraship/fetch.sh", camel.sub(r'n64/\1/', src))
    if out != src:
        open(f, "w").write(out)
        print(f"fixed: {f}")
PY
echo "done"
