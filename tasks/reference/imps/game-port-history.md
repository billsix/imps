# Reference: N64 game-port history — per-project detail

> **Provenance:** relocated 2026-09-13 from the N64 family `n64/CLAUDE.md`
> ("Projects" and the crawl-history part of "libultraship — the shared engine") as
> part of the CLAUDE.md trim (`tasks/trim-claude-md.md`). Deliberately kept OUT of
> the tier-3 `n64/<Game>/CLAUDE.md` files (those are themselves ancestor-loaded and
> would re-bloat a game's own sessions — maintainer decision, 2026-09-13).
> `n64/CLAUDE.md` keeps a one-line-per-project index (upstream URL, pin, one-line
> status) and points here for the detailed patch-count / verification-date /
> fork-migration history. The per-project operational facts still live in each
> game's tier-3 `n64/<Game>/CLAUDE.md`.

## Projects

- `n64/OcarinaOfTime/` — Ship of Harkinian
  (https://github.com/HarbourMasters/Shipwright), pinned at `acdbc651d`
  (tip of `develop`, 2026-09-01; submodules libultraship + torch). Details:
  `n64/OcarinaOfTime/CLAUDE.md`. Status: a **488-patch decomp-rename series**
  (3,781 symbols + 18 file renames, one patch per definition file), originally
  ported from the maintainer's old fork as a single 145-file commit, then split
  one-rename-per-commit and finally regrouped for review on 2026-09-08 — the
  regroup is content-neutral (identical tree SHA). Patched tree
  **build-verified on-host 2026-09-01**, container-build- and AppImage-verified
  2026-09-08, and **run on-host 2026-09-08 (William Emerison Six
  <billsix@gmail.com>)**. The old fork's
  docs-only commits were migrated into
  `n64/OcarinaOfTime/CLAUDE.md` + `tasks/reference/ocarina/` per the
  documentation structure above (stale fork-era claims fixed or bannered
  in the move); its submodule-pin changes were dropped as obsolete.
  Also carries a podman build (`Dockerfile` ubuntu-22.04 CI mirror +
  `Makefile` → `out/soh.appimage`, verified nested 2026-09-01 and
  **built + run on-host 2026-09-01 (William Emerison Six
  <billsix@gmail.com>)** — pipeline closed) and a container-verified
  `installdependencies.sh`.
- `n64/MajorasMask/` — 2 Ship 2 Harkinian
  (https://github.com/HarbourMasters/2ship2harkinian), pinned at
  `04a1a4319` (tip of `develop`, 2026-05-31; submodules libultraship +
  ZAPDTR + OTRExporter — pre-torch pipeline). Details:
  `n64/MajorasMask/CLAUDE.md`. Status: two patches — the 64-bit audio/scheduler
  fixes (a strong upstream-submission candidate), exported verbatim from
  the maintainer's old `fedora44Fixes` fork branch and verified
  byte-identical on apply, plus a BUILDING.md fix adding the four
  required audio libraries (upstream candidate, found 2026-09-01 by the
  install-script container verification); patched tree **build- and
  run-verified on-host 2026-09-01 (William Emerison Six
  <billsix@gmail.com>)**. Also carries a
  podman build (`Dockerfile` + `Makefile` → AppImage), ported from the old
  fork's `podmanBuildAppImage` branch as native imps files — the first
  container build in imps; the `ci` variant's AppImage built on-host
  2026-09-01 (William Emerison Six <billsix@gmail.com>).
- `n64/SuperMario64/` — Ghostship
  (https://github.com/HarbourMasters/Ghostship), pinned at `49c5312a`
  (tip of `develop`, 2026-09-01 — deliberately modern: upstream had
  merged the maintainer's always-fly-on-triple-jump cheat, so it needs no
  patch; submodules libultraship 1.3.1-544 + Torch). Details:
  `n64/SuperMario64/CLAUDE.md`. Status: 3-patch cheat series (Super Jump,
  Infinite Air Jumps, Disable Skybox — plus a libshaderc-devel doc fix,
  an upstream candidate) ported 2026-09-01 from the old fork's topic
  branches across upstream's hooks→events restructure; **fully verified
  2026-09-01**: byte-identical on apply, builds in sandbox and on the
  maintainer's host, runs with all three cheats in the menu. Also carries a **Sphinx book** (`SuperMario64/book/`, *How a Production Game
  Is Built* — 16 chapters + appendices, HTML/EPUB/PDF) that `literalinclude`s
  this source by doc-region; see `SuperMario64/CLAUDE.md`. Run
  gotchas (Vulkan-on-RADV hang → OpenGL config; libtcc rpath) recorded
  in `n64/SuperMario64/CLAUDE.md`. The old
  fork's doc set migrated to `tasks/reference/mario64/` (bannered — the
  events restructure postdates them) and its cheat-idea task stubs to
  `tasks/mario64-*.md`; the messy `bill` branch history was deliberately
  not ported. Also carries a podman build (`Dockerfile` ubuntu-24.04 CI
  mirror + `Makefile` → `out/ghostship.appimage`, verified nested
  2026-09-01 and **built on-host 2026-09-01 (William Emerison Six
  <billsix@gmail.com>)**; `run.sh` seeds the OpenGL renderer by default
  for the from-source build (2026-09-06), while a directly-launched
  AppImage still picks Vulkan — see the RADV Vulkan-hang caveat in
  `n64/SuperMario64/CLAUDE.md`) and a
  container-verified `installdependencies.sh`. Also carries a
  **Sphinx book** (`SuperMario64/book/`, *How a Production Game Is Built* —
  16 chapters + appendices, HTML/EPUB/PDF via its own Dockerfile/Makefile) that
  `literalinclude`s this source by doc-region; see `SuperMario64/CLAUDE.md`.
- `n64/BanjoKazooie/` — Lighthouse
  (https://github.com/HarbourMasters/Lighthouse), pinned at `6d30df9a`
  (tip of `develop`, 2026-09-01, just past the 1.0.0 release; submodules
  libultraship 1.3.1-482 + Torch). Details: `n64/BanjoKazooie/CLAUDE.md`.
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
- `n64/libultraship/` — the shared engine (see the "libultraship" section
  above). Docs-only; the reference crawl lives at
  `tasks/reference/libultraship/`.

## libultraship crawl history

The crawl is **complete** (2026-09-01, 18 iterations —
13 release tags + the 4 games' submodule pins + Ghostship's newer fork pin);
the 8-doc set lives at `tasks/reference/libultraship/` with git history as
the time axis, and `tasks/reference/libultraship/crawl.md` holds the protocol
+ iteration log (a game's future LUS pin bump reopens it). Current doc state =
Ghostship's `c151cc91` (1.3.1-544, a KiritoDv FORK branch — see the drift
table's fork-topology caveat).

## Per-game tier-3 detail (relocated 2026-09-14)

> Relocated from the tier-3 `n64/<Game>/CLAUDE.md` files as part of the
> tier-3 CLAUDE.md trim (`tasks/trim-tier3-game-claude-md.md`, follow-on to
> `tasks/trim-claude-md.md`). Those files are ancestor-loaded for a game's own
> sessions, so their long production/verification narrative was moved here (a
> non-loaded reference doc) and replaced with a one-line pointer. Each tier-3
> file keeps the operational facts (patch list, build/run commands, gotchas
> that bite during a build).

### OcarinaOfTime — decomp rename production & verification history

The `patches/personal/0001…0488-*.patch` decomp rename series:

**Squashed 2026-09-08 from 3,799 one-rename-per-commit patches** — that grain
was right for *producing* the work (a breakage localises to one symbol) and
wrong for *reviewing* it. The squash is content-neutral: the pre- and
post-squash trees have the identical SHA and the identical diff from the pin.
Each grouped patch keeps every folded commit's per-symbol justification in its
message, under a header that states the provenance rules once. Method, decisions
and the branches left behind (`squash-backup` is the undo):
[`../../ocarina-deduce-remaining-decomp-names.md`](../../archive/ocarina/2026/09/08/ocarina-deduce-remaining-decomp-names.md),
"Step 9 as executed". Provenance per symbol: **665 adopted from zeldaret/oot**,
**2,844 deduced at HIGH confidence**, **272 deduced as GUESS**.

**Split from a single 6,854-line commit on 2026-09-07**; the split is
content-neutral (only the new comments differ from the pre-split tree), proven
by `tools/prove_comment_only.sh` at the imps root (it has gcc strip the comments
and compares) and gated by `tools/check_renames.py`. Originally ported
2026-09-01 from a fork based at `988b53665`; one conflict resolved in
`z_demo_kankyo.c` (upstream's `Audio_PlaySfxGeneral` rename crossing the series'
`CutsceneCamera_UpdateSpline` rename), and upstream-added identifiers were
checked for references to renamed-away symbols (none). The **pre-split** tree
was build- and run-verified on-host 2026-09-01 (William Emerison Six
<billsix@gmail.com>). The **squashed** series is **container-build-verified
2026-09-08**: `make image` + `make build` in the ubuntu-22.04 CI-mirror image
compiled all 1,581 targets with zero errors and linked `soh.elf`, and
`make appimage` produced `out/soh.appimage` (31 MB, `Ship-9.2.3-jammy`).
`tools/check_renames.py all` and `tools/check_patches_apply.sh` are both green.
It was **built and run on-host 2026-09-08 (William Emerison Six
<billsix@gmail.com>)** using `fetch.sh`/`apply.sh`/`build.sh`; the game launched
and played. One oddity was seen — illegible text on the save prompt — which is
**not** from this series: every one of the 484 changed files, taken at the pin
with the rename map applied and comments stripped, is byte-identical to its HEAD
form with comments stripped, so the series changes identifiers and comments and
nothing else. Suspect the pin (upstream `develop` tip); a pristine
`./fetch.sh && ./build.sh` with no `apply.sh` settles it. Commit messages carry
`Co-Authored-By` and deliberately **no session URL** (runClaudeInContainer
`tasks/suppress-claude-session-trailer.md`). The deduction effort is tracked in
[`../../ocarina-deduce-remaining-decomp-names.md`](../../archive/ocarina/2026/09/08/ocarina-deduce-remaining-decomp-names.md)
and its parent
[`../../archive/ocarina/2026/09/08/ocarina-decomp-rename-and-cleanup.md`](../../archive/ocarina/2026/09/08/ocarina-decomp-rename-and-cleanup.md);
method, the comment convention, and the one-rename-per-commit rule in
[`../ocarina/decomp-renaming.md`](../ocarina/decomp-renaming.md).

**Podman build history.** Created 2026-09-01 per
`../../archive/ocarina/2026/09/01/ocarina-podman-appimage-build.md`, on the
MajorasMask/BanjoKazooie template. Three "the GitHub runner pre-provides it"
gaps surfaced (now in the master drift table): **cmake ≥ 3.26** (jammy apt ships
3.22 → the Kitware repo block, same fix as the maintainer's original 2ship
Dockerfile), **python3** (the asset extractor), and **imagemagick** (the
AppImage icon is generated at configure time by `convert`, silently skipped when
absent — the appimage step then fails on a missing `sohIcon.png`). Verified
nested 2026-09-01: image, `make build` of the patched tree, and `make appimage`
(`out/soh.appimage`, 32 MB) all green. The AppImage was **built and run on-host,
2026-09-01 (William Emerison Six <billsix@gmail.com>)** — the `COPY` Dockerfile
fix cleared the SELinux block that had stopped host builds (see the Dockerfile
comment) — the full pipeline is closed.

### SuperMario64 — cheat-series porting & podman build history

**Patches — ported 2026-09-01 from the old fork's topic branches.** The old
fork's topic branches (`highjump`, `infiniteJump`, `noSkybox`, all based 120+
commits back at `67e561c6`) were linearized into one series and ported across
upstream's hooks→events restructure (`src/port/hooks/` became
`src/port/events/`; the merged fly cheat served as the template for the new
shape). Byte-identical `git am` reproduction verified against the ported branch.
Per-patch port notes: `0001-cheat-high-jump.patch` — events moved into
`src/port/events/list/PlayerEvent.h`; in `check_fall_damage` the event now runs
after upstream's new `PlayerLanded` event (both kept). `0002-cheat-infinite-jumps.patch`
— the cancel field is `Cancelled` (capital) in the events layer; the original
commit's lowercase `cancelled` was fixed during the port.
`0003-disable-skybox.patch` — **slimmed in the port:** upstream now ships a
cancellable `SkyboxRender` event already wired into `level_geo.c`, so the patch
reduces to a listener cancelling that event plus the menu widget.

**libultraship fork caveat (found 2026-09-01 by the LUS crawl).** The pin's LUS
`c151cc91` (1.3.1-544) is a KiritoDv **fork** branch of LUS, not Kenix3
mainline — branch point `f30fe0ed` (1.3.1-463) + 81 fork commits (Vulkan
backend, GPU-side T&L, postprocessing/multipass shaders, RT64 mipmapping, async
texture loading, web/emscripten). The ~23 mainline commits after the branch
point (Context `GetRawInstance` rework, `.meta` priority resolution, several
audio/texture fixes) are absent from it. The crawl's docs at
`../libultraship/` cover this pin as iteration 18 — the current working-tree
state of that doc set (the crawl's final stop).

**Podman build history.** Created 2026-09-01 per
`../../archive/mario64/2026/09/01/mario64-podman-appimage-build.md`, on the
MajorasMask/BanjoKazooie template. `Dockerfile` mirrors upstream CI's
build-linux job (`.github/workflows/main.yml` at the pin, `ubuntu-latest`
resolved to **24.04**): CI's apt line verbatim (including the Vulkan set —
libvulkan/libshaderc/glslang/spirv-tools), python deps **`COPY`d from the
checkout's `libultraship/requirements.txt`** (pip `--break-system-packages` for
noble's PEP668; `COPY` not `RUN --mount=type=bind` on purpose — a build-time
bind mount is read by the confined `container_t` RUN process with the file's
on-disk SELinux label, so a `:Z`-poisoned checkout makes a host-side `podman
build` fail with an MCS-mismatch AVC on `requirements.txt`; `COPY` is read by
buildah as the unconfined host user, immune to the label — fixed 2026-09-01),
SDL 2.30.3 / tinyxml2 10.0.0 / libzip 1.10.1 from source. `GeneratePortO2R` runs
in-container; the `appimage` target also copies `build-cmake/.tcc` to `out/.tcc`
(CI ships it beside the AppImage and hard-fails without it — the scripting
runtime). Two fresh-environment gaps surfaced (in the master drift table):
**cmake ≥ 3.30** (LUS's FindVulkan uses policy CMP0159; noble apt ships 3.28;
runners pre-provide newer → the Kitware repo block), and a **shaderc/spirv-tools
packaging skew on noble**: LUS prefers `shaderc_shared`, Ubuntu names the lib
plain `libshaderc.so`, so cmake fell back to `libshaderc_combined.a` — which is
ABI-skewed against noble's newer spirv-tools static libs (undefined `spvtools::`
at link). The Dockerfile adds a `libshaderc_shared.so` compat symlink so LUS
takes its preferred, self-consistent shared path. Verified nested 2026-09-01:
image, `make build` of the patched tree, and `make appimage`
(`out/ghostship.appimage`, 16 MB, + `.tcc`) all green. The on-host AppImage
build was **confirmed 2026-09-01 (William Emerison Six <billsix@gmail.com>)** —
the `COPY` Dockerfile fix cleared the SELinux block that had stopped host builds
(see the Dockerfile comment). **The OpenGL-default seed lives in `run.sh`, not
in the AppImage** — an AppImage launched directly (not via `run.sh`) still
auto-picks Vulkan on first run, so the RADV Vulkan-hang caveat applies to it:
switch to OpenGL in the menu if it goes silent after "Vulkan device:". This is
accepted, not a bug — the podman AppImage exists only to mirror upstream's CI/CD;
the maintainer's own play path is a from-source build run via `run.sh`, which is
seeded. The default-to-OpenGL task:
`../../archive/mario64/2026/09/06/mario64-default-to-opengl-backend.md`.

