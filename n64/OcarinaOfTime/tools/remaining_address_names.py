#!/usr/bin/env python3
"""Print every address-named symbol still left in the decomp.

WHEN TO RUN IT
    After a pin bump, after any batch of renames, and whenever you want to
    know whether the naming effort is actually finished. It reads the
    CHECKOUT rather than any census, so it cannot go stale: what it prints is
    what is really still address-named.

    As of 2026-09-08 it prints 6 rows covering 4 distinct names, all of them
    in the exclusions the task declared (the RCP block in code_800FBCE0.c and
    two z_player.c functions). Anything MORE than that is new work -- most
    likely symbols an upstream pin bump introduced.

ORIGIN
    Promoted from tasks/adhoc/ (2026-09-08). It began as the second-pass
    work-list: address names the 4,235-symbol census missed.

next_symbols.py is driven by oracle.tsv, the census of file-scope symbols taken
at the start of the task. Two classes of address name were never in it:

  * statics declared INSIDE a function body, and
  * symbols in files the census did not walk (notably the generated `.inc`
    data files).

This script ignores the census and reads the checkout instead: every address
name still present as *code* (comments stripped, for the same reason
next_symbols.py strips them -- each rename leaves a provenance comment citing
the old name), minus the same declared exclusions.

Usage:  n64/OcarinaOfTime/tools/remaining_address_names.py [how-many-files]
"""
import collections
import os
import re
import subprocess
import sys

# <project>/tools/remaining_address_names.py -> <project>/Shipwright, so this
# runs from anywhere rather than only from the repo root.
SW = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                  "Shipwright")
ADDR = re.compile(r"\b(func_[0-9A-Fa-f]{6,8}|D_[0-9A-Fa-f]{6,8}"
                  r"|Struct_[0-9A-Fa-f]{6,8})\b")
EXCLUDE = {
    "soh/src/overlays/actors/ovl_player_actor/z_player.c",
    "soh/src/overlays/actors/ovl_En_Zl3/z_en_zl3.c",
    "soh/src/overlays/actors/ovl_En_Zl2/z_en_zl2.c",
    "soh/src/code/code_800FBCE0.c",
}
SEGMENT_ADDRESS = re.compile(r"^D_0[0-9A-F]{7}$")


def otr_asset_names():
    """Address names that are OTR asset paths, not code symbols.

    soh/assets/**/*.h declares them as `static const char D_XXXXXXXX[] =
    "__OTR__.../D_XXXXXXXX"`, so the identifier IS the archive key. Renaming
    one would mean renaming the asset in the OTR, which is the same
    asset-pipeline edit that put segmented addresses out of scope.
    """
    out = subprocess.run(["git", "grep", "-h", "-oE",
                          r"__OTR__[^\"]*/(D_[0-9A-Fa-f]{6,8})",
                          "--", "soh/assets"],
                         cwd=SW, capture_output=True, text=True).stdout
    return {line.rsplit("/", 1)[-1] for line in out.split()}


def main(limit):
    files = subprocess.run(
        ["git", "grep", "-l", "-E", ADDR.pattern, "--", "soh/src", "soh/include"],
        cwd=SW, capture_output=True, text=True).stdout.split()
    assets = otr_asset_names()
    pending = collections.defaultdict(set)
    for path in files:
        if path in EXCLUDE:
            continue
        text = open(os.path.join(SW, path), encoding="utf-8",
                    errors="replace").read()
        # Strip both comment forms: block comments carry the long provenance
        # note, line comments the short tag, and both cite the old name.
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        text = re.sub(r"//[^\n]*", "", text)
        for name in ADDR.findall(text):
            if not SEGMENT_ADDRESS.match(name) and name not in assets:
                pending[path].add(name)

    ordered = sorted(((p, sorted(n)) for p, n in pending.items() if n),
                     key=lambda kv: (len(kv[1]), kv[0]))
    print("files:", len(ordered),
          "symbols:", sum(len(n) for _, n in ordered))
    for path, names in ordered[:limit]:
        print(len(names), path, " ".join(names))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 40)
