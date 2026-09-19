# dash (Debian Almquist Shell) — reference-doc set + doc-region teaching book (imps)

**Status:** proposed — needs go-ahead. Scoped autonomously 2026-09-19 (William Emerison Six
<billsix@gmail.com> away; asked me to make the task + research). One of FOUR sibling documentation-only
initiatives — see [ripgrep](ripgrep-refdocs-and-book.md) for the shared recipe + family decision, plus
[coreutils](coreutils-refdocs-and-book.md), [Fossify](fossify-refdocs-and-book.md).
**Priority:** 7
**Difficulty:** 8 (small LOC but dense: terse old-school C, heavy global state, `longjmp` errors, a custom
stack allocator, and build-time code generation)

## BLUF

Bring **dash** (the Debian Almquist Shell — a minimal POSIX `/bin/sh`, C) into imps as a
**documentation-only** carrier and produce, in the mario64 mould, a `file:line`-anchored **reference
set** and a **Sphinx teaching book** ("*How a POSIX Shell Works*") walking the classic shell pipeline
(lexer → parse → expand → eval → exec → jobs), with snippets pulled from the real source via
**doc-region markers**. dash is a superb teaching target precisely because it is *minimal* — the whole of
what a POSIX shell must do, and nothing bash adds. No code is patched; the only stream is the comment-only
`book/` markers — and because dash is **C**, the existing `tools/check_comment_only_streams.sh` (gcc
`-fpreprocessed`) covers it directly. "Done" = carrier + reference set + a book building HTML/PDF/EPUB.
Split into step-tasks once approved.

## Context (cold-start)

**Reuse the mario64 machinery** (doc-region markers, L0–L3 Levels of Detail, the house-style
`_TEMPLATE.md`, the `n64/SuperMario64/book/` Sphinx+container template, the umbrella/step-task shape) —
full pointer list in [ripgrep-refdocs-and-book.md](ripgrep-refdocs-and-book.md) "Reuse the mario64
machinery". Documentation-only carrier (one comment-only `book/` stream), under the **`unixutils/`**
family (shared with ripgrep + coreutils — DECIDED 2026-09-19; by kind like `n64/`, in the imps root
`CLAUDE.md`). **Advantage over the two Rust siblings:** dash is
C, so the comment-only gate works as-is (`gcc -fpreprocessed` proves the markers change nothing compiled)
— no new gate needed. Use C `//` (C99) markers to match the existing tooling's expectation.

### dash profile (researched 2026-09-19)

- **Canonical source:** `git.kernel.org/pub/scm/utils/dash/dash.git` (Herbert Xu, upstream). **Fetch
  gotcha:** kernel.org returns 403 to some fetch tools — `fetch.sh` may need a GitHub mirror
  (`github.com/tklauser/dash`) or a plain `git clone` of the kernel.org URL. **License:** BSD-3-Clause
  (from NetBSD ash). **Build:** GNU autotools (`./autogen.sh && ./configure && make`).
- **Size:** small — ~30+ `.c` files in `src/`, a few tens of thousands of LOC. Deliberately minimal
  (POSIX conformance + slimness/speed) — it's Debian/Ubuntu's `/bin/sh` because it starts fast and is lean.
