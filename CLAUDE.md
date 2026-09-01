# imps — Island of Misfit Patches Storage

Patch carrier for third-party projects, replacing maintained forks. The
maintainer has git work he wants applied to other people's projects without
managing GitHub forks of them: imps stores the patch series plus the scripts
that fetch pristine upstream source at a pinned commit, apply the patches,
and build/run the result — eventually both on the host and in a podman
container. One folder per project; each folder is self-contained.

## Documentation structure — three tiers, docs live in imps, patches carry code

The dividing principle: **a patch carries only what must live inside
upstream's own files — code. Everything that is purely the maintainer's
(CLAUDE.md content, task docs, reference docs) lives natively in imps**,
where editing it is a plain file edit (no patch regeneration), it exists
whether or not a checkout does, and it never rides along in a pin-bump
rebase.

The tiers, exploiting Claude Code's ancestor CLAUDE.md loading (a session
working anywhere under `imps/`, including deep inside a project's checkout,
auto-loads every CLAUDE.md on the path from cwd to the repo root):

1. **`CLAUDE.md` (this file, the master)** — lean: what imps is, the
   contracts, and a one-line-per-project index pointing at tier 2.
2. **`<Project>/CLAUDE.md`** — that project's operational facts: upstream
   URL, pin and why it sits there, the patch list one line each, build/run
   gotchas, and an index of its tier-3 reference docs. Sits OUTSIDE the
   checkout but is its ancestor, so it auto-loads exactly when a session
   works inside that project.
3. **`tasks/reference/<project>/*.md`** — the deep-dive reference docs,
   one subdirectory per project (e.g. `tasks/reference/ocarina/`). Pointed
   at from tier 2 — plain pointers, not `@`-imports, so one project's
   large doc set never bloats sessions about another project.

`tasks/` is shared across all projects at the imps root (this repo is the
one that versions them): in-flight task docs at `tasks/*.md` (named with a
project prefix, e.g. `ocarina-…`), reference docs namespaced per project
as above. **Archives are per-project — this overrides the global
convention's flat date layout for this repo** (decided with William
Emerison Six <billsix@gmail.com>, 2026-09-01): a completed task moves to
`tasks/archive/<project>/<YYYY>/<MM>/<DD>/<slug>.md` — project first, then
the standard date buckets. Repo-wide tasks (not about one game) use
`imps` as their project directory.

## Per-project folder contract

- `fetch.sh` — clone upstream (URL and pinned full base SHA live in this
  script, the SHA commented with its date and the upstream branch it was
  taken from), checkout the pin, `git submodule update --init --recursive`.
  Idempotent; never destroys local branches or committed work.
- `build.sh` — host build; calls `fetch.sh` when the checkout is missing, so
  it is the only command a fresh clone needs.
- `run.sh` — launch the installed binary with `runDir/` as the game's cwd
  (saves, config, logs, extracted assets accumulate there).
- `README.md` — human-facing, commands-forward: the fetch/apply/build/run
  sequence and the clean-rebuild recipe at the top, caveats as one-liners.
- `CLAUDE.md` — the tier-2 per-project doc (see "Documentation structure").
- `apply.sh` — `git am --3way` of `patches/*.patch` onto the checkout;
  guarded to run only when HEAD is exactly at the pin (it reads the pin out
  of `fetch.sh`, the single source of truth). Optional: skipping it gives a
  pristine upstream build.
- `patches/` — numbered `git format-patch` series (with `base-commit:`
  footers naming the pin), **code changes only** per the dividing principle
  above. Regenerate after editing commits in the checkout with
  `git format-patch --no-cover-letter --base=<pin> <pin>..HEAD -o patches/`.
- `.gitignore` — the upstream checkout, `build-cmake/`, `bldInstall/`, and
  `runDir/` are all untracked.
- Optionally a **podman build**: `Dockerfile` + `Makefile` (native imps
  files, never patches) derived from the project's own CI workflow —
  `make image/build/appimage/run`, image context = the checkout,
  `PODMAN_RUN_FLAGS` threaded into every `run` (never `build`), and where
  multiple base images exist, a `VARIANT` switch with per-variant image
  tags. `MajorasMask/` is the reference implementation.

## Patch philosophy — upstream first, personal second

(William Emerison Six <billsix@gmail.com>, 2026-09-01.) The project has
two goals, ranked:

