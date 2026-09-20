# ripgrep carrier — bake Cargo deps offline (cargo vendor / warmed CARGO_HOME)

**Status:** DONE — 2026-09-20. Go-ahead + implementation 2026-09-20. Raised 2026-09-20
(William Emerison Six <billsix@gmail.com>) as follow-up #2 to the ripgrep Phase-A carrier
([ripgrep-refdocs-and-book.md](ripgrep-refdocs-and-book.md)).

## Outcome (2026-09-20)
`CARGO_HOME=/opt/cargo-cache` (fixed, committed layer). A new `entrypoint/warm-cargo-cache.sh` (the Cargo
analogue of Fossify's `warm-gradle-cache.sh`) clones ripgrep at the pin at image-build and `cargo fetch
--locked`s the whole `Cargo.lock` graph into that layer (all targets/features, so feature flags don't
matter), discarding the clone in the same `RUN`. The pin lives twice — `PIN_SHA` (fetch.sh) + an
`ARG RIPGREP_PIN` default (Dockerfile), documented to match; re-warm on a pin bump. `make build` runs
`cargo build --offline` against the bind-mounted checkout. Image 1.06 GB. **Offline export test PASSED
(independently re-verified):** export → `rmi` → import → `rm -rf target` → `cargo build --offline` under
`--network=none` compiled every third-party crate + ripgrep's own workspace from the baked cache alone,
`Finished in ~5.8s`. Docs updated (`unixutils/ripgrep/CLAUDE.md` + `README.md`; the old "fetches at run
time" gotcha removed). Comment-only gate still green.
The Cargo sibling of the Fossify/Gradle offline task
([fossify-jdk-toolchain-and-gradle-offline.md](fossify-jdk-toolchain-and-gradle-offline.md)).
**Priority:** 5
**Difficulty:** 4 (Cargo has first-class offline vendoring; easier than the Gradle side)

## BLUF

Phase A's ripgrep image compiles the pinned checkout only to prove the doc patches are comment-only, and
its `make build`/`check-comment-only` **fetch crates from crates.io at run time** (the gitignored checkout
doesn't exist at image-build, so deps aren't baked). Make the image self-contained per the maintainer's
"exported image runs offline in 5 years" convention: bake the pinned crate dependencies into a **committed
image layer** and build **`--offline`**. "Done" = `cargo build --offline` (and the comment-only gate)
succeed with the network cut (`--network=none`), against the mounted checkout, using only baked deps.

## Can Cargo do it (like mvp's pip/venv bake)? — YES, cleanly

Cargo has first-class offline support, so this is easier than the Gradle sibling:

- **`cargo vendor`** copies every dependency (at the exact versions in `Cargo.lock`) into a local
  `vendor/` dir and prints a `[source.crates-io] replace-with = "vendored-sources"` snippet for
  `.cargo/config.toml`; then **`cargo build --offline`** builds with zero network. This is the direct
  analogue of vendoring pip wheels into a layer.
- **Or warm `CARGO_HOME`**: run `cargo fetch` against the pinned `Cargo.lock` so the registry cache
  (`$CARGO_HOME/registry`) fills, commit that layer, and build `--offline` at runtime reusing it.

## The chicken-and-egg (same as the Gradle task) and the fix

The checkout is fetched at **runtime** (gitignored), so at image-build there is no `Cargo.toml`/`Cargo.lock`
to vendor from. Two ways to resolve, both keying the baked layer to the pin (`PIN_SHA` in `fetch.sh`,
tag 14.1.1):

- **(a) Clone-at-pin-and-fetch in the Dockerfile** (recommended, closest to mvp): shallow-clone ripgrep at
  the pin inside the image build, `cargo fetch` (or `cargo vendor` into a baked `/vendor`), keep
  `$CARGO_HOME`/`/vendor` as a committed layer, discard the clone. The runtime bind-mounted checkout (same
  pin ⇒ same `Cargo.lock`) builds `--offline` against the baked deps.
- **(b) Commit a vendor dir in the carrier** keyed to the pin. Heavier in git and must be regenerated on a
  pin bump; (a) is cleaner for a docs-only carrier that shouldn't grow a big committed `vendor/`.

Set `CARGO_NET_OFFLINE=true` (or pass `--offline`) in the Makefile's `build`/`check-comment-only` targets
so a stray network fetch fails loudly (the check that the bake actually worked).

## Plan
1. In the Dockerfile: pin the ripgrep tag as an ARG (default = `fetch.sh`'s pin), shallow-clone at build,
   `cargo fetch` into a committed `CARGO_HOME` layer (or `cargo vendor` into `/vendor` + a config).
2. Makefile `build`/`check-comment-only`: add `--offline` / `CARGO_NET_OFFLINE=true`.
3. Verify with the offline export test: `make image-export` → `image-import` → run under
   `--network=none`, `cargo build --offline` + the comment-only gate both green.
4. Document the pin-bump step (re-warm/re-vendor when `PIN_SHA` moves) in `unixutils/ripgrep/CLAUDE.md`.

## Decisions (William Emerison Six <billsix@gmail.com>, 2026-09-20)
1. **Warm `CARGO_HOME` via clone-at-pin** at image-build (no big committed `vendor/` dir in git).
2. **Yes, full offline reproducibility** — bake the crates into a committed layer so an exported podman
   image builds under `--network=none` later.

## Related
- Phase-A carrier + the offline gotcha it documented: [ripgrep-refdocs-and-book.md](ripgrep-refdocs-and-book.md),
  `unixutils/ripgrep/CLAUDE.md`.
- Sibling (Gradle/Android): [fossify-jdk-toolchain-and-gradle-offline.md](fossify-jdk-toolchain-and-gradle-offline.md).
- Model: github.com/billsix/modelviewprojection self-contained-image convention (deps fetched+compiled
  into committed layers at build; own source built from the mount at runtime).
