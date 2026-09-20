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
./check-comment-only.sh <repo>      # must PASS before staging
```

## Building (heavy — best-effort, largely UNVERIFIED)

```sh
make help              # list targets
make image             # build the Fedora-44 Android/Gradle/JDK builder image
make build             # compile one module (REPO=Commons GRADLE_MODULE=:commons)
make shell             # interactive shell in the builder container
```

> `make image` and `make build` (Commons) are **verified**: the image builds
> (JDK 25 + Android SDK platform 36 / build-tools / platform-tools) and
> `:commons:compileReleaseKotlin` compiles cleanly with the doc patches applied
> (~1m45s). Building an *app* module (`REPO=Gallery GRADLE_MODULE=:app`, …) is
> untested and heavier. See `CLAUDE.md` ("Build status"). The comment-only proof
> needs no build: `./check-comment-only.sh` runs on the host in seconds.

- `make` threads `PODMAN_RUN_FLAGS` (nested-podman `--cgroups=disabled`) into
  every `run`, never into `build`. `make shell-exec CMD='...'` is the batch twin
  of `shell`.
- Patch/architecture detail and the per-repo pin table: `CLAUDE.md` here.
