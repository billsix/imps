# unixutils — command-line Unix tools, documented for teaching (imps docs-only family)

The **unixutils** family carries pinned checkouts of well-written command-line Unix tools **to document
them**, not to port them. Read the repo-root [`../CLAUDE.md`](../CLAUDE.md) first (the imps carrier idea,
the four-tier doc structure, the per-project contract, and the patch philosophy); this tier-2 doc holds
the *documentation-only* carrier contract shared by every unixutils project and the per-project index. It
auto-loads for any session working under `unixutils/`.

## How a docs-only family differs from `n64/`

The `n64/` family **ports games** — it carries real code-change streams (`cheats/`, `personal/`,
`upstream-candidates/`) and *also* documents one game. A unixutils project **documents a tool it does not
change**. So the only patch streams a project here carries are **comment-only**:

- **`patches/docs/`** — explanatory **doc comments** added to interesting parts of the upstream source
  (Rust `///`, C `/* … */`). This is the "start adding docstrings to the codebase" deliverable
  (William Emerison Six <billsix@gmail.com>, 2026-09-20): human-facing documentation of *what the
  interesting code does and why*, shaped so it could plausibly be offered upstream (a pure doc
  contribution). One commit per coherent area; keep messages reviewer-facing.
- **`patches/book/`** — `// doc-region-begin <name>` / `-end` markers for the Sphinx teaching book's
  `literalinclude`s (the mario64 mechanism). Added when the book (Phase C of each project's task) is
  built; may be empty (`.keep`) until then.

Both streams are **comment-only** and must change nothing the compiler/interpreter sees — this is the
family's one hard invariant (see the gate below). `patches/ORDER` lists the stream order (`docs` then
`book`). There is no `cheats`/`personal` lane and no `run.sh` (nothing is *run*; the tool is built only to
prove the doc patches are comment-only, and to host the book).

## Per-project folder contract (on top of the generic one in `../CLAUDE.md`)

`unixutils/<tool>/`:
- `fetch.sh` — clone the upstream into a gitignored checkout and detach at `PIN_SHA` (a **released tag's**
  commit, for stable `file:line` anchors; SHA commented with its date + tag). Sets `commit.gpgsign false`
  in the checkout (sandbox signing fails and would abort `git am`). Idempotent. Copy an `n64/` `fetch.sh`
  and strip it to this.
- `apply.sh` — `git am --3way` the `patches/docs/` (then `patches/book/`) streams onto the checkout,
  guarded to run only when HEAD is exactly at the pin (read the pin out of `fetch.sh`). Copy an `n64/`
  `apply.sh` shape.
- `Makefile` + `Dockerfile` — a Fedora-44 image (the maintainer's container template: `PODMAN_RUN_FLAGS`
  threaded into every `run`, a `shell`/`shell-exec` pair, `##`-documented `help`) carrying the tool's
  **build toolchain**, so the tool can be compiled to **prove the doc patches are comment-only**. Targets:
  `fetch`, `apply`, `image`, `build` (compile the checkout), and `check-comment-only` (build the pinned
  source, apply the docs stream, rebuild, and prove the compiled output is unchanged — the family gate).
- `patches/docs/.keep`, `patches/book/.keep`, `patches/ORDER`, `.gitignore` (ignore the checkout + build
  dirs), tier-3 `CLAUDE.md` (upstream URL, pin, the doc-stream contents one line each, build gotchas),
  `README.md` (commands-forward: fetch → apply → build → check-comment-only).

## The comment-only gate

A doc-comment / doc-region stream must be provably comment-only. `../tools/check_comment_only_streams.sh`
does this for **C** via `gcc -fpreprocessed` (so **dash** is covered as-is). **Rust has no
`-fpreprocessed`** — a Rust project (ripgrep) needs the analogue: build at the pin, apply the stream,
rebuild, and diff the compiled artifact (or compare a comment-stripped token stream). Wire this as the
project's `check-comment-only` make target; a shared Rust helper can graduate to `../tools/` once a second
Rust project needs it.

## Books

Each project's Sphinx teaching book lives in `unixutils/<tool>/book/` (copied from the mario64
`n64/SuperMario64/book/` template) and is built HTML/PDF/EPUB in the tool's image. Reference sets live at
`../tasks/reference/<tool>/`. Full plan per project is in its task doc under `../tasks/`.

## Projects

- **`ripgrep/`** — BurntSushi's fast recursive grep (Rust, MIT OR Unlicense). github.com/BurntSushi/ripgrep.
  Reference-set + book plan: `../tasks/ripgrep-refdocs-and-book.md`. Book: "*How a Fast Search Tool Is
  Built*".
- **`dash/`** — the Debian Almquist Shell, a minimal POSIX `/bin/sh` (C, BSD-3-Clause). Upstream
  git.kernel.org (mirror github.com/tklauser/dash). Plan: `../tasks/dash-refdocs-and-book.md`. Book:
  "*How a POSIX Shell Works*". (coreutils — `../tasks/coreutils-refdocs-and-book.md` — is a planned third
  member, not yet landed.)
