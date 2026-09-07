#!/usr/bin/env python3
"""Gate: is every rename in the commit traceable, and is every rename complete?

Two failure modes this catches:

  * UNTRACEABLE -- a symbol was renamed but no provenance comment cites the old
    address name, so nobody can re-derive or overturn the guess.
  * INCOMPLETE  -- a comment claims a rename but the old name is still live in
    the code, i.e. the rename missed a site (classically soh/include/).

Method: list the address-names present in real code at the pin and at the
rename commit; the set difference is what was actually renamed. Compare that
against the set of old names quoted by the provenance comments the commit adds.

Both passes SKIP provenance-comment lines themselves -- they quote the old name,
which would otherwise make every completed rename look un-done.

Run from the repo root:
    python3 tasks/adhoc/ocarina-split-rename-patch/completeness.py
Exits non-zero if either set is non-empty, so it works as a gate.
"""
import sys

from _common import (ADDR_RE, CITED_RE, SOURCE_PATHS, code_part, git,
                     is_marker_line, pin_sha, rename_range)


def address_names_in_code(rev):
    """Address-names live in real code at `rev`, excluding those that appear
    only inside a provenance comment."""
    # git grep -hnE: -h no filename, -n line number, -E extended regex. Piping
    # through Python rather than `grep -o` keeps whole lines so we can drop the
    # comment lines before extracting names.
    output = git("grep", "-hnE", ADDR_RE.pattern, rev, "--", *SOURCE_PATHS,
                 check=False)
    names = set()
    for line in output.splitlines():
        # code_part drops both provenance forms -- the long definition comment
        # and the short inline declaration tag -- so only live code counts.
        names.update(ADDR_RE.findall(code_part(line)))
    return names


def cited_old_names(rev_range):
    """Old names quoted by provenance comments the work ADDS (leading '+')."""
    cited = set()
    for line in git("diff", rev_range).splitlines():
        if line.startswith("+") and is_marker_line(line):
            cited.update(CITED_RE.findall(line))
    return cited


def main():
    pin, rev_range = pin_sha(), rename_range()
    before = address_names_in_code(pin)
    after = address_names_in_code("HEAD")
    renamed = before - after
    cited = cited_old_names(rev_range)

    untraceable = sorted(renamed - cited)
    incomplete = sorted(cited & after)

    print(f"pin                              : {pin[:9]}")
    print(f"commits applied on top           : "
          f"{git('rev-list', '--count', rev_range).strip()}")
    print(f"address-names in code at pin     : {len(before)}")
    print(f"address-names in code after      : {len(after)}")
    print(f"actually renamed                 : {len(renamed)}")
    print(f"cited by a provenance comment    : {len(cited)}")
    print(f"UNTRACEABLE (renamed, not cited) : {len(untraceable)}")
    print(f"INCOMPLETE  (cited, still live)  : {len(incomplete)}")

    for name in untraceable:
        print(f"  untraceable: {name}")
    for name in incomplete:
        print(f"  incomplete : {name}")

    return 1 if (untraceable or incomplete) else 0


if __name__ == "__main__":
    sys.path.insert(0, __file__.rsplit("/", 1)[0])
    sys.exit(main())
