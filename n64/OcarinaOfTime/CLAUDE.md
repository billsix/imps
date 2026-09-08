# OcarinaOfTime — Ship of Harkinian (OoT PC port), under imps

Shipwright / **SoH** is a PC/console port of *The Legend of Zelda: Ocarina of
Time* — the original "Ship of Harkinian" port (Ghostship, the SM64 port,
derived its approach from this). It combines the **OoT decomp** (`soh/src/`,
zeldaret/oot lineage), a **C++ port layer** (`soh/soh/`, `OTRGlobals` the
central glue), and the **libultraship** runtime (`libultraship/` submodule).

Managed by imps: `Shipwright/` here is a pristine clone of
https://github.com/HarbourMasters/Shipwright, pinned by `fetch.sh` at
`acdbc651d` (9.2.3-421, tip of upstream `develop` as of 2026-09-01), with the
maintainer's patches applied by `apply.sh`. It is not a fork and has no
personal branches — the patch series is the whole delta.

## Scripts

- `./installdependencies.sh` — dnf install of the Fedora build deps
  (inline list; run once, as root). Verified 2026-09-01 in a fresh
  fedora:44 container: script + full configure + o2r + build all green.
- `./fetch.sh` — clone if missing, checkout the pin, init submodules.
- `./apply.sh` — `git am` the series (refuses unless HEAD is at the pin).
- `./build.sh` — cmake+ninja → `bldInstall/` (fetches first if needed).
- `./run.sh` — launch `bldInstall/soh.elf` with `runDir/` as cwd.

## Patches

**Stream order is pinned here — `personal` FIRST.** `patches/ORDER` lists it,
and `apply.sh` honours that. The renames touch 3,781 symbols and 18 filenames, so
**any stream added later must be written against the renamed tree**; without the
pin, a future `book/` stream would sort alphabetically ahead of `personal/` and
try to patch symbols that no longer exist under those names. The stream folders
stay separate regardless — that is what keeps `upstream-candidates/` submittable
on its own (see `../CLAUDE.md`).

