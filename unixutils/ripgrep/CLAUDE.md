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
  `make build` compiles the checkout OFFLINE; `make shell` / `shell-exec` open
  the builder image. All `run` lines thread `PODMAN_RUN_FLAGS` (nested-podman
  auto).

## Offline-self-contained image (baked Cargo cache)

The image is **offline-self-contained** per the maintainer's "exported image
runs offline in 5 years" convention (the Cargo analogue of modelviewprojection's
baked `/venv` and the Fossify sibling's warmed Gradle cache — see
`../../tasks/ripgrep-cargo-vendor-offline.md`):

- **Baked at image-build:** `entrypoint/warm-cargo-cache.sh` (run by the
  Dockerfile) clones ripgrep at the pin and `cargo fetch --locked`s ripgrep's
  whole `Cargo.lock` dependency graph into a **fixed, committed** `CARGO_HOME`
  layer, `ENV CARGO_HOME=/opt/cargo-cache`. The throwaway clone is created and
  removed inside one `RUN` layer, so only `/opt/cargo-cache` persists. `cargo
  fetch` pulls every crate in the lockfile (all targets/features) regardless of
  feature flags, covering the default build.
- **Built at runtime:** `make build` runs `cargo build --offline` against the
  bind-mounted checkout, resolving crates **only** from the baked cache — a
  cache miss fails loudly instead of reaching crates.io. Only ripgrep's own
  source is (re)compiled from the mount; the third-party crates come from the
  layer. Verified with the offline export test (export/import roundtrip →
  `cargo build --offline` under `--network=none`).
- **Pin-bump re-warm (REQUIRED):** the pin lives twice — `PIN_SHA` in `fetch.sh`
  and the `RIPGREP_PIN` ARG default in the `Dockerfile` (documented to match).
  When the pin moves, **update both together and rebuild `make image`** so the
  Cargo cache is re-warmed for the new lockfile; the ARG keeps the two honest
  (or pass `--build-arg RIPGREP_PIN=<sha>` for a one-off). A stale cache would
  make the offline build miss newly-pinned crates.

This carrier only compiles ripgrep to prove the doc patches are comment-only —
it ships nothing.

## Patch streams (comment-only, gated)

Both streams change **nothing the compiler sees** — proved by the **shared**
family-agnostic gate `../../tools/check_comment_only_streams.sh ripgrep` (wrapped
by `make check-comment-only` and the thin `./check-comment-only.sh` shim). It
reads `patches/LANG` (= `rust`) and, for every file the stream touches, compares
the comment-stripped pin version against the applied version via
`../../tools/prove_comment_only_strip.py --lang rust`. (The former local
`check_comment_only.py` was promoted into `tools/`; the gate no longer runs
`cargo build` — `make build` still compiles the checkout separately.)

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
