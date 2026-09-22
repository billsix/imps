#!/usr/bin/env python3
"""Rename identifiers inside ONE function body (or a prototype line): the decomp's stack-slot
locals (`sp3C`), register-named parameters (`a0`, `f12`) and `argN` parameters.

usage: rename_in_function.py <file> <function-name> old=new [old=new ...]

The scope is from the first line containing `<function-name>(` at column 0 (the definition or a
prototype) to the next line that is exactly `}` — or just that one line for a prototype (no `{`
before the next `;`). Renames are whole-word (`\\b`), applied in one pass so `a=b b=a` swaps are
safe, and every old name must occur at least once or the tool fails loudly. Comments inside the
scope are renamed too (a `// sp24` trailing comment naming the slot is the decomp's own
annotation and follows the variable).
"""

import re
import sys
from pathlib import Path


def find_scope(lines: list[str], func: str) -> tuple[int, int]:
    """Return (start, end) line indices, inclusive, of the definition or prototype of `func`."""
    head_re: re.Pattern[str] = re.compile(r"[A-Za-z_].*\b" + re.escape(func) + r"\(")
    start: int | None = next((i for i, line in enumerate(lines) if head_re.match(line)), None)
    if start is None:
        sys.exit(f"no definition/prototype line for {func}")
    end: int = start
    while end < len(lines):
        if lines[end].rstrip().endswith(";") and "{" not in "".join(lines[start : end + 1]):
            break  # prototype
        if lines[end] == "}":
            break
        end += 1
    return start, end


def parse_pairs(args: list[str]) -> dict[str, str]:
    pairs: dict[str, str] = {}
    a: str
    for a in args:
        old: str
        new: str
        old, new = a.split("=", 1)
        pairs[old] = new
    return pairs


def main(argv: list[str]) -> None:
    path: Path = Path(argv[1])
    func: str = argv[2]
    pairs: dict[str, str] = parse_pairs(argv[3:])
    lines: list[str] = path.read_text().split("\n")
    start: int
    end: int
    start, end = find_scope(lines, func)

    pat: re.Pattern[str] = re.compile(r"\b(" + "|".join(re.escape(k) for k in pairs) + r")\b")
    seen: dict[str, int] = {k: 0 for k in pairs}

    def repl(m: re.Match[str]) -> str:
        seen[m.group(1)] += 1
        return pairs[m.group(1)]

    i: int
    for i in range(start, end + 1):
        lines[i] = pat.sub(repl, lines[i])
    missing: list[str] = [k for k, n in seen.items() if n == 0]
    if missing:
        sys.exit(f"{path}:{func}: names not found in scope (lines {start + 1}-{end + 1}): {missing}")
    path.write_text("\n".join(lines))
    summary: str = ", ".join(f"{k}->{v} x{seen[k]}" for k, v in pairs.items())
    print(f"{path}:{func}: lines {start + 1}-{end + 1}: {summary}")


if __name__ == "__main__":
    main(sys.argv)
