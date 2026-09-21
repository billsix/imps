# Teach the comment-only gate to discover the `games/` family layout

**Status:** proposed — needs go-ahead. Filed 2026-09-20 (William Emerison Six <billsix@gmail.com>) — a gap
surfaced landing the GZDoom `book/` stream: the shared gate can't *discover* the new `games/` family.
**Priority:** 6
**Difficulty:** 3

## BLUF

The shared comment-only gate `tools/check_comment_only_streams.sh` recognizes three project *shapes* — an
n64 port (named checkout subdir beside `fetch.sh`), a single-repo docs carrier (`checkout/.git`), and a
multi-repo carrier (`repos` manifest + `patches/<repo>/`). The new **`games/`** family matches none: it has
`checkout/<name>/` **subdirs** (e.g. `checkout/gzdoom/` + `checkout/zmusic/`), a **single `patches/` lane**,
and its pin lives in **`<PROJECT>_PIN_SHA`** (`GZDOOM_PIN_SHA`). So `check_comment_only_streams.sh gzdoom`
prints `no checkout … skipped` instead of proving the stream. The comment-only property is still *proven*
today by calling `tools/prove_comment_only.sh` directly, but the discovery wrapper should learn this shape
so `games/` carriers are gated like everyone else. "Done" = `tools/check_comment_only_streams.sh gzdoom`
discovers `games/gzdoom/`, reads `patches/LANG`, and PROVES its `book/` stream (and the same for future
`games/` projects).

## What to add (a fourth shape)

In `tools/check_comment_only_streams.sh`'s per-project discovery: recognize a **`games/`-style carrier** —
a project dir with a `patches/` dir and one or more `checkout/<name>/` git checkouts, whose primary
checkout + pin come from a `<PROJECT>_PIN_SHA` in `fetch.sh` (the doc/marker stream targets that primary
checkout — for GZDoom that is `checkout/gzdoom` at `GZDOOM_PIN_SHA`). Reuse the existing single-`patches/`
lane + `patches/LANG` dispatch (GZDoom declares `c`, reusing `prove_comment_only.sh`). Keep the other three
shapes unchanged.

## Plan
1. Read the current shape-detection in `tools/check_comment_only_streams.sh` (how it finds the checkout +
   pin per shape).
2. Add the `games/` shape: primary checkout = the one whose name matches a `<NAME>_PIN_SHA` in `fetch.sh`
   (or a documented convention); pin from that var; single `patches/` lane; `patches/LANG` prover dispatch.
3. Verify: `tools/check_comment_only_streams.sh gzdoom` (and bare, all-projects) now PROVES the GZDoom
   `book/` stream comment-only — matching the direct `prove_comment_only.sh` result — and the n64 / unixutils
   / android shapes still pass unchanged.
4. Drop the "gate can't discover this yet" caveat from `games/gzdoom/CLAUDE.md`.

## Related
- The gate: `tools/check_comment_only_streams.sh`, `tools/prove_comment_only.sh`, and the generalization it
  extends: `tasks/archive/imps/2026/09/20/generalize-comment-only-gate.md`.
- Surfaced by: the GZDoom book (`tasks/gzdoom-port-and-cli-wad-patch.md`, `games/gzdoom/`). The caveat is
  noted in `games/gzdoom/CLAUDE.md`.
