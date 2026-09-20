# fossify — the Fossify app suite, documented (imps docs-only, multi-repo)

The tier-3 per-project doc for the Fossify carrier. Read the family
[`../CLAUDE.md`](../CLAUDE.md) first (the docs-only, multi-repo Android carrier
contract) and the repo-root [`../../CLAUDE.md`](../../CLAUDE.md) (the imps carrier
idea, four-tier docs, patch philosophy, unsigned-checkout-commits rule). This
file holds the concrete manifest, pins, layout, and doc-stream contents.

Plan / task: [`../../tasks/fossify-refdocs-and-book.md`](../../tasks/fossify-refdocs-and-book.md).
Book (later): "*How Android Apps Are Built*".

## Multi-repo layout

This is the one carrier that pins **several** upstreams, because the Fossify apps
share a `Commons` library. The upstreams and pins live in the [`repos`](repos)
manifest (URL, pin SHA, `# tag date`); `fetch.sh` loops over it and clones each
into `checkout/<name>/` (gitignored). Per repo there is a `patches/<repo>/docs/`
and `patches/<repo>/book/` stream; `patches/ORDER` (shared) applies `docs` then
`book`. `apply.sh` loops the manifest and, per repo, `git am --3way`s its streams
guarded at that repo's pin.

```
fossify/
├── repos                     # the manifest (URL  pin  # tag date)
├── fetch.sh apply.sh         # loop the manifest; per-repo clone / am
├── check-comment-only.sh     # the comment-only gate (host, fast)
├── Dockerfile Makefile       # Fedora-44 Android/Gradle/JDK image (heavy build)
├── checkout/<repo>/          # gitignored pristine checkouts at their pins
└── patches/<repo>/{docs,book}/  + patches/ORDER
```

## Pins (released tags — conservative anchors)

Read from the `github`-style upstream at the tag; re-verify on a pin bump.

| repo     | tag   | pin SHA (commit) | commit date | UI stack notes |
|----------|-------|------------------|-------------|----------------|
| Commons  | 6.2.0 | `70c2c6eab9e61b7a38f6d232ca1e326a51ce1353` | 2026-07-31 | mixed Views + Compose (`compose/` package present) |
| Gallery  | 1.3.0 | `7c11d0a2ffac25902b4007ca1f45d05080fa8f52` | 2025-05-31 | mostly classic Views/XML |
| Phone    | 1.5.0 | `572590d3b0909a124038197ea95baa17a2bb25a6` | 2025-06-06 | classic Views/XML |
| Messages | 1.2.0 | `fa05eb582b54a8d22a25a714676c5cc9b0a71c22` | 2025-06-04 | classic Views/XML |
| Keyboard | 1.2.0 | `cc016c06bf6e4ef5dfe8ab150f65449f3140b967` | 2025-06-03 | classic Views/XML |

Compose/Views migration is mid-flight suite-wide, so pins are deliberately at
released tags; note in a doc which UI stack the code you anchor uses (open
question 5 in the task).

Commons 6.2.0 build toolchain (from `gradle/libs.versions.toml`): Gradle 9.6.1
(project wrapper), Kotlin 2.3.10, AGP 9.3.1, compileSdk/targetSdk 36,
kotlinJVMTarget 17.

## Doc streams (`patches/<repo>/docs/`) — comment-only KDoc

All are `/** … */` KDoc; no code changes. Proven comment-only by
`./check-comment-only.sh` (PASS across all seven, verified).

**Commons** (in depth, 5 patches):
- `0001` — `BaseSimpleActivity`: the shared app skeleton — theming lifecycle,
  the font inflater factory, forced-English locale wrapping, and the
  callback-style runtime permission helpers.
- `0002` — the runtime theming/color-resolution system: `getThemeId`
  (`Activity-themes.kt`) and the `Context-styling.kt` resolvers (theme-mode
  predicates, `getProper*Color`, `updateTextColors`, `syncGlobalConfig`,
  `toggleAppIconColor`).