1. **Upstreaming is the ultimate goal.** If a change is something
   upstream would plausibly accept — a bug fix, a portability fix, a doc
   correction — shape it as a **standalone, submission-ready patch**:
   its own commit, a commit message written for an upstream reviewer
   (problem → cause → fix, like the banjo series), no entanglement with
   personal changes. Never fold an upstreamable fix into a personal
   patch, and split a mixed change into two patches rather than ship one
   hybrid. Mark upstream candidates as such in the per-project
   CLAUDE.md patch list.
2. **Personal patches are maintained independently, indefinitely.**
   Changes upstream won't take (cheats, personal tweaks) are carried in
   the same series and **replayed onto newer upstream pins as time
   progresses** — that replay (the pin-bump operation below) is a core
   workflow, not an afterthought.

Lifecycle consequence: an upstreamable patch is temporary — once merged
upstream, it retires at the next pin bump (the bump's `git am` will show
it as already applied, or the rebase drops it); a personal patch is
permanent and its long-term rebase cost is a design consideration when
writing it (prefer hooking the port's event/enhancement layers over
editing decomp internals — the mario64 cheats are the worked example).

## Derived artifacts — where drift occurs, and what the source of truth is

(Maintainer request, 2026-09-01.) Much of imps is DERIVED from files
inside the pinned checkouts. Those copies are correct **at the pin** and
rot silently when the pin moves — so **every pin bump must re-verify each
derived artifact against its source** (this is part of the pin-bump
operation in the agent contract below). The pairs:

| Derived artifact (imps) | Source of truth (in the checkout) | Drift notes |
|---|---|---|
| `<Project>/Dockerfile` | the upstream CI workflow's Linux job (Shipwright: `generate-builds.yml`; 2ship/Lighthouse/Ghostship: `main.yml` build-linux) | from-source lib versions (SDL 2.30.3, tinyxml2 10.0.0, libzip 1.10.1), base-OS choice, build flags — all hand-copied. Where a deps list exists as a FILE it is `COPY`d from the checkout at image build (2ship `apt-deps.txt`, Shipwright `linux-build-deps/apt.txt`, Ghostship `libultraship/requirements.txt`) and stays auto-current; the inline extras and steps do not. (`COPY`, not `RUN --mount=type=bind` — a build-time bind mount is read by the confined `container_t` RUN process with the file's on-disk SELinux label, so a `:Z`-poisoned checkout fails a host-side `podman build` with an MCS-mismatch AVC and a build mount has no relabel step; `COPY` is read by buildah as the unconfined host user. Fixed across all four Dockerfiles 2026-09-01.) Also: runner images pre-provide tools a bare base lacks (modern cmake on 22.04 and ≥3.30 on 24.04 → the Kitware blocks; python3; imagemagick for SoH's configure-time AppImage icon; noble's shaderc/spirv-tools ABI skew → the libshaderc_shared.so symlink) — CI won't notice those needs changing, we must. |
| `<Project>/installdependencies.sh` | `docs/BUILDING.md` Fedora section (Lighthouse/2ship/Ghostship) or `linux-build-deps/dnf.txt` (Shipwright) | list is inlined by design (works before first fetch) — re-diff against the doc at every pin bump. Some lines are OURS via patches (banjo SDL2_net = patch 0001; mario libshaderc = patch 0004; mm audio libs ogg/vorbis/opus/opusfile = patch 0002): derive from the PATCHED doc, and if upstream merges those patches, the doc and script converge on their own. |
| `<Project>/build.sh` + `Makefile` build targets | upstream CMake target names and flags (`GenerateSohOtr` / `Generate2ShipOtr` / `GeneratePortO2R`, `BUILD_REMOTE_CONTROL`, `cpack -G External`, Ghostship's `.tcc` dir) | target names have changed across pins before (ocarina's ZAPDTR→torch restructure); check them each bump. |
| `patches/*.patch` | upstream code itself | the core case — covered by the pin-bump rebase procedure. |
| `tasks/reference/<project>/` docs | the pinned source | covered by per-doc provenance banners. |
| pin comments in `fetch.sh` (date, describe, "tip of develop") | the `PIN_SHA` itself | update the prose when updating the SHA. |
| per-project `CLAUDE.md` facts (submodule SHAs, patch lists, gotchas) | the checkout + `patches/` | re-verify at every pin bump and series change. |
| `libultraship/fetch.sh` `PIN_SHA` | the crawl iteration log in `tasks/reference/libultraship/crawl.md` | the two advance together, one commit per iteration; check fork topology (`git merge-base`) before assuming a new pin descends from the documented one. |
| the FUTURE upstream-container-CI patches (`tasks/*-upstream-container-ci.md`) | both the Dockerfile AND the workflow | double-derived; their acceptance strategy requires re-checking fidelity against whatever CI looks like at submission time. |

