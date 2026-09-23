#!/usr/bin/env python3
"""Batch tool for the function-local filler class: delete `UNUSED u8 fillerN[K];` declarations
inside function bodies. These are stack-frame padding the decomp needed to reproduce the ROM's
frame layout; they are never read or written (the name says so, and the `UNUSED` attribute is the
only reason the compiler does not complain). Struct members are NOT touched: the pattern is
restricted to lines that are indented and end the declaration on the same line, and this tool is
only ever run on `.c`/`.inc.c` files, where the reader verified no struct definition uses the
`filler` idiom (the layout-fixed fillers all live in headers).

usage: drop_filler_locals.py <file>...   (prints every deleted line; edits in place; idempotent)
"""

import re
import sys
from pathlib import Path

PAT: re.Pattern[str] = re.compile(r"^\s+UNUSED u8 [A-Za-z_0-9]*[fF]iller[A-Za-z_0-9]*\[[^\]]*\];\s*$")


def rewrite_file(path: Path) -> int:
    """Rewrite one file in place; returns the number of lines deleted."""
    lines: list[str] = path.read_text().split("\n")
    kept: list[str] = []
    n: int = 0
    i: int
    line: str
    for i, line in enumerate(lines):
        if PAT.match(line):
            print(f"{path}:{i + 1}: deleted: {line.strip()}")
            n += 1
            continue
        kept.append(line)
    if n:
        path.write_text("\n".join(kept))
    return n


def main(argv: list[str]) -> None:
    total: int = 0
    f: str
    for f in argv[1:]:
        n: int = rewrite_file(Path(f))
        total += n
        print(f"# {f}: {n} deleted")
    print(f"# total: {total}")


if __name__ == "__main__":
    main(sys.argv)
