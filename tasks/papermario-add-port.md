# PaperMario: add PaperBoat as a new n64-family port (compile-as-is first)

**Status:** ready — first step is a pristine compile-as-is (William Emerison Six
<billsix@gmail.com> requested it 2026-09-17)
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

- [ ] Clone PaperBoat to a scratch checkout and read its own build docs
      (`README`, `BUILDING*`, `.github/workflows/*`, `CMakeLists.txt`) to
      learn its real dependencies, submodules, and build commands. Confirm
      whether it is libultraship-based and which LUS commit it pins.
- [ ] Create `n64/PaperMario/` with `fetch.sh` (copy SuperMario64's shape;
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
- [ ] Run `./fetch.sh && ./build.sh` and produce a runnable binary from
      the **unmodified** checkout — no `apply.sh`, no `patches/` yet. Record
      the exact dependency list and any deviations from the SM64 build.
- [ ] Write the tier-3 `n64/PaperMario/CLAUDE.md` (upstream URL, pin SHA,
      libultraship pin, build/run gotchas; empty patch list for now).
- [ ] Maintainer host-verifies the build actually runs (ROM extraction in
      `runDir/`, display/audio) — sandbox can build but not verify a
      display/FUSE/audio run.

Follow-on (separate units, once the bare build works — do NOT bundle):

- [ ] Add the one-line entry to the `n64/CLAUDE.md` Projects index and the
      `tasks/reference/imps/game-port-history.md` detail row.
- [ ] Scaffold `apply.sh` + `patches/` (empty streams) so the project
      matches the family contract for when a first patch is carried.
- [ ] Optional podman build (`Dockerfile` + `Makefile`, `MajorasMask`/
      `SuperMario64` as the reference) — its own task, like the existing
      `*-upstream-container-ci.md` tasks.

## Open questions

1. **Pin choice.** Pin the tip of PaperBoat's default branch at execution,
   or a specific tagged/known-good commit? Recommendation: tip of the
   default branch at execution (matches how the other four were pinned),
   recorded with its date — unless the maintainer knows of a stable tag.
2. **libultraship lane.** If PaperBoat pins a libultraship commit not yet
   covered by the `tasks/reference/libultraship/` crawl, do we reopen the
   crawl now or defer until a LUS-lane patch is actually needed?
   Recommendation: defer — the first bare build needs no LUS docs.

## See also

- `n64/CLAUDE.md` — the HarbourMasters N64 family build/patch contract.
- `n64/SuperMario64/` and `n64/BanjoKazooie/` — the folder templates.
- master `CLAUDE.md` — per-project folder contract, unsigned-commits rule,
  `runDir/`-is-sacred rule.
- `tasks/reference/imps/game-port-history.md` — where the per-project
  patch-count/verification history lives.
