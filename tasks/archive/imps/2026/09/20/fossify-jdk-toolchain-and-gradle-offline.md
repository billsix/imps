# Fossify carrier — pin the build JDK (toolchain) and bake Gradle deps offline

**Status:** DONE (Commons) — 2026-09-20; one follow-up filed (the two exemplar apps don't build at their
pins — upstream rot, see Outcome). Go-ahead + implementation 2026-09-20. Raised 2026-09-20
(William Emerison Six <billsix@gmail.com>) as follow-up #1 to the Fossify Phase-A carrier
([fossify-refdocs-and-book.md](../../../../../fossify-refdocs-and-book.md)). Two questions the maintainer asked, answered
below with the fix each implies.
**Priority:** 5
**Difficulty:** 6 (the Gradle offline-bake is the hard, heavy part)

## BLUF

Harden `android/fossify/`'s build image on two axes the Phase-A pass left open: (1) make the **build JDK
deterministic** instead of relying on Fedora 44's JDK 25, and (2) **bake the Gradle dependency cache into
the image at build time** so an exported image builds Commons/apps **offline** — the Gradle analogue of
how modelviewprojection bakes pip deps into a `/venv` layer. "Done" = `make build` (Commons, and ideally
an app module) runs with `--offline` against a baked `GRADLE_USER_HOME`, on a JDK the toolchain officially
supports.

## Q1: does JDK 25 cause problems for a JVM-17 target? (researched 2026-09-20)

Short answer: **not for the bytecode target itself — the maintainer's intuition is right** — but the
build *tooling* is the thing to pin.

- **Running is backward-compatible.** A JDK 25 runtime runs classes compiled to JVM 17 (or older) bytecode
  fine. "Newer JVM runs older bytecode" holds.
- **Compiling to target 17 from JDK 25 is fine.** `javac --release 17` / Kotlin `jvmTarget = 17` emit
  17 bytecode regardless of the JDK running the compiler. Kotlin's only current limit is it can't *target*
  the very newest JDK — "Kotlin does not yet support 25 JDK target, falling back to JVM_24" — which is
  irrelevant at target **17** (well below 24). This matches Phase A: Commons compiled clean on JDK 25.
