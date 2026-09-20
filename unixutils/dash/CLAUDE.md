# dash — Debian Almquist Shell (minimal POSIX /bin/sh), under imps

**dash** is a small, fast, strictly-POSIX `/bin/sh` in C (BSD-3-Clause, from the
NetBSD `ash` lineage; maintained by Herbert Xu). It is Debian/Ubuntu's `/bin/sh`
because it starts fast and stays lean. imps carries it **documentation-only**
(the `unixutils/` family — read the master [`../../CLAUDE.md`](../../CLAUDE.md) and
the family tier [`../CLAUDE.md`](../CLAUDE.md) first): we do not change dash, we
document it. The only patch streams are **comment-only**.

## Upstream + pin

- **Canonical upstream:** <https://git.kernel.org/pub/scm/utils/dash/dash.git>
  (Herbert Xu). **Mirror:** <https://github.com/tklauser/dash> — `fetch.sh` tries
  kernel.org first and falls back to the mirror if the clone 403s.
- **Pin (`PIN_SHA` in `fetch.sh`):** `037bbdfd330017c368caf6242f977974123239b5` —
  release tag **v0.5.13.5** (the newest dash release as of 2026-09-20). Pinned to
  a released tag so the reference set's `file:line` anchors stay stable.
- **Build:** GNU autotools, in-tree: `./autogen.sh && ./configure && make`. The
  arith parser (`arith_yacc.c`) is hand-written and committed, so **no yacc/lex**
  is needed; libedit is optional (`--with-libedit`) and left off.

## The generated-files gotcha (read before documenting anything)

Several C sources do **not exist in the tree** — they are produced at build time
by small generator programs and vanish on `make clean`. **Never add doc comments
to a generated file; document the generator or its template instead.**

| Generated (do NOT edit) | Produced by (DO document) | From |
| --- | --- | --- |
| `nodes.c`, `nodes.h` | `mknodes.c` | `nodetypes`, `nodes.c.pat` |
| `syntax.c`, `syntax.h` | `mksyntax.c` | `token.h` |
| `init.c` | `mkinit.c` | the `.c` sources |
| `builtins.c`, `builtins.h` | `mkbuiltins` (shell) | `builtins.def.in` |
| `signames.c` | `mksignames.c` | — |
| `token.h`, `token_vars.h` | `mktokens` (shell) | — |

So the parse-tree node structs and the `union node` are generated from the
declarative `nodetypes` file — a reader looking for a hand-written `nodes.c`
should be pointed at `nodetypes` + `nodes.c.pat` instead (documented in the
`patches/docs/` mknodes commit).

## Patch streams (both comment-only — see `patches/ORDER`: docs then book)

- **`patches/docs/`** — explanatory C doc comments on the shell-pipeline spine
  (first pass, 6 commits, `git am`-clean onto the pin, proven comment-only by
  `make check-comment-only`):
  1. `memalloc.c` — the `stalloc` stack allocator and its setstackmark/popstackmark
     bulk-release memory model.
  2. `mknodes.c` — the parse-tree node **generator**: why `nodes.c`/`nodes.h` are
     generated, and the `%SIZES`/`%CALCSIZE`/`%COPY` template splices.
  3. `parser.c` — the recursive-descent grammar spine
     (`parsecmd → list → andor → pipeline → command → simplecmd`).
  4. `expand.c` — word expansion: the `CTL*` marker scheme and the four stages
     (param/command/arith substitution, IFS splitting, glob), plus `subevalvar`
     and the `pmatch` shell-pattern matcher.
  5. `eval.c` — the tree-walking evaluator and per-shape dispatch (subshell fork,
     `evalcommand`, function calls).
  6. `exec.c` — command resolution (`find_command`), the `shellexec` PATH search,
     and the ENOEXEC "run as a /bin/sh script" fallback.
- **`patches/book/`** — Sphinx `// doc-region-begin/end` markers for the future
  teaching book (Phase C of the task). Currently just `.keep`.

## Build + gate (Makefile)

- `make image` — Fedora-44 image with the C toolchain (gcc, make, autoconf,
  automake) + git/gcc for the gate. `PODMAN_RUN_FLAGS` is threaded into every
  `run` (auto `--cgroups=disabled` when nested), never into `build`.
- `make build` — compile the checkout in the container (autotools) and smoke-run
  `dash -c`. Proves the doc series still builds; also exercises the generators.
- `make check-comment-only` — the family gate. Runs `./check_comment_only.sh`,
  which builds before/after branches per stream and hands them to the repo-root
  `../../tools/prove_comment_only.sh` (gcc `-fpreprocessed` comment stripping).
  Needs git + gcc; runs on the host or in the image, needs no full build. NOTE:
  the n64 wrapper `../../tools/check_comment_only_streams.sh` is hardcoded to the
  `n64/` family, so dash uses this local wrapper around the shared proof engine.
- `make shell` / `make shell-exec CMD=... | SCRIPT=...` — interactive / batch
  shell in the build image (share one `SHELL_RUN_FLAGS` block so they can't drift).

Verified 2026-09-20: `fetch` (kernel.org) → `apply` (6/6 clean) → `build` (dash
built and ran) → `check-comment-only` (all 6 files PROVEN comment-only).

## Reference set + book (planned)

The deep reference set (`../../tasks/reference/dash/`) and the Sphinx book
*How a POSIX Shell Works* (`book/`) are Phases B–C of
[`../../tasks/dash-refdocs-and-book.md`](../../tasks/dash-refdocs-and-book.md);
not yet started. This carrier + the first doc-comment pass are Phase A.
