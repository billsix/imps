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


def rename_commit():
    """The rename commit's SHA, found by subject so it survives a rebuild."""
    # --format=%H%x09%s prints "<sha>\t<subject>"; %x09 is a literal tab.
    for line in git("log", "--format=%H%x09%s",
                    f"{pin_sha()}..HEAD").splitlines():
        sha, _, subject = line.partition("\t")
        if RENAME_SUBJECT in subject:
            return sha
    raise SystemExit(f"no commit titled {RENAME_SUBJECT!r} above the pin — "
                     "is the patch series applied? (run ./apply.sh)")


def is_marker_line(line):
    """True for a provenance comment line. Such lines quote the OLD name, so
    every count that asks 'is the old name still in the code?' must skip them."""
    return any(marker in line for marker in MARKERS)
