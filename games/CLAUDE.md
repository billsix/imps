# games — buildable open-source game/engine ports family

The `games/` family carries patch series on top of **buildable open-source games
and engines** — real C/C++/etc. source you fetch pristine at a pin, patch, and
**compile in a container**. It is a **code-patch** family, the same KIND as
`n64/` (real patch streams that change upstream code), NOT a documentation-only
carrier like `unixutils/`/`android/`. This tier-2 `CLAUDE.md` holds the family's
build/patch contract and its per-project index; it auto-loads (Claude Code's
ancestor-`CLAUDE.md` loading) for any session working under `games/`, and only
those. The cross-family principles — what imps is, the four doc tiers, the patch
philosophy, the unsigned-commits rule, the `tasks/`-keying convention — live in
the master `CLAUDE.md` at the imps root.

## Build/patch contract — the per-project machinery

The master `CLAUDE.md` states the generic self-contained-folder contract
(`fetch.sh`/`apply.sh` + `patches/` + docs). The `games/` family adds:

- **`fetch.sh`** clones each upstream at a pinned commit into a **gitignored
  `checkout/`** (a game may need more than one repo — e.g. an engine plus a
  music/codec dependency — cloned side by side as `checkout/<name>/`). Each pin
  is a `*_PIN_SHA` variable, commented with its tag and the date it was resolved;
  `commit.gpgsign false` is set repo-locally in every clone (a failed signature
  aborts `git am` mid-series). Idempotent.
- **`apply.sh`** `git am --3way`s the `patches/` **streams** onto the primary
  checkout, guarded to run only at the pin (reads the `*_PIN_SHA` out of
  `fetch.sh`, the single source of truth). Streams and `patches/ORDER` work
  exactly as in `n64/CLAUDE.md` (within a stream order matters, across streams it
  doesn't; disjoint files commute). A dependency built only to link against
  (ZMusic for GZDoom) is fetched pristine and **never patched** — one lane only.
- **`installdependencies.sh` + `build.sh` + `run.sh`** — the native host-build
  baseline (master `CLAUDE.md`): install the game's build deps on the host, build
  it (into `bldInstall/<BUILD_TYPE>/` beside the scripts) and run it, **with no
  container**. `build.sh` self-fetches when the checkout is missing, so with
  `installdependencies.sh` a fresh clone needs only `./build.sh`. This is the
  **primary** build path; the Dockerfile/Makefile below are an extra layer.
- **`Dockerfile` + `Makefile`** (native imps files, not patches — the *optional*
  container build). The image carries only the toolchain + the game's build deps;
  **the source is bind-mounted, never baked** — so host edits and applied
  patches propagate without an image rebuild, and
  `checkout/`/`build/`/`install/` stay gitignored.
  Standard targets: `fetch`, `apply`, `image`, `build` (Release default,
  `BUILD_TYPE` overridable), `run` (launch the built game with a CLI-passed data
  file; X/Wayland passthrough, or Xvfb headless for a no-display smoke run),
  `shell`/`shell-exec` (sharing one `SHELL_RUN_FLAGS` block so batch and
  interactive can't drift), `image-export`/`image-import`, `help`. `PODMAN_RUN_FLAGS`
  (the `NESTED_PODMAN`-keyed `--cgroups=disabled`) is threaded into every
  `run` — **never `build`** (`podman build` rejects `--cgroups`).

## Game DATA is the maintainer's own — NEVER committed

Same rule as the N64 ROMs (master `CLAUDE.md`): the build ships the **engine + its
bundled resources only**; the maintainer supplies the game data (WADs/IWADs,
ROMs) at run time. Data lives under a gitignored `runDir/` (or is bind-mounted
read-only into `run`/`smoke`); it is never committed and its host location is
never recorded in a committed file.

## Projects

One line each (upstream URL, pin, one-line status). Per-project operational facts
are in each game's tier-3 `games/<Game>/CLAUDE.md`; deep dives in
`tasks/reference/<game>/`.

- `games/gzdoom/` — GZDoom, the open-source Doom-engine source port
  (https://github.com/ZDoom/gzdoom, pin `g4.14.2`), built with its ZMusic
  dependency (https://github.com/ZDoom/ZMusic, pin `1.3.0`). Builds + launches
  natively on the host (`installdependencies.sh`/`build.sh`/`run.sh`) or in a
  Fedora-44 container; carries a comment-only `patches/book/` doc-region stream
  feeding the Sphinx book *How a Doom Engine Works* (`games/gzdoom/book/`), and a
  CLI-WAD-loading fix is the planned code stream. Details: `games/gzdoom/CLAUDE.md`.
