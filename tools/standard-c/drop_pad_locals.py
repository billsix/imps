#!/usr/bin/env python3
"""Batch tool for the function-local stack-padding class of the OoT decomp: delete `s32 pad;`-style
declarations that a function never references again. The worklist is
`data/filler_function_local_unreferenced.txt` (one `path:line:decl [function]` per line, produced by
the naming reader from a per-function reference count); line numbers in it rot as other batches
edit the files, so each entry is located by FUNCTION + exact declaration text, not by line: the
tool finds the function's definition, scans its body for a line whose stripped text equals the
declaration, and deletes the first such line. Entries it cannot find are printed as REVIEW and left.

usage: drop_pad_locals.py <checkout> <worklist> [<path-prefix-filter>]
   (edits in place; prints every deletion; idempotent — a second run finds nothing to delete)
"""

import re
import sys
from pathlib import Path

ENTRY: re.Pattern[str] = re.compile(
    r"^(?P<path>[^:]+):(?P<line>\d+):(?P<decl>.+?) \[(?P<func>[A-Za-z_0-9]+)\]$"
)


def find_function(lines: list[str], func: str) -> tuple[int, int] | None:
    """(start, end) of the function definition `func` — start = the line with `func(` at column 0
    context (a definition, not a call), end = the matching `}` line."""
    head: re.Pattern[str] = re.compile(r"^[A-Za-z_][A-Za-z_0-9 *]*\b" + re.escape(func) + r"\(")
    i: int
    for i, line in enumerate(lines):
        if head.match(line) and not line.rstrip().endswith(";"):
            depth: int = 0
            j: int
            for j in range(i, len(lines)):
                depth += lines[j].count("{") - lines[j].count("}")
                if depth == 0 and "{" in "".join(lines[i : j + 1]):
                    return i, j
            return None
    return None


def rewrite_file(path: Path, entries: list[tuple[str, str]]) -> int:
    lines: list[str] = path.read_text().split("\n")
    deleted: int = 0
    decl: str
    func: str
    for decl, func in entries:
        span: tuple[int, int] | None = find_function(lines, func)
        if span is None:
            print(f"{path}: REVIEW no definition found for {func} ({decl})")
            continue
        start: int
        end: int
        start, end = span
        hit: int | None = next((k for k in range(start, end + 1) if lines[k].strip() == decl), None)
        if hit is None:
            print(f"{path}: REVIEW {decl!r} not found in {func}")
            continue
        print(f"{path}:{hit + 1}: deleted: {decl}  [{func}]")
        del lines[hit]
        deleted += 1
    if deleted:
        path.write_text("\n".join(lines))
    return deleted


def main(argv: list[str]) -> None:
    root: Path = Path(argv[1])
    worklist: Path = Path(argv[2])
    prefix: str = argv[3] if len(argv) > 3 else ""
    by_file: dict[str, list[tuple[str, str]]] = {}
    raw: str
    for raw in worklist.read_text().split("\n"):
        m: re.Match[str] | None = ENTRY.match(raw.strip())
        if not m or not m.group("path").startswith(prefix):
            continue
        by_file.setdefault(m.group("path"), []).append((m.group("decl"), m.group("func")))
    total: int = 0
    rel: str
    entries: list[tuple[str, str]]
    for rel, entries in sorted(by_file.items()):
        n: int = rewrite_file(root / rel, entries)
        total += n
        print(f"# {rel}: {n} deleted of {len(entries)}")
    print(f"# total: {total}")


if __name__ == "__main__":
    main(sys.argv)
