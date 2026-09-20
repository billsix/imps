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
  **build toolchain**, so the tool can be compiled by `make build`. Targets: `fetch`, `apply`, `image`,
  `build` (compile the checkout), and `check-comment-only` (the family gate — calls the shared
  `../../tools/check_comment_only_streams.sh <project>`; see below).
- `patches/LANG` (one word: `c`/`rust`/`kotlin` — the shared gate reads it to pick the prover; see
  below), `patches/docs/.keep`, `patches/book/.keep`, `patches/ORDER`, `.gitignore` (ignore the checkout +
  build dirs), tier-3 `CLAUDE.md` (upstream URL, pin, the doc-stream contents one line each, build
  gotchas), `README.md` (commands-forward: fetch → apply → build → check-comment-only).

## The comment-only gate — one shared, family-agnostic tool

A doc-comment / doc-region stream must be provably comment-only. That gate is **shared**, at the imps
repo root — there is no per-project wrapper any more (the earlier "add a local wrapper" stopgap is gone):

- **`../../tools/check_comment_only_streams.sh [project ...]`** discovers every project across all
  families (n64/, unixutils/, android/), reads each project's **`patches/LANG`** declaration, and
  **dispatches** to the right prover per language. It builds a BEFORE/AFTER scratch-branch pair per
  comment-only stream (pin + the streams that apply before it, then that stream on top) and restores the
  checkout afterward. Run it host-side (git + gcc/python3; no build, no container — the shared `tools/`
  live above a carrier and are not mounted into its image).
- **Language declaration is explicit, per project** — a one-word `patches/LANG` file (`c`, `rust`, or
  `kotlin`), **not** inferred from file extensions. An undeclared project is treated as C (that is how
  the n64 ports keep working unchanged).
- **Two provers (dispatch, not replace):**
  - `c` → **`../../tools/prove_comment_only.sh`** (gcc `-fpreprocessed` strips comments, then the token
    streams are compared). **dash** uses this.
  - `rust`/`kotlin` → **`../../tools/prove_comment_only_strip.py --lang <lang>`**, a language-aware
    comment stripper: for each touched file it strips comments (and collapses whitespace) from both refs
    and byte-compares — the same strip-then-compare argument, since those languages have no C
    preprocessor. **ripgrep** uses `--lang rust`. (`prove_comment_only_strip.py --self-test` runs its
    tricky-case suite: nested block comments, raw strings, char/lifetime, string templates.)

Each project's `make check-comment-only` calls the shared tool with its own project name; its
`./check_comment_only.sh` (or `./check-comment-only.sh`) is a thin shim to the same entry point.

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
