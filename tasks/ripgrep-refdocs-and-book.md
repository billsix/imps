# ripgrep — reference-doc set + doc-region teaching book (imps)

**Status:** in progress — go-ahead 2026-09-20 (William Emerison Six <billsix@gmail.com>). **Phase A**
(the `unixutils/ripgrep/` docs-only carrier — fetch/apply/Makefile/Dockerfile) + a first pass of
`patches/docs/` doc comments is DONE this session: pinned tag 14.1.1
(`4649aa97…`, the annotated tag's peeled commit), 3 doc-comment patches on `grep-searcher` internals
(`line_buffer.rs`, `searcher/core.rs`, `searcher/glue.rs` — the public library APIs already carry
`#![deny(missing_docs)]`, so the gap is internal engine code), proven comment-only + `cargo build` green
in-container. Details/gotchas in `unixutils/ripgrep/CLAUDE.md` (incl. the crates.io-fetch-at-build vs
offline-vendor decision). **Phase B** (the `tasks/reference/ripgrep/` set) and **Phase C** (the Sphinx
book) are **DEFERRED** until the follow-ups land (maintainer's call 2026-09-20):
[ripgrep-cargo-vendor-offline.md](ripgrep-cargo-vendor-offline.md) and
[generalize-comment-only-gate.md](generalize-comment-only-gate.md). Scoped
autonomously 2026-09-19. One of FOUR sibling "documentation-only" initiatives — see
[dash](dash-refdocs-and-book.md), [coreutils](coreutils-refdocs-and-book.md),
[Fossify](fossify-refdocs-and-book.md).
**Priority:** 7 (proposed; large initiative, not do-first)
**Difficulty:** 7 (the codebase is the *easiest* of the four to document; the effort is breadth of prose)

## BLUF

Bring **ripgrep** (BurntSushi's fast recursive grep, Rust) into imps as a **documentation-only** carrier
and produce, in the mario64 mould, (1) a `file:line`-anchored **reference-doc set** and (2) a **Sphinx
teaching book** ("*How a Fast Search Tool Is Built*") whose code snippets are pulled from the real
source by **doc-region markers**. Unlike the N64 game ports, there is **no code to patch** — the only
patch stream is the comment-only `book/` doc-region markers, so the carrier exists purely to pin the
upstream, carry those markers, and host the book. "Done" (for this umbrella) = the carrier folder builds
nothing but the docs, the reference set covers ripgrep's crates, and the book builds HTML/PDF/EPUB with
working `literalinclude`s. This is a big initiative; it should be split into step-tasks (below) once
approved.

## Context (cold-start)

### Reuse the mario64 machinery — do NOT re-derive it

imps already has a complete, proven "reference set + doc-region book" apparatus, built for Super Mario 64
("*How a Production Game Is Built*"). **Reuse it wholesale** — the methodology is domain-agnostic:

- **Doc-region mechanism** — named comment markers `// doc-region-begin <name>` / `// doc-region-end
  <name>` added to the upstream source as a **comment-only `book/` patch stream**, so the Sphinx book
  `literalinclude`s exact spans BY NAME (drift-proof), never line numbers or pasted code. Exemplar:
  `n64/SuperMario64/book/docs/rotation.rst` + the marker patch in `n64/SuperMario64/patches/book/`.
- **Comment-only gate** — `tools/check_comment_only_streams.sh` auto-discovers each project's `book/`
  stream and proves (via gcc `-fpreprocessed` for C) it changes nothing the compiler sees. **For Rust it
  needs a Rust-aware equivalent** (see open question 3) — `rustc` has no `-fpreprocessed`; a
  `cargo build` before/after diff, or a comment-stripping check, is the analogue.
- **Levels of Detail (L0–L3)** and the **house style** — `tasks/reference/mario64/README.md` (the L0 map:
  provenance banner + LoD explainer + capsule table) and `tasks/reference/mario64/_TEMPLATE.md` (per-doc
  template: provenance banner, every claim `file:line`-anchored + verified, state what's absent, a
  "How this relates to the course" section, and a "Candidate doc-region spans" trailer). Copy both.
- **The book container template** — the entire `n64/SuperMario64/book/` dir (Sphinx `conf.py` with furo +
  graphviz + myst + lualatex; `Dockerfile`; `Makefile` that mounts the PARENT project dir so
  `literalinclude` reaches `../<Checkout>/`; `entrypoint/build.sh` → HTML/EPUB/PDF). `cp -r` it.
- **The umbrella + step-task shape** — the archived
  `tasks/archive/mario64/2026/09/06/mario64-graphics-refdocs.md` (reference-set umbrella + 9 step-tasks)
  and the live `tasks/mario64-sphinx-book.md` (book umbrella). Clone their section structure.

### The shared "documentation-only" difference from the N64 family

The N64 projects PORT games (real `cheats`/`personal`/`upstream-candidate` code streams) AND document
one of them. These four new codebases are **documented, not ported** — the carrier's ONLY patch stream
is the comment-only `book/` markers. That means: a simpler one-lane patch model (no `patches-<engine>/`
second lane unless a codebase vendors a submodule), and the tier-2 family doc should state "documentation
only." **Family — DECIDED 2026-09-19:** these docs-only carriers are categorized by KIND, exactly like
`n64/` — **`unixutils/`** for the command-line tools (ripgrep, coreutils, dash) and **`android/`** for
the Fossify apps. So this project lands at `unixutils/ripgrep/`, with a tier-2 `unixutils/CLAUDE.md`
(the docs-only carrier contract, shared with coreutils + dash). Recorded in the imps root `CLAUDE.md`
"Families" section.

### ripgrep profile (researched 2026-09-19)

- **Repo:** github.com/BurntSushi/ripgrep. **License:** MIT OR Unlicense (permissive). **Language:** Rust,
  Cargo workspace. Clean crate seams — the easiest of the four to document; published rustdoc, stable API,
  no generated code, minimal macros.
- **Workspace crates (under `crates/`):** `core` (the `rg` binary: CLI/args/glue), `grep` (facade
  re-exporting the pieces), `grep-matcher` (the `Matcher` trait — the abstraction every engine
  implements, the *spine* of the design), `grep-regex` (Matcher via Rust's `regex`), `grep-pcre2` +
  `pcre2` (optional PCRE2 backend), `grep-searcher` (the engine: line/multiline iteration, mmap vs
  buffered, context), `grep-printer` (standard/JSON/summary output, color), `grep-cli` (CLI helpers),
  `globset` (globs → fast matcher), `ignore` (gitignore/.ignore traversal + parallel walker).
- **Search flow (the book's narrative spine):** `core` parses args → builds a `Matcher`
  (`grep-regex`/`grep-pcre2`) → `ignore` walks the tree applying gitignore rules (which use `globset`) →
  `grep-searcher` reads each file and finds matches via the `Matcher` → `grep-printer` formats + streams
  to stdout.

## Plan (phases → become step-tasks once approved)

**Phase A — land the docs-only carrier.** Create `unixutils/ripgrep/` (copy an N64 folder's script shape,
stripped to docs-only): `fetch.sh` (clone ripgrep, pin `PIN_SHA` to a recent tag/commit), `apply.sh`
(apply only the `book/` stream, guarded at the pin), `patches/book/.keep`, `.gitignore`, tier-3
`unixutils/ripgrep/CLAUDE.md`; plus the tier-2 `unixutils/CLAUDE.md` (the docs-only family contract). No
`build.sh`/`run.sh` needed (nothing is built but the book). Record the pin + provenance.

**Phase B — the reference set** (`tasks/reference/ripgrep/`). Scaffold `README.md` (L0 map) + copy
`_TEMPLATE.md`. One L2 doc per crate/subsystem, deepest-first then compress upward to L0/L1:
1. CLI & argument model (`core`) — flags → a search configuration.
2. **The `Matcher` trait** (`grep-matcher`) — the central abstraction (write this first; it's the spine).
3. Regex vs PCRE2 backends (`grep-regex`, `grep-pcre2`/`pcre2`).
4. The searcher (`grep-searcher`) — mmap vs buffered heuristics, line/multiline iteration, context.
5. The ignore engine (`ignore` + `globset`) — gitignore precedence rules (the subtle chapter), parallel
   directory walk.
6. The printer (`grep-printer`) — standard/JSON/summary formats, colorization.
7. Parallelism model — the work-stealing walker + per-file search.
Each doc ends with its "How this relates to the course" (compare to the maintainer's own systems/Rust
interests) and a "Candidate doc-region spans" list feeding Phase C.

**Phase C — the doc-region book** (`unixutils/ripgrep/book/`, "*How a Fast Search Tool Is Built*"). `cp -r`
the mario64 `book/` template; retitle `conf.py` (`highlight_language="rust"`); write `index.rst` toctree
(≈ one chapter per Phase-B topic, following the search flow). Add the `book/` doc-region stream: markers
into the Rust source (`// doc-region-begin <name>`) per each chapter's `literalinclude` needs. Build
HTML/PDF/EPUB in the container. Stand up a book umbrella + chapter-outline/prose-review children (clone
`tasks/mario64-sphinx-book.md`).

## Open questions

1. **Family name — DECIDED 2026-09-19:** `unixutils/` (shared with coreutils + dash); Fossify goes under
   `android/`. Categorized by kind, like `n64/`. No longer open — see the imps root `CLAUDE.md` Families
   section.
2. **Book scope.** All seven crates, or a focused core (matcher → searcher → ignore → printer) with the
   CLI/printer as lighter chapters? Recommend cover all, weighting the `Matcher` spine + ignore rules.
3. **Rust comment-only gate.** `tools/check_comment_only_streams.sh` uses gcc `-fpreprocessed` (C-only).
   For Rust, add a sibling check: a `cargo build` (or `cargo expand`/token-stream) diff proving the
   `book/` marker stream changes no compiled output. (Applies to coreutils too.)
4. **Pin policy.** Pin to a released tag (stable `file:line` anchors) vs a recent `main` commit. Recommend
   a tag.

## Related

- Sibling docs-only initiatives (same recipe): [coreutils](coreutils-refdocs-and-book.md),
  [dash](dash-refdocs-and-book.md), [Fossify](fossify-refdocs-and-book.md).
- The template machinery: `tasks/reference/mario64/{README.md,_TEMPLATE.md}`,
  `tasks/mario64-sphinx-book.md`, `n64/SuperMario64/book/`, `tools/check_comment_only_streams.sh`,
  and the archived reference-set umbrella `tasks/archive/mario64/2026/09/06/mario64-graphics-refdocs.md`.
