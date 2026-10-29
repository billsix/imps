#!/usr/bin/env python3
"""Gate every patch stream that is comment-only BY CONTRACT, across ALL families.

WHICH STREAMS
    Streams named ``docs`` or ``book``:
      * ``docs/`` -- explanatory doc comments added to interesting source (the
        docs-only carriers: unixutils/, android/).
      * ``book/`` -- ``// doc-region-begin/end`` markers so a Sphinx book can
        ``literalinclude`` spans by NAME (the mario64 mechanism; n64/CLAUDE.md).
    A code stream (n64's cheats/, personal/, upstreamable-*/) is NEVER checked -- it
    is not comment-only. Adding a doc comment or a doc-region marker must never change
    the program; if one ever does, the docs have silently started patching the code.

HOW IT DISCOVERS PROJECTS (no family is hardcoded)
    Every ``<family>/<project>/patches/`` dir whose project has a ``fetch.sh``. Three
    project shapes are handled: multi-repo carrier (a ``repos`` manifest + checkout/<repo>/
    and patches/<repo>/), single-repo carrier (a checkout/ + patches/), and the n64 port
    shape (a named checkout subdir + the game-tree lane plus a ``patches-libultraship`` lane).

HOW IT PICKS THE PROVER (dispatch, not one engine)
    Each project declares its source language in ``patches/LANG`` (one word: c, rust or
    kotlin; undeclared -> C). Per comment-only stream: ``c`` -> tools/prove_comment_only.sh
    (gcc -fpreprocessed strips comments, then token streams are compared); ``rust``/``kotlin``
    -> tools/prove_comment_only_strip.py --lang <lang> (a language-aware comment stripper).

WHAT IT DOES, per comment-only stream
    Builds two scratch branches inside the checkout -- BEFORE = the pin plus every stream
    that applies before this one, and AFTER = that plus this stream -- then hands them to
    the right prover with --allow-line-shift. The BEFORE..AFTER diff is exactly this
    stream's patches.

USAGE
    tools/check_comment_only_streams.sh [project ...]     # default: all
    tools/check_comment_only_streams.sh dash ripgrep SuperMario64

It works on scratch branches inside the checkouts, RESTORES each checkout to the state
it was in beforehand, drops the scratch branches, and never touches ``runDir/`` (a
sibling of the checkout). Exits non-zero if any checked stream is NOT comment-only.

Invoked through the ``tools/check_comment_only_streams.sh`` shim (ported from that bash
2026-10-29, William Emerison Six <billsix@gmail.com>; behaviour-identical).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# repo root = one dir above tools/ (this file lives in tools/).
ROOT: Path = Path(__file__).resolve().parent.parent
PROVE_C: Path = ROOT / "tools" / "prove_comment_only.sh"
PROVE_STRIP: Path = ROOT / "tools" / "prove_comment_only_strip.py"

# The comment-only stream names.
COS_NAMES: frozenset[str] = frozenset({"docs", "book"})


def git(
    repo: Path, *args: str, inherit: bool = False
) -> subprocess.CompletedProcess[str]:
    """Run ``git -C <repo> <args>``; capture output unless ``inherit`` lets it stream through."""
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=not inherit,
        text=True,
        check=False,
    )


def read_lang(patches_dir: Path) -> str:
    """Return the declared language (c/rust/kotlin) from ``patches/LANG``, or "".

    LANG is one word; ``#``-comments and blank lines are ignored.
    """
    lang_file: Path = patches_dir / "LANG"
    if not lang_file.is_file():
        return ""
    for line in lang_file.read_text().splitlines():
        word: str = "".join(line.split("#", 1)[0].split())
        if word:
            return word
    return ""


def read_pin(fetch_sh: Path) -> str:
    """Return the first whitespace token of the ``PIN_SHA=`` value in ``fetch.sh``."""
    for line in fetch_sh.read_text().splitlines():
        if line.startswith("PIN_SHA="):
            tokens: list[str] = line[len("PIN_SHA=") :].split()
            return tokens[0] if tokens else ""
    return ""


def subdirs(directory: Path) -> list[Path]:
    """Return the immediate subdirectories of ``directory``, sorted by name (empty if none)."""
    if not directory.is_dir():
        return []
    return sorted(child for child in directory.iterdir() if child.is_dir())


def checkout_for(proj: Path) -> str | None:
    """Return the basename of the one subdirectory holding a ``.git``, else None."""
    for sub in subdirs(proj):
        if (sub / ".git").exists():
            return sub.name
    return None


def ordered_streams(pdir: Path) -> list[str]:
    """Return stream names in apply order: those listed in ORDER first, then the rest alphabetically.

    ORDER lives at ``<pdir>/ORDER`` or one level up (a multi-repo carrier shares one
    ``patches/ORDER`` across every ``patches/<repo>/``). Comments/blanks in ORDER are ignored.
    """
    order_file: Path | None = None
    if (pdir / "ORDER").is_file():
        order_file = pdir / "ORDER"
    elif (pdir.parent / "ORDER").is_file():
        order_file = pdir.parent / "ORDER"

    listed: list[str] = []
    if order_file is not None:
        for line in order_file.read_text().splitlines():
            name: str = "".join(line.split("#", 1)[0].split())
            if name and (pdir / name).is_dir():
                listed.append(name)

    listed_set: set[str] = set(listed)
    rest: list[str] = [sub.name for sub in subdirs(pdir) if sub.name not in listed_set]
    return listed + rest


def populated(patchbase: Path, stream: str) -> bool:
    """True iff the stream directory holds at least one ``*.patch`` file."""
    return any((patchbase / stream).glob("*.patch"))


def patch_files(patchbase: Path, stream: str) -> list[str]:
    """Return the stream's ``*.patch`` paths as strings, sorted (as the shell glob delivered them)."""
    return sorted(str(p) for p in (patchbase / stream).glob("*.patch"))


