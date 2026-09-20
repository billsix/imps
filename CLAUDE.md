# imps — Island of Misfit Patches Storage

Patch carrier for third-party projects, replacing maintained forks. The
maintainer has git work he wants applied to other people's projects without
managing GitHub forks of them: imps stores the patch series plus the scripts
that fetch pristine upstream source at a pinned commit, apply the patches,
and build/run the result — eventually both on the host and in a podman
container. One folder per project; each folder is self-contained.

## Documentation structure — four tiers, docs live in imps, patches carry code

**Dividing principle: a patch carries only code (what must live inside
upstream's own files); everything purely the maintainer's — CLAUDE.md content,
task docs, reference docs — lives natively in imps** (editing it is a plain file
edit, no patch regeneration, and it never rides a pin-bump rebase). The tiers
exploit Claude Code's ancestor-CLAUDE.md loading (a session anywhere under
`imps/` auto-loads every CLAUDE.md from cwd to the repo root), with a **family
folder** tier between master and project so a family's contract loads exactly for
that family's sessions:

1. **`CLAUDE.md` (this file, the master)** — lean and family-agnostic: what imps
   is, the cross-family contracts, and a one-line-per-family index (tier 2).
2. **`<family>/CLAUDE.md`** (e.g. `n64/CLAUDE.md`) — that family's build/patch
   contract, drift table, gotchas, and a one-line-per-project index (tier 3).
3. **`<family>/<Project>/CLAUDE.md`** — that project's operational facts (upstream
   URL, pin, patch list one line each, build/run gotchas) + index of its tier-4
   reference docs. Sits outside the checkout but is its ancestor, so it loads
   exactly when a session works inside that project.
4. **`tasks/reference/<project>/*.md`** — the deep-dive reference docs, one subdir
   per project, pointed at from tier 3 (plain pointers, not `@`-imports).

`tasks/` is shared at the imps root and stays **project-keyed** regardless of
family: reference docs at `tasks/reference/<project>/`, archives at
`tasks/archive/<project>/<YYYY>/<MM>/<DD>/<slug>.md` (project first, then date —
**overriding** the global flat-date convention, decided 2026-09-01). Repo-wide
tasks use `imps` as the project key.

Full mechanics — the dividing principle in full, the ancestor-loading rationale,
why the family tier sits between master and project, and the tasks/-keying +
per-project-archive decision: `tasks/reference/imps/documentation-structure.md`.

## Per-project folder contract

This is the **generic** self-contained-folder contract shared by every family.
Each family's `CLAUDE.md` adds its concrete build/patch specifics on top (the
N64 HarbourMasters-port contract — pristine-upstream fetch at a pin, `git am`
the series, the podman AppImage build — is in `n64/CLAUDE.md`).

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
- `patches/` — a `git format-patch` series with `base-commit:` footers naming
  the pin, **code changes only** per the dividing principle above. A project MAY
  group these into **purpose-stream subfolders** (`patches/<stream>/`) when it
  carries independent patch sets — order matters within a stream, not across
  them; see the family `CLAUDE.md`. Regenerate after editing commits in the
  checkout with `git format-patch --no-cover-letter --base=<pin> <pin>..HEAD`.
- `.gitignore` — the upstream checkout, `build-cmake/`, `bldInstall/`, and
  `runDir/` are all untracked.

