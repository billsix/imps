# Reference: N64 build gotchas (post-mortems)

> **Provenance:** relocated 2026-09-13 from the N64 family `n64/CLAUDE.md`
> ("Never build a checkout from a foreign toolchain via a bind mount") as part of
> the CLAUDE.md trim (`tasks/trim-claude-md.md`). `n64/CLAUDE.md` keeps a one-line
> pointer and the operational rule; this doc carries the post-mortem detail.

## Never build a checkout from a foreign toolchain via a bind mount — copy the source into the throwaway container first

libultraship at 1.3.1-482+ (banjo, mario) writes build artifacts INTO its
submodule source dir even for an out-of-tree configure, so a fedora:44
verification container that builds `-S /proj/<checkout> -B /tmp/b` leaves
Fedora-compiled `.a`s inside the checkout, and the next podman (ubuntu) build
silently reuses them — bit us 2026-09-01 as a `libmonocypher.a … can not be
used when making a PIE object` link failure in mario's `make build`.
Recovery: `git clean -fdx` in the submodule (+ `git checkout --` any tracked
file the build overwrote, e.g. Ghostship's `src/generate_keys_header`) and
wipe `build-cmake/`.
