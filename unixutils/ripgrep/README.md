# ripgrep — documentation-only carrier (imps / unixutils)

A pinned checkout of [ripgrep](https://github.com/BurntSushi/ripgrep) carrying
**comment-only** patch streams (explanatory doc comments now, Sphinx
`doc-region` markers later). ripgrep is documented here, not changed.

```sh
./fetch.sh                 # clone upstream into checkout/, detach at tag 14.1.1
./apply.sh                 # git am the comment-only streams (docs, then book)
make build                 # cargo build the checkout in a Fedora-44 + Rust image
make check-comment-only    # prove the docs stream is comment-only AND compiles
```

Clean re-fetch from nothing:

```sh
rm -rf checkout && ./fetch.sh && ./apply.sh
```

- `make help` lists all targets (`fetch`, `apply`, `image`, `build`,
  `check-comment-only`, `shell`, `shell-exec`, `image-export`/`import`, `clean`).
- `[HOST]` `./fetch.sh` and `./apply.sh` run on the host (just git). `[CONTAINER]`
  `make build` / `check-comment-only` run in the builder image.
- `./check-comment-only.sh` runs the gate on the host too (from this dir), with
  the same result as `make check-comment-only`.
- > `apply.sh` refuses unless the checkout is exactly at the pin; `./fetch.sh`
  > gets you back there. It reads `PIN_SHA` from `fetch.sh` (single source).
- > `make build` fetches crates from crates.io at run time (the gitignored
  > checkout has no baked deps); the *image* needs no network, the *build* does.
- Pin, stream contents, and gotchas: `CLAUDE.md` here. Plan (reference set +
  teaching book): `../../tasks/ripgrep-refdocs-and-book.md`.