**`runDir/` IS SACRED — never delete or rewrite it** (William Emerison Six
<billsix@gmail.com>, 2026-09-07). It holds irreplaceable personal state: save
files (`runDir/Save/`), the extracted `.o2r` (regenerable only from the
maintainer's own ROM), controller/graphics config, and installed texture-pack
mods under `runDir/mods/`. **Reworking patches must never touch it.** This is
structurally safe today and must stay that way:

- `runDir/` is a **sibling** of the upstream checkout, not inside it, so every
  `git` operation on the checkout (`reset --hard`, `clean -fd`, `am`, `mv`)
  cannot reach it by construction. Keep it that way — never place it inside the
  checkout.
- `fetch.sh`, `apply.sh` and `build.sh` never mention `runDir`; only `run.sh`
  touches it, and only via `mkdir -p`.
- The Makefile's `clean` removes `build-cmake/`, `_packages/` and `out/` — **not
  `runDir/`**. A `clean` target that deletes `runDir` would be a bug.

When rewriting a patch series, work only inside the checkout, and scope any
`git clean` to the source subtree (e.g. `git clean -fd soh`) rather than the
whole tree.

## Patch philosophy — must keep working; upstream where it can

(William Emerison Six <billsix@gmail.com>, 2026-09-01; reframed 2026-09-07.)
Two goals, ranked:

0. **The patches must keep working for the maintainer over time, across machines,
   as he pulls from upstream.** Primary goal, and the reason imps exists.
   Upstreaming is the ideal but has proven hard — an aspiration, not the mechanism.
1. **Shape for upstreaming anyway, where the change plausibly fits.** A bug fix,
   portability fix, or doc correction gets shaped as a standalone, submission-ready
   patch (own commit, reviewer-facing message, no entanglement with personal
   changes). Split a mixed change into two rather than ship a hybrid. Mark upstream
   candidates in the per-project CLAUDE.md patch list.
2. **Personal patches are maintained independently, indefinitely** — cheats and
   personal tweaks carried in the same series and replayed onto newer pins (the
   pin-bump operation).

**That invariant is gated** (2026-09-07). `tools/check_patches_apply.sh` resets
every project to its pin and runs the project's own `apply.sh` — the real path,
including stream order, both lanes, and the pin guard — then reports the commit
count per lane:

```sh
tools/check_patches_apply.sh                 # every project
tools/check_patches_apply.sh OcarinaOfTime   # just one
```

Run it after a pin bump, after reshaping a series, and when picking the repo up
after a gap. A failure IS the pin-bump conflict surfacing early. It leaves each
checkout on the fully-applied series (the documented default working state) and
never touches `runDir/` (a sibling of the checkout).

A companion at the same level, **not** a gate: `tools/squash_series.py` regroups a
one-change-per-commit series into review units without losing the reasoning;
method in `tasks/reference/imps/squashing-a-produced-series-for-review.md`.

Why imps exists, the full goal statements, what it buys, the upstream-vs-pin-bump
tradeoff, and the patch-lifecycle consequence:
`tasks/reference/imps/patch-philosophy.md`.

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
  series renames), build and run, then update the `PIN_SHA` in `fetch.sh`
  (the variable is named `PIN_SHA` in every project), regenerate the
  patches, and refresh the pin references and provenance banners in the
  docs — one unit, staged together. **Re-verify every derived artifact
  against its source at each bump** — the family `CLAUDE.md` lists the
  drift pairs (e.g. the drift table in `n64/CLAUDE.md`).

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

## Families

Each family is a folder grouping projects that patch the same kind of thing.
Its `<family>/CLAUDE.md` (tier 2) holds that family's concrete build/patch
contract and its per-project index; open it when working in that family.

- **`n64/`** — the HarbourMasters N64 PC ports (Ocarina of Time, Majora's
  Mask, Super Mario 64, Banjo-Kazooie) plus the shared `libultraship`
  engine. Contract, drift table, and project index: `n64/CLAUDE.md`.

### Documentation-only carrier families (landing 2026-09-20)

A second KIND of family: **documentation-only** carriers that pin an upstream to
**document** it, not port it. They add only **comment-only** patch streams —
`patches/docs/` (explanatory doc comments on interesting source, the maintainer's
"add docstrings to the codebase" ask, 2026-09-20) and `patches/book/` (Sphinx
doc-region markers, the mario64 machinery — see `tasks/reference/mario64/` and
`n64/SuperMario64/book/`) — plus a Makefile/Dockerfile that builds the upstream
only to prove the doc patches are comment-only, and hosts the Sphinx book.
Categorized by kind, like `n64/`. Each family's tier-2 contract is its
`<family>/CLAUDE.md`:

- **`unixutils/`** — command-line Unix tools documented for teaching:
  **ripgrep** (Rust), **dash** (C) landing 2026-09-20; **coreutils** (uutils,
  Rust) still planned. Contract + project index: `unixutils/CLAUDE.md`. Tasks:
  `tasks/ripgrep-refdocs-and-book.md`, `tasks/dash-refdocs-and-book.md`,
  `tasks/coreutils-refdocs-and-book.md`.
- **`android/`** — Android apps documented for teaching: the **Fossify** suite
  (Kotlin) + its shared `Commons` library, multi-repo. Contract + index:
  `android/CLAUDE.md`. Task: `tasks/fossify-refdocs-and-book.md`.

The maintainer's OpenStax textbook port — the same carrier idea applied to
CNXML→LaTeX books — lives in the sibling repo **impo**
(https://github.com/billsix/impo), split out to keep imps small (its committed
OpenStax content is large).
