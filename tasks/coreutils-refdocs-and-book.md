# uutils/coreutils — reference-doc set + doc-region teaching book (imps)

**Status:** proposed — needs go-ahead. Scoped autonomously 2026-09-19 (William Emerison Six
<billsix@gmail.com> away; asked me to make the task + research). One of FOUR sibling documentation-only
initiatives — see [ripgrep](ripgrep-refdocs-and-book.md) for the shared recipe + family decision,
plus [dash](dash-refdocs-and-book.md), [Fossify](fossify-refdocs-and-book.md).
**Priority:** 7
**Difficulty:** 8 (breadth: ~107 utilities — the challenge is documenting PATTERNS + `uucore`, not 107 programs)

## BLUF

Bring **uutils/coreutils** (a from-scratch Rust reimplementation of GNU coreutils) into imps as a
**documentation-only** carrier and produce, in the mario64 mould, a `file:line`-anchored **reference
set** and a **Sphinx teaching book** ("*How Unix Utilities Are Built (in Rust)*") whose snippets come
from the real source via **doc-region markers**. The book must be **architecture-forward, NOT
one-chapter-per-utility** — with ~107 utility crates the teaching value is the *shared machinery*
(multicall dispatch + the `uucore` library + "the anatomy of one utility"), not 107 near-identical
programs. No code is patched; the only stream is the comment-only `book/` markers. "Done" = carrier +
reference set (grouped by utility family) + a book building HTML/PDF/EPUB with working `literalinclude`s.
Split into step-tasks once approved.

## Context (cold-start)

**Reuse the mario64 machinery** (doc-region markers, the L0–L3 Levels of Detail system, the house-style
`_TEMPLATE.md`, the `n64/SuperMario64/book/` Sphinx+container template, the umbrella/step-task shape) —
see [ripgrep-refdocs-and-book.md](ripgrep-refdocs-and-book.md) "Reuse the mario64 machinery" for the full
pointer list; it is domain-agnostic. This is a **documentation-only** carrier (one comment-only `book/`
patch stream, no ported code), living under the **`unixutils/`** family (shared with ripgrep + dash —
DECIDED 2026-09-19; categorized by kind like `n64/`, recorded in the imps root `CLAUDE.md`). The Rust
comment-only gate caveat (rustc has no gcc `-fpreprocessed`) applies here too.

### coreutils profile (researched 2026-09-19)

- **Repo:** github.com/uutils/coreutils. **License:** MIT (contrast GNU coreutils' GPL-3.0+). **Language:**
  Rust; builds with **Cargo AND GNU Make** (Make also builds completions/manpages).
- **Shape — large by breadth:** ~**107 utility crates** under `src/uu/<name>/` (e.g. `src/uu/ls/`,
  `src/uu/cp/`), each a small library exposing a `uumain`-style entry. Individually trivial; the bulk is
  the aggregate + the GNU-compatibility test suite.
- **`uucore`** — the shared library every utility builds on: clap-based arg-parsing helpers, error types,
  formatting, fs/backup utilities, POSIX quirks. **This is the documentation centre of gravity.**
- **Multicall binary** — the default build is one BusyBox-style `coreutils` binary that dispatches by
  `argv[0]`/first arg; per-utility binaries can also be built.
- **Feature flags** gate platform sets (`--features unix|windows|feat_selinux|feat_wasm|openssl`, …).
- **GNU parity** — they run GNU's own test suite and treat divergence as bugs (README: "all programs
  implemented"; option-level gaps remain).

## Plan (phases → step-tasks once approved)

**Phase A — docs-only carrier.** `unixutils/coreutils/`: `fetch.sh` (pin `PIN_SHA` to a release tag),
`apply.sh` (only the `book/` stream), `patches/book/.keep`, `.gitignore`, tier-3 CLAUDE.md. (Shares the
tier-2 `unixutils/CLAUDE.md` created by whichever of the four initiatives lands first.)

**Phase B — the reference set** (`tasks/reference/coreutils/`), scaffolded from mario64's `README.md`
(L0 map) + `_TEMPLATE.md`. **Architecture-forward, grouped — NOT 107 docs:**
1. Workspace & **multicall dispatch** model (how one binary becomes many utilities).
2. **`uucore` tour** — the shared services (args, errors, formatting, fs/backup, POSIX quirks); likely
   several L2 docs, one per major `uucore` submodule.
3. **Anatomy of a utility** — a worked example (`ls` and/or `cp`) from `uumain` to output, the pattern
   every utility follows.
4. Utilities grouped by FAMILY (one doc per family, exemplars not exhaustive): file ops (cp/mv/ln/…),
   text (cat/head/sort/…), hashing (md5sum/sha*/…), system-info (uname/nproc/…).
5. The **GNU-compatibility test harness** — how divergence from GNU is tracked/tested.
6. Cross-platform strategy — the `cfg`/feature-flag gating.
7. Build — Cargo vs the Make targets (completions/manpages).

**Phase C — the doc-region book** (`unixutils/coreutils/book/`, "*How Unix Utilities Are Built (in Rust)*").
`cp -r` the mario64 `book/` template; `highlight_language="rust"`; `index.rst` chapters mirroring Phase B
(dispatch → uucore → anatomy-of-a-utility → a few utility-family case studies → GNU parity →
cross-platform). Add the `book/` doc-region marker stream (Rust `//`) for each chapter's snippets. Build
HTML/PDF/EPUB. Book umbrella + children cloned from `tasks/mario64-sphinx-book.md`.

## Open questions

1. **Family name — DECIDED 2026-09-19:** `unixutils/` (shared with ripgrep + dash). Settled.
2. **Utility coverage in the book.** Recommend depth on `uucore` + 3–4 exemplar utilities (`ls`, `cp`,
   `sort`, a hash), NOT a chapter per utility. Confirm which exemplars.
3. **Rust comment-only gate** — as in the ripgrep task (a `cargo build` before/after diff proving the
   `book/` markers change nothing compiled).
4. **Pin policy** — a release tag for stable anchors; note the ~107-crate tree means a lot of `file:line`
   anchors to keep fresh, so pin conservatively and re-verify on any bump.

## Related

- Sibling initiatives + shared recipe: [ripgrep](ripgrep-refdocs-and-book.md),
  [dash](dash-refdocs-and-book.md), [Fossify](fossify-refdocs-and-book.md).
- Templates: `tasks/reference/mario64/{README.md,_TEMPLATE.md}`, `tasks/mario64-sphinx-book.md`,
  `n64/SuperMario64/book/`, `tools/check_comment_only_streams.sh`.