- **The real risk is tooling certification.** Gradle added full **Java 25 support in 9.1.0**, so Fossify's
  **Gradle 9.6.1 daemon on JDK 25 is officially supported**. The open piece is **AGP 9.3.1** — verify its
  officially-supported JDK range (Android's "Java versions in Android builds" doc); AGP has historically
  pinned to a specific JDK (e.g. AGP 8.x → JDK 17). Phase A got Commons to compile on 25, but "compiled
  once" ≠ "supported".
- **The clean fix (mvp analogy = "pin the toolchain"):** use a **Gradle Java toolchain**
  (`java { toolchain { languageVersion = JavaLanguageVersion.of(17) } }`, or `-Porg.gradle.java...`),
  which **decouples the compile JDK from the daemon JDK** (Gradle ≥ 6.7). Then install a **Temurin/Adoptium
  17 (or 21)** JDK in the image for the toolchain to use, and let Gradle run its daemon on whatever. This
  removes the "off-target JDK" uncertainty entirely. NOTE: Fossify's build scripts must not *forbid*
  toolchains; if a repo hardcodes `sourceCompatibility`/a specific JDK, reconcile.

**Recommendation:** install an Adoptium 17 (LTS, matches `kotlinJVMTarget 17`) or 21 JDK in the Dockerfile
and configure a Gradle toolchain pointing at it (auto-detect via `-Porg.gradle.java.installations.paths`
or a provisioned path); keep JDK 25 out of the compile path. Verify AGP 9.3.1's supported JDK before
choosing 17 vs 21.

## Q2: can Gradle bake deps into the image like mvp bakes pip/venv? (researched 2026-09-20)

**Yes, via a warmed `GRADLE_USER_HOME`, though Gradle has no single `vendor` command.** mvp creates a
`/venv` and `pip install`s into a committed layer, then runs offline. Gradle's equivalent:

- Point `GRADLE_USER_HOME` at a fixed path (the Dockerfile already sets `/opt/gradle-cache`).
- **At image-build**, with the source present at the pin, run a resolve/build that downloads every
  dependency + the Gradle distribution the wrapper needs into that dir (e.g. `./gradlew --no-daemon
  :commons:compileReleaseKotlin` or a dedicated `dependencies`/`resolveAllDependencies` task), so the
  artifacts land in a **committed image layer**. Then at runtime build with **`--offline`**.
- **The chicken-and-egg to solve:** the checkout is fetched at *runtime* (gitignored), so at image-build
  there is no source to resolve against. Options: (a) **clone each repo at its pin inside the Dockerfile**
  (a shallow clone keyed to the manifest pin) purely to warm the cache, then discard the clone but keep
  `GRADLE_USER_HOME` — the runtime bind-mounted checkout reuses the warmed cache offline; or (b) commit a
  Gradle **dependency lockfile** + use `--offline` against a cache warmed from it. (a) is closest to mvp's
  "fetch+compile deps into a committed layer at build".
- **Android SDK is already baked** (cmdline-tools + platform + build-tools in committed layers) — only the
  Gradle dep cache is missing, so this is the remaining gap for the "exported image runs offline in 5
  years" convention.
- **Cost caveat:** warming the cache means running a real Gradle resolve at image-build (minutes, network
  on) — the heavy step Phase A skipped. Per-repo pins mean the warm must cover each documented repo.

**Recommendation:** clone-at-pin-and-warm inside the Dockerfile (option a), gated so the layer is keyed to
the manifest pins; runtime `make build`/`check-comment-only` pass `--offline`. This is the sibling of
[ripgrep-cargo-vendor-offline.md](ripgrep-cargo-vendor-offline.md) (the Cargo version of the same idea).

## Plan (as executed — see Outcome above for the result)
1. **JDK:** add Adoptium 17 (or 21, per AGP 9.3.1's supported range — verify first) to the Dockerfile;
   configure a Gradle toolchain so compilation uses it regardless of the daemon JDK; keep or drop JDK 25
   as the daemon per what Gradle/AGP want. Re-verify Commons compiles.
2. **Offline:** set `GRADLE_USER_HOME` (done), warm it at image-build by cloning each manifest repo at its
   pin and resolving its deps into a committed layer; switch `make build`/`check-comment-only` to
   `--offline`. Verify with the offline export test (`--network=none`) per the maintainer's convention.
3. **Verify app modules**, not just the Commons library (Phase A only built Commons): at least one app
   (Gallery) offline.

## Outcome (2026-09-20) — DONE for Commons, apps blocked by upstream rot

- **JDK: Adoptium/Temurin 17** via the Adoptium dnf repo (`entrypoint/adoptium.repo`, `gpgcheck=1`; Fedora
  44 has no `java-17-openjdk`). JDK 25 dropped. One JDK-17 daemon runs both Gradle 9.6.1 (Commons) and
  8.11.1 (apps) — no toolchain/daemon split needed. Bonus: JDK 25 had literally broken Phone (its AGP
  8.10.1 aborted on the bare version string `25.0.4.1`); JDK 17 fixes it.
- **Offline bake (the mvp `/venv` analogue):** `entrypoint/warm-gradle-cache.sh` clones each documented repo
  at its pin at image-build and runs its runtime compile task with network ON, baking the dep graph + both
  Gradle wrapper distributions into a committed `GRADLE_USER_HOME=/opt/gradle-cache` layer. Also added SDK
  platform 34 + build-tools 35.0.0 (the apps' targets) alongside 36. Image ~3.99 GB. `make build` runs
  `./gradlew --offline`.
- **Offline export test PASSED for Commons (independently re-verified):** after `make image-export` →
  `podman rmi` → `make image-import`, `:commons:compileReleaseKotlin` built `BUILD SUCCESSFUL` under
  `--network=none` from only the baked cache. The maintainer's "exported image runs offline" convention is
  met for Commons.
- **The two exemplar apps (Gallery, Phone) do NOT build at their pins — upstream JitPack/Bintray rot, not an
  offline/JDK gap.** Each depends on an old *published* `org.fossify:commons` JitPack can no longer serve
  (Gallery 1.3.0 → a transitive `com.github.duolingo:rtl-viewpager` whose JitPack build needs the shut-down
  `jcenter.bintray.com`; Phone 1.5.0 → `commons:3.0.3` 404s). They fail **online too**, so warming can't
  cache what won't resolve anywhere. **Follow-up:** bump Gallery/Phone to newer tags whose published-Commons
  dep resolves, or substitute the locally-checked-out Commons for the published artifact. (The warm still
  *attempts* them each build (~1 min of expected failure) so it auto-heals on a pin bump; comment them out to
  save the time until then.) Messages/Keyboard not warmed (undocumented, per decision 3).
- Full detail: `android/fossify/CLAUDE.md` ("Build status") + `README.md`.

## Decisions (William Emerison Six <billsix@gmail.com>, 2026-09-20)
1. **Build JDK: 17**, pinned via a Gradle Java toolchain (matches `kotlinJVMTarget 17`). Still verify AGP
   9.3.1's daemon-JDK requirement first: keep the *compile* toolchain at 17 regardless; if AGP forces a
   newer daemon, run the daemon on that but leave compilation on 17.
2. **Bake deps for full offline reproducibility.** Accept the multi-minute, network-on image build so an
   exported podman image builds/runs under `--network=none` later — "if I ever have a podman image of
   this, I can run it offline" is the whole point.
3. **Warm only the documented repos** (Commons + Gallery + Phone). Messages/Keyboard are undocumented, so
   skip warming them until they are.

## Related
- Phase-A carrier + caveats: [fossify-refdocs-and-book.md](../../../../../fossify-refdocs-and-book.md),
  `android/fossify/CLAUDE.md` (the JDK-25 + offline TODOs).
- Sibling (Cargo): [ripgrep-cargo-vendor-offline.md](ripgrep-cargo-vendor-offline.md).
- Model: github.com/billsix/modelviewprojection (bakes pip deps into a `/venv` layer; `make type-check`
  BUILD_DOCS=0 lean image) and its `tasks/reference/container-source-and-mounts.md`.
- Sources: Gradle 9.1 release notes / compatibility matrix (Java 25 daemon support), Gradle "Toolchains
  for JVM projects" (docs.gradle.org), Android "Java versions in Android builds"
  (developer.android.com/build/jdks).