class Gate:
    """Accumulates the pass/fail status and checked-stream count across all projects."""

    def __init__(self) -> None:
        self.status: int = 0
        self.checked: int = 0

    def restore(self, repo: Path, prev: str) -> None:
        """Put the checkout back where it was and drop the scratch branches.

        A checkout's documented resting state is "pin + full series" (master CLAUDE.md);
        leaving it on a half-built branch would surprise later.
        """
        if git(repo, "checkout", "-q", prev).returncode != 0:
            git(repo, "checkout", "-q", "--detach", prev)
        git(repo, "branch", "-q", "-D", "cos-before", "cos-after")

    def prove(self, repo: Path, lang: str, label: str) -> None:
        """Run the language's prover over cos-before..cos-after, setting status on failure."""
        sys.stdout.flush()
        if lang == "c":
            rc: int = subprocess.run(
                [
                    str(PROVE_C),
                    "--allow-line-shift",
                    str(repo),
                    "cos-before",
                    "cos-after",
                ],
                check=False,
            ).returncode
            if rc != 0:
                self.status = 1
        elif lang in ("rust", "kotlin"):
            rc = subprocess.run(
                [
                    "python3",
                    str(PROVE_STRIP),
                    "--lang",
                    lang,
                    "--allow-line-shift",
                    str(repo),
                    "cos-before",
                    "cos-after",
                ],
                check=False,
            ).returncode
            if rc != 0:
                self.status = 1
        else:
            print(
                f"  UNKNOWN language '{lang}' for {label} -- cannot prove",
                file=sys.stderr,
            )
            self.status = 1

    def check_unit(
        self, repo: Path, pin: str, patchbase: Path, lang: str, label: str
    ) -> None:
        """Prove every populated comment-only stream in ``patchbase`` is comment-only.

        Against ``repo`` at ``pin``, using the prover for ``lang``.
        """
        if not (repo / ".git").exists():
            print(f"== {label}: no checkout ({repo}) -- run ./fetch.sh; skipped")
            return
        if git(repo, "cat-file", "-e", f"{pin}^{{commit}}").returncode != 0:
            print(f"== {label}: pin {pin[:9]} not in {repo} -- run ./fetch.sh; skipped")
            return

        ordered: list[str] = ordered_streams(patchbase)
        if not any(s in COS_NAMES and populated(patchbase, s) for s in ordered):
            return

        git(repo, "config", "commit.gpgsign", "false")
        if (repo / ".git" / "rebase-apply").is_dir():
            print(
                f"  interrupted 'git am' in {repo} -- run: git -C {repo} am --abort",
                file=sys.stderr,
            )
            self.status = 1
            return

        symref: subprocess.CompletedProcess[str] = git(
            repo, "symbolic-ref", "--quiet", "--short", "HEAD"
        )
        prev_ref: str = (
            symref.stdout.strip()
            if symref.returncode == 0
            else git(repo, "rev-parse", "HEAD").stdout.strip()
        )

        for stream in ordered:
            if not (stream in COS_NAMES and populated(patchbase, stream)):
                continue

            print()
            print(f"############ {label} / {stream} ({lang}) ############")

            # BEFORE: the pin plus every stream that applies before this one.
            git(repo, "checkout", "-q", "-B", "cos-before", pin)
            git(repo, "reset", "-q", "--hard", pin)
            ok: bool = True
            for other in ordered:
                if other == stream:
                    break  # only streams before this one
                if not populated(patchbase, other):
                    continue
                if (
                    git(
                        repo, "am", "--3way", "-q", *patch_files(patchbase, other)
                    ).returncode
                    != 0
                ):
                    print(
                        f"  FAILED to apply {other} -- cannot build the baseline",
                        file=sys.stderr,
                    )
                    git(repo, "am", "--abort")
                    self.status = 1
                    ok = False
                    break
            if not ok:
                self.restore(repo, prev_ref)
                continue

            # AFTER: this stream on top.
            git(repo, "checkout", "-q", "-b", "cos-after")
            if (
                git(
                    repo, "am", "--3way", "-q", *patch_files(patchbase, stream)
                ).returncode
                != 0
            ):
                print(f"  FAILED to apply the {stream} stream", file=sys.stderr)
                git(repo, "am", "--abort")
                self.status = 1
                self.restore(repo, prev_ref)
                continue

            self.prove(repo, lang, label)
            self.checked += 1
            self.restore(repo, prev_ref)


