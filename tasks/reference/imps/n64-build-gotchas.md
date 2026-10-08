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

## After a pin bump that also moves libultraship, do a CLEAN rebuild — an incremental one garbles textures

A game pin bump usually moves the `libultraship` submodule too (it is pinned per
game). An **incremental** rebuild then links stale LUS object files against the new
game code — or new LUS against stale game objects — and the ABI/struct skew shows up
at **runtime, not as a build error**: garbled textures and fonts, visible from the
opening scene. Bit us on the MajorasMask bump (2026-10-08, LUS 1.3.1-397 →
1.3.1-490, whose 93 commits rewrote the fast3d texture-upload path — which made the
symptom look like an upstream rendering regression). A clean rebuild fixed it.
Rules: after a bump, run `./fetch.sh` (it re-detaches the pin AND updates submodules
— confirm `git -C <checkout> submodule status libultraship` shows the NEW commit),
then wipe the build dir (`make clean` or `rm -rf <checkout>/build-cmake`) before
rebuilding. Don't debug post-bump graphics corruption until you've ruled this out —
it is far more common than an upstream regression.

## Headless runs of a built port: hard-kill, never plain `timeout`

The games ignore SIGTERM and a forgotten instance can grow to tens of GB. The
full method and the rules (`timeout -s KILL`, an EXIT trap, a `ps` audit,
never a renamed binary): `tasks/reference/imps/headless-gui-port-testing.md`.
