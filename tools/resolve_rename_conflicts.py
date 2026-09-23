#!/usr/bin/env python3
"""Resolve `git am --3way` conflicts when replaying the OoT `personal` rename stream on top of the
`standard-c` rewrites.

Every `personal` patch is a pure rename (plus provenance comments): its body lists the renames as
`  * <old> -> <new>` lines (or its subject says `rename <old> -> <new>`). So in a conflicted region
the right answer is mechanical: take OUR side (the standard-c tree), apply that patch's renames to
it, and re-insert any lines the patch ADDED beside the renamed ones (the provenance comments), which
are the lines of THEIR side that are not simply the renamed BASE side. The conflicts must be written
in diff3 style (`git -c merge.conflictStyle=diff3 am --3way …`) so the BASE side is available.

usage: resolve_rename_conflicts.py <checkout> <patch-file> <conflicted-file>...
Prints one line per resolved block; exits non-zero if a block could not be resolved (left as is).
"""

import difflib
import re
import sys
from pathlib import Path

RENAME_LINE: re.Pattern[str] = re.compile(
    r"^\s*\*\s+([A-Za-z_][A-Za-z_0-9.]*)\s+->\s+([A-Za-z_][A-Za-z_0-9.]*)\s*$"
)
SUBJECT_RENAME: re.Pattern[str] = re.compile(
    r"rename\s+([A-Za-z_][A-Za-z_0-9.]*)\s+->\s+([A-Za-z_][A-Za-z_0-9.]*)"
)


def renames_of(patch: Path) -> list[tuple[str, str]]:
    """The (old, new) pairs a personal patch performs, read from its body/subject (up to the first diff)."""
    pairs: list[tuple[str, str]] = []
    text: str = patch.read_text(errors="replace").split("\ndiff --git ", 1)[0]
    line: str
    for line in text.split("\n"):
        m: re.Match[str] | None = RENAME_LINE.match(line)
        if m and not m.group(1).endswith(".c"):
            pairs.append((m.group(1), m.group(2)))
    if not pairs:
        m2: re.Match[str] | None = SUBJECT_RENAME.search(text.replace("\n ", " "))
        if m2:
            pairs.append((m2.group(1), m2.group(2)))
    return pairs


def apply_renames(lines: list[str], pairs: list[tuple[str, str]]) -> list[str]:
    out: list[str] = []
    line: str
    for line in lines:
        old: str
        new: str
        for old, new in pairs:
            line = re.sub(r"\b" + re.escape(old) + r"\b", new, line)
        out.append(line)
    return out


def common_prefix_len(a: str, b: str) -> int:
    n: int = 0
    x: str
    y: str
    for x, y in zip(a, b, strict=False):
        if x != y:
            break
        n += 1
    return n


def ours_line_for(result: list[str], renamed_base: list[str], base_idx: int) -> int | None:
    """Which line of OUR (renamed) side corresponds to base line `base_idx`: positional when the
    block sizes agree, otherwise the line sharing the longest prefix (a rewrite usually changes the
    tail of a statement, not its head); None when OUR side deleted the line."""
    if len(result) == len(renamed_base):
        return base_idx
    rb: str = renamed_base[base_idx]
    best: int | None = None
    best_len: int = 0
    i: int
    line: str
    for i, line in enumerate(result):
        n: int = common_prefix_len(line, rb)
        if n > best_len:
            best, best_len = i, n
    return best if best_len >= max(8, len(rb.strip()) // 3) else None


def resolve_block(
    base: list[str], ours: list[str], theirs: list[str], pairs: list[tuple[str, str]]
) -> list[str] | None:
    """OURS with the renames applied, plus THEIR added lines (provenance comments) anchored to the line
    that follows them; None when THEIRS changed something that is not a rename or an addition."""
    renamed_base: list[str] = apply_renames(base, pairs)
    result: list[str] = apply_renames(ours, pairs)
    sm: difflib.SequenceMatcher[str] = difflib.SequenceMatcher(a=renamed_base, b=theirs, autojunk=False)
    tag: str
    i1: int
    i2: int
    j1: int
    j2: int
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        if tag == "replace" and (i2 - i1) == (j2 - j1):
            # the other rename-patch edit: an inline provenance tag APPENDED to a line
            # (`… ;  // was func_… [LLM:HIGH]`) — carry the suffix over to our version of that line
            k: int
            for k in range(i2 - i1):
                rb: str = renamed_base[i1 + k]
                th: str = theirs[j1 + k]
                if not th.startswith(rb):
                    return None
                suffix: str = th[len(rb) :]
                target: int | None = ours_line_for(result, renamed_base, i1 + k)
                if target is not None:
                    result[target] = result[target] + suffix
            continue
        if tag != "insert":
            return None  # theirs did something beyond rename+insert: hand it to a human
        added: list[str] = theirs[j1:j2]
        anchor: str | None = renamed_base[i1] if i1 < len(renamed_base) else None
        if anchor is not None and anchor in result:
            k: int = result.index(anchor)
            result[k:k] = added
        else:
            result.extend(added)
    return result


def resolve_file(path: Path, pairs: list[tuple[str, str]]) -> bool:
    lines: list[str] = path.read_text().split("\n")
    out: list[str] = []
    i: int = 0
    ok: bool = True
    while i < len(lines):
        if not lines[i].startswith("<<<<<<< "):
            out.append(lines[i])
            i += 1
            continue
        j: int = i + 1
        ours: list[str] = []
        while not lines[j].startswith("||||||| "):
            ours.append(lines[j])
            j += 1
        j += 1
        base: list[str] = []
        while lines[j] != "=======":
            base.append(lines[j])
            j += 1
        j += 1
        theirs: list[str] = []
        while not lines[j].startswith(">>>>>>> "):
            theirs.append(lines[j])
            j += 1
        resolved: list[str] | None = resolve_block(base, ours, theirs, pairs)
        if resolved is None:
            print(f"{path}:{i + 1}: UNRESOLVED (theirs is not rename+insert)")
            out.extend(lines[i : j + 1])
            ok = False
        else:
            shape: str = f"{len(ours)} ours / {len(base)} base / {len(theirs)} theirs"
            print(f"{path}:{i + 1}: resolved ({shape} -> {len(resolved)})")
            out.extend(resolved)
        i = j + 1
    path.write_text("\n".join(out))
    return ok


def main(argv: list[str]) -> None:
    root: Path = Path(argv[1])
    patch: Path = Path(argv[2])
    pairs: list[tuple[str, str]] = renames_of(patch)
    print(f"# {patch.name}: {len(pairs)} rename(s)")
    status: int = 0
    f: str
    for f in argv[3:]:
        if not resolve_file(root / f, pairs):
            status = 1
    sys.exit(status)


if __name__ == "__main__":
    main(sys.argv)