def discover_projects() -> list[str]:
    """Return every ``<family>/<project>`` (relative to ROOT) whose project has a ``fetch.sh``, sorted."""
    projects: list[str] = []
    for patches in ROOT.glob("*/*/patches"):
        proj: Path = patches.parent
        if (proj / "fetch.sh").is_file():
            projects.append(str(proj.relative_to(ROOT)))
    return sorted(projects)


def main(argv: list[str]) -> int:
    requested: list[str] = argv
    all_projects: list[str] = discover_projects()
    if requested:
        projects: list[str] = [p for p in all_projects if Path(p).name in requested]
    else:
        projects = all_projects

    gate: Gate = Gate()
    for proj_rel in projects:
        proj: Path = ROOT / proj_rel
        name: str = Path(proj_rel).name
        lang: str = read_lang(proj / "patches") or "c"

        if (proj / "repos").is_file():
            # Multi-repo carrier: one unit per manifest repo, at that repo's pin.
            for line in (proj / "repos").read_text().splitlines():
                fields: list[str] = line.split()
                if not fields or fields[0].startswith("#"):
                    continue
                url: str = fields[0]
                sha: str = fields[1] if len(fields) > 1 else ""
                if not sha:
                    continue
                rname: str = Path(url).name.removesuffix(".git")
                gate.check_unit(
                    proj / "checkout" / rname,
                    sha,
                    proj / "patches" / rname,
                    lang,
                    f"{name}/{rname}",
                )

        elif (proj / "checkout" / ".git").exists():
            # Single-repo docs carrier.
            pin: str = read_pin(proj / "fetch.sh")
            gate.check_unit(proj / "checkout", pin, proj / "patches", lang, name)

        else:
            # n64 port shape (the default): a named checkout subdir + up to two lanes.
            co: str | None = checkout_for(proj)
            if co is None:
                print(f"== {name}: no checkout (run ./fetch.sh) -- skipped")
                continue
            pin = read_pin(proj / "fetch.sh")
            gate.check_unit(proj / co, pin, proj / "patches", lang, name)
            if any((proj / "patches-libultraship").glob("*/*.patch")):
                lus_pin: str = git(
                    proj / co, "rev-parse", f"{pin}:libultraship"
                ).stdout.strip()
                if lus_pin:
                    gate.check_unit(
                        proj / co / "libultraship",
                        lus_pin,
                        proj / "patches-libultraship",
                        lang,
                        f"{name}/libultraship",
                    )

    print()
    print("############ SUMMARY ############")
    if gate.checked == 0:
        print("  no comment-only streams found -- nothing to check")
    elif gate.status == 0:
        print(f"  {gate.checked} stream(s) checked, all PROVEN comment-only")
    else:
        print("  failures above")
    return gate.status


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
