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

    series        Every rename the history performs is CLAIMED by its commit
                  message, and each claimed rename is total: the old name
                  survives only inside provenance comments.

                  Two commit shapes are accepted. A single-symbol commit says
                  so in its subject ("soh: rename <old> -> <new>"). A GROUPED
                  commit -- the shape the 2026-09-08 squash produced, one per
                  definition file -- says how many it carries in its subject
                  and lists them in its body as "  * <old> -> <new>" entries;
                  the count and the entries must agree. Before the squash this
                  check read "exactly one rename per commit"; that was the
                  right rule while the series was being PRODUCED one rename at
                  a time, and the wrong one once it was regrouped for review.
                  The property worth gating never changed: no rename may
                  happen that the message does not account for.

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
                            SHORT_TAG_CITE_RE,
                            MARKERS, SOURCE_PATHS, code_part, git,
                            is_comment_only, is_marker_line, pin_sha,
                            rename_range, renamed_symbols)

SUBJECT_RE = re.compile(r"^soh: rename (\S+) -> (\S+)$")
GROUP_RE = re.compile(r"^soh: name the (\d+) address-named symbols in (\S+)$")
FILE_GROUP_RE = re.compile(r"^soh: rename (\d+) address-named source files\b")
ENTRY_RE = re.compile(r"^  \* (\S+) -> (\S+)$", re.M)


def claimed_renames(sha, subject):
    """The (old, new) pairs a commit's message says it performs.

    Returns None for a commit that claims no symbol rename (a file rename, or
    anything that is not part of the series).
    """
    if FILE_GROUP_RE.match(subject):
        return None                      # paths, not symbols -- see below
    single = SUBJECT_RE.match(subject)
    if single:
        return None if single.group(1).endswith(".c") else [single.groups()]
    group = GROUP_RE.match(subject)
    if not group:
        return None
    body = git("show", "-s", "--format=%B", sha)
    pairs = ENTRY_RE.findall(body)
    if len(pairs) != int(group.group(1)):
        raise ValueError(f"subject claims {group.group(1)} symbols but the "
                         f"body lists {len(pairs)}")
    return pairs


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
        if not line.startswith("+"):
            continue
        if is_marker_line(line):
            cited.update(CITED_RE.findall(line))
            continue
        # A static declared INSIDE a function body gets only the SHORT tag --
        # a long provenance comment in the middle of a body would be noise,
        # and the tagger correctly declines to add one. The short tag is a
        # citation too, so read it here as renamed_symbols() already does.
        # Without this, every function-local static reads as untraceable
        # (17 of them on 2026-09-08, all correctly tagged).
        cited.update(m.group(1) for m in SHORT_TAG_CITE_RE.finditer(line))

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
            # A prototype split across several lines carries its name on the
            # FIRST line, which ends in ',' -- appending a "//" tag there would
            # comment out the rest of the parameter list.  Its tag therefore
            # goes on the line that closes the prototype with ';'.
            if not line.rstrip().endswith((";", "{")):
                for ahead in range(index + 1, min(len(lines), index + 8)):
                    if INLINE_TAG_RE.search(lines[ahead]):
                        tagged_ahead = True
                        break
                    if lines[ahead].rstrip().endswith(";"):
                        tagged_ahead = False
                        break
                else:
                    tagged_ahead = False
                if tagged_ahead:
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
    """Every rename is claimed by its commit message, and each is total."""
    failures = []
    log = [ln.split(" ", 1) for ln in
           git("log", "--reverse", "--format=%H %s", rename_range()).splitlines()]
    symbol_commits = 0
    renames = 0
    for sha, subject in log:
        if not git("show", "--stat", "--format=", sha).strip():
            failures.append(f"empty commit: {subject}")
            continue
        try:
            pairs = claimed_renames(sha, subject)
        except ValueError as exc:
            failures.append(f"{subject}: {exc}")
            continue
        if pairs is None:
            continue
        symbol_commits += 1
        renames += len(pairs)
        olds = {old for old, _ in pairs}
        news = {new for _, new in pairs}

        added, removed = set(), set()
        added_text = []
        for line in git("show", "--format=", sha).splitlines():
            if not line.startswith(("+", "-")) or line.startswith(("+++", "---")):
                continue
            body = code_part(line[1:])
            if line.startswith("+"):
                added_text.append(body)
                added.update(ADDR_RE.findall(body))
            else:
                removed.update(ADDR_RE.findall(body))
        introduced, retired = added - removed, removed - added
        # An address name must only ever LEAVE the code, never arrive.
        if introduced:
            failures.append(f"{subject}: introduces address names "
                            f"{sorted(introduced)}")
        # ...and exactly the ones the message claims must leave. Compare only
        # against the claimed names ADDR_RE can actually see: SoH adds its own
        # derivatives of an address name (func_808C1554_Raw,
        # func_80AB70A0_nocutscene) whose trailing suffix defeats the pattern's
        # word boundary, so they never show up in `retired` however correctly
        # they are renamed. The totality loop below still holds them to account.
        addr_olds = {o for o in olds if ADDR_RE.fullmatch(o)}
        if retired and retired != addr_olds:
            failures.append(f"{subject}: retires {sorted(retired)}, "
                            f"claimed {sorted(addr_olds)}")
        # every new name the message claims must actually appear in the diff
        joined = "\n".join(added_text)
        for new in sorted(news):
            if not re.search(rf"\b{re.escape(new)}\b", joined):
                failures.append(f"{subject}: claims {new} but never adds it")

        # totality: each old name must survive only inside comments
        for old in sorted(olds):
            for line in git("grep", "-lw", old, "HEAD", "--", *SOURCE_PATHS,
                            check=False).splitlines():
                path = line.split(":", 1)[1] if ":" in line else line
                text = git("show", f"HEAD:{path}", check=False)
                if any(re.search(rf"\b{re.escape(old)}\b", code_part(l))
                       for l in text.splitlines()):
                    failures.append(f"{subject}: {old} still live in {path}")

    print(f"  commits on the series   : {len(log)}")
    print(f"  symbol-rename commits   : {symbol_commits}")
    print(f"  renames they claim      : {renames}")
    for failure in failures:
        print(f"  FAIL {failure}")
    if not failures:
        print("  OK  every rename is claimed by its commit, and every "
              "rename is total")
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
