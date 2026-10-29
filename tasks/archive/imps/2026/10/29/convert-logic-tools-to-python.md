# Convert imps' logic-heavy shell tools to Python

**Status:** done (2026-10-29; both tools converted, proven byte-identical, committed `2d43ce88`)
**Priority:** 6
**Difficulty:** 4

## BLUF

Two of imps' own `tools/*.sh` do real data/graph logic that is markedly harder to
read in bash than it would be in Python; rewrite exactly those two in Python,
behaviour-identical, leaving a thin `.sh` shim at each old path so no caller
changes. Done = `apply_unit.py` and `check_comment_only_streams.py` exist, the
old `.sh` paths are 2-line shims that `exec` them, every existing caller still
works unchanged, and the Python reproduces the bash output (verified by
`--closure` equivalence on the live checkouts). Decided with the maintainer
2026-10-29 (William Emerison Six <billsix@gmail.com>): convert ONLY these two;
the mostly-git-orchestration gates stay bash (see "Explicitly left as bash").

## Context

This came out of a cross-repo sweep (2026-10-29) for `tools/` shell scripts whose
"advanced bash" (arrays, `mapfile`, process substitution, substring-membership
`case`, associative arrays, bit-twiddling) makes them harder to read than the
equivalent Python. imps was the biggest offender. The maintainer chose a
conservative scope: convert the two scripts that do genuine *logic*, not the ones
that are ~70% `git` subprocess glue (bash reads those fine).

These are imps' **own** tooling, not patch-carried code — so the "do NOT apply the
C coding standard / style sweeps to imps-carried code" rule in the master
`CLAUDE.md` does **not** apply here. Normal house Python style applies (annotate
every binding; Google docstrings; see `~/.claude/reference/python-coding-standard.md`).

imps already ships Python tools (`prove_comment_only_strip.py`, `squash_series.py`,
`resolve_rename_conflicts.py`, `asmdiff_normalise.py`) and the images carry
`python3`, so there is no new dependency.

### The shim mechanism (how callers stay untouched)

`tools/foo.sh` becomes a 2-line shim:
```sh
#!/usr/bin/env bash
exec python3 "$(dirname "$0")/foo.py" "$@"
```
and the logic moves to `tools/foo.py`. Callers keep saying `tools/foo.sh`. This is
already idiomatic in imps (e.g. `unixutils/ripgrep/check-comment-only.sh` is itself
just `exec ../../tools/check_comment_only_streams.sh ripgrep`). Keep the shim's
executable bit (`git add --chmod=+x`) — `check_upstreamable_applies.sh` invokes
`apply_unit.sh` by path, and the local `check-comment-only.sh` wrappers invoke the
other by path.

## Scope

Convert (each: new `.py` + `.sh` shim, behaviour-identical):

1. **`tools/apply_unit.sh`** (101 lines) — transitive `DEPENDS` graph DFS with
   `declare -A VISITED` + recursion echoed into `mapfile`. The post-order,
   cycle-safe closure is textbook Python.
   - Preserve exactly: the `--closure` stdout (one stream per line, prerequisites
     first — consumed by `check_upstreamable_applies.sh` via `mapfile -t cl`); the
     `==> applied N patch(es) for '<slug>' (closure: ...)` line (that sibling greps
     it for `applied [0-9]+ patch`); every usage/error string + exit code (2 for
     usage/no-such-stream, 1 for missing-dep/no-checkout/pin-missing/apply-fail).
   - Preserve behaviour: find the checkout (first subdir with `.git`), read the pin
     from `fetch.sh` (`PIN_SHA=`), set `commit.gpgsign false` repo-locally, reset to
     pin on branch `imps-<slug>`, `git am --3way` each stream's `*.patch` in closure
     order, `am --abort` + exit 1 on failure. **Never touch `runDir/`.**

2. **`tools/check_comment_only_streams.sh`** (284 lines) — family-agnostic project
   discovery + `patches/LANG` dispatch + per-stream BEFORE/AFTER scratch-branch build
   driving the right prover (`prove_comment_only.sh` for C, `prove_comment_only_strip.py`
   for rust/kotlin). Arrays, `mapfile`, process substitution, `ordered_streams` from
   `ORDER`, substring-membership `case` on `COS_NAMES=" docs book "`.
   - Preserve exactly: the per-project discovery set (`*/*/patches` whose project has
     `fetch.sh`, sorted), the optional basename filter from argv, stream ORDER
     resolution (listed-first then alphabetical), the three project shapes (multi-repo
     `repos` manifest, single-repo `checkout/`, n64 named-checkout + `patches-libultraship`
     lane), the prover dispatch, scratch-branch BEFORE/AFTER construction with
     `--allow-line-shift`, the `restore` of each checkout to its prior state, and the
     SUMMARY/exit semantics. **Never touch `runDir/`.** Shell out to the two provers
     (don't reimplement them; `prove_comment_only.sh` stays bash by decision).

### Explicitly left as bash (maintainer decision 2026-10-29)

Mostly `git`/process orchestration — bash reads them fine, Python would add a
`subprocess` call per git step for no readability gain:
`check_patches_apply.sh`, `check_upstreamable_applies.sh`, `asmdiff.sh` (also a
delicate codegen gate), `prove_comment_only.sh`, `asmdiff_tree.sh`,
`verify_appimage_builds.sh`.

## Verification

- `tools/apply_unit.sh --closure <Project> <slug>` output is byte-identical between
  the old bash and the new shim→py, for every present upstreamable unit (the
  checkouts are present). Capture both and `diff`.
- `tools/check_upstreamable_applies.sh` (the sibling that calls `apply_unit`) still
  runs and its closure/invariant checks behave as before.
- `tools/check_comment_only_streams.sh <project>` produces the same project
  discovery, stream ordering, and PASS/FAIL verdicts as the bash did; checkouts are
  left on their prior resting state (pin + full series), `runDir/` untouched.
- Shims keep `+x`; `grep -rn 'apply_unit.sh\|check_comment_only_streams.sh'` callers
  all still resolve (paths unchanged by design).

## Ad-hoc

Equivalence-check scripts (capture old bash output, convert, diff) under
`tasks/adhoc/convert-logic-tools-to-python/`; `git rm` on archive.
