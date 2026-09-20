# Fossify — a documentation-only, multi-repo imps carrier

Pinned checkouts of the [Fossify](https://github.com/FossifyOrg) Android apps and
their shared `Commons` library, carried **only to document them** — the patch
streams are comment-only (KDoc, and later Sphinx doc-region markers). Nothing
here changes what any app does.

```sh
./fetch.sh              # clone every upstream in `repos` at its pinned tag
./apply.sh              # apply each repo's comment-only doc patches
./check-comment-only.sh # prove the doc patches change no code (host, fast)
```

- Upstreams and pins live in [`repos`](repos) (one line each: URL, pin SHA,
  `# tag date`). Each is pinned at a **released tag**. `fetch.sh` clones each
  into `checkout/<name>/` (gitignored) and detaches it at its pin.
- `apply.sh` applies, per repo, `patches/<repo>/docs/*.patch` then `book/*.patch`
  with `git am --3way`, guarded so it only runs when a checkout is at its pin.
  Re-run `./fetch.sh` (which resets each HEAD to its pin) to get back there.
- The default working state after `fetch` + `apply` is each checkout at its pin
  **with the doc patches applied**.

## What is documented

Documentation centre of gravity is **`Commons`** — every app depends on it, so
it is documented in depth; the apps get a thin, app-specific pass.

- **Commons** (5 patches): the shared app skeleton (`BaseSimpleActivity`), the
  runtime theming/color-resolution system, the `BaseConfig` settings store, the
  HSV color-picker dialog, and the storage-path helpers.
- **Gallery** (1 patch): the `MediaFetcher` media pipeline and its `Config`.
- **Phone** (1 patch): `CallManager`, the live-call singleton.
- **Messages**, **Keyboard**: cloned and pinned; doc streams empty so far.

## Editing the docs (regenerating patches)

Work as commits inside a checkout, then regenerate that repo's series:

```sh
# edit + commit inside checkout/<repo>/ (comments only!), then:
PIN=$(sed -n 's#.*/<repo>.git[[:space:]]*\([0-9a-f]*\).*#\1#p' repos)
git -C checkout/<repo> format-patch --no-cover-letter --base="$PIN" \
    "$PIN"..HEAD -o patches/<repo>/docs/
./check-comment-only.sh             # checks the whole suite; must PASS before staging
```

## Building (heavy — Commons builds OFFLINE; the apps are best-effort)

```sh
make help              # list targets
make image             # build the Fedora-44 Android/Gradle/JDK image (~4 GB, warms the cache)
make build             # compile Commons OFFLINE (REPO=Commons GRADLE_MODULE=:commons)
make shell             # interactive shell in the builder container
```

> **Verified 2026-09-20:** the image builds on **Adoptium/Temurin JDK 17** (AGP's
> minimum, and it matches Commons' JVM-17 compile target) with the Android SDK
> (platforms 34 & 36, build-tools 35 & 36) AND the Gradle dependency cache **baked
> in at image-build** — so `:commons:compileReleaseKotlin` compiles **offline**.
> Proof: an export→`rmi`→import roundtrip then a `--network=none` build succeeded
> (`BUILD SUCCESSFUL in 33s`), meeting the "exported image runs offline" convention.
>
> The exemplar **apps do NOT build at their pinned tags** — Gallery and Phone each
> depend on an old published `org.fossify:commons` that JitPack can no longer serve
> (Gallery: a transitive `rtl-viewpager` whose build needs the dead
> `jcenter.bintray.com`; Phone: commons `3.0.3` 404s). This fails online too, so
> it's upstream rot, not an offline gap — bump those apps to newer tags to build
> them. Detail: `CLAUDE.md` ("Build status"). The comment-only proof needs no build:
> `./check-comment-only.sh` runs on the host in seconds.

- To build an app once its pin resolves, override the flavor-qualified task, e.g.
  `make build REPO=Gallery GRADLE_TASK=:app:compileFossReleaseKotlin`.
- `make` threads `PODMAN_RUN_FLAGS` (nested-podman `--cgroups=disabled`) into
  every `run`, never into `build`. `make shell-exec CMD='...'` is the batch twin
  of `shell`.
- Patch/architecture detail and the per-repo pin table: `CLAUDE.md` here.
