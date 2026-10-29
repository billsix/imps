#!/usr/bin/env python3
"""Apply ONE upstreamable unit (one PR's worth) in ISOLATION on pristine upstream.

The currency of upstreaming is a unit of work (one PR), carried as an
``upstreamable-<slug>/`` stream (master ``CLAUDE.md``, "Patch philosophy").
``apply.sh`` applies the WHOLE series (the full personal stack); this applies only
the named unit plus its declared upstreamable prerequisites -- the honest "will this
PR build on upstream by itself" setup.

The invariant it relies on: an upstreamable unit depends only on pristine upstream
and OTHER upstreamable units -- never on personal/cheats/book. Prerequisites are
declared in ``patches/<slug>/DEPENDS`` (one upstreamable stream name per line; absent
= depends only on the bare pin). ``check_upstreamable_applies.sh`` enforces this.

Usage::

    tools/apply_unit.sh <Project> <slug>            # reset to pin, apply the closure
    tools/apply_unit.sh --closure <Project> <slug>  # print the closure, mutate nothing
    # then, to build the isolated AppImage:
    make -C n64/<Project>/<checkout>/docker appimage

Leaves the checkout on branch ``imps-<slug>`` at pin + the unit's closure. Never
touches ``runDir/`` (a sibling of the checkout). Game-tree lane only (no upstreamable
unit lives in the libultraship lane today).

Invoked through the ``tools/apply_unit.sh`` shim (the logic was ported from that bash
2026-10-29, William Emerison Six <billsix@gmail.com>; the output is byte-identical,
so the ``--closure`` stdout that ``check_upstreamable_applies.sh`` consumes, and the
``applied N patch(es)`` line it greps, are unchanged).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import NoReturn

# repo root = one dir above tools/ (this file lives in tools/).
ROOT: Path = Path(__file__).resolve().parent.parent


def die(message: str, code: int) -> NoReturn:
    """Print ``message`` to stderr and exit with ``code``."""
    print(message, file=sys.stderr)
    raise SystemExit(code)


def git(
    repo: Path,
    *args: str,
    check: bool = True,
    quiet_fail: bool = False,
    inherit: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run ``git -C <repo> <args>`` and return the completed process.

    Args:
        repo: The checkout to operate in (``git -C``).
        args: The git arguments.
        check: Forward the command's stderr when it fails and this is True; when
            False the caller inspects ``returncode`` itself.
        quiet_fail: Suppress the command's own stderr (for probes like ``cat-file``).
        inherit: Let the command write straight to this process's stdout/stderr
            (for ``git am`` without ``-q``, whose "Applying:"/conflict output the
            caller tails on failure) instead of capturing it.
    """
    result: subprocess.CompletedProcess[str] = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=not inherit,
        text=True,
        check=False,
    )
    if check and not inherit and result.returncode != 0 and not quiet_fail:
        sys.stderr.write(result.stderr)
    return result


def read_pin(fetch_sh: Path) -> str:
    """Return the ``PIN_SHA=`` value from a project's ``fetch.sh`` (the single source of truth)."""
    lines: list[str] = [
        line[len("PIN_SHA=") :].rstrip("\n")
        for line in fetch_sh.read_text().splitlines(keepends=True)
        if line.startswith("PIN_SHA=")
    ]
    return "\n".join(lines)


def closure(pdir: Path, slug: str, visited: set[str], ordered: list[str]) -> None:
    """Append the transitive DEPENDS closure of ``slug`` to ``ordered``, prerequisites first.

    Post-order and cycle-safe (``visited`` guards re-entry), so each stream appears once
    and after every stream it depends on.
    """
    if slug in visited:
        return
    visited.add(slug)
    if not (pdir / slug).is_dir():
        die(f"DEPENDS names a missing stream: {slug}", 1)
    depends: Path = pdir / slug / "DEPENDS"
    if depends.is_file():
        for line in depends.read_text().splitlines():
            dep: str = "".join(line.split("#", 1)[0].split())
            if dep:
                closure(pdir, dep, visited, ordered)
    ordered.append(slug)


def find_checkout(proj: Path) -> str | None:
    """Return the basename of the one subdirectory holding a ``.git``, else None."""
    for sub in sorted(p for p in proj.glob("*/") if p.is_dir()):
        if (sub / ".git").exists():
            return sub.name
    return None


def main(argv: list[str]) -> int:
    closure_only: bool = False
    if argv and argv[0] == "--closure":
        closure_only = True
        argv = argv[1:]

    proj_name: str = argv[0] if len(argv) >= 1 else ""
    slug: str = argv[1] if len(argv) >= 2 else ""
    if not proj_name or not slug:
        die("usage: tools/apply_unit.sh [--closure] <Project> <slug>", 2)

    proj: Path = ROOT / "n64" / proj_name
    pdir: Path = proj / "patches"
    if not (pdir / slug).is_dir():
        die(f"no such stream: n64/{proj_name}/patches/{slug}", 2)

    streams: list[str] = []
    closure(pdir, slug, set(), streams)

    if closure_only:
        for name in streams:
            print(name)
        return 0

    checkout: str | None = find_checkout(proj)
    if checkout is None:
        die(f"no checkout in n64/{proj_name} -- run ./fetch.sh", 1)
    repo: Path = proj / checkout
    pin: str = read_pin(proj / "fetch.sh")

    if (repo / ".git" / "rebase-apply").is_dir():
        die(f"interrupted 'git am' -- run: git -C {repo} am --abort", 1)
    if (
        git(
            repo, "cat-file", "-e", f"{pin}^{{commit}}", check=False, quiet_fail=True
        ).returncode
        != 0
    ):
        die("pin not in checkout -- run ./fetch.sh", 1)

    branch: str = f"imps-{slug}"
    print(f"==> {proj_name}: reset {checkout} to pin {pin[:9]}, branch {branch}")
    # Repo-local only (never imps itself): signing fails in the sandbox and aborts git am.
    git(repo, "config", "commit.gpgsign", "false")
    git(repo, "checkout", "-q", "-B", branch, pin)
    git(repo, "reset", "-q", "--hard", pin)
    git(repo, "clean", "-qfd")

    for stream in streams:
        patches: list[str] = sorted(str(p) for p in (pdir / stream).glob("*.patch"))
        if patches:
            print(f"    apply unit stream: patches/{stream}/")
            if (
                git(
                    repo, "am", "--3way", *patches, check=False, inherit=True
                ).returncode
                != 0
            ):
                print(
                    f"FAIL: {stream} did not apply cleanly on pristine upstream (+closure)",
                    file=sys.stderr,
                )
                git(repo, "am", "--abort", check=False, quiet_fail=True)
                return 1

    count: str = git(repo, "rev-list", "--count", f"{pin}..HEAD").stdout.strip()
    print(f"==> applied {count} patch(es) for '{slug}' (closure: {' '.join(streams)})")
    print(f"    build it:  make -C n64/{proj_name}/{checkout}/docker appimage")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
