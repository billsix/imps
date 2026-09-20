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

The gate is the **shared** `../../tools/check_comment_only_streams.sh fossify`
(wrapped by `make check-comment-only` and the thin `./check-comment-only.sh`
shim — which now checks the whole suite; a per-`repo` argument is no longer
honored). It reads `patches/LANG` (= `kotlin`, one lang for every repo in the
manifest), loops the `repos` manifest, and for every file each repo's
`docs`/`book` stream touches, strips Kotlin comments/KDoc and byte-compares the
pin-vs-applied token stream via `../../tools/prove_comment_only_strip.py --lang
kotlin`. Kotlin has no `gcc -fpreprocessed`, and a naive compiled-output diff is
unreliable (adding comment lines shifts the `.class` `LineNumberTable` even for a
comment-only edit); the strip-and-compare proof sidesteps that and is **stronger**
than the earlier per-hunk "is every changed line a comment?" check — it proves
token identity of what the compiler sees. It needs no Android SDK (git + python3
only), so run it host-side before staging regenerated patches.

## Build status — image + Commons OFFLINE build VERIFIED (JDK 17, baked cache)

Verified 2026-09-20, nested (`NESTED_PODMAN=1`), after the JDK-17 + Gradle-offline
hardening (`../../tasks/fossify-jdk-toolchain-and-gradle-offline.md`):

- **JDK: Adoptium/Temurin 17** (`temurin-17-jdk`, GPG-verified via the Adoptium
  dnf repo — `entrypoint/adoptium.repo`; Fedora 44 ships no `java-17-openjdk`).
  Rationale: AGP 9.0+ requires **JDK 17 minimum**, and Commons' `libs.versions.toml`
  sets `app-build-javaVersion=VERSION_17` + `kotlinJVMTarget=17`, so JDK 17 both
  satisfies AGP's floor and matches the compile target — removing the off-target
  uncertainty the Phase-A JDK 25 had. (JDK 25 also literally broke Phone: its AGP
  8.10.1 aborted with the bare version string `25.0.4.1`; JDK 17 fixes that.) One
  JDK-17 daemon runs both Gradle 9.6.1 (Commons) and 8.11.1 (the apps), so no
  toolchain-vs-daemon split is needed.
- **`make image`** builds the Fedora-44 image (~4 GB): Temurin 17, Android SDK
  platform-tools + **platforms 34 & 36** + **build-tools 35.0.0 & 36.0.0** (Commons
  wants 36; the apps want 34 + build-tools 35), licenses accepted, then the Gradle
  cache is **warmed at build time** (see next bullet).
- **Offline-self-contained (the mvp `/venv` analogue).** At image-build,
  `entrypoint/warm-gradle-cache.sh` clones each documented repo at its manifest pin
  and runs its runtime compile task with network ON, baking the full dependency
  graph + both Gradle wrapper distributions into a committed `GRADLE_USER_HOME`
  layer (`/opt/gradle-cache`). `make build` then runs `./gradlew --offline`.
- **Offline export test PASSED for Commons.** After `make image-export` → `podman
  rmi` → `make image-import` (a 3.8 GB tar roundtrip), `:commons:compileReleaseKotlin`
  built **`BUILD SUCCESSFUL in 33s` under `--network=none`** against only the baked
  cache — the maintainer's "exported image runs offline in 5 years" convention is
  now met for Commons. (Comment-only proof is independent: `check-comment-only.sh`
  runs host-side and stays the real gate.)

### The two exemplar apps DON'T build at their pins — upstream JitPack/Bintray rot

Both Gallery and Phone fail to build **online AND offline** at their pinned RELEASED
tags, because each depends on an *old published* `org.fossify:commons` that JitPack
can no longer serve (this is orthogonal to the JDK/offline work — warming can't cache
what won't resolve anywhere). The warm treats them as **best-effort** (a failure is
logged, Commons is the only required warm), so the image still builds:

- **Gallery 1.3.0** → published `org.fossify:commons:3dd1f7f33e` → transitive
  `com.github.duolingo:rtl-viewpager:940f12724f`, whose **own** JitPack build fails
  (it needs `gradle-bintray-plugin` from the shut-down `jcenter.bintray.com`), so the
  artifact 404s permanently. Offline it fails with "No cached version … for offline
  mode" — same missing dep.
- **Phone 1.5.0** → published `org.fossify:commons:3.0.3`, which **404s** on JitPack
  (both `.pom` and `.aar`). (JDK 17 got Phone past the JDK-25 abort; the dep is just
  gone.)

Fix path when the maintainer wants an app built: **bump Gallery/Phone to newer tags**
whose published-Commons dependency still resolves (re-check at the bump), or substitute
the locally-checked-out Commons for the published artifact. Messages/Keyboard were not
attempted (undocumented, not warmed). The comment-only invariant does **not** depend on
any app build; `check-comment-only.sh` is the real, verified gate for all seven streams.

## Conventions

- Comment-only, always: doc patches add KDoc and (later) doc-region markers and
  nothing else; keep `check-comment-only.sh` green.
- Read the code before documenting it — a wrong docstring is worse than none.
- In committed docs, refer to upstreams by GitHub URL
  (`github.com/FossifyOrg/<repo>`), never a container path.
- Checkout commits are unsigned (`fetch.sh` sets `commit.gpgsign false` per
  checkout); the durable product is the patch files.