- `patches/personal/0001…0488-*.patch` — the decomp rename series, **one
  file per patch**: patch 0001 renames the 18 address-named
  `soh/src/code/code_<addr>.c` files, and each of the other 487 names every
  address-named symbol in one definition file (156 of those files hold a single
  symbol). **Squashed 2026-09-08 from 3,799 one-rename-per-commit patches** —
  that grain was right for *producing* the work (a breakage localises to one
  symbol) and wrong for *reviewing* it. The squash is content-neutral: the
  pre- and post-squash trees have the identical SHA and the identical diff from
  the pin. Each grouped patch keeps every folded commit's per-symbol
  justification in its message, under a header that states the provenance rules
  once. Method, decisions and the branches left behind (`squash-backup` is the
  undo):
  [`../../tasks/ocarina-deduce-remaining-decomp-names.md`](../../tasks/archive/ocarina/2026/09/08/ocarina-deduce-remaining-decomp-names.md),
  "Step 9 as executed". Provenance per symbol:
  **665 adopted from zeldaret/oot**, **2,844 deduced at HIGH confidence**,
  **272 deduced as GUESS**. Every renamed symbol carries a
  provenance comment at its definition **and** a short `// was func_… [oot]`
  / `[LLM:HIGH]` tag at each header declaration (and, for a guess, at every
  call site), so a reader of `functions.h` can tell an upstream name from one
  of our deductions. `git grep '\[LLM:'` lists every place the decomp leans on
  an inference. `tools/check_renames.py series` gates the whole series on one
  property: **no rename may happen that its commit message does not account
  for**, and every claimed rename must be total.
  **Every address-named symbol in the tree now has a name except four**, all in
  declared exclusions: `func_800FBCE0` / `func_800FBFD8` (the RCP block in
  `code_800FBCE0.c`) and `func_80837C0C` / `func_80838940` (`z_player.c`).
  Segmented asset addresses (`D_0xxxxxxx`) and OTR asset identifiers are out of
  scope by construction — the identifier IS the archive key.
  **Split from a single 6,854-line commit on 2026-09-07**; the split is
  content-neutral (only the new comments differ from the pre-split tree),
  proven by `tools/prove_comment_only.sh` at the imps root (it has gcc strip
  the comments and compares) and gated by `tools/check_renames.py`.
  Originally ported 2026-09-01 from a fork based at `988b53665`; one
  conflict resolved in `z_demo_kankyo.c` (upstream's `Audio_PlaySfxGeneral`
  rename crossing the series' `CutsceneCamera_UpdateSpline` rename), and
  upstream-added identifiers were checked for references to renamed-away
  symbols (none). The **pre-split** tree was build- and run-verified
  on-host 2026-09-01 (William Emerison Six <billsix@gmail.com>); the split
  series has **not** been rebuilt or re-run on-host yet — it builds clean
  in-sandbox (`soh.elf` links) and `tools/check_renames.py all` is green.
  The deduction effort is tracked in
  [`../../tasks/ocarina-deduce-remaining-decomp-names.md`](../../tasks/archive/ocarina/2026/09/08/ocarina-deduce-remaining-decomp-names.md)
  and its parent
  [`../../tasks/ocarina-decomp-rename-and-cleanup.md`](../../tasks/ocarina-decomp-rename-and-cleanup.md);
  method, the comment convention, and the one-rename-per-commit rule in
  [`../../tasks/reference/ocarina/decomp-renaming.md`](../../tasks/reference/ocarina/decomp-renaming.md).

## Version notes

- **libultraship pinned at `1.3.1-486` (`62e973ae`)**, `torch` at
  `v1.0.0-427`. Upstream replaced the old ZAPDTR/OTRExporter asset pipeline
  with torch (`soh-torch` extractor + `soh-o2r-packer`) between the old fork
  base and this pin — the asset-pipeline and build-system reference docs
  predate that and carry stale-warning banners.
- Archives are **`.o2r` (ZIP)** now, not `.otr` (MPQ) — old "OTR" naming is
  a generation behind.

## Architecture reference (read to get oriented without re-reading the code)

Deep, standing reference docs in **`../../tasks/reference/ocarina/`** — start
with the overview, pull the subsystem doc you need. Each carries a
provenance banner (authored at the old base, `988b53665`); spot-check
details against the pinned checkout.

- [`architecture-overview.md`](../../tasks/reference/ocarina/architecture-overview.md) —
  **read first.** The three bodies of code, the coroutine frame loop, the
  two seams (`__OTR__`/GbiWrap for graphics+assets, GameInteractor for
  behavior hooks).
- [`decomp-map.md`](../../tasks/reference/ocarina/decomp-map.md) — "where does
  X live" in the OoT decomp: GameState, actors-as-overlays (+ `ActorDB`),
  `z_player.c`, collision/camera/scenes.
- [`port-layer.md`](../../tasks/reference/ocarina/port-layer.md) — `soh/soh/`:
  `OTRGlobals`, the frame loop, CVars, the resource/OTR glue, SaveManager,
  `stubs.c`.
- [`libultraship-integration.md`](../../tasks/reference/ocarina/libultraship-integration.md) —
  how SoH consumes LUS (written at 1.3.1-463; now 1.3.1-486).
- [`asset-pipeline.md`](../../tasks/reference/ocarina/asset-pipeline.md) —
  **stale: describes the pre-torch ZAPD/OTRExporter pipeline.**
- [`frame-interpolation.md`](../../tasks/reference/ocarina/frame-interpolation.md) —
  how the fixed OoT tick is decoupled from render FPS.
- [`enhancements-gui-rando.md`](../../tasks/reference/ocarina/enhancements-gui-rando.md) —
  GameInteractor (hooks + `VB_*` overrides), SohGui, the randomizer.
- [`build-system.md`](../../tasks/reference/ocarina/build-system.md) —
  **stale: pre-torch CMake/submodule graph.**
- [`decomp-renaming.md`](../../tasks/reference/ocarina/decomp-renaming.md) —
  how to rename `func_/D_` symbols safely; read before touching the
  decomp-rename task.
- [`../../tasks/reference/imps/squashing-a-produced-series-for-review.md`](../../tasks/reference/imps/squashing-a-produced-series-for-review.md)
  — repo-wide: how a series produced at one change per commit is regrouped into
  reviewable units without losing the per-commit reasoning, and how to prove the
  regrouping changed history only. The Ocarina rename series is the worked
  example.

Upstream human-facing docs live in `Shipwright/docs/` (BUILDING, MODDING,
VERSIONING, CUSTOM_MUSIC).

## libultraship reference docs

The crawl set at `../../tasks/reference/libultraship/` documents this
project's exact LUS pin (`62e973ae`, 1.3.1-486) as **iteration 17** —
the working tree shows a newer pin, so read it via git history
(`git log --oneline -- tasks/reference/libultraship/`, commit
"1.3.1-486 (62e973ae)").

## Podman build (Dockerfile + Makefile)

Created 2026-09-01 per `../../tasks/archive/ocarina/2026/09/01/ocarina-podman-appimage-build.md`, on
the MajorasMask/BanjoKazooie template. `Dockerfile` mirrors upstream
CI's linux job (`.github/workflows/generate-builds.yml` at the pin,
**ubuntu-22.04**): the apt list is **`COPY`d from the checkout's
own `linux-build-deps/apt.txt`** at image build (stays auto-current;
`COPY` not `RUN --mount=type=bind` — the latter is read by the confined
`container_t` RUN process and fails on a `:Z`-poisoned checkout, see the
SuperMario64 Dockerfile comment, fixed 2026-09-01);
SDL 2.30.3, SDL2_net 2.2.0 (CI's local action), tinyxml2 10.0.0, and
libzip 1.10.1 (no crypto) built from source, shadowing the apt ones the
way CI does. Build flags mirror CI: Release + `BUILD_REMOTE_CONTROL=1`;
`GenerateSohOtr` runs in-container (CI uses a separate job + artifact).

Three "the GitHub runner pre-provides it" gaps surfaced (now in the
master drift table): **cmake ≥ 3.26** (jammy apt ships 3.22 → the
Kitware repo block, same fix as the maintainer's original 2ship
Dockerfile), **python3** (the asset extractor), and **imagemagick**
(the AppImage icon is generated at configure time by `convert`,
silently skipped when absent — the appimage step then fails on a
missing `sohIcon.png`).

Verified nested 2026-09-01: image, `make build` of the patched tree,
and `make appimage` (`out/soh.appimage`, 32 MB) all green. The AppImage
was **built and run on-host, 2026-09-01 (William Emerison Six
<billsix@gmail.com>)** — the `COPY` Dockerfile fix cleared the SELinux
block that had stopped host builds (see the Dockerfile comment) — the
full pipeline is closed.

## Tools

- `tools/check_renames.py` — gate for the decomp-renaming conventions.
  Subcommands `traceable` (every rename cited, none half-done),
  `declarations` (every header declaration tagged), `series` (one rename per
  commit, every rename total), `all`. Run it after any rename batch; the
  method it enforces is
  [`../../tasks/reference/ocarina/decomp-renaming.md`](../../tasks/reference/ocarina/decomp-renaming.md).
- `tools/tag_declarations.py` — adds the short `// was func_… [oot]` provenance
  tag to header declarations of renamed symbols. Idempotent; run until
  `check_renames.py declarations` is clean.
- `tools/renames_common.py` — shared helpers for the two above (reads the pin
  from `fetch.sh`, discovers renames from the tree's provenance comments).
- `tools/save_generator.py` — interactive base-quest save-file generator
  (dungeons-first interview, progression-derived defaults, full stocks;
  writes locally, never installs). `--selftest <real.sav>` proves an
  all-defaults save matches a pristine one. The save-format knowledge
  behind it — including the Spirit/Shadow `randomizerInf` trap and the
  section-version `.bak` landmine — lives in
  [`../../tasks/reference/ocarina/save-file-generator.md`](../../tasks/reference/ocarina/save-file-generator.md).
