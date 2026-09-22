#!/usr/bin/env python3
"""Batch tool for the boolean-comparison class: rewrite `E == TRUE` / `E != FALSE` to `E`, and
`E == FALSE` / `E != TRUE` to `!E`, ONLY where the left operand E is a simple boolean-valued
expression the reader verified is 0/1: an identifier, a member chain (`a->b.c`), an array element, a
function call, or a parenthesised expression. Any line whose left operand contains a binary operator
outside parentheses (e.g. `x & FLAG == TRUE`, whose precedence differs) is left untouched and
listed for manual review. Explicit skip list for the sites the survey marked load-bearing.

usage: drop_true_false_cmp.py <file>...   (prints every change; edits in place)
"""

import re
import sys
from pathlib import Path

SKIP: set[tuple[str, str]] = {
    # --- SuperMario64 (Ghostship) ---
    ("src/game/behaviors/hoot.inc.c", "oInteractStatus == TRUE"),  # flags word; documented guard
    ("src/game/behaviors/bowser.inc.c", "oBowserBitsJustJump == FALSE"),  # documented dead code, leave
    # --- OcarinaOfTime (Shipwright) — from reports/booleans-comments-whole-functions.md ---
    ("soh/src/code/z_camera.c", "manualCamera == false"),  # SoH's own enhancement line, not decomp
    ("ovl_select/z_select.c", "lockUp == true"),  # SoH's own (enhanced warp copy)
    ("ovl_select/z_select.c", "lockDown == true"),  # SoH's own (enhanced warp copy)
    ("soh/src/code/z_message_PAL.c", "noStop == false"),  # value test: one writer stores hudVisibilityMode
    ("soh/src/code/z_eff_shield_particle.c", "lightDecay == true"),  # value test: copied from init params
    ("soh/src/code/audio_heap.c", "(apply != false) && (apply == true)"),  # folds to == 1; leave
}
# left operand: optional `!`, then identifier / member chain / calls / subscripts / parens, no bare binary ops
SIMPLE_OPERAND: str = (
    r"[A-Za-z_][A-Za-z_0-9]*(?:(?:->|\.)[A-Za-z_][A-Za-z_0-9]*|\[[^\]]*\]|\([^()]*(?:\([^()]*\)[^()]*)*\))*"
)
OPERAND: str = r"(?:\(\s*[^()]*?(?:\([^()]*\))?[^()]*?\s*\)|!?" + SIMPLE_OPERAND + r")"
PAT: re.Pattern[str] = re.compile(
    r"(?P<lhs>" + OPERAND + r")\s*(?P<op>==|!=)\s*(?P<rhs>TRUE|FALSE|true|false)\b"
)
SIMPLE_OPERAND_RE: re.Pattern[str] = re.compile(SIMPLE_OPERAND)
CMP_RE: re.Pattern[str] = re.compile(r"(==|!=)\s*(TRUE|FALSE|true|false)\b")
TRUE_WORDS: tuple[str, ...] = ("TRUE", "FALSE", "true", "false")
# binary operators that bind looser than `==`, when they end the text before the operand
ARITH_BEFORE_RE: re.Pattern[str] = re.compile(r"[-+*/%^]\s*$")
SINGLE_AMP_BEFORE_RE: re.Pattern[str] = re.compile(r"(?<!&)&\s*$")
SINGLE_BAR_BEFORE_RE: re.Pattern[str] = re.compile(r"(?<!\|)\|\s*$")
SHIFT_BEFORE_RE: re.Pattern[str] = re.compile(r"(?<![<>=!])[<>]\s*$")


def replacement(m: re.Match[str]) -> str:
    """The bare operand for a positive test, its negation for a negative one."""
    lhs: str = m.group("lhs")
    op: str = m.group("op")
    rhs: str = m.group("rhs")
    positive: bool = (op == "==" and rhs.upper() == "TRUE") or (op == "!=" and rhs.upper() == "FALSE")
    if positive:
        return lhs
    if lhs.startswith("!"):
        return lhs[1:]  # !E == FALSE  ->  E
    if lhs.startswith("("):
        return "!" + lhs
    return "!" + lhs if SIMPLE_OPERAND_RE.fullmatch(lhs) else "!(" + lhs + ")"


def binary_operator_before(before: str) -> bool:
    """True when the text before the match ends in a binary operator that binds looser than `==`.
    (`&&` / `||` are fine: the comparison binds tighter than either, exactly as the bare operand does.)"""
    return bool(
        ARITH_BEFORE_RE.search(before)
        or SINGLE_AMP_BEFORE_RE.search(before)
        or SINGLE_BAR_BEFORE_RE.search(before)
        or SHIFT_BEFORE_RE.search(before)
    )


def is_skipped(path: Path, line: str) -> bool:
    """True for a site on the SKIP list (matched by file suffix + the exact comparison text)."""
    rel: str = str(path)
    fn: str
    needle: str
    for fn, needle in SKIP:
        if rel.endswith(fn) and needle in line:
            return True
    return False


def rewrite_file(path: Path) -> int:
    """Rewrite one file in place; returns the number of lines changed."""
    lines: list[str] = path.read_text().split("\n")
    changed: int = 0
    i: int
    line: str
    for i, line in enumerate(lines):
        if not any(w in line for w in TRUE_WORDS):
            continue
        code: str = line.split("//")[0]  # do not touch comments
        if not CMP_RE.search(code):
            continue
        if is_skipped(path, line):
            print(f"{path}:{i + 1}: SKIP (listed): {line.strip()}")
            continue
        new: str = PAT.sub(replacement, code)
        if new == code:
            print(f"{path}:{i + 1}: REVIEW (operand shape not handled): {line.strip()}")
            continue
        # precedence guard: the text just before the match must not end in a binary operator
        m0: re.Match[str] | None = PAT.search(code)
        assert m0 is not None
        if binary_operator_before(code[: m0.start()]):
            print(f"{path}:{i + 1}: REVIEW (binary operator before operand): {line.strip()}")
            continue
        comment: str = line[len(code) :]
        lines[i] = new + comment
        print(f"{path}:{i + 1}: {line.strip()}  ->  {lines[i].strip()}")
        changed += 1
    if changed:
        path.write_text("\n".join(lines))
    return changed


def main(argv: list[str]) -> None:
    total: int = 0
    f: str
    for f in argv[1:]:
        changed: int = rewrite_file(Path(f))
        total += changed
        print(f"# {f}: {changed} rewritten")
    print(f"# total: {total}")


if __name__ == "__main__":
    main(sys.argv)
