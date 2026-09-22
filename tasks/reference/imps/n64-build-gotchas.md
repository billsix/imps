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

## `libshaderc-devel` must be installed BEFORE cmake configures (Vulkan backend)

Every port whose libultraship builds the Vulkan backend (`gfx_vulkan.cpp`
includes `shaderc/shaderc.hpp`) needs `libshaderc-devel`; the project
`installdependencies.sh` scripts list it. The trap (PaperMario, 2026-09-22):
install it *after* `cmake --preset` has run and the build still fails — at the
**final link**, on `shaderc_*` undefined references — because the configure
cache never recorded the library. Re-run the configure step (`build.sh` does)
after installing. Symptom to recognise: a clean compile of 3,600 objects, then
`undefined reference to shaderc_compile_into_spv` in `Paperboat`.

## Headless runs of a built port: hard-kill, never plain `timeout`

The games ignore SIGTERM and a forgotten instance can grow to tens of GB. The
full method and the rules (`timeout -s KILL`, an EXIT trap, a `ps` audit,
never a renamed binary): `tasks/reference/imps/headless-gui-port-testing.md`.
