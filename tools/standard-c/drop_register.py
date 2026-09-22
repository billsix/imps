#!/usr/bin/env python3
"""Batch tool for the `register` class: remove the `register` storage-class specifier from local
declarations in the given files, and (optionally) the trailing MIPS register-map comment that
only existed to name the register (`// a0`, `// s1 (78)`, `// t0-t3`). Everything else on the line
is kept byte-for-byte. Prints every change; refuses a line where `register` is not at the start of
a declaration (so a comment or a string cannot be mangled).

usage: drop_register.py [--strip-regmap-comments] <file>...
"""

import re
import sys
from pathlib import Path

REG_DECL: re.Pattern[str] = re.compile(r"^(\s*)register\s+")
REG_WORD: re.Pattern[str] = re.compile(r"\bregister\b")
# a trailing comment that is ONLY a MIPS register name (optionally with a stack offset in parens)
REGMAP_COMMENT: re.Pattern[str] = re.compile(
    r"\s*//\s*(?:[asvtkf][0-9](?:\s*\(\s*[0-9]+\s*\))?|f[0-9]{1,2}|[asvt][0-9]-[asvt][0-9])\s*$"
)
COMMENT_STARTS: tuple[str, ...] = ("//", "*", "/*")


def rewrite_file(path: Path, strip: bool) -> int:
    """Rewrite one file in place; returns the number of declarations changed."""
    out: list[str] = []
    changed: int = 0
    n: int
    line: str
    for n, line in enumerate(path.read_text().split("\n"), 1):
        if "register" in line and not REG_DECL.match(line):
            # not a declaration start: a comment/string mentioning the word — leave, but say so
            if REG_WORD.search(line) and not line.lstrip().startswith(COMMENT_STARTS):
                print(f"{path}:{n}: SKIP (register not at declaration start): {line.strip()}")
            out.append(line)
            continue
        m: re.Match[str] | None = REG_DECL.match(line)
        if m:
            new: str = m.group(1) + line[m.end() :]
            if strip:
                new2: str = REGMAP_COMMENT.sub("", new)
                if new2 != new:
                    new = new2.rstrip()
            print(f"{path}:{n}: {line.strip()}  ->  {new.strip()}")
            out.append(new)
            changed += 1
        else:
            out.append(line)
    if changed:
        path.write_text("\n".join(out))
    return changed


def main(argv: list[str]) -> None:
    strip: bool = False
    files: list[str] = []
    a: str
    for a in argv[1:]:
        if a == "--strip-regmap-comments":
            strip = True
        else:
            files.append(a)
    total: int = 0
    f: str
    for f in files:
        changed: int = rewrite_file(Path(f), strip)
        total += changed
        print(f"# {f}: {changed} declarations")
    print(f"# total: {total}")


if __name__ == "__main__":
    main(sys.argv)
