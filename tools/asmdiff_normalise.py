#!/usr/bin/env python3
"""asmdiff helper: normalise one .s file in place — drop .file/.ident, canonicalise __FILE__ paths and
line numbers inside strings, drop definitions of compiler-local labels (.L<n>:) that nothing
references, and renumber the remaining .L labels by order of first appearance. After this, two
compiles whose instruction streams are identical compare equal even if GCC numbered its labels
differently (e.g. because a source `goto` label disappeared)."""

import re
import sys
from pathlib import Path

# compiler-local labels: `.L12` (basic blocks) and the lettered families `.LFB12`/`.LFE12` (function
# begin/end), `.LC12` (constants), `.LVL12`/`.LBB12`/`.LBE12` (debug ranges) — all numbered by GCC in
# an order that shifts when a function's shape changes, so both kinds are renumbered by appearance
LABEL_RE: re.Pattern[str] = re.compile(r"\.L[A-Z]*[0-9]+")
LABEL_DEF_RE: re.Pattern[str] = re.compile(r"^(\.L[A-Z]*[0-9]+):\s*$")
FILE_DIRECTIVE_RE: re.Pattern[str] = re.compile(r"^\s*\.file\s")
IDENT_DIRECTIVE_RE: re.Pattern[str] = re.compile(r"^\s*\.ident")
TMP_SOURCE_RE: re.Pattern[str] = re.compile(r"(/[^\"]*)?\.asmdiff_tmp_[0-9]+\.c")
SOURCE_PATH_RE: re.Pattern[str] = re.compile(r"/[^\"]*/(?:Ghostship|Shipwright)/(?:soh/)?src/[^\":]*\.c")
SOURCE_LINE_RE: re.Pattern[str] = re.compile(r"SRC:[0-9]+")


def strip_noise(lines: list[str]) -> list[str]:
    """Drop .file/.ident and canonicalise source paths + line numbers inside strings."""
    out: list[str] = []
    line: str
    for line in lines:
        if FILE_DIRECTIVE_RE.match(line) or IDENT_DIRECTIVE_RE.match(line):
            continue
        line = TMP_SOURCE_RE.sub("SRC", line)
        line = SOURCE_PATH_RE.sub("SRC", line)
        line = SOURCE_LINE_RE.sub("SRC:N", line)
        out.append(line)
    return out


def drop_unreferenced_labels(lines: list[str]) -> list[str]:
    """Delete `.L<n>:` definitions that no instruction references."""
    refs: dict[str, int] = {}
    line: str
    for line in lines:
        m: re.Match[str] | None = LABEL_DEF_RE.match(line)
        lab: str
        for lab in LABEL_RE.findall(line):
            if not m or lab != m.group(1):
                refs[lab] = refs.get(lab, 0) + 1
    kept: list[str] = []
    for line in lines:
        m = LABEL_DEF_RE.match(line)
        if m and refs.get(m.group(1), 0) == 0:
            continue
        kept.append(line)
    return kept


def renumber_labels(lines: list[str]) -> list[str]:
    """Rename `.L<n>` labels to `.LN<k>` in order of first appearance."""
    mapping: dict[str, str] = {}

    def ren(m: re.Match[str]) -> str:
        lab: str = m.group(0)
        if lab not in mapping:
            family: str = re.sub(r"[0-9]+$", "", lab)  # ".L", ".LFB", ".LC", …
            mapping[lab] = f"{family}N{len(mapping)}"
        return mapping[lab]

    return [LABEL_RE.sub(ren, line) for line in lines]


def main(argv: list[str]) -> None:
    p: Path = Path(argv[1])
    lines: list[str] = p.read_text().split("\n")
    lines = renumber_labels(drop_unreferenced_labels(strip_noise(lines)))
    p.write_text("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv)
