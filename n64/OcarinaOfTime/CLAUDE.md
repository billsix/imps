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

**Stream order is pinned here — `personal` FIRST** (`patches/ORDER`; `apply.sh`
honours it). The renames touch 3,781 symbols and 18 filenames, so **any stream
added later must be written against the renamed tree** — without the pin a future
`book/` stream would sort alphabetically ahead of `personal/` and try to patch
symbols that no longer exist. Stream folders stay separate regardless (keeps
`upstream-candidates/` submittable on its own; see `../CLAUDE.md`).

- `patches/personal/0001…0488-*.patch` — the decomp rename series, **one file
  per patch**: 0001 renames the 18 address-named `soh/src/code/code_<addr>.c`
  files, and each other patch names the address-named symbols in one definition
  file (156 files hold a single symbol). Every renamed symbol carries a
  provenance comment at its definition **and** a short `// was func_… [oot]` /
  `[LLM:HIGH]` tag at each header declaration (and, for a guess, at every call
  site), so a reader of `functions.h` can tell an upstream name from a deduction;
  `git grep '\[LLM:'` lists every inferred name.
  **Every address-named symbol now has a name except four**, all declared
  exclusions: `func_800FBCE0` / `func_800FBFD8` (the RCP block in
  `code_800FBCE0.c`) and `func_80837C0C` / `func_80838940` (`z_player.c`).
  Segmented asset addresses (`D_0xxxxxxx`) and OTR asset identifiers are out of
  scope by construction — the identifier IS the archive key.
  Gated by `tools/check_renames.py series`: **no rename may happen that its
  commit message does not account for**, and every claimed rename must be total.
  Method, comment convention, and the one-rename-per-commit rule:
  [`../../tasks/reference/ocarina/decomp-renaming.md`](../../tasks/reference/ocarina/decomp-renaming.md).
  Production & verification history (squash from 3,799 one-rename-per-commit
  patches, provenance counts, the original fork port, container/on-host
  build-and-run verification, the illegible-save-text oddity):
  `../../tasks/reference/imps/game-port-history.md`.

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
- [`oot-oracle-census.tsv`](../../tasks/reference/ocarina/oot-oracle-census.tsv)
  — the 2,982-row record of what zeldaret/oot called each address-named symbol
  at this pin. **Historical, not live**: its `BOTH` verdicts mean "oot had no
  name *then*", so re-run `tools/oot_oracle.py` and treat it as superseded after
  a pin bump. Read `decomp-renaming.md` for the full expiry note.
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

`Dockerfile` mirrors upstream CI's linux job
(`.github/workflows/generate-builds.yml` at the pin, **ubuntu-22.04**): the apt
list is **`COPY`d from the checkout's own `linux-build-deps/apt.txt`** at image
build (auto-current; `COPY` not `RUN --mount=type=bind` — see the SuperMario64
Dockerfile comment and the drift table); SDL 2.30.3, SDL2_net 2.2.0, tinyxml2
10.0.0, libzip 1.10.1 built from source; flags Release + `BUILD_REMOTE_CONTROL=1`;
`GenerateSohOtr` in-container. `make image/build/appimage/run`. Fresh-environment
gaps (cmake ≥ 3.26 via the Kitware block, python3, imagemagick for the
configure-time AppImage icon) are in the master drift table. Build/run
verification history: `../../tasks/reference/imps/game-port-history.md`.

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
- `tools/remaining_address_names.py` — **is the naming finished?** Prints every
  address-named symbol still in the decomp, read from the checkout rather than
  from any census, so it cannot go stale. Today it prints 6 rows covering 4
  distinct names, all in the declared exclusions (`code_800FBCE0.c`'s RCP pair
  and two `z_player.c` functions); **anything more than that is new work**,
  most likely introduced by a pin bump. Run it after a pin bump and after any
  rename batch.
- `tools/oot_oracle.py` — asks zeldaret/oot what SoH's address-named symbols are
  really called, by aligning the two decomps' address-ordered function
  sequences. **Re-run after a pin bump**: oot keeps naming symbols, so a newer
  revision can turn `func_8xxxxxxx` into a name with real upstream authority.
  Needs network; writes `oracle.tsv` and a fetch cache beside the checkout
  (both gitignored). It yielded the 770 adopted names in this series.

  Neither of the two above is wired into a gate, deliberately: they are
  informational audits, and a pin bump legitimately changes their output.
  `check_renames.py` remains the pass/fail gate.
- `tools/save_generator.py` — interactive base-quest save-file generator
  (dungeons-first interview, progression-derived defaults, full stocks;
  writes locally, never installs). `--selftest <real.sav>` proves an
  all-defaults save matches a pristine one. The save-format knowledge
  behind it — including the Spirit/Shadow `randomizerInf` trap and the
  section-version `.bak` landmine — lives in
  [`../../tasks/reference/ocarina/save-file-generator.md`](../../tasks/reference/ocarina/save-file-generator.md).
