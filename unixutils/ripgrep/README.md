# ripgrep — documentation-only carrier (imps / unixutils)

A pinned checkout of [ripgrep](https://github.com/BurntSushi/ripgrep) carrying
**comment-only** patch streams (explanatory doc comments now, Sphinx
`doc-region` markers later). ripgrep is documented here, not changed.

```sh
./fetch.sh                 # clone upstream into checkout/, detach at tag 14.1.1
./apply.sh                 # git am the comment-only streams (docs, then book)
make build                 # cargo build the checkout OFFLINE (baked crate cache)
make check-comment-only    # prove the docs stream is comment-only (host: git + python3)
```

Clean re-fetch from nothing:

```sh
rm -rf checkout && ./fetch.sh && ./apply.sh
```

- `make help` lists all targets (`fetch`, `apply`, `image`, `build`,
  `check-comment-only`, `shell`, `shell-exec`, `image-export`/`import`, `clean`).
- `[HOST]` `./fetch.sh` and `./apply.sh` run on the host (just git). `[CONTAINER]`
  `make build` runs in the builder image. `[HOST]` `make check-comment-only` (and
  the `./check-comment-only.sh` shim) run on the host — the shared gate lives at
  the repo root, above this carrier, so it isn't mounted into the image.
- `./check-comment-only.sh` runs the shared gate from this dir, with the same
  result as `make check-comment-only`.
- > `apply.sh` refuses unless the checkout is exactly at the pin; `./fetch.sh`
  > gets you back there. It reads `PIN_SHA` from `fetch.sh` (single source).
- > `make build` runs `cargo build --offline`: ripgrep's whole Cargo dependency
  > graph is baked into a committed `CARGO_HOME` layer (`/opt/cargo-cache`) at
  > image-build, so the build needs **no network** and an exported image stays
  > self-contained. On a pin bump, update `PIN_SHA` (fetch.sh) AND the
  > `RIPGREP_PIN` ARG (Dockerfile) together and rebuild `make image` to re-warm
  > the cache — see `CLAUDE.md`.
- Pin, stream contents, and gotchas: `CLAUDE.md` here. Plan (reference set +
  teaching book): `../../tasks/ripgrep-refdocs-and-book.md`.