- `0003` — `BaseConfig`: the shared SharedPreferences settings store and the
  subclass-per-app pattern.
- `0004` — `ColorPickerDialog` (+ its `Hsv` value class).
- `0005` — the storage-path helpers (`Context-storage.kt`: SD/OTG/storage-root
  discovery and the SAF-only directories).

**Gallery** (thin, 1 patch): `0001` — `MediaFetcher` (the media pipeline across
the OTG / pre-scoped / Android-11+ MediaStore paths) and `Config` (the canonical
example of an app extending `Commons`' `BaseConfig`).

**Phone** (thin, 1 patch): `0001` — `CallManager`, the process-wide live-call
singleton mediating Android's `InCallService` and the in-call UI.

**Messages, Keyboard**: cloned + pinned, doc streams empty (`.keep`) — a first
pass deliberately went deep on Commons rather than shallow on all apps.

`book/` streams (Sphinx doc-region markers) are all empty pending the book
(Phase C of the task).

## The comment-only gate

`./check-comment-only.sh [repo]` is the android-family analogue of the C
`../../tools/check_comment_only_streams.sh`. Kotlin has no `gcc -fpreprocessed`,
and a naive compiled-output diff is unreliable: adding comment lines shifts
source line numbers, changing the `.class` `LineNumberTable` even for a
comment-only edit. Since Kotlin comments/KDoc are non-semantic (discarded by the
lexer, never in bytecode), the gate instead proves **every changed line in each
`docs`/`book` patch hunk is a comment or blank line** — a source-level proof that
is correct, fast, and needs no Android SDK. Run it before staging regenerated
patches. (A heavier compile-and-diff-a-comment-stripped-disassembly alternative
is possible but left best-effort/UNVERIFIED given how heavy an Android build is.)

## Build status — image + Commons build VERIFIED

Both verified 2026-09-20, nested (`NESTED_PODMAN=1`):
- `make image` builds the Fedora-44 image (JDK 25, Android command-line tools,
  platform 36 + build-tools 36.0.0 + platform-tools, licenses accepted).
- `make build` (default `REPO=Commons GRADLE_MODULE=:commons`) compiled
  `:commons:compileReleaseKotlin` **cleanly in ~1m45s with the doc patches
  applied** — Gradle 9.6.1 + AGP 9.3.1 + Kotlin 2.3.10 run fine on JDK 25, and
  the KDoc compiles (only pre-existing deprecation warnings). This also
  independently confirms the doc patches don't break the build.

Remaining gaps / decisions for the maintainer:

- **Only Commons build-checked.** `make build REPO=Gallery GRADLE_MODULE=:app`
  (and Phone/Messages/Keyboard) were not run — an *app* (vs the Commons library)
  pulls more of the dependency graph and may need `:app` and more time. Untested.
- **JDK 25 works but is off-target.** Fedora 44 ships only `java-25-openjdk-devel`
  (no 17/21). The project targets JVM 17 *bytecode*; JDK 25 running Gradle was
  fine for Commons. If a future toolchain rejects it, drop in an Adoptium 17/21
  tarball and repoint `JAVA_HOME`.
- **Not offline-self-contained:** the SDK is baked into the image, but the
  per-project **Gradle dependency cache is warmed on first `make build`** (needs
  network), not at image-build. So the maintainer's "exported image runs offline
  in 5 years" convention is only partially met. Warming `~/.gradle` at
  image-build is a candidate follow-up (heavy — deliberately skipped this pass).
- The comment-only invariant does **not** depend on any build;
  `check-comment-only.sh` is the real, verified gate.

## Conventions

- Comment-only, always: doc patches add KDoc and (later) doc-region markers and
  nothing else; keep `check-comment-only.sh` green.
- Read the code before documenting it — a wrong docstring is worse than none.
- In committed docs, refer to upstreams by GitHub URL
  (`github.com/FossifyOrg/<repo>`), never a container path.
- Checkout commits are unsigned (`fetch.sh` sets `commit.gpgsign false` per
  checkout); the durable product is the patch files.
