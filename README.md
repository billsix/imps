# imps — Island of Misfit Patches Storage

Patches I want carried on top of other people's projects, without maintaining
forks of those projects. Each project gets one folder holding a pinned
upstream commit, a patch series, and short scripts to fetch, build, and run.
The upstream checkout and all build products are gitignored — the scripts,
patches, and docs ARE the repo.

Two goals, in order:

1. **Getting my patches upstreamed is the ultimate goal.** Anything upstream
   would plausibly take (bug fixes, portability fixes, doc corrections) is
   kept as a standalone, submission-ready patch — and retires from the
   series once merged.
2. **Maintaining the rest myself, independent of upstream** — patches for my
   own purposes (cheats, personal tweaks) that I carry indefinitely and
   replay onto newer upstream pins as time progresses.

## Layout

- `<family>/` — projects are grouped into family folders by the kind of
  thing they patch (currently `n64/` for the HarbourMasters game ports).
  Each family folder has its own `CLAUDE.md`.
- `<family>/<Project>/` — scripts (`fetch.sh`, `apply.sh`, `build.sh`,
  `run.sh`), `patches/` (**code changes only**), and that project's
  `CLAUDE.md`.
- `tasks/` — shared across all projects at the imps root (stays
  project-keyed, no family level): task docs, plus deep-dive reference docs
  under `tasks/reference/<project>/`.
- Prose about a project lives here in imps, never inside the patches — a
  patch carries only what must change upstream's own files. The full
  doc-structure contract is in `CLAUDE.md`.

## License

MIT (see `LICENSE`) for the original content of this repo — the scripts,
docs, and patch authorship. The files under each project's `patches/`
necessarily contain fragments of the upstream project's code (diff context
and modified lines); those fragments remain under the respective upstream
project's own license, not this repo's.

## N64 ports (HarbourMasters)

The `n64/` family: patch series on top of the HarbourMasters PC ports, all
sharing the libultraship engine — `n64/OcarinaOfTime/`, `n64/MajorasMask/`,
`n64/SuperMario64/`, `n64/BanjoKazooie/`, plus the docs-only
`n64/libultraship/`. Every game folder follows the same
fetch/apply/build/run contract; Ocarina of Time is shown in full below and
the others work the same way from their own `n64/<Game>/` folder. Family
contract and per-project index: `n64/CLAUDE.md`.

### Ocarina of Time (Ship of Harkinian)

Upstream: <https://github.com/HarbourMasters/Shipwright>

```sh
cd n64/OcarinaOfTime
sudo ./installdependencies.sh   # Fedora: dnf install the build deps (once)
./fetch.sh    # clone if missing, checkout the pinned commit, init submodules
./apply.sh    # apply my patch series (patches/*.patch) on top of the pin
./build.sh    # cmake+ninja → bldInstall/  (fetches first if you skipped fetch.sh)
./run.sh      # launches bldInstall/soh.elf with runDir/ as the game's working dir
```

- `apply.sh` is optional — skip it for a pristine upstream build. It refuses
  to run unless the checkout is exactly at the pin (re-run `fetch.sh` to get
  back there; local branches survive).
- The pin is the tip of upstream `develop` as of 2026-09-01; it lives in
  `fetch.sh` (`PIN_SHA`).
- > On first launch the game asks for a legally-acquired OoT ROM and
  > generates `runDir/oot.o2r` from it; saves, config, and logs also land in
  > `runDir/`. Nothing ROM-derived is ever committed.

### Status / planned

- **OcarinaOfTime** — builds and runs with the patch series applied
  (verified 2026-09-01). One code patch (decomp renames), ported from my
  old fork; the fork's docs now live in `n64/OcarinaOfTime/CLAUDE.md` and
  `tasks/reference/ocarina/`.
- **MajorasMask** — builds and runs with the patch applied (verified
  2026-09-01). Two patches: 64-bit audio/scheduler fixes (exported from
  my old `fedora44Fixes` fork branch) and a BUILDING.md fix adding the
  four required audio libraries (upstream candidate, found by the
  install-script verification). Also has the first podman build:
  `make appimage` → `out/2ship.appimage` (see its README).
- **SuperMario64** — builds and runs with the patches applied, cheats
  confirmed in the menu (verified 2026-09-01). Series: Super Jump,
  Infinite Air Jumps, Disable Skybox, plus a Fedora-deps doc fix
  (upstream candidate), on a modern develop pin that already includes my
  merged fly-on-triple-jump cheat. Fork docs migrated to
  `n64/SuperMario64/CLAUDE.md` + `tasks/reference/mario64/`.
- **BanjoKazooie** — 4-patch series from my `fixOnFedora` fork branch
  (submitted upstream as a PR): Fedora deps doc fix, bk.o2r version stamp,
  the post-ROM-import freeze fix, review-round cleanup. Builds and runs
  with the patches applied (verified 2026-09-01 via the podman AppImage
  pipeline: image → build → appimage → host run). Fork docs migrated to
  `n64/BanjoKazooie/CLAUDE.md` + `tasks/reference/banjo/`.
- All four projects now have a podman AppImage build (`make appimage`)
  and a container-verified `installdependencies.sh` — **all four
  AppImages now build on my host** (2026-09-01): OcarinaOfTime and
  BanjoKazooie are run-confirmed, SuperMario64 launches on the Vulkan
  backend (see its `CLAUDE.md` RADV caveat).
- The libultraship reference-documentation crawl is **complete** (18
  iterations: 13 release tags + all 5 consumer pins): one evolving
  8-doc set at `tasks/reference/libultraship/`, one commit per
  version — git history is the time axis, and
  `tasks/reference/libultraship/crawl.md` is the protocol + log a
  future pin bump reopens.
- **Planned** (all tasked under `tasks/`): save-generator story-flag
  fidelity (blocked on reference saves I provide); replacing each
  project's upstream CI Linux job with the Dockerfile build (future,
  upstream-submission oriented); mario64 cheat research stubs; the
  long-running decomp-rename cleanups.

## OpenStax — moved to the sibling repo `impo`

The maintainer's OpenStax textbook port (a CNXML→LaTeX toolchain that builds
each book to HTML/PDF/EPUB) uses this same carrier design, but lives in its
own repository, [impo](https://github.com/billsix/impo) — split out to keep
imps small, since the committed OpenStax content is large.