### BanjoKazooie — patch-series export & podman build history

**Patches.** Exported 2026-09-01 from the maintainer's `fixOnFedora` branch
(same base as the pin) — this series was **submitted upstream as a PR and
reviewed by JeodC** (patch 0004 is the review round), so when it merges, the
series retires at the next pin bump. Patch 0002's commit subject was repaired
during export (the original commit had lost its subject line to a formatting
accident; the intended message survived in the maintainer's draft). Byte-identical
to `fixOnFedora` verified on apply.

**Podman build history.** Created 2026-09-01 per the banjo-podman-appimage-build
task (archived at `../../archive/banjo/2026/09/01/banjo-podman-appimage-build.md`),
on the MajorasMask template. `Dockerfile` mirrors upstream CI's `build-linux` job
(`.github/workflows/main.yml` at the pin): base **ubuntu:24.04** (CI says
`ubuntu-latest`, which has resolved to the 24.04 LTS since early 2025 — recorded
in the Dockerfile header), the workflow's apt list inlined (Lighthouse has no
apt-deps.txt file), and SDL 2.30.3 / tinyxml2 10.0.0 / libzip 1.10.1 (no crypto)
built from source. The Makefile builds `GeneratePortO2R` in-container (CI uses a
separate Torch job + artifact download; same result), then the game, then
`cpack -G External` → `out/lighthouse.appimage`. Verified 2026-09-01: `make image`
(1.08 GB), `make build` of the patched tree (17 MB binary), and `make appimage`
(`out/lighthouse.appimage`, 12.5 MB) all green nested in the sandbox, and
**`make run` confirmed working on the maintainer's host** — the full pipeline is
closed.

