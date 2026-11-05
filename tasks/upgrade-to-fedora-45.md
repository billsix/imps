# Upgrade the container base from Fedora 44 to Fedora 45

**Status:** in progress
**Priority:** 4
**Difficulty:** 7

## BLUF
Bump all six tracked Dockerfiles to `fedora:45` and build each nested as far as
it goes. The six are heterogeneous: `games/gzdoom/` (C++), `games/gzdoom/book/`
(Sphinx), `n64/SuperMario64/book/` (Sphinx), `unixutils/ripgrep/` (Rust),
`unixutils/dash/` (C), `android/fossify/` (Android/gradle). "Done" = each builds
on 45, with any that can't complete nested (fossify gradle, game data) documented.

## Context
Fleet-wide Fedora 44 → 45 bump (William Emerison Six <billsix@gmail.com>,
2026-11-05). Fedora 45: GCC 16.2 / clang LLVM 23, Python 3.15, Rust, glibc 2.44.
Risk spans C++/C compiles (gzdoom, dash), Rust (ripgrep), Sphinx/Python (the two
books), and a heavy Android gradle build (fossify) that may not finish nested.

**CRITICAL gpg note (per maintainer memory):** imps must NEVER be left with
`commit.gpgsign=false`. It is set false only transiently to commit; it MUST be
restored to `true` at completion and verified. Do not let false leak.

## Plan
1. Bump all six FROM lines. 2. Build each nested (`build + smoke as far as it
goes`); document the unbuildable ones. 3. Fix toolchain breakage minimally
(discretion; log here). 4. Stage by path; archive. 5. Restore gpgsign=true; verify.

## Notes / findings
(appended as each build runs)
