#!/usr/bin/env python3
"""Print the remaining deduction work-list, smallest files first.

Reads oracle.tsv, keeps the rows the oracle could not resolve (verdict BOTH --
neither SoH nor zeldaret/oot has a name for the address), drops everything the
task declared out of scope, and then drops any symbol whose old name no longer
appears in the checkout as *code*.

That last step is why the file text has its `//` comments stripped before the
search: every rename leaves a provenance comment behind that cites the old name
("was D_8016B780 [LLM:HIGH]"), so a naive grep reports symbols we already
finished as still pending.

Usage (from the imps repo root):  python3 next_symbols.py [how-many-files]
"""
import collections
import os
import re
import sys

SW = "n64/OcarinaOfTime/Shipwright"
ORACLE = "tasks/adhoc/ocarina-decomp-rename-and-cleanup/oracle.tsv"

# Declared out of scope: the three huge files, and the RCP file skipped since
# 2026-07-31. See the task doc's "Measuring progress" table.
EXCLUDE = {
    "soh/src/overlays/actors/ovl_player_actor/z_player.c",
    "soh/src/overlays/actors/ovl_En_Zl3/z_en_zl3.c",
    "soh/src/overlays/actors/ovl_En_Zl2/z_en_zl2.c",
    "soh/src/code/code_800FBCE0.c",
}
# Segmented asset addresses (D_06..., D_0F...) are not RAM symbols; renaming
# them would mean editing the asset pipeline, so they are out of scope too.
SEGMENT_ADDRESS = re.compile(r"^D_0[0-9A-F]{7}$")


def main(limit):
    rows = [l.rstrip("\n").split("\t") for l in open(ORACLE)][1:]
    pending = collections.defaultdict(list)
    code_only = {}

    for path, _kind, _idx, name, _oot, verdict, _match in rows:
        if verdict != "BOTH" or path in EXCLUDE or SEGMENT_ADDRESS.match(name):
            continue
        full = os.path.join(SW, path)
        if full not in code_only:
            try:
                text = open(full, encoding="utf-8", errors="replace").read()
            except OSError:
                text = ""
            code_only[full] = "\n".join(l.split("//")[0]
                                        for l in text.splitlines())
        if re.search(r"\b%s\b" % re.escape(name), code_only[full]):
            pending[path].append(name)

    ordered = sorted(pending.items(), key=lambda kv: (len(kv[1]), kv[0]))
    print("files:", len(ordered),
          "symbols:", sum(len(v) for v in pending.values()))
    for path, names in ordered[:limit]:
        print(len(names), path, " ".join(names))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 20)
