# dash — documentation-only carrier (imps / unixutils)

Pinned checkout of **dash** (the Debian Almquist Shell, a minimal POSIX
`/bin/sh` in C) carried in imps to **document** it, not to change it. The only
patches are comment-only doc streams.

```sh
./fetch.sh                  # clone dash into checkout/ (kernel.org, mirror fallback), detach at the pin
./apply.sh                  # git am the comment-only doc streams (patches/docs, then patches/book)
make build                  # compile the checkout in the container (autotools) — proves it still builds
make check-comment-only     # PROVE the doc streams change nothing the C compiler sees (the family gate)
```

Clean re-fetch from nothing:

```sh
rm -rf checkout
./fetch.sh && ./apply.sh && make check-comment-only
```

- **Upstream:** <https://git.kernel.org/pub/scm/utils/dash/dash.git> (mirror
  <https://github.com/tklauser/dash>), pinned in `fetch.sh` (`PIN_SHA`) at release
  tag **v0.5.13.5**. `fetch.sh` tries kernel.org first, falls back to the mirror.
- **Documentation-only:** no `run.sh`, no code changes. `patches/docs/` adds C doc
  comments to the shell-pipeline spine (memalloc/mknodes/parser/expand/eval/exec);
  `patches/book/` will add Sphinx doc-region markers later.
- `apply.sh` is optional — skip it for a pristine build. It refuses to run unless
  the checkout is exactly at the pin; `./fetch.sh` gets you back there.
- > **Generated files:** `nodes.c`/`syntax.c`/`init.c`/`builtins.c` do not exist
  > in the tree — they are produced at build time from generators (`mknodes.c`,
  > `mksyntax.c`, `mkinit.c`) and templates (`nodetypes`, `nodes.c.pat`). Document
  > the generators, never the generated files. See `CLAUDE.md`.
- > `make check-comment-only` needs `git` + `gcc` (both in the image, and usually
  > on the host); it needs no full build. The proof engine is the repo-root
  > `tools/prove_comment_only.sh` (gcc `-fpreprocessed`).
- `make help` lists all targets (fetch, apply, image, build, check-comment-only,
  image-export/import, shell, shell-exec, clean, distclean).
- Patch details, the pin, and the generated-files gotcha: `CLAUDE.md` here.
