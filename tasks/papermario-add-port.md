# PaperMario: add PaperBoat as a new n64-family port (compile-as-is first)

**Status:** in progress — first step (pristine compile-as-is) built AND
extraction-verified in the sandbox 2026-09-21 (pin moved to stable `1.0.1`).
The reported "extraction does nothing / No ROM O2R" was diagnosed to an
over-dumped ROM, not a build/pin issue — fix + proof recorded in
`n64/PaperMario/CLAUDE.md` ("ROM requirements"). Pin confirmed as `1.0.1`
(2026-09-22). Remaining: the maintainer's interactive gameplay verify
(display/audio), then the follow-on units. (William Emerison Six
<billsix@gmail.com> requested it 2026-09-17; executed 2026-09-21.)
**Priority:** 5
**Difficulty:** 6
**Project key:** papermario (a new `n64/PaperMario/` folder)

## BLUF

Add HarbourMasters' **PaperBoat** — the PC port of Paper Mario (N64) —
as a new project in the `n64/` family, following the existing
per-project folder contract (`fetch.sh`/`build.sh`/`run.sh` + docs).
**The first and only immediate goal: build pristine upstream at a pinned
commit with NO patches** — exactly the "compile it as-is" path the other
four ports (OcarinaOfTime, MajorasMask, SuperMario64, BanjoKazooie) went
through before carrying any series. "Done" for this first step = a fresh
`./fetch.sh && ./build.sh` produces a runnable binary from an unmodified
PaperBoat checkout at the pin, host-verified by the maintainer, with the
pin recorded in `fetch.sh` and a tier-3 `n64/PaperMario/CLAUDE.md`
capturing the operational facts. Patches, a podman build, and the
`n64/CLAUDE.md` Projects-index line follow once the bare build works.

## Context (cold-start)

- **Upstream:** https://github.com/HarbourMasters/PaperBoat.git (the
  HarbourMasters PC port of Paper Mario). A HarbourMasters N64 port, so
  it belongs in the **`n64/`** family and almost certainly follows the
  same shape as the other four: a **libultraship** submodule + a
  Torch/ZAPDTR-style asset pipeline, with in-app ROM extraction into
  `runDir/`. **Verify this at execution** — clone it and read its own
  `README`/`BUILDING`/CI before assuming; PaperBoat may pin a different
  libultraship commit (each game does — see the `n64/CLAUDE.md`
  per-game LUS-pin note) or diverge from the SoH/Ghostship build.
- **The family contract is `n64/CLAUDE.md`** (read it first): the
  HarbourMasters-port `fetch.sh`/`apply.sh`/`build.sh`/`run.sh` machinery,
  the two patch lanes (game-tree + libultraship), purpose streams, and
  the derived-artifact drift rules. The generic per-project folder
  contract is in the master `CLAUDE.md` ("Per-project folder contract").
- **Template to copy from: `n64/SuperMario64/`** — it is the closest
  analogue (Ghostship, a mainline-ish HM port with a podman build and a
  book). Its `fetch.sh` is the pattern for this port's `fetch.sh`
  (`UPSTREAM=`, `PIN_SHA=` commented with its date + upstream branch,
  clone-if-absent, repo-local `commit.gpgsign false`, checkout pin,
  `submodule update --init --recursive`). `n64/BanjoKazooie/` is the
  other recent from-scratch add and a good second reference.
- **Unsigned commits in the checkout are authorized and automated**
  (master `CLAUDE.md`, Rules): `fetch.sh` sets `commit.gpgsign false`
  repo-locally in the checkout it manages, never globally — the sandbox
  cannot sign, and a failed signature aborts `git am`. The libultraship
  submodule is its own repo, so disable signing in ITS config too if you
  ever commit there.
- **`runDir/` is sacred** and a **sibling** of the checkout — keep it that
  way (master `CLAUDE.md`). Not relevant to a first bare build, but the
  folder scaffolding must not place it inside the checkout.
- **Never build a checkout from a foreign toolchain via a bind mount**
  (`n64/CLAUDE.md`): libultraship writes artifacts into its submodule
  source dir, poisoning the next podman build — copy source into the
  throwaway container instead. Applies once a podman build is added.

## Approach

