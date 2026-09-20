# android — Android apps, documented for teaching (imps docs-only family)

The **android** family carries pinned checkouts of well-written open-source Android apps **to document
them**, not to port them. Read the repo-root [`../CLAUDE.md`](../CLAUDE.md) first (the carrier idea, the
four-tier doc structure, the per-project contract, the patch philosophy); this tier-2 doc holds the
*documentation-only* carrier contract for Android projects and the per-project index. It auto-loads for any
session under `android/`.

## Docs-only, like `unixutils/` — and multi-repo

Same principle as [`../unixutils/CLAUDE.md`](../unixutils/CLAUDE.md): the only patch streams are
**comment-only** — `patches/docs/` (explanatory **doc comments**, KDoc `/** … */`, on interesting parts of
the source — the "start adding docstrings" deliverable, William Emerison Six <billsix@gmail.com>,
2026-09-20) and `patches/book/` (Sphinx doc-region markers, later). Both must change nothing the Kotlin
compiler sees.

The distinctive trait of this family (today, Fossify) is that it is **multi-repo**: an app suite shares a
`Commons` library, so one carrier pins **several upstreams** (Commons + a chosen set of apps). Design the
fetch/apply around a **`repos` manifest** (repo URL → pin, one line each) that the scripts loop over, with
a per-repo `book/`/`docs/` stream and a per-repo checkout. This is the main way an `android/` carrier
departs from the single-repo `unixutils/` shape.

## Per-project folder contract (on top of the generic one in `../CLAUDE.md`)

`android/<suite>/`:
- `fetch.sh` — read the `repos` manifest; clone each upstream into its own gitignored checkout and detach
  at that repo's pin (a **released tag** where one exists, for stable anchors; SHA + date commented). Set
  `commit.gpgsign false` in each checkout. Idempotent.
- `apply.sh` — per repo, `git am --3way` its `docs/` (then `book/`) stream, guarded at that repo's pin.
- `Makefile` + `Dockerfile` — Fedora-44 image (maintainer's template conventions: `PODMAN_RUN_FLAGS`,
  `shell`/`shell-exec`, `##` help) with the Android/Gradle/JDK toolchain. **Building a full Android app is
  heavy (SDK, Gradle, license acceptance) — set the Dockerfile up correctly but treat a green app build as
  best-effort; the comment-only proof for Kotlin can also be a compile-before/after or comment-strip diff
  of just the touched modules rather than a full APK build.** Targets: `fetch`, `apply`, `image`,
  optionally `build`, and `check-comment-only`.
- `repos` (the manifest), `patches/LANG` (one word — `kotlin` — read by the shared gate to pick the
  prover; one lang for every repo in the manifest; see below), `patches/<repo>/docs/.keep` +
  `patches/<repo>/book/.keep` per repo, `patches/ORDER`, `.gitignore` (all checkouts + build dirs), tier-3
  `CLAUDE.md` (the repo manifest, pins, doc-stream contents, build gotchas), `README.md` (fetch → apply →
  build).

## The comment-only gate — one shared, family-agnostic tool

The gate is **shared**, at the imps repo root — there is no per-project Kotlin re-implementation any more
(the earlier "add a local wrapper" stopgap is gone). **`../../tools/check_comment_only_streams.sh
[project ...]`** discovers every project across all families, reads each project's **`patches/LANG`**
declaration (`kotlin` for an android carrier — one lang covers all repos in the manifest, so `patches/LANG`
sits once at the patches root, above the per-repo `patches/<repo>/` dirs), and **dispatches** per language:

- Kotlin has no `gcc -fpreprocessed`, so a `kotlin` project routes to **`../../tools/
  prove_comment_only_strip.py --lang kotlin`** — a Kotlin-aware comment stripper. For every file a repo's
  `docs`/`book` stream touches, it strips comments/KDoc (handling `//`, nested `/* */`, `"..."` strings
  with `$`-templates, `"""..."""` raw strings, and char literals) and byte-compares the pinned-vs-applied
  token stream. This is **stronger** than the old per-hunk "is every changed line a comment?" check — it
  proves token identity of what the compiler sees, and it needs **no Android SDK** (git + python3 only).
- Multi-repo is handled natively: the tool loops the `repos` manifest, checking each repo's stream at
  that repo's pin.

Run it host-side (the shared `tools/` live above a carrier and are not mounted into its heavy Android
image). `make check-comment-only` calls the shared tool with the project name; `./check-comment-only.sh`
is a thin shim to the same entry point (a per-repo argument is no longer honored — every repo is checked).

## Books & references

The Sphinx book lives in `android/<suite>/book/` (from the mario64 `n64/SuperMario64/book/` template), and
because a suite shares `Commons`, it is **one book** documenting Commons + the shared app skeleton with
thin per-app chapters — not a book per app. Reference set at `../tasks/reference/<suite>/`.

## Projects

- **`fossify/`** — the Fossify suite (~17 privacy-first Android apps, Kotlin, GPL-3.0; the Simple Mobile
  Tools continuation) built on the shared **`Commons`** library (github.com/FossifyOrg). Multi-repo:
  document Commons + the shared skeleton in depth, a few exemplar apps (Gallery/Phone/Messages/Keyboard)
  thinly. Plan: `../tasks/fossify-refdocs-and-book.md`. Book: "*How Android Apps Are Built*".
