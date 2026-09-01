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
one that versions them): in-flight task docs at `tasks/*.md`, reference
docs namespaced per project as above, archives under `tasks/archive/`.

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

## Working on a project — agent contract

- **Assume the patches are applied.** The default working state of a
  project's checkout is the pin plus the full `patches/` series. Verify
  before starting (`git log --oneline` in the checkout should show the
  series' subjects on top of the pin); if it's at the bare pin, run
  `./apply.sh` first.
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
  series renames), build and run, then update `SHIPWRIGHT_SHA` in
  `fetch.sh`, regenerate the patches, and refresh the pin references and
  provenance banners in the docs — one unit, staged together.

## Rules

- Scripts start with `cd "$(dirname "$0")"` and use only relative paths —
  runnable from anywhere, no hardcoded home/host paths.
- Moving a pin is a deliberate act: after any pin bump, re-verify the patch
  series applies and the project builds before committing the new SHA.
- ROM/asset acquisition is out of scope — each game's own in-app extraction
  handles it in `runDir/`. Never commit the upstream checkout or anything
  ROM-derived.
- **Unsigned commits in checkouts/scratch clones are authorized** (William
  Emerison Six <billsix@gmail.com>, 2026-09-01): the maintainer's gitconfig
  enables commit signing, which fails in the sandbox. When making the
  intermediate commits that patch work requires (cherry-picks, `git am`,
  series edits), disable signing **repo-locally in the throwaway clone or
  checkout** (`git config commit.gpgsign false` there, or per-command
  `git -c commit.gpgsign=false`) — never in the global gitconfig. These
  commits are scaffolding; the durable product is the patch files.

## Projects

- `OcarinaOfTime/` — Ship of Harkinian
  (https://github.com/HarbourMasters/Shipwright), pinned at `acdbc651d`
  (tip of `develop`, 2026-09-01; submodules libultraship + torch). Details:
  `OcarinaOfTime/CLAUDE.md`. Status: one code patch (a 145-file decomp
  rename), ported from the maintainer's old fork; patched tree
  **build-verified on the maintainer's host 2026-09-01**. The old fork's
  docs-only commits were migrated into
  `OcarinaOfTime/CLAUDE.md` + `tasks/reference/ocarina/` per the
  documentation structure above (stale fork-era claims fixed or bannered
  in the move); its submodule-pin changes were dropped as obsolete.