## Working on a project — agent contract

- **Assume the patches are applied.** The default working state of a
  project's checkout is the pin plus the full `patches/` series. Verify
  before starting (`git log --oneline` in the checkout should show the
  series' subjects on top of the pin); if it's at the bare pin, run
  `./apply.sh` first.
- **Never build a checkout from a foreign toolchain via a bind mount —
  copy the source into the throwaway container first.** libultraship at
  1.3.1-482+ (banjo, mario) writes build artifacts INTO its submodule
  source dir even for an out-of-tree configure, so a fedora:44
  verification container that builds `-S /proj/<checkout> -B /tmp/b`
  leaves Fedora-compiled `.a`s inside the checkout, and the next podman
  (ubuntu) build silently reuses them — bit us 2026-09-01 as a
  `libmonocypher.a … can not be used when making a PIE object` link
  failure in mario's `make build`. Recovery: `git clean -fdx` in the
  submodule (+ `git checkout --` any tracked file the build overwrote,
  e.g. Ghostship's `src/generate_keys_header`) and wipe `build-cmake/`.
- **The deliverable of any work is patches, never checkout state.** Do the
  work as commits in the checkout (repo-local unsigned commits — see
  Rules), then regenerate the series
  (`git format-patch --no-cover-letter --base=<pin> <pin>..HEAD -o patches/`)
  and stage the patch files in imps. The checkout is disposable scaffolding;
  if the patches don't reflect the work, the work doesn't exist.
- **Pin bumps are a defined operation** the maintainer will request: fetch
  upstream, apply the existing series onto the new commit (`git am --3way`
  on a branch at the candidate SHA), resolve conflicts, check for
  non-textual breakage (e.g. upstream-added references to symbols the
  series renames), build and run, then update the `PIN_SHA` in `fetch.sh`
  (the variable is named `PIN_SHA` in every project), regenerate the
  patches, and refresh the pin references and provenance banners in the
  docs — one unit, staged together.

## Rules

- Scripts start with `cd "$(dirname "$0")"` and use only relative paths —
  runnable from anywhere, no hardcoded home/host paths.
- Moving a pin is a deliberate act: after any pin bump, re-verify the patch
  series applies and the project builds before committing the new SHA.
- ROM/asset acquisition is out of scope — each game's own in-app extraction
  handles it in `runDir/`. Never commit the upstream checkout or anything
  ROM-derived.
- **Unsigned commits in checkouts/scratch clones are authorized and
  automated** (William Emerison Six <billsix@gmail.com>, 2026-09-01): the
  maintainer's gitconfig enables commit signing, which fails in the
  sandbox — and a failed signature aborts `git am` mid-series. **Every
  project's `fetch.sh` therefore sets `commit.gpgsign false` repo-locally
  in the checkout it manages** — never in the global gitconfig. For
  throwaway scratch clones, do the same by hand (`git config
  commit.gpgsign false`, or per-command `git -c commit.gpgsign=false`).
  These commits are scaffolding; the durable product is the patch files.

## Projects

- `OcarinaOfTime/` — Ship of Harkinian
  (https://github.com/HarbourMasters/Shipwright), pinned at `acdbc651d`
  (tip of `develop`, 2026-09-01; submodules libultraship + torch). Details:
  `OcarinaOfTime/CLAUDE.md`. Status: one code patch (a 145-file decomp
  rename), ported from the maintainer's old fork; patched tree
  **build-verified on-host 2026-09-01 (William Emerison Six
  <billsix@gmail.com>)**. The old fork's
  docs-only commits were migrated into
  `OcarinaOfTime/CLAUDE.md` + `tasks/reference/ocarina/` per the
  documentation structure above (stale fork-era claims fixed or bannered
  in the move); its submodule-pin changes were dropped as obsolete.
  Also carries a podman build (`Dockerfile` ubuntu-22.04 CI mirror +
  `Makefile` → `out/soh.appimage`, verified nested 2026-09-01 and
  **built + run on-host 2026-09-01 (William Emerison Six
  <billsix@gmail.com>)** — pipeline closed) and a container-verified
  `installdependencies.sh`.
- `MajorasMask/` — 2 Ship 2 Harkinian
  (https://github.com/HarbourMasters/2ship2harkinian), pinned at
  `04a1a4319` (tip of `develop`, 2026-05-31; submodules libultraship +
  ZAPDTR + OTRExporter — pre-torch pipeline). Details:
  `MajorasMask/CLAUDE.md`. Status: two patches — the 64-bit audio/scheduler
  fixes (a strong upstream-submission candidate), exported verbatim from
  the maintainer's old `fedora44Fixes` fork branch and verified
  byte-identical on apply, plus a BUILDING.md fix adding the four
  required audio libraries (upstream candidate, found 2026-09-01 by the
  install-script container verification); patched tree **build- and
  run-verified on-host 2026-09-01 (William Emerison Six
  <billsix@gmail.com>)**. Also carries a
  podman build (`Dockerfile` + `Makefile` → AppImage), ported from the old
  fork's `podmanBuildAppImage` branch as native imps files — the first
  container build in imps.
- `SuperMario64/` — Ghostship
  (https://github.com/HarbourMasters/Ghostship), pinned at `49c5312a`
  (tip of `develop`, 2026-09-01 — deliberately modern: upstream had
  merged the maintainer's always-fly-on-triple-jump cheat, so it needs no
  patch; submodules libultraship 1.3.1-544 + Torch). Details:
  `SuperMario64/CLAUDE.md`. Status: 3-patch cheat series (Super Jump,
  Infinite Air Jumps, Disable Skybox — plus a libshaderc-devel doc fix,
  an upstream candidate) ported 2026-09-01 from the old fork's topic
  branches across upstream's hooks→events restructure; **fully verified
  2026-09-01**: byte-identical on apply, builds in sandbox and on the
  maintainer's host, runs with all three cheats in the menu. Run
  gotchas (Vulkan-on-RADV hang → OpenGL config; libtcc rpath) recorded
  in `SuperMario64/CLAUDE.md`. The old
  fork's doc set migrated to `tasks/reference/mario64/` (bannered — the
  events restructure postdates them) and its cheat-idea task stubs to
  `tasks/mario64-*.md`; the messy `bill` branch history was deliberately
  not ported. Also carries a podman build (`Dockerfile` ubuntu-24.04 CI
  mirror + `Makefile` → `out/ghostship.appimage`, verified nested
  2026-09-01 and **built on-host 2026-09-01 (William Emerison Six
  <billsix@gmail.com>)** — launches on the Vulkan backend, see the RADV
  Vulkan-hang caveat in `SuperMario64/CLAUDE.md`) and a
  container-verified `installdependencies.sh`.
- `BanjoKazooie/` — Lighthouse
  (https://github.com/HarbourMasters/Lighthouse), pinned at `6d30df9a`
  (tip of `develop`, 2026-09-01, just past the 1.0.0 release; submodules
  libultraship 1.3.1-482 + Torch). Details: `BanjoKazooie/CLAUDE.md`.
  Status: 4-patch series exported from the maintainer's `fixOnFedora`
  branch (Fedora build-deps doc fix, bk.o2r version stamp, the
  post-ROM-import freeze fix, and a JeodC review round — the series is a
  submitted upstream PR and retires if merged); patch 0002's lost commit
  subject repaired during export; verified byte-identical on apply, and
  the patched tree **builds and runs** (2026-09-01: compiled in the
  podman builder nested; AppImage `make run` confirmed on the
  maintainer's host). Also carries a podman build (`Dockerfile`
  ubuntu-24.04 CI mirror + `Makefile`, derived from upstream's
  `main.yml` build-linux job) — verified end to end
  (image/build/appimage/run); its task is archived at
  `tasks/archive/banjo/2026/09/01/`. The `bill` branch's doc set (8 reference docs + the
  freeze investigation) migrated to `tasks/reference/banjo/`.
- `libultraship/` — the shared engine under all four ports
  (https://github.com/Kenix3/libultraship). Docs-only project: no
  patches, no build scripts — `fetch.sh` pins whichever commit the
  reference-doc crawl currently describes. The crawl is **complete**
  (2026-09-01, 18 iterations — 13 release tags + the 4 games' submodule
  pins + Ghostship's newer fork pin); the 8-doc set lives at
  `tasks/reference/libultraship/` with git history as the time axis,
  and `tasks/reference/libultraship/crawl.md` holds the protocol +
  iteration log (a game's future LUS pin bump reopens it). Current
  doc state = Ghostship's `c151cc91` (1.3.1-544, a KiritoDv FORK
  branch — see the drift table's fork-topology caveat).
