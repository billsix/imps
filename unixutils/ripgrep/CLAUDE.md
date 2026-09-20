# ripgrep — BurntSushi's fast recursive grep, documented (imps, unixutils)

Managed by imps as a **documentation-only** carrier: `checkout/` here is a
pristine clone of <https://github.com/BurntSushi/ripgrep>, pinned by `fetch.sh`,
with comment-only patch streams applied by `apply.sh`. Not a fork — ripgrep is
**documented, not changed**. Read the family contract
[`../CLAUDE.md`](../CLAUDE.md) (docs-only streams, the comment-only gate) and the
repo-root `../../CLAUDE.md` (the carrier model) first.

## Pin

- Upstream: <https://github.com/BurntSushi/ripgrep>, license MIT OR Unlicense.
- `PIN_SHA` (in `fetch.sh`) = `4649aa9700619f94cf9c66876e9549d83420e16c`, the
  commit tag **14.1.1** points at (released 2024-09-08), the latest stable
  release. Pinned to a released tag's commit so reference-doc `file:line`
  anchors and (later) book doc-region spans stay valid.
  - `14.1.1` is an **annotated** tag: `PIN_SHA` is the commit it peels to
    (`git rev-parse 14.1.1^{}`), NOT the tag-object SHA. `git rev-parse HEAD`
    equals `PIN_SHA`, so `apply.sh`'s pin guard matches. Do not "correct" it to
    the tag-object SHA `0e8390a…` — that would break the guard.

## Scripts & build

- `./fetch.sh` — clone if missing, detach at `PIN_SHA`, set `commit.gpgsign
  false` in the checkout (sandbox signing would abort `git am`).
- `./apply.sh` — `git am --3way` the streams in `patches/ORDER` (`docs` then
  `book`); refuses unless the checkout is exactly at the pin.
- `make help` — lists targets. `make check-comment-only` is the family gate;
  `make build` compiles the checkout; `make shell` / `shell-exec` open the
  builder image. All `run` lines thread `PODMAN_RUN_FLAGS` (nested-podman auto).
- **Build gotcha:** `cargo build` in the container fetches crates from
  crates.io at run time (the gitignored checkout does not exist at image-build,
  so deps cannot be baked). The image itself needs no network; the *build* does.
  The host build reuses `~/.cargo`. This carrier only compiles ripgrep to prove
  the doc patches are comment-only — it ships nothing.

## Patch streams (comment-only, gated)

Both streams change **nothing the compiler sees** — proved by
`./check-comment-only.sh` (`make check-comment-only`), the Rust analogue of the
C `-fpreprocessed` gate: for every file the stream touches it compares the
comment-stripped pin version against the applied version, then runs `cargo
build`. Helper: `check_comment_only.py` (a Rust-aware comment stripper).

- `patches/docs/` — explanatory Rust doc comments on interesting internals,
  shaped to be upstreamable. First pass (3 commits, all in **grep-searcher**,
  whose public API is already fully documented but whose engine internals were
  not):
  - `0001` — `line_buffer.rs`: module overview of the rolling line buffer.
  - `0002` — `searcher/core.rs`: module + `Core` struct/fields + method docs for
    the line-oriented search engine (fast-vs-slow path, context windows, rolls,
    lazy line numbering, binary detection).
  - `0003` — `searcher/glue.rs`: module overview + docs on the three search
    strategies (`ReadByLine`, `SliceByLine`, `MultiLine`).
- `patches/book/` — Sphinx `doc-region` markers for the teaching book (empty
  `.keep` until the book — Phase C of `../../tasks/ripgrep-refdocs-and-book.md`
  — is built).

## Not yet done (see `../../tasks/ripgrep-refdocs-and-book.md`)

The reference set (`../../tasks/reference/ripgrep/`) and the Sphinx book
(`book/`, "*How a Fast Search Tool Is Built*") are later phases. The docs stream
is a **first pass** over grep-searcher; the matcher trait / ignore engine /
printer are candidates for later passes (their public APIs are already
exhaustively documented via `#![deny(missing_docs)]`, so future passes should
target undocumented internals as this one did).
