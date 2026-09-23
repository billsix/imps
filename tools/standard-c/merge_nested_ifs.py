#!/usr/bin/env python3
"""Batch tool for nested single-statement `if`s: `if (A) { if (B) { if (C) { body } } }` where each
inner `if` is the ONLY statement of its parent's block and no arm has an `else`, becomes
`if (A && B && C) { body }`. `&&` short-circuits left to right exactly as the nesting evaluated the
conditions, so side effects and their order are preserved; GCC lowers both to the same CFG.

Only chains of depth >= MIN_DEPTH (default 3) are merged, and only when every condition fits on its
`if` line (no multi-line conditions), so the result is one readable line per chain or a natural
wrap. Prints every merge; edits in place.

usage: merge_nested_ifs.py [--min-depth N] <file>...
"""

import re
import sys
from pathlib import Path

IF_LINE: re.Pattern[str] = re.compile(r"^(?P<ind>[ \t]*)if \((?P<cond>.*)\) \{[ \t]*$")
CLOSE_LINE: re.Pattern[str] = re.compile(r"^(?P<ind>[ \t]*)\}[ \t]*$")


def balanced(cond: str) -> bool:
    return cond.count("(") == cond.count(")")


def find_chain(lines: list[str], i: int) -> list[int] | None:
    """Indices of the consecutive nested `if (` lines starting at i, each the sole statement of the
    previous block (i.e. immediately following it, indented one level deeper)."""
    chain: list[int] = [i]
    while True:
        m: re.Match[str] | None = IF_LINE.match(lines[chain[-1]])
        if m is None or not balanced(m.group("cond")):
            return None
        nxt: int = chain[-1] + 1
        if nxt >= len(lines):
            break
        m2: re.Match[str] | None = IF_LINE.match(lines[nxt])
        if m2 and len(m2.group("ind")) == len(m.group("ind")) + 4 and balanced(m2.group("cond")):
            chain.append(nxt)
            continue
        break
    return chain


def closing_brace(lines: list[str], open_idx: int) -> int | None:
    depth: int = 0
    j: int
    for j in range(open_idx, len(lines)):
        depth += lines[j].count("{") - lines[j].count("}")
        if depth == 0:
            return j
    return None


def rewrite_file(path: Path, min_depth: int) -> int:
    lines: list[str] = path.read_text().split("\n")
    merged: int = 0
    i: int = 0
    while i < len(lines):
        chain: list[int] | None = find_chain(lines, i) if IF_LINE.match(lines[i]) else None
        if chain is None or len(chain) < min_depth:
            i += 1
            continue
        closes: list[int | None] = [closing_brace(lines, k) for k in chain]
        # every inner `if` must be the sole statement: its `}` is immediately followed by the
        # parent's `}`, and no `}` may carry an `else`
        ok: bool = all(c is not None for c in closes)
        if ok:
            cl: list[int] = [c for c in closes if c is not None]
            k: int
            for k in range(len(cl) - 1, 0, -1):  # innermost first
                if (
                    cl[k] + 1 != cl[k - 1]
                    or not CLOSE_LINE.match(lines[cl[k]])
                    or not CLOSE_LINE.match(lines[cl[k - 1]])
                ):
                    ok = False
                    break
            if ok and (
                not CLOSE_LINE.match(lines[cl[0]])
                or (cl[0] + 1 < len(lines) and lines[cl[0] + 1].lstrip().startswith("else"))
            ):
                ok = False
        if not ok:
            i += 1
            continue
        cl2: list[int] = [c for c in closes if c is not None]
        depth: int = len(chain)
        heads: list[re.Match[str] | None] = [IF_LINE.match(lines[k]) for k in chain]
        assert all(h is not None for h in heads)
        ind: str = heads[0].group("ind") if heads[0] is not None else ""
        conds: list[str] = [h.group("cond") for h in heads if h is not None]
        head: str = f"{ind}if ({' && '.join(conds)}) {{"
        body: list[str] = [
            ln[4 * (depth - 1) :] if ln.startswith(" " * (4 * (depth - 1))) else ln
            for ln in lines[chain[-1] + 1 : cl2[-1]]
        ]
        print(f"{path}:{chain[0] + 1}: merged {depth} nested ifs -> {head.strip()[:100]}")
        lines[chain[0] : cl2[0] + 1] = [head] + body + [f"{ind}}}"]
        merged += 1
        i = chain[0] + 1
    if merged:
        path.write_text("\n".join(lines))
    return merged


def main(argv: list[str]) -> None:
    min_depth: int = 3
    files: list[str] = []
    args: list[str] = argv[1:]
    while args:
        a: str = args.pop(0)
        if a == "--min-depth":
            min_depth = int(args.pop(0))
        else:
            files.append(a)
    total: int = 0
    f: str
    for f in files:
        n: int = rewrite_file(Path(f), min_depth)
        total += n
        print(f"# {f}: {n} merged")
    print(f"# total: {total}")


if __name__ == "__main__":
    main(sys.argv)
