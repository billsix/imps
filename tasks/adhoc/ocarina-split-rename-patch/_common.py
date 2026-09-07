#!/usr/bin/env python3
"""Shared helpers for the ocarina-split-rename-patch analysis scripts.

All scripts here are repo-relative: run them from the imps repo root, e.g.
    python3 tasks/adhoc/ocarina-split-rename-patch/inventory.py

They read the Shipwright checkout under n64/OcarinaOfTime/, which fetch.sh
creates. They never write to it.
"""
import os
import re
import subprocess

# Repo-relative paths: this file is <repo>/tasks/adhoc/<slug>/_common.py, so the
# repo root is three directories up.
REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".."))
PROJECT = os.path.join(REPO_ROOT, "n64", "OcarinaOfTime")
CHECKOUT = os.path.join(PROJECT, "Shipwright")

# The commit under study is the tip of the applied patch series; the pin it sits
# on is the single source of truth in fetch.sh (see n64/CLAUDE.md).
RENAME_SUBJECT = "LLM generated renames"

# The two greppable provenance markers the renaming convention defines
# (tasks/reference/ocarina/decomp-renaming.md).
MARKERS = ("LLM generated name", "Name from zeldaret/oot")

# A decomp "address name": a symbol still named after its ROM address.
ADDR_RE = re.compile(r"\b(func_[0-9A-Fa-f]{6,8}"
                     r"|D_[0-9A-Fa-f]{6,8}"
                     r"|Struct_[0-9A-Fa-f]{6,8})\b")

# The old name quoted inside a provenance comment: "was func_800C3C20" or
# "(was func_800C3C20)".
CITED_RE = re.compile(r"(?:was |\(was )(func_[0-9A-Fa-f]{6,8}"
                      r"|D_[0-9A-Fa-f]{6,8}"
                      r"|Struct_[0-9A-Fa-f]{6,8})")

# Only these trees are game/port source; everything else is submodules or build
# output and would skew every count.
SOURCE_PATHS = ("soh/src", "soh/include", "soh/soh")


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
    raise SystemExit("no PIN_SHA in n64/OcarinaOfTime/fetch.sh")


def rename_range():
    """The revision range holding the renaming work: everything applied on top
    of the pin. Before the 2026-09-07 split this was a single commit; it is now
    ~225, so every analysis works on the RANGE and keeps working as more
    renames land."""
    count = git("rev-list", "--count", f"{pin_sha()}..HEAD").strip()
    if count == "0":
        raise SystemExit("nothing applied on top of the pin — run ./apply.sh")
    return f"{pin_sha()}..HEAD"


def renamed_files():
    """Every path the renaming work touches, at its post-rename name."""
    out = git("diff", "--name-only", rename_range())
    return [p for p in out.split() if p]


def is_marker_line(line):
    """True for a LONG provenance comment line (the definition-site form). Such
    lines quote the OLD name, so every count that asks 'is the old name still in
    the code?' must skip them."""
    return any(marker in line for marker in MARKERS)


# The SHORT declaration-site tag added 2026-09-07: "// was func_800C3C20 [oot]"
# or "[LLM:HIGH]". It is APPENDED to a real declaration -- and, where the line
# already ended in a comment, appended after that comment with a comma:
#   } RumbleMgr; // size = 0x10E, was UnkRumbleStruct [LLM:HIGH]
# so the "//" is optional in the pattern. Strip it rather than skipping the
# whole line, or the declaration it rides on looks like a content change.
INLINE_TAG_RE = re.compile(r"(?:\s*//)?[\s,]*was\s+\w+\s*\[(?:oot|LLM:\w+)\]")


def is_comment_only(line):
    """True if the line is nothing but a comment. Such a line is not a
    declaration -- functions.h carries decomp placeholders like
    "// ? Audio_ResetData(?);" for symbols whose prototype is unknown -- so it
    is not a site that needs a declaration tag."""
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
    """The line with any provenance comment removed -- '' if the line is
    nothing but a comment. Use this before asking whether an old name is still
    live in the CODE, or the provenance comments (which quote the old name by
    design) make every completed rename look unfinished."""
    if is_marker_line(line):
        return _strip_trailing_comment(line)
    return INLINE_TAG_RE.sub("", line)
