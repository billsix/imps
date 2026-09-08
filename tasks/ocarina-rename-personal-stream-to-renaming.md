# Ocarina: rename the `personal` patch stream to `renaming`

**Status:** proposed — deferred by the maintainer 2026-09-07 ("hold off for now"),
to be done at a quiet point rather than mid-batch. Not blocking anything.
**Priority:** 6
**Difficulty:** 2
**Created:** 2026-09-07

## BLUF

`n64/OcarinaOfTime/patches/personal/` holds **852 patches, and every one of them
is a decomp rename** — the folder is not "personal patches, many of which are
renames", it is the renaming effort entire, heading for ~3,000. Rename the
stream to `renaming/` so the folder says what it holds, leaving `personal/` free
for a genuine non-renaming personal patch later. Done = the stream is
`patches/renaming/`, `./fetch.sh && ./apply.sh` reproduces the same tree, and the
three docs that name the old path are updated.

## Context

### Read first

- **`n64/CLAUDE.md`** → "Patches are grouped into purpose STREAMS" — the family
  contract this must not violate, including the `patches/ORDER` mechanism.
- **`n64/OcarinaOfTime/CLAUDE.md`** → the patch list and the ORDER explanation.
- **[`tasks/archive/ocarina/2026/09/08/ocarina-decomp-rename-and-cleanup.md`](archive/ocarina/2026/09/08/ocarina-decomp-rename-and-cleanup.md)**
  and
  **[`tasks/ocarina-deduce-remaining-decomp-names.md`](archive/ocarina/2026/09/08/ocarina-deduce-remaining-decomp-names.md)**
  — the work that fills this stream.

### Why a SIBLING stream, not a nested one

The obvious shape is `patches/personal/renaming/`. **Do not do that.** The
family contract defines a stream as exactly one level, `patches/<stream>/`, and
`apply.sh` iterates `"$dir"/*/` then globs `"$stream"*.patch`. A nested
directory *is* matched by that glob but holds no `.patch` files directly, so it
would be **silently skipped and its patches never applied** — the worst kind of
failure, since nothing errors. Supporting nesting means changing `apply.sh`, the
`ORDER` reader, and the contract across all four games, to express a
distinction a sibling stream already covers.

### What actually needs changing (surveyed 2026-09-07)

Only **three files** reference the path, all documentation:

| File | Change |
|---|---|
| `n64/OcarinaOfTime/CLAUDE.md` | the patch-list entry and the ORDER paragraph |
| `n64/CLAUDE.md` | the stream catalogue (`patches/personal/` bullet) and the OcarinaOfTime ORDER example |
| `tasks/archive/ocarina/2026/09/07/ocarina-split-rename-patch.md` | archived — add a one-line "the stream was later renamed to `renaming/`" note rather than rewriting the record |

**Nothing else breaks**, verified by grep:

- `apply.sh` — stream-agnostic; iterates whatever directories exist.
- `patches/ORDER` — one word, `personal` → `renaming`.
- `tools/check_patches_apply.sh`, `tools/check_comment_only_streams.sh` — both
  stream-agnostic.
- No `Makefile` or `Dockerfile` names the path.
- The adhoc scripts operate on the *checkout*, not the patch directory; only the
  regenerate command names the output folder.

The patch **files** need no edit: `git format-patch` output does not encode its
own directory.

## Goal

Give the stream a name that matches its contents, without disturbing the applied
tree or the family's one-level stream contract, at a moment when no rename batch
is in flight.

## Plan

- [ ] 1. `git mv n64/OcarinaOfTime/patches/personal n64/OcarinaOfTime/patches/renaming`
- [ ] 2. Update `patches/ORDER` (`personal` → `renaming`).
- [ ] 3. Update the three docs above.
- [ ] 4. Verify: `./fetch.sh` to a pristine pin, `./apply.sh`, and confirm the
      resulting tree matches the pre-move tip exactly (`git diff` empty).
- [ ] 5. `tools/check_patches_apply.sh OcarinaOfTime` and
      `n64/OcarinaOfTime/tools/check_renames.py all`.
- [ ] 6. Re-point the regenerate command in both renaming task docs.

## Notes / decisions

**Do it sooner rather than later.** The cost is a `git mv` plus three doc edits
regardless of size, but the *diff* a reviewer sees grows with the patch count —
852 renames today, ~3,000 projected. Deferred only because the maintainer would
rather not interleave it with an active batch.

**Why not fold it into a rename batch:** a stream move touches every patch path
at once, which would swamp the batch's own diff and make a bad batch harder to
revert. Its own commit, on its own.

## Open questions

1. **Is `renaming/` terminal, or a staging area?** If a rename patch later turns
   out upstreamable (a genuinely wrong name upstream would take a fix for), does
   it *move* to `upstream-candidates/`, or stay in `renaming/` and get
   cherry-picked when submitting? This decides whether the stream is described
   as "personal refactors, permanent" or "renaming work, some of which may
   graduate". My recommendation: **stay put and cherry-pick** — moving patches
   between streams renumbers both and breaks the one-rename-per-commit audit
   trail for no gain.
2. **Should the other games' `personal/` streams be renamed for symmetry?**
   Ocarina is the only project with one today, so there is nothing to align —
   but if the answer to this is "streams should be named for content, always",
   that is worth stating in `n64/CLAUDE.md` as a naming rule rather than left as
   a one-off. Not blocking.
