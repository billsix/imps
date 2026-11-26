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
├── Dockerfile Makefile       # Fedora-45 Android/Gradle/JDK image (heavy build)
├── checkout/<repo>/          # gitignored pristine checkouts at their pins
└── patches/<repo>/{docs,book}/  + patches/ORDER
```

## Pins (released tags — conservative anchors)

Read from the `github`-style upstream at the tag; re-verify on a pin bump.

| repo     | tag   | pin SHA (commit) | commit date | UI stack notes |
|----------|-------|------------------|-------------|----------------|
| Commons  | 7.1.3 | `227e7d3cdea2343679eb0863bb597fc7a9200b4d` | 2026-10-10 | mixed Views + Compose (`compose/` package present) |
| Gallery  | 1.14.3 | `b286bf52f755474bc4f8fdf1d68e17765d4316d4` | 2026-11-21 | mostly classic Views/XML |
| Phone    | 1.11.1 | `7de52a31a4d3cfc53e6cbc298a17ffca4e69141e` | 2026-02-03 | classic Views/XML |
| Messages | 1.10.3 | `60f3557be0cb5d8dfe472f2434a224236eb6620a` | 2026-11-21 | classic Views/XML |
| Keyboard | 1.9.1 | `1a2ecdff4e07826d8673576c82637541abbe5264` | 2026-02-02 | classic Views/XML |

Compose/Views migration is mid-flight suite-wide, so pins are deliberately at
released tags; note in a doc which UI stack the code you anchor uses (open
question 5 in the task).

### Carried apps (pinned, empty streams) — added 2026-10-07

The rest of the Fossify suite is now **carried** (fetched + pinned at its latest
release tag, with empty `.keep` `docs`/`book` streams) so the whole suite is
present; documentation depth is the refdocs task's call, not a fetch concern
(`../../tasks/fossify-add-remaining-apps.md`). UI-stack notes are TBD per app
(set when each is first documented).

| repo | tag | commit date |
|------|-----|-------------|
| Calculator | 1.4.0 | 2026-01-30 |
| Calendar | 1.12.2 | 2026-11-07 |
| Camera | 1.5.0 | 2026-01-30 |
| Clock | 1.6.0 | 2026-01-30 |
| Contacts | 1.6.0 | 2026-01-30 |
| Documents | 1.2.2 | 2026-11-21 |
| File-Manager | 1.6.5 | 2026-11-21 |
| Launcher | 1.10.0 | 2026-02-17 |
| Music-Player | 1.8.6 | 2026-11-21 |
| Notes | 1.7.0 | 2026-01-30 |
| Paint | 1.4.0 | 2026-01-30 |
| Thank-You | 1.4.2 | 2026-11-07 |
| Voice-Recorder | 1.7.5 | 2026-11-21 |

SHAs are in the [`repos`](repos) manifest. **Flashlight** is omitted — it has no
released tag yet; add it when it cuts a release. Not-yet-cloned: run `./fetch.sh`
to pull all (the comment-only gate skips un-cloned repos; the 13 SHAs were
confirmed to exist via `git ls-remote` when added).

Commons 7.1.3 build toolchain (from `gradle/libs.versions.toml`): Gradle 9.7.0
(project wrapper), Kotlin 2.3.10, AGP 9.3.1, compileSdk/targetSdk 36,
kotlinJVMTarget 17. Gallery 1.14.3: Gradle 9.5.1, AGP 9.2.1, published Commons
7.1.3. Phone 1.11.1: Gradle 8.13, AGP 8.11.1, Kotlin 2.3.0, published Commons
6.1.0. All three use compileSdk 36.

All pins were moved to each repo's newest release tag on 2026-11-26
(`../../tasks/fossify-sync-upstream-pins.md`); the seven doc patches replayed
with no conflict.

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

## Build status — image + Commons, Gallery, Phone OFFLINE builds VERIFIED (JDK 17, baked cache)

Toolchain verified 2026-09-20, nested (`NESTED_PODMAN=1`), after the JDK-17 + Gradle-offline
hardening (`../../tasks/fossify-jdk-toolchain-and-gradle-offline.md`):

- **JDK: Adoptium/Temurin 17** (`temurin-17-jdk`, GPG-verified via the Adoptium
  dnf repo — `entrypoint/adoptium.repo`; Fedora 45 ships no `java-17-openjdk`).
  Rationale: AGP 9.0+ requires **JDK 17 minimum**, and Commons' `libs.versions.toml`
  sets `app-build-javaVersion=VERSION_17` + `kotlinJVMTarget=17`, so JDK 17 both
  satisfies AGP's floor and matches the compile target — removing the off-target
  uncertainty the Phase-A JDK 25 had. (JDK 25 also literally broke Phone: its AGP
  8.10.1 aborted with the bare version string `25.0.4.1`; JDK 17 fixes that.) One
  JDK-17 daemon runs every repo's Gradle wrapper (9.7.0 Commons, 9.5.1 Gallery, 8.13 Phone), so no
  toolchain-vs-daemon split is needed.
- **`make image`** builds the Fedora-45 image (~4 GB): Temurin 17, Android SDK
  platform-tools + **platforms 34 & 36** + **build-tools 35.0.0 & 36.0.0** (all three
  documented repos use compileSdk 36 at the current pins; 34 and build-tools 35 remain from the older app pins), licenses accepted, then the Gradle
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

### All three documented repos build at the current pins, online and offline

Verified 2026-11-26, nested, after every pin moved to its newest release tag
(`../../tasks/fossify-sync-upstream-pins.md`). `make image`
warmed all three (`BUILD SUCCESSFUL` for Commons 7.1.3, Gallery 1.14.3 and
Phone 1.11.1), and each then compiled with the doc patches applied under
`--network=none` (`./gradlew --no-daemon --offline`): Commons
`:commons:compileReleaseKotlin`, Gallery and Phone `:app:compileFossReleaseKotlin`.
The image export/import roundtrip was not repeated at these pins.

Gallery and Phone did **not** build at their previous pins (1.3.0, 1.5.0): each
depended on an old published `org.fossify:commons` artifact that JitPack no longer
serves. The newer tags depend on published Commons 7.1.3 and 6.1.0, which resolve.
The warm still treats the two apps as **best-effort** (a failure is logged, Commons
is the only required warm), so a future tag with a dead dependency cannot block the
image. Messages/Keyboard were not attempted (undocumented, not warmed). The comment-only invariant does **not** depend on
any app build; `check-comment-only.sh` is the real, verified gate for all seven streams.

## Conventions

- Comment-only, always: doc patches add KDoc and (later) doc-region markers and
  nothing else; keep `check-comment-only.sh` green.
- Read the code before documenting it — a wrong docstring is worse than none.
- In committed docs, refer to upstreams by GitHub URL
  (`github.com/FossifyOrg/<repo>`), never a container path.
- Checkout commits are unsigned (`fetch.sh` sets `commit.gpgsign false` per
  checkout); the durable product is the patch files.
