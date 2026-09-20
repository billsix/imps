# Add explicit Python type annotations to imps's tooling (globals + locals + params + returns)

**Status:** DONE — 2026-09-20 (William Emerison Six <billsix@gmail.com> gave the go-ahead as the impo
sibling's follow-on). `tools/squash_series.py` annotated generously (globals + locals + params + returns);
`ruff check` + `ty check` clean; behavior preserved. Requested 2026-09-19 ("add python types to
everything, global variables, local variables, etc" for all impo + imps tools). Archived.
Sibling in impo: `impo/tasks/annotate-tooling-python-types.md` (that repo's larger tool set — DONE too).
**Priority:** 6
**Difficulty:** 2 (imps has a single maintainer-owned Python tool)

## BLUF

Annotated imps's Python tooling generously — module globals, function params/returns, AND local variables
— per the maintainer's cross-project standard. imps has exactly **one** maintainer-owned Python tool:
`tools/squash_series.py` (the other `tools/` scripts — `check_patches_apply.sh`,
`check_comment_only_streams.sh`, `prove_comment_only.sh` — are shell, not Python; every other `*.py` in
the tree is upstream checkout code under `n64/*/` and is out of scope). Done: `tools/squash_series.py`
has annotated globals, locals, params, and returns, and is `ruff`/`ty`-clean.

## Outcome (2026-09-20)

Annotated `tools/squash_series.py` (the git-history squash helper) to the trench-tools exemplar density:
all 12 module globals (`HERE`/`ROOT`/`PROJECT`/`BACKUP`/`WORK`: `str`; `MARKERS: tuple[str, str]`; the
three `re.Pattern[str]` regexes; etc.), every function's params + return (`-> str`/`-> int`/`-> None`,
the `dict[str, str]` commit records and `list[list[dict[str, str]]]` unit lists), and locals + loop/unpack
targets (declared on the line above per the standard). Added `from __future__ import annotations` so the
annotations are never evaluated at runtime. Two locals in `entry()` (`source`, `reason`) are each a
`re.Match[str] | None` then reassigned to `str`, so they correctly carry no annotation (ty narrows them);
noted inline.

**Also cleared pre-existing lint/type errors this file carried at HEAD** (unrelated to types, but needed
to meet the "ruff/ty-clean" done-criterion — all behavior-neutral):
- 4× `FURB167` — `re.M`/`re.S` aliases → `re.MULTILINE`/`re.DOTALL` (same constants).
- `PLW1510` — made `subprocess.run`'s `check=` explicit (`check=False`, its prior implicit default; the
  helper does its own return-code check).
- `SIM115` — `pin_sha()`'s `open(...).read()` → a `with` block (was leaking the fd).
- `ty` (line 85) — `re.search(...).group(1)` on a possibly-`None` match: added an explicit `None` guard
  that raises `SystemExit` with a clear message (success path unchanged).

### Verification (all green)
- `ruff check tools/squash_series.py` — All checks passed (was 6 errors at HEAD).
- `ty check tools/squash_series.py` — All checks passed (was 1 error at HEAD).
- `python3 -m py_compile` — OK.
- **Behavior:** `--dry-run` exits identically (graceful "make the backup branch first"); `pin_sha()` +
  `project_dir()` called directly return the real pin SHA, exercising the new `with`-open + `None`-guard
  on the success path. The success-path logic is untouched; the only new behavior is a clearer error on
  the (previously crashing) missing-`PIN_SHA` path.
- **Did NOT run `ruff format`:** this file is deliberately hand-wrapped in a compact style (not
  Black/ruff-format style) — it was already not format-clean at HEAD, so reformatting would fight the
  maintainer's style and reflow the whole file. `ruff check` (the relevant gate) is clean.

## Context (cold-start)

- **The standard:** `~/.claude/reference/python-coding-standard.md` ("annotate generously — locals +
  globals too"). The exemplar to match for density is the sibling **impo** repo's trench tools
  (`trench/elementary-differential-equations/tools/*.py`), recently done to this standard.
- **Only one file is in scope.** `tools/squash_series.py` — the git-history squash helper (walks
  `<upstream>..HEAD`, reconstructs a one-commit-per-task history). Everything else under `tools/` is a
  shell script; everything else matching `*.py` lives in a game checkout (`n64/OcarinaOfTime/Shipwright/…`,
  `n64/libultraship/…`) and belongs to upstream, not the maintainer — do NOT touch it.
- **No baked gate today.** Unlike impo (whose Dockerfile runs `ty check tools/`), imps has no Python CI
  gate. Verify by running `ruff check tools/squash_series.py` and `ty check tools/squash_series.py`
  locally (both are in the sandbox image).

## Plan

1. Annotate `tools/squash_series.py`: module globals, every function's params + return type, and local
   variables (`x: T = …`), matching the trench tools' density. Keep any externally-dictated names as-is.
2. `ruff check tools/squash_series.py` clean; `ty check tools/squash_series.py` clean.
3. Confirm no behavior change — the script's output/logic is untouched by annotations (a dry-run or its
   `--help` still works).

## Related
- Standard: `~/.claude/reference/python-coding-standard.md`.
- Exemplar density: impo `trench/elementary-differential-equations/tools/*.py`.
- Sibling: `impo/tasks/annotate-tooling-python-types.md` (impo's `convert.py`, `build_nav.py`,
  `preprocess.py`, `fetch_exercises.py`, tests).
