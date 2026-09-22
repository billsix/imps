#!/usr/bin/env python3
"""Batch tool for Yoda conditions: `LITERAL op EXPR` -> `EXPR op' LITERAL` where op' mirrors op
(`<`↔`>`, `<=`↔`>=`, `==`/`!=` unchanged). Only when the right operand is a simple expression (an
identifier / member chain / subscript / call, optionally with a trailing `++`/`--`) and the literal
is a number; the mirrored comparison has the same value, so the generated code is unchanged.

usage: flip_yoda.py <file>...   (prints every change; edits in place; idempotent)
"""

import re
import sys
from pathlib import Path

SIMPLE: str = (
    r"-?[A-Za-z_][A-Za-z_0-9]*(?:(?:->|\.)[A-Za-z_][A-Za-z_0-9]*|\[[^\]]*\]|\([^()]*\))*(?:\+\+|--)?"
)
PAT: re.Pattern[str] = re.compile(
    r"(?<![A-Za-z_0-9.\]\)])(?P<lit>-?(?:0x[0-9A-Fa-f]+|[0-9]+(?:\.[0-9]*)?f?))\s*(?P<op><=|>=|<|>)\s*(?P<rhs>"
    + SIMPLE
    + r")"
    r"(?![A-Za-z_0-9(\[.]|->)"
)
MIRROR: dict[str, str] = {"<": ">", ">": "<", "<=": ">=", ">=": "<="}


def flip(m: re.Match[str]) -> str:
    return f"{m.group('rhs')} {MIRROR[m.group('op')]} {m.group('lit')}"


def rewrite_file(path: Path) -> int:
    lines: list[str] = path.read_text().split("\n")
    changed: int = 0
    i: int
    line: str
    for i, line in enumerate(lines):
        code: str = line.split("//")[0]
        if "<" not in code and ">" not in code:
            continue
        # only inside a condition or a plain expression: skip declarations of arrays and templates-ish text
        new: str = PAT.sub(flip, code)
        if new != code:
            lines[i] = new + line[len(code) :]
            print(f"{path}:{i + 1}: {line.strip()}  ->  {lines[i].strip()}")
            changed += 1
    if changed:
        path.write_text("\n".join(lines))
    return changed


def main(argv: list[str]) -> None:
    total: int = 0
    f: str
    for f in argv[1:]:
        n: int = rewrite_file(Path(f))
        total += n
        print(f"# {f}: {n} flipped")
    print(f"# total: {total}")


if __name__ == "__main__":
    main(sys.argv)
