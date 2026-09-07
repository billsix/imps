# imps — Island of Misfit Patches Storage

Patch carrier for third-party projects, replacing maintained forks. The
maintainer has git work he wants applied to other people's projects without
managing GitHub forks of them: imps stores the patch series plus the scripts
that fetch pristine upstream source at a pinned commit, apply the patches,
and build/run the result — eventually both on the host and in a podman
container. One folder per project; each folder is self-contained.

## Documentation structure — four tiers, docs live in imps, patches carry code

The dividing principle: **a patch carries only what must live inside
upstream's own files — code. Everything that is purely the maintainer's
(CLAUDE.md content, task docs, reference docs) lives natively in imps**,
where editing it is a plain file edit (no patch regeneration), it exists
whether or not a checkout does, and it never rides along in a pin-bump
rebase.

The tiers exploit Claude Code's ancestor CLAUDE.md loading (a session
working anywhere under `imps/`, including deep inside a project's checkout,
auto-loads every CLAUDE.md on the path from cwd to the repo root). Projects
are grouped into **family folders** by the kind of thing they patch
(currently `n64/` for the HarbourMasters game ports), and the family tier
sits between the master and the project so that a
family's specialized contract loads **exactly** for that family's sessions
and never bloats another's:

1. **`CLAUDE.md` (this file, the master)** — lean and **family-agnostic**:
   what imps is, the cross-family contracts (patch philosophy, the generic
   self-contained-folder principle, the unsigned-commits rule, the
   tasks/archive convention), and a one-line-per-family index pointing at
   tier 2.
2. **`<family>/CLAUDE.md`** (e.g. `n64/CLAUDE.md`) — that family's concrete
   build/patch contract, its derived-artifact drift table and gotchas, and a
   one-line-per-project index pointing at tier 3. Auto-loads for any session
   under that family folder, and only those — a session in one family never
   loads another family's detail.
3. **`<family>/<Project>/CLAUDE.md`** — that project's operational facts:
   upstream URL, pin and why it sits there, the patch list one line each,
   build/run gotchas, and an index of its tier-4 reference docs. Sits
   OUTSIDE the checkout but is its ancestor, so it auto-loads exactly when a
   session works inside that project.
4. **`tasks/reference/<project>/*.md`** — the deep-dive reference docs,
   one subdirectory per project (e.g. `tasks/reference/ocarina/`). Pointed
   at from tier 3 — plain pointers, not `@`-imports, so one project's
   large doc set never bloats sessions about another project.

`tasks/` is shared across all projects at the imps root (this repo is the
one that versions them): in-flight task docs at `tasks/*.md` (named with a
project prefix, e.g. `ocarina-…`), reference docs namespaced per project
as above. **`tasks/` stays project-keyed regardless of family folder** — a
project's reference docs live at `tasks/reference/<project>/` and its archives
at `tasks/archive/<project>/…` using the **project name** as the key, never a
family segment (project names stay unique across families, so no collision).
**Archives are per-project — this overrides the global convention's flat date
layout for this repo** (decided with William Emerison Six
<billsix@gmail.com>, 2026-09-01): a completed task moves to
`tasks/archive/<project>/<YYYY>/<MM>/<DD>/<slug>.md` — project first, then
the standard date buckets. Repo-wide tasks (not about one game) use
`imps` as their project directory.

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
Two goals, and the ranking matters:

0. **The patches must keep working for the maintainer over time, across
   machines, as he pulls from upstream.** This is the primary goal and the
   reason imps exists — see the paragraphs below. Upstreaming is the ideal
   outcome and has proven hard in practice, so it is the aspiration, not the
   mechanism.
1. **Shape for upstreaming anyway, where the change plausibly fits.** If a change is something
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

**What imps actually buys, and must keep buying:**

- **Repeatability across computers.** A pin + a patch series reproduces the
  same tree anywhere, with no per-project git branches to keep in sync between
  machines. That is the thing forks were failing to provide.
- **Survivable pin bumps.** The patches are replayed onto newer upstream
  commits as a routine operation; a patch's long-term rebase cost is a design
  consideration when writing it (prefer the port's event/enhancement layers over
  editing decomp internals).
- **No fork maintenance.** No branches, no merges, no divergence to reconcile —
  just a SHA and a folder of patches.
- **Coordination cost is real and deliberate to avoid.** Patching libultraship
  and its downstream consumers would mean keeping several projects in step; the
  patch-carrier design is what keeps that tractable rather than a standing
  obligation.

So when a choice arises between "shaped for upstream" and "survives the next
pin bump cleanly", both matter — but a patch that no longer applies has failed
at its primary job.

**That invariant is gated** (2026-09-07). `tools/check_patches_apply.sh` resets
every project to its pin and runs the project's own `apply.sh` — the real path,
including stream order, both lanes, and the pin guard — then reports the commit
count per lane:

```sh
tools/check_patches_apply.sh                 # every project
tools/check_patches_apply.sh OcarinaOfTime   # just one
```

Run it after a pin bump, after reshaping a series, and when picking the repo up
after a gap. A failure IS the pin-bump conflict surfacing early, which is the
point. It leaves each checkout on the fully-applied series — the documented
default working state — so it doubles as "put everything back in a known-good
state". It never touches `runDir/` (a sibling of the checkout; see above).

Lifecycle consequence: an upstreamable patch is temporary — once merged
upstream, it retires at the next pin bump (the bump's `git am` will show
it as already applied, or the rebase drops it); a personal patch is
permanent and its long-term rebase cost is a design consideration when
writing it (prefer hooking the port's event/enhancement layers over
editing decomp internals — the mario64 cheats are the worked example).

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

imps currently carries this single family. The maintainer's OpenStax textbook
port — the same carrier idea applied to CNXML→LaTeX books — lives in the
sibling repo **impo** (https://github.com/billsix/impo), split out to keep
imps small (its committed OpenStax content is large).