### MajorasMask — patch export & podman build history

**Patches.** `patches/0001` (the audio/scheduler fixes) was exported verbatim
2026-09-01 from the maintainer's old fork branch (`fedora44Fixes`, same base) and
verified byte-identical on apply; patched tree build- and run-verified on-host
2026-09-01 (William Emerison Six <billsix@gmail.com>). `patches/0002` (the
BUILDING.md audio-libs fix) was found by the install-script fresh-container
verification.

**Podman build history.** Ported 2026-09-01 from the maintainer's old fork's
`podmanBuildAppImage` branch (2 commits: "Added Bill's Dockerfile based on the
github action" + "updated to ubuntu 26.04") — as **native imps files, not
patches**, per the patches-carry-code-only principle. The branch's two Dockerfile
versions were kept as **two selectable variants** instead of the second
overwriting the first (`Dockerfile` = `VARIANT=ci`, ubuntu 22.04 gcc-12 pin
Kitware cmake; `Dockerfile.ubuntu26.04` = `VARIANT=2604`, ubuntu 26.04
distro-default gcc-15/cmake). Both: apt list `COPY`d from the checkout's
`.github/workflows/apt-deps.txt`, SDL 2.30.3 / tinyxml2 10.0.0 / libzip 1.10.1
from source; each variant its own image tag. The branch's v2 also dropped
`--userns=keep-id` from the `shell` target only; with one shared Makefile that
difference was deliberately NOT carried — `shell` keeps `--userns=keep-id` in
both variants. Makefile adapted for the imps layout (`SRC` = `2ship2harkinian/`;
`make image` passes the checkout as the build context so the apt-deps bind mount
resolves + auto-runs `fetch.sh`; standard `PODMAN_RUN_FLAGS` added and threaded
into `run`; the old branch's `.gitignore` hunk became this folder's `.gitignore`
entries). `make build`/`make appimage` compile the checkout as-is into
`2ship2harkinian/build-cmake`; `make run` executes the AppImage from the shared
`runDir/`. The default (`ci`, ubuntu-22.04) variant's AppImage build was
**confirmed on-host 2026-09-01 (William Emerison Six <billsix@gmail.com>)** — the
`COPY` Dockerfile fix having cleared the SELinux block that stopped host builds;
the `2604` variant and an on-host run of the AppImage were not exercised.
