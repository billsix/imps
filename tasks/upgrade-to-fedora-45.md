# Upgrade the container base from Fedora 44 to Fedora 45 (done)

Done 2026-11-05 (William Emerison Six <billsix@gmail.com>). Part of a fleet-wide
Fedora 44 -> 45 bump.

## What changed

- Bumped all six tracked Dockerfiles to `fedora:45`:
  `games/gzdoom/`, `games/gzdoom/book/`, `n64/SuperMario64/book/`,
  `unixutils/ripgrep/`, `unixutils/dash/`, `android/fossify/`.

No source changes. All six `make image` builds green nested on the 45 base:
- **unixutils/dash** (C) and **unixutils/ripgrep** (Rust): clean.
- **games/gzdoom/book** and **n64/SuperMario64/book**: Sphinx docs toolchains.
- **games/gzdoom** (C++): the GZDoom source build compiled clean under GCC 16 /
  clang LLVM 23 (needs game data only to RUN, which is not part of the image build).
- **android/fossify**: the Android SDK/gradle build completed on 45 (SDK licenses
  accepted + build-tools installed in-image).

## Note
`commit.gpgsign` was set false only transiently to make these commits and has
been restored to `true` (verified) -- per the standing rule that imps must never
be left unsigned.
