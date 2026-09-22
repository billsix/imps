#!/usr/bin/env python3
"""Batch tool for the empty-then class of the OoT decomp: delete `if (<expr>) {}` statements whose
condition is a pure read — no assignment, no `++`/`--`, no function call — and that have no `else`.
These are matching artefacts (the ROM's compiler needed the read to schedule a register); with
nothing in the body and no side effect in the condition, the statement is a no-op that GCC at -O2
already removes, so the rewrite is byte-identical. Both the one-line form `if (x) {}` and the
two-line form `if (x) {` / `}` are handled; a body with anything in it (even a comment) is kept.

usage: drop_empty_if.py <file>...   (prints every deleted statement; edits in place; idempotent)
"""

import re
import sys
from pathlib import Path

ONE_LINE: re.Pattern[str] = re.compile(r"^(?P<indent>\s*)if \((?P<cond>.*)\) \{\s*\}\s*$")
OPEN_LINE: re.Pattern[str] = re.compile(r"^(?P<indent>\s*)if \((?P<cond>.*)\) \{\s*$")
CLOSE_LINE: re.Pattern[str] = re.compile(r"^\s*\}\s*$")
ELSE_LINE: re.Pattern[str] = re.compile(r"^\s*(\}\s*)?else\b")
# a condition is a pure read iff none of these appear in it
SIDE_EFFECT: re.Pattern[str] = re.compile(r"\+\+|--|(?<![=!<>])=(?!=)|[A-Za-z_][A-Za-z_0-9]*\s*\(")


def pure_read(cond: str) -> bool:
    return SIDE_EFFECT.search(cond) is None


def rewrite_file(path: Path) -> int:
    """Rewrite one file in place; returns the number of statements deleted."""
    lines: list[str] = path.read_text().split("\n")
    kept: list[str] = []
    n: int = 0
    i: int = 0
    while i < len(lines):
        line: str = lines[i]
        m1: re.Match[str] | None = ONE_LINE.match(line)
        if m1 and pure_read(m1.group("cond")):
            nxt: str = lines[i + 1] if i + 1 < len(lines) else ""
            if not ELSE_LINE.match(nxt):
                print(f"{path}:{i + 1}: deleted: {line.strip()}")
                n += 1
                i += 1
                continue
        m2: re.Match[str] | None = OPEN_LINE.match(line)
        if m2 and pure_read(m2.group("cond")) and i + 1 < len(lines) and CLOSE_LINE.match(lines[i + 1]):
            nxt2: str = lines[i + 2] if i + 2 < len(lines) else ""
            if not ELSE_LINE.match(nxt2) and not lines[i + 1].strip().startswith("} else"):
                print(f"{path}:{i + 1}: deleted: {line.strip()} }}")
                n += 1
                i += 2
                continue
        kept.append(line)
        i += 1
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
