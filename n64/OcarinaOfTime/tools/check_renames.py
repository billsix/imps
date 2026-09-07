#!/usr/bin/env python3
"""Gate the OoT decomp-renaming conventions.

WHEN TO RUN IT
    After any batch of decomp renames, before handing the patches over. The
    conventions in tasks/reference/ocarina/decomp-renaming.md are rules with
    teeth only if something checks them; this is that something. ~3,988 symbols
    are still un-named, so this runs many more times.

WHAT IT CHECKS (subcommands; `all` runs every one)

    traceable     Every symbol renamed since the pin is cited by a provenance
                  comment, and no cited old name is still live in the code
                  (i.e. no half-finished rename). Catches the classic miss:
                  forgetting soh/include/, which leaves orphan prototypes.

    declarations  Every HEADER declaration of a renamed symbol carries the
                  short `// was func_… [oot]` / `[LLM:HIGH]` tag. Without it a
                  reader of functions.h cannot tell an upstream name from one
                  of our guesses -- and most of these names ARE guesses.

    series        Every commit renames exactly one symbol (never two), and each
                  claimed rename is total: the old name survives only inside
                  provenance comments.

Content-equivalence is deliberately NOT checked here -- that is
tools/prove_comment_only.sh at the repo root, which settles it with a compiler.

USAGE
    n64/OcarinaOfTime/tools/check_renames.py [traceable|declarations|series|all]

Exits non-zero on any failure, so it works as a gate.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from renames_common import (ADDR_RE, CITED_RE, CHECKOUT, INLINE_TAG_RE,
                            MARKERS, SOURCE_PATHS, code_part, git,
                            is_comment_only, is_marker_line, pin_sha,
                            rename_range, renamed_symbols)

SUBJECT_RE = re.compile(r"^soh: rename (\S+) -> (\S+)$")


def _address_names_in_code(rev):
    """Address-names live in real code at `rev`, ignoring provenance comments
    (which quote the old name and would mask every completed rename)."""
    output = git("grep", "-hnE", ADDR_RE.pattern, rev, "--", *SOURCE_PATHS,
                 check=False)
    names = set()
    for line in output.splitlines():
        names.update(ADDR_RE.findall(code_part(line)))
    return names


def check_traceable():
    """Every rename is cited, and no rename is half-done."""
    pin = pin_sha()
    before, after = _address_names_in_code(pin), _address_names_in_code("HEAD")
    renamed = before - after

    cited = set()
    for line in git("diff", rename_range()).splitlines():
        if line.startswith("+") and is_marker_line(line):
            cited.update(CITED_RE.findall(line))

    untraceable = sorted(renamed - cited)
    incomplete = sorted(cited & after)
    print(f"  renamed since the pin : {len(renamed)}")
    print(f"  cited by a comment    : {len(cited & (renamed | cited))}")
    for name in untraceable:
        print(f"  FAIL untraceable (renamed but never cited): {name}")
    for name in incomplete:
        print(f"  FAIL incomplete (cited but still live)   : {name}")
    ok = not untraceable and not incomplete
    print("  OK  every rename is traceable and complete" if ok else "")
    return ok


def check_declarations():
    """Every header declaration of a renamed symbol carries the short tag."""
    names = renamed_symbols()
    if not names:
        print("  no renamed symbols found -- nothing to check")
        return True
    word_re = re.compile("|".join(rf"\b{re.escape(n)}\b" for n in names))
    bare, total = [], 0
    for path in git("diff", "--name-only", rename_range()).split():
        if not path.endswith((".h", ".hpp")):
            continue
        full = os.path.join(CHECKOUT, path)
        if not os.path.isfile(full):
            continue
        with open(full, encoding="utf-8", errors="replace") as handle:
            lines = handle.read().splitlines()
        for index, line in enumerate(lines):
            # A commented-out placeholder is not a declaration site.
            if not word_re.search(line) or is_comment_only(line):
                continue
            total += 1
            if INLINE_TAG_RE.search(line):
                continue
            if any(is_marker_line(a) for a in lines[max(0, index - 3):index]):
                continue
            # A typedef names itself on its CLOSING brace, so its comment sits
            # above the "typedef struct {" -- far outside a 3-line window.
            if line.lstrip().startswith("}"):
                for back in range(index - 1, max(-1, index - 400), -1):
                    if lines[back].strip().startswith("typedef struct"):
                        if back > 0 and is_marker_line(lines[back - 1]):
                            break
                else:
                    bare.append(f"{path}:{index + 1}")
                continue
            bare.append(f"{path}:{index + 1}")
    print(f"  header declaration sites : {total}")
    for site in bare:
        print(f"  FAIL untagged declaration: {site}")
    if not bare:
        print("  OK  every header declaration is tagged")
    return not bare


def check_series():
    """One rename per commit, and each claimed rename is total."""
    failures = []
    log = [ln.split(" ", 1) for ln in
           git("log", "--reverse", "--format=%H %s", rename_range()).splitlines()]
    symbol_commits = 0
    for sha, subject in log:
        if not git("show", "--stat", "--format=", sha).strip():
            failures.append(f"empty commit: {subject}")
            continue
        match = SUBJECT_RE.match(subject)
        # A file-rename commit shares the subject shape but names paths.
        if not match or match.group(1).endswith(".c"):
            continue
        symbol_commits += 1
        old, new = match.groups()

        added, removed = set(), set()
        for line in git("show", "--format=", sha).splitlines():
            if not line.startswith(("+", "-")) or line.startswith(("+++", "---")):
                continue
            body = code_part(line[1:])
            names = set(ADDR_RE.findall(body))
            if re.search(rf"\b{re.escape(new)}\b", body):
                names.add(new)
            (added if line.startswith("+") else removed).update(names)
        introduced, retired = added - removed, removed - added
        if introduced != {new}:
            failures.append(f"{subject}: introduces {sorted(introduced)}, "
                            f"expected [{new}]")
        if retired and retired != {old}:
            failures.append(f"{subject}: retires {sorted(retired)}, "
                            f"expected [{old}]")

        # totality: the old name must survive only inside comments
        for line in git("grep", "-lw", old, "HEAD", "--", *SOURCE_PATHS,
                        check=False).splitlines():
            path = line.split(":", 1)[1] if ":" in line else line
            text = git("show", f"HEAD:{path}", check=False)
            if any(re.search(rf"\b{re.escape(old)}\b", code_part(l))
                   for l in text.splitlines()):
                failures.append(f"{subject}: {old} still live in {path}")

    print(f"  commits on the series   : {len(log)}")
    print(f"  symbol-rename commits   : {symbol_commits}")
    for failure in failures:
        print(f"  FAIL {failure}")
    if not failures:
        print("  OK  one rename per commit, and every rename is total")
    return not failures


CHECKS = {"traceable": check_traceable,
          "declarations": check_declarations,
          "series": check_series}


def main(argv):
    which = argv[1] if len(argv) > 1 else "all"
    if which not in CHECKS and which != "all":
        print(__doc__)
        return 2
    names = list(CHECKS) if which == "all" else [which]
    ok = True
    for name in names:
        print(f"\n=== {name} ===")
        ok &= CHECKS[name]()
    print("\n" + ("ALL CHECKS PASSED" if ok else "FAILURES ABOVE"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
