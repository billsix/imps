# Generalize the comment-only gate across families and languages

**Status:** DONE — 2026-09-20. The gate is now one shared, family-agnostic, language-dispatched tool
(`tools/check_comment_only_streams.sh` discovers all families + dispatches by `patches/LANG`; the new
`tools/prove_comment_only_strip.py --lang rust|kotlin` handles the non-C languages; the three per-carrier
scripts are thin shims and ripgrep's `check_comment_only.py` was promoted into `tools/`). Verified: stripper
self-tests (rust + kotlin, with negatives) pass, and the unified gate proves all 5 docs streams comment-only
across dash (C→gcc), ripgrep (rust→strip), and Fossify's 3 Kotlin repos (n64 SuperMario64's book streams
also still pass, undeclared→C). Awaiting go-ahead was given by the maintainer 2026-09-20 (implement 1–3,
starting with 3). Archived after the maintainer commits.

## Outcome (2026-09-20)
Implemented per the locked decisions below (subagent + maintainer verification). `patches/LANG` (one word:
`c`/`rust`/`kotlin`) is the explicit per-project declaration; an undeclared project defaults to C (keeps the
n64 ports working untouched). Dispatch: `c` → `tools/prove_comment_only.sh` (gcc `-fpreprocessed`,
unchanged); `rust`/`kotlin` → `tools/prove_comment_only_strip.py` (strip-comments-then-byte-compare, stronger
than a hunk-diff). The gate now runs **host-side** for the carriers (the shared `tools/` sit above a carrier
and aren't mounted into its image), and no longer runs `cargo build` as part of the proof (`make build` still
compiles). Tier-3 carrier CLAUDE.md/README prose was reconciled to the shared gate. Files: created
`tools/prove_comment_only_strip.py` + three `patches/LANG`; edited `tools/check_comment_only_streams.sh`, the
three carriers' shims + Makefile targets + tier-3 docs, and `unixutils/CLAUDE.md` + `android/CLAUDE.md`;
removed `unixutils/ripgrep/check_comment_only.py` (promoted).

## Original scope (kept for the record)
**Priority:** 5
**Difficulty:** 5

## BLUF

The "a `docs`/`book` patch stream is comment-only" gate is currently **fragmented**: one shared C engine,
one shared wrapper hardcoded to `n64/`, and **three new per-carrier re-implementations** (Rust, C, Kotlin)
the Phase-A agents had to write because the shared wrapper couldn't see their family. Unify it into a
**family-agnostic, language-dispatched** gate under `tools/`, so a new docs-only carrier gets the check
for free. "Done" = one `tools/` entry point discovers every project across all families
(`n64/`, `unixutils/`, `android/`, future) and proves each project's comment-only streams, dispatching to
the right per-language proof; the three per-carrier scripts are removed (or become thin shims).

## Current state (surveyed 2026-09-20)

- **`tools/prove_comment_only.sh`** — the generic **C** proof engine: two trees differ only in comments iff
  (line counts equal) AND (each differing file is byte-identical after `gcc -fpreprocessed -dD -E -P`
  strips comments). Sound, language = C only (relies on the C preprocessor). Reusable as-is for C.
- **`tools/check_comment_only_streams.sh`** — the **wrapper**: builds scratch branches per stream and calls
  `prove_comment_only.sh`. **Hardcoded to `n64/`** (`find n64 -maxdepth 1`, `proj=$ROOT/n64/$name`), so it
  cannot see `unixutils/` or `android/`. This is the thing to generalize.
- **Per-carrier re-implementations (the duplication to fold in):**
  - `unixutils/ripgrep/check_comment_only.py` — a **Rust**-aware comment stripper (handles strings, raw
    strings `r#""#`, char/byte literals, lifetimes, nested block comments), strips + byte-compares.
  - `unixutils/dash/check_comment_only.sh` — **C**; wraps `tools/prove_comment_only.sh` directly (only
    exists because the n64 wrapper is hardcoded).
  - `android/fossify/check-comment-only.sh` — **Kotlin**; a source-level hunk proof (every changed hunk
    line is a comment/blank), robust to comment-induced line shifts.

## The design (proposed)

Two layers, mirroring what already exists:

1. **A family-agnostic discovery wrapper** (`tools/check_comment_only_streams.sh`, generalized): scan
   **every family folder**, not just `n64/` — discover projects by "has a `patches/` dir with a `docs/` or
   `book/` stream" (or read a small registry), independent of which family folder they sit in. Keep the
   scratch-branch-per-stream + pin-guard machinery.
2. **A per-language proof dispatch.** Detect the stream's language (by touched file extensions, or a
   per-project declaration) and call the right prover:
   - **C** → `tools/prove_comment_only.sh` (gcc `-fpreprocessed`) — unchanged.
   - **Rust / Kotlin / other C-comment-syntax languages** → a **shared comment-stripper** generalized from
     `ripgrep/check_comment_only.py`. Rust and Kotlin share `//` + `/* */` (Kotlin allows nested block
     comments, Rust too), string/char rules differ slightly — parameterize by language. The Kotlin
     source-hunk proof and the Rust strip-and-compare are two expressions of the same idea; pick one
     (the strip-and-compare is stronger — it proves token identity, not just "the diff looks like
     comments") and make it language-aware.

Then delete the three per-carrier scripts (or leave one-line shims that call the shared tool), and point
each carrier's `check-comment-only` Makefile target at `tools/`.

## Plan
1. Generalize `check_comment_only_streams.sh` discovery to all families (glob `*/*/patches` or a registry);
   keep its stream/scratch-branch logic.
2. Promote a **language-parameterized comment stripper** into `tools/` (from `ripgrep/check_comment_only.py`);
   give it C-family-comment language profiles (start: rust, kotlin; C stays on the gcc engine).
3. Wire the wrapper to dispatch C→gcc-engine, rust/kotlin→stripper.
4. Re-verify against all four existing exemplars (n64 book stream, dash docs, ripgrep docs, fossify docs) —
   each must still prove comment-only.
5. Replace the three per-carrier scripts with shims / removal; repoint the carriers' `check-comment-only`
   targets; update `unixutils/CLAUDE.md` + `android/CLAUDE.md` (they currently say "add a local wrapper").

## Decisions (William Emerison Six <billsix@gmail.com>, 2026-09-20)
1. **Explicit `lang:` declaration per project** (not extension-inference) — e.g. a one-liner in the tier-3
   CLAUDE.md or `patches/ORDER`. No surprises on mixed-extension repos.
2. **Two provers (dispatch, not replace):** keep the C `gcc -fpreprocessed` engine (it argues via a real
   compiler) for C; use the language-parameterized stripper for Rust/Kotlin/other C-comment-syntax
   languages.
3. **On-demand** — stay a manually-run gate like `tools/check_comment_only_streams.sh` is today; do not
   auto-wire it into a committed always-run check (that's a separate opt-in).

## Related
- The pieces to unify: `tools/prove_comment_only.sh`, `tools/check_comment_only_streams.sh`,
  `unixutils/ripgrep/check_comment_only.py`, `unixutils/dash/check_comment_only.sh`,
  `android/fossify/check-comment-only.sh`.
- Family contracts to update: `unixutils/CLAUDE.md`, `android/CLAUDE.md` (both currently document a local
  wrapper as a stopgap).
- The carriers: [ripgrep](ripgrep-refdocs-and-book.md), [dash](dash-refdocs-and-book.md),
  [Fossify](fossify-refdocs-and-book.md).