First step (the maintainer's immediate ask — pristine compile-as-is):
**Done in the sandbox 2026-09-21** except the maintainer's host run-verify.
Work record + verified facts live in `n64/PaperMario/CLAUDE.md`.

- [x] Clone PaperBoat to a scratch checkout and read its own build docs
      (`README`, `BUILDING*`, `.github/workflows/*`, `CMakeLists.txt`) to
      learn its real dependencies, submodules, and build commands. Confirm
      whether it is libultraship-based and which LUS commit it pins.
      → Yes, libultraship-based, but with **JeodC forks** for both submodules
      (`external/libultraship` @ `601f7002`, branch `lus-converge`;
      `external/torch` @ `106f4e30`, branch `pm64`) — distinct from the other
      four ports' engine pins. Build = CMake presets (`ninja-release`); deps
      from the CI apt line mapped to Fedora. No Python needed for the port
      build (the big `requirements.txt` is the ROM/decomp pipeline).
- [x] Create `n64/PaperMario/` with `fetch.sh` (copy SuperMario64's shape;
      `UPSTREAM=https://github.com/HarbourMasters/PaperBoat.git`, `PIN_SHA=`
      = tip of the default branch at execution, commented with the date and
      branch), `installdependencies.sh` (host package-manager install of the
      dependency list learned from upstream's build docs; guard the manager
      exists and fail loudly, inline the package list), `build.sh` (host build
      mirroring upstream's documented commands; calls `fetch.sh` when the
      checkout is missing), `run.sh`
      (launch installed binary with `runDir/` as cwd), a `.gitignore` (the
      checkout, `build-cmake/`, `bldInstall/`, `runDir/`), and a
      commands-forward `README.md`.
- [x] Run `./fetch.sh && ./build.sh` and produce a runnable binary from
      the **unmodified** checkout — no `apply.sh`, no `patches/` yet. Record
      the exact dependency list and any deviations from the SM64 build.
      → Full 3666-step build green (Fedora 44, gcc 16.2.1); 37 MB `Paperboat`
      ELF + `paperboat.o2r` + `assets/` produced. Dep deltas vs Ghostship and
      the confirmed-vs-carried-over notes are in the CLAUDE.md Version notes.
- [x] Write the tier-3 `n64/PaperMario/CLAUDE.md` (upstream URL, pin SHA,
      libultraship pin, build/run gotchas; empty patch list for now).
      → Plus a commands-forward `README.md` and a `.gitignore`.
- [ ] **(maintainer — owed)** Host-verify the build actually runs (ROM
      extraction in `runDir/`, display/audio) — sandbox can build but not
      verify a display/FUSE/audio run. Deviation from SM64: this LUS fork
      builds no `libtcc.so` and bakes no RPATH, so `run.sh` needs no
      `LD_LIBRARY_PATH` (verified). No OpenGL-default seed added yet — add one
      à la Ghostship's `run.sh` only if the Vulkan backend hangs on the host.

Follow-on (separate units, once the bare build works — do NOT bundle):

- [ ] Add the one-line entry to the `n64/CLAUDE.md` Projects index and the
      `tasks/reference/imps/game-port-history.md` detail row.
- [ ] Scaffold `apply.sh` + `patches/` (empty streams) so the project
      matches the family contract for when a first patch is carried.
- [ ] Optional podman build (`Dockerfile` + `Makefile`, `MajorasMask`/
      `SuperMario64` as the reference) — its own task, like the existing
      `*-upstream-container-ci.md` tasks.

## Open questions

Both resolved at execution (2026-09-21) via their recommendations — no
maintainer input was needed for the bare build:

1. **Pin choice.** → First pinned tip-of-`develop`
   (`611f5b685750e3e7f3a99eefe90fd874e8f1eb7b`, 2026-09-20); then moved to the
   stable release tag **`1.0.1`** (`424c220f0`, 2026-09-18) at the maintainer's
   request while diagnosing the extraction failure. That failure turned out to
   be a ROM problem, NOT pin-related (extraction code is byte-identical between
   the two pins), so the pin is now a plain stable-vs-develop preference.
   **Decided (William Emerison Six <billsix@gmail.com>, 2026-09-22): keep
   `1.0.1`.** Bump to develop later only if a develop-only gameplay fix is
   wanted.
2. **libultraship lane.** → **Deferred.** PaperBoat pins a JeodC LUS fork
   (`601f7002`, `lus-converge`) not covered by the
   `tasks/reference/libultraship/` crawl, but the bare build needs no LUS
   docs. Reopen the crawl against `601f7002` only when a LUS-lane patch is
   actually needed.

## See also

- `n64/CLAUDE.md` — the HarbourMasters N64 family build/patch contract.
- `n64/SuperMario64/` and `n64/BanjoKazooie/` — the folder templates.
- master `CLAUDE.md` — per-project folder contract, unsigned-commits rule,
  `runDir/`-is-sacred rule.
- `tasks/reference/imps/game-port-history.md` — where the per-project
  patch-count/verification history lives.
