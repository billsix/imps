#!/usr/bin/env python3
"""Shared helpers for the OoT decomp-renaming tools.

The renaming effort (tasks/archive/ocarina/2026/09/08/ocarina-decomp-rename-and-cleanup.md, method in
tasks/reference/ocarina/decomp-renaming.md) gives every renamed symbol a
provenance comment. These helpers read that convention back out of the tree, so
the tools need no external table and keep working as more renames land.
"""
import os
import re
import subprocess

# <project>/tools/renames_common.py -> <project>
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKOUT = os.path.join(PROJECT, "Shipwright")

# Only these trees are game/port source; the rest is submodules and build output.
SOURCE_PATHS = ("soh/src", "soh/include", "soh/soh")

# The two LONG provenance forms, written above a symbol's DEFINITION.
MARKERS = ("LLM generated name", "Name from zeldaret/oot")

# The SHORT declaration tag, appended to a header declaration:
#     void AudioMgr_StopAllSfx(void);   // was func_800C3C20 [oot]
#     } RumbleMgr; // size = 0x10E, was UnkRumbleStruct [LLM:HIGH]
# The "//" is optional because the tag may follow an existing trailing comment.
INLINE_TAG_RE = re.compile(r"(?:\s*//)?[\s,]*was\s+\w+\s*\[(?:oot|LLM:\w+)\]")

# A decomp "address name": a symbol still named after its ROM address.
ADDR_RE = re.compile(r"\b(func_[0-9A-Fa-f]{6,8}"
                     r"|D_[0-9A-Fa-f]{6,8}"
                     r"|Struct_[0-9A-Fa-f]{6,8})\b")

# The old name quoted inside a provenance comment.
CITED_RE = re.compile(r"(?:was |\(was )(\w+)")


def git(*args, check=True):
    """Run git inside the Shipwright checkout and return stdout."""
    result = subprocess.run(("git", "-C", CHECKOUT) + args,
                            capture_output=True, text=True)
    if check and result.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed:\n{result.stderr}")
    return result.stdout


def pin_sha():
    """The pinned upstream commit, read from fetch.sh -- the single source of
    truth for the pin (n64/CLAUDE.md)."""
    with open(os.path.join(PROJECT, "fetch.sh")) as handle:
        for line in handle:
            if line.startswith("PIN_SHA="):
                return line.split("=", 1)[1].strip()
    raise SystemExit("no PIN_SHA in fetch.sh")


def rename_range():
    """Everything applied on top of the pin -- the renaming work."""
    if git("rev-list", "--count", f"{pin_sha()}..HEAD").strip() == "0":
        raise SystemExit("nothing applied on top of the pin -- run ./apply.sh")
    return f"{pin_sha()}..HEAD"


def is_marker_line(line):
    """True for a LONG provenance comment line."""
    return any(marker in line for marker in MARKERS)


def is_comment_only(line):
    """True if the line is nothing but a comment -- so not a declaration.
    functions.h carries placeholders like "// ? Audio_ResetData(?);"."""
    return line.lstrip().startswith("//")


def _strip_trailing_comment(line):
    """Remove a trailing comment, keeping any code before it.

    A provenance marker normally occupies a whole line, but a TYPE rename puts
    it on the line that names the type ("} RumbleMgr; // ... was
    UnkRumbleStruct ..."). Dropping that line would delete real code, so split
    at the first "//" and keep the left side when it holds anything.
    """
    head, sep, _ = line.partition("//")
    return head.rstrip() if sep and head.strip() else ""

def code_part(line):
    """The line with any provenance comment removed, '' if it is only a comment.
    Use this before asking whether an old name is still live in the CODE: the
    comments quote the old name by design, and would make every completed
    rename look unfinished."""
    if is_marker_line(line):
        return _strip_trailing_comment(line)
    return INLINE_TAG_RE.sub("", line)


# The short tag on its own, for symbols that carry no long comment: a TYPEDEF is
# its own declaration and definition, so one tag is the whole convention there
# (`} RumbleMgr; // size = 0x10E, was UnkRumbleStruct [LLM:HIGH]`).
SHORT_TAG_CITE_RE = re.compile(r"\bwas\s+(\w+)\s*\[(oot|LLM:\w+)\]")


def renamed_symbols():
    """{new_name: (old_name, provenance)} read out of the tree's provenance
    comments. The long definition-site form is authoritative; the short tag is
    also read, so type renames -- which carry only a short tag -- are seen."""
    files = git("grep", "-l", "-e", MARKERS[0], "-e", MARKERS[1],
                "-e", "was ", check=False).split()
    found = {}
    for path in files:
        full = os.path.join(CHECKOUT, path)
        if not os.path.isfile(full):
            continue
        with open(full, encoding="utf-8", errors="replace") as handle:
            lines = handle.read().splitlines()
        for index, line in enumerate(lines):
            if is_marker_line(line):
                cited = CITED_RE.search(line)
                if not cited:
                    continue
                # skip continuation lines of a multi-line comment
                cursor = index + 1
                while (cursor < len(lines)
                       and lines[cursor].lstrip().startswith("//")):
                    cursor += 1
                decl = lines[cursor] if cursor < len(lines) else ""
                new = _declared_name(decl)
                if new:
                    found[new] = (cited.group(1),
                                  "oot" if MARKERS[1] in line else "llm")
                continue
            # A short tag rides on a declaration -- but ALSO, since 2026-09-07,
            # on every call site of a guessed name. A call site is indented and
            # is not a declaration, so parsing a "name" out of it yields junk
            # ("if", "actionFunc"). Only column-0 lines declare something.
            short = SHORT_TAG_CITE_RE.search(line)
            if short and line[:1].strip() and not line.lstrip().startswith("//"):
                new = _declared_name(code_part(line))
                if new and new not in found:
                    found[new] = (short.group(1),
                                  "oot" if short.group(2) == "oot" else "llm")
    return found


_IDENT_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b")
_NOT_A_NAME = {
    "static", "const", "void", "u8", "s8", "u16", "s16", "u32", "s32", "f32",
    "f64", "u64", "s64", "char", "int", "float", "double", "struct", "union",
    "enum", "unsigned", "signed", "extern", "typedef", "volatile", "register",
    "long", "short",
}


def _declared_name(decl):
    """The identifier a C declaration introduces, or '' if unparseable."""
    def first(chars):
        found = [decl.index(c) for c in chars if c in decl]
        return min(found) if found else len(decl)

    # A function POINTER wraps its name in parens -- `void (*name)(args)` --
    # so the plain "identifier before the first (" rule returns the return
    # type instead. Left unhandled that poisons the renamed-symbol set with
    # "void", and every `void` line in every header then reads as an untagged
    # declaration (hit 2026-09-08 on gAudioCustomUpdateFunc). An ARRAY of
    # function pointers -- `s32 (*name[])(args)` -- puts the subscript inside
    # the same parens, so the pattern allows it (sSpot09ObjChecks).
    pointer = re.search(
        r"\(\s*\*+\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:\[[^\]]*\]\s*)*\)\s*\(", decl)
    if pointer:
        return pointer.group(1)

    if first("(") < first("=["):
        match = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", decl)
        return match.group(1) if match else ""
    head = re.split(r"[\[=;]", decl, maxsplit=1)[0]
    candidates = [t for t in _IDENT_RE.findall(head)
                  if t not in _NOT_A_NAME
                  and not re.match(r"^(func_|D_|Struct_)", t)]
    return candidates[-1] if candidates else ""
