#!/usr/bin/env python3
"""Batch tool for the `if (c) { return true; } return false;` shape (and its `else` and `1`/`0`
variants): fold into `return c;` when the condition fits on the `if` line. The value is unchanged —
`c` is a comparison or a `&&`/`||` chain, which already evaluates to 0 or 1 — and the return type
keeps the same bits. Any other shape (multi-line condition, statements before the return) is left.

usage: fold_return_bool.py <file>...   (prints every change; edits in place; idempotent)
"""

import re
import sys
from pathlib import Path

# if (c) {            if (c) {
#     return true;        return true;
# }                   } else {
# return false;           return false;
#                     }
PLAIN: re.Pattern[str] = re.compile(
    r"^(?P<ind>[ \t]*)if \((?P<cond>[^\n{]*)\) \{\n[ \t]*return (?P<t>true|1);\n[ \t]*\}\n"
    r"(?P=ind)return (?P<f>false|0);\n",
    re.MULTILINE,
)
WITH_ELSE: re.Pattern[str] = re.compile(
    r"^(?P<ind>[ \t]*)if \((?P<cond>[^\n{]*)\) \{\n[ \t]*return (?P<t>true|1);\n[ \t]*\} else \{\n"
    r"[ \t]*return (?P<f>false|0);\n(?P=ind)\}\n",
    re.MULTILINE,
)


def fold(m: re.Match[str]) -> str:
    cond: str = m.group("cond")
    # a lone identifier or member read is not known to be 0/1 — only fold comparisons and logic
    if not re.search(r"==|!=|<|>|&&|\|\||^!", cond):
        return m.group(0)
    print(f"  folded: if ({cond}) return {m.group('t')} … return {m.group('f')}  ->  return {cond};")
    return f"{m.group('ind')}return {cond};\n"


def rewrite_file(path: Path) -> int:
    s: str = path.read_text()
    before: str = s
    s = PLAIN.sub(fold, s)
    s = WITH_ELSE.sub(fold, s)
    n: int = before.count("return") - s.count("return")
    if s != before:
        path.write_text(s)
    return n


def main(argv: list[str]) -> None:
    total: int = 0
    f: str
    for f in argv[1:]:
        print(f"# {f}")
        n: int = rewrite_file(Path(f))
        total += n
        print(f"# {f}: {n} folded")
    print(f"# total: {total}")


if __name__ == "__main__":
    main(sys.argv)