- **Source layout (`src/`) — the book's chapters map 1:1 to the shell pipeline:**
  `main.c` (entry/REPL), `parser.c` (tokenizer + recursive-descent parser → command AST), `eval.c`
  (walks the AST, runs commands/pipelines/loops), `expand.c` (parameter/command-sub/arith/glob/field
  splitting — the biggest, subtlest part), `exec.c` (builtin-vs-path lookup, `execve`, hash table),
  `redir.c` (I/O redirection), `jobs.c` (job control), `var.c` (variables/environment), `input.c`/
  `output.c` (buffered I/O), `memalloc.c` (the `stalloc` stack allocator — dash's memory model), builtins
  (`cd.c`, `trap.c`, `alias.c`, `miscbltin.c`, `bltin/` e.g. `test`/`printf`/`echo`), arithmetic
  (`arith_yacc.c`, `arith_yylex.c`).
- **GENERATED CODE (the key documenting gotcha):** `mkinit.c`, `mknodes.c`, `mksyntax.c` are build-time C
  programs that GENERATE C sources (`init.c`, `nodes.c`/`nodes.h`, `syntax.c`) from templates
  (`nodetypes`, token lists). The AST node structs and char-class syntax tables are **produced, not
  hand-written** — a reference doc MUST flag this so readers don't hunt for a hand-written `nodes.c`, and
  doc-region markers must go in the GENERATORS/templates or hand-written source, never the generated files
  (which are recreated each build).
- **vs. bash** (a natural book theme): dash is POSIX-only — none of bash's arrays/`[[ ]]`/process
  substitution/readline richness/associative arrays. Minimal-by-design; bash is a large interactive shell.

## Plan (phases → step-tasks once approved)

**Phase A — docs-only carrier.** `unixutils/dash/`: `fetch.sh` (clone the kernel.org repo or a mirror, pin
`PIN_SHA` to a release tag; handle the 403 gotcha), `apply.sh` (only the `book/` stream), `patches/book/
.keep`, `.gitignore`, tier-3 CLAUDE.md. (Shares the tier-2 `unixutils/CLAUDE.md`.)

**Phase B — the reference set** (`tasks/reference/dash/`), from mario64's `README.md` (L0 map) +
`_TEMPLATE.md`. One L2 doc per pipeline stage, deepest-first then compress up:
1. Input & the lexer (`input.c`, tokenizing in `parser.c`).
2. **Parser & the node AST** (`parser.c`) — *and how `mknodes` generates `nodes.c`/`nodes.h`*.
3. **Expansion** (`expand.c`) — parameter/command-sub/arith/glob/field-splitting (the hardest chapter).
4. Evaluation & the fork/exec model (`eval.c`, `exec.c`).
5. Redirection (`redir.c`).
6. Job control (`jobs.c`).
7. Variables & the `stalloc` memory model (`var.c`, `memalloc.c`).
8. Builtins (`bltin/`, `cd.c`, `trap.c`, …).
9. Arithmetic (`arith_yacc.c`, `arith_yylex.c`).
Plus an orientation doc flagging the **generated files** (mkinit/mknodes/mksyntax → init/nodes/syntax)
and a "dash vs bash: what a minimal shell needs" doc. Each ends with "How this relates to the course" and
a "Candidate doc-region spans" list.

**Phase C — the doc-region book** (`unixutils/dash/book/`, "*How a POSIX Shell Works*"). `cp -r` the mario64
`book/` template; `highlight_language="c"` (already the template default); `index.rst` chapters following
the pipeline. Add the C `book/` doc-region markers (in hand-written source + the generator templates, NOT
generated files). Build HTML/PDF/EPUB; the C comment-only gate applies unchanged. Book umbrella + children
cloned from `tasks/mario64-sphinx-book.md`.

## Open questions

1. **Family name — DECIDED 2026-09-19:** `unixutils/` (shared with ripgrep + coreutils). Settled.
2. **Generated-file markers.** Confirm the approach: put doc-region markers in the generator inputs
   (`nodetypes`, the `mk*.c` templates) and teach the generation step, rather than marking generated
   `nodes.c`/`syntax.c` (which regenerate). Recommended.
3. **autotools in the book container.** The book only needs the SOURCE for `literalinclude` (no compile),
   so the book image needs Sphinx, not autotools — but a "build dash" appendix might. Decide whether the
   carrier also ships a `build.sh` (optional; the initiative is docs-only, so probably not).
4. **Pin policy** — a dash release tag for stable anchors.

## Related

- Sibling initiatives + shared recipe: [ripgrep](ripgrep-refdocs-and-book.md),
  [coreutils](coreutils-refdocs-and-book.md), [Fossify](fossify-refdocs-and-book.md).
- Templates: `tasks/reference/mario64/{README.md,_TEMPLATE.md}`, `tasks/mario64-sphinx-book.md`,
  `n64/SuperMario64/book/`, `tools/check_comment_only_streams.sh` (works for dash's C directly).
