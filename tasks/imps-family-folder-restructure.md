# Restructure imps into family folders (`n64/`, `openstax/`)

**Status:** approved 2026-09-02 (William Emerison Six <billsix@gmail.com> blessed the
recommendations below — "use your discretion") — **ready to execute; not started.**
**Priority:** 5
**Difficulty:** 4
**Created:** 2026-09-02 (William Emerison Six <billsix@gmail.com>)

## BLUF

Insert a **family/category tier** between the imps root and the per-project folders, so projects
group by the kind of thing they patch: `imps/n64/OcarinaOfTime/`, `imps/n64/MajorasMask/`,
`imps/n64/SuperMario64/`, `imps/n64/BanjoKazooie/`, `imps/n64/libultraship/`, with a future
`imps/openstax/<repo>/` family alongside. **The per-project build/patch machinery is move-safe**
(scripts are `cd "$(dirname "$0")"`-relative and self-contained, `.gitignore` is per-project,
`patches/` apply inside the checkout) — verified 2026-09-02 — so this is a **docs-and-layout change
with near-zero risk to anything that builds or runs.** The substantive work is **re-tiering
`CLAUDE.md`**: move the N64/HarbourMasters-specific content into a new `n64/CLAUDE.md` (which
auto-loads via ancestor-CLAUDE.md loading only for N64 sessions), leaving the master generic and
family-agnostic. "Done" = the 5 projects live under `n64/`, `CLAUDE.md` + `n64/CLAUDE.md` split
cleanly, `README.md` grouped by family, every cross-link/path fixed, and a project still
`fetch`/`apply`/`build`s from its new path.

## Context — read first

- **`CLAUDE.md`** (master) — the current three-tier doc design and the per-project folder contract.
  This task turns it into a four-tier design (master → **family** → project → reference).
- **`README.md`** — currently a flat per-project list; becomes grouped by family.
- The five project folders each hold self-contained scripts + `patches/` + a tier-2 `CLAUDE.md`.

**Why now:** imps is going multi-family — the maintainer wants an `openstax/` group (patches for the
`osbooks-*` textbook repos) beside the N64 game ports. imps's doc design already leans on Claude
Code's **ancestor-`CLAUDE.md` loading** (a session anywhere under the repo auto-loads every
`CLAUDE.md` from cwd up to the root), so a family tier is the natural fit: `n64/CLAUDE.md` loads
exactly for N64 sessions and `openstax/CLAUDE.md` for textbook sessions, and neither pays for the
other's noise.

## Decisions (blessed 2026-09-02; discretion granted)

1. **Create `n64/` now** and move the 5 existing projects into it. **`openstax/` is the motivating
   second family but is NOT created in this task** — empty dirs aren't tracked by git, and there are
   no openstax projects here yet. This task only establishes `n64/` and makes the master docs
   family-generic so `openstax/` slots in trivially when its first project lands.
2. **`tasks/`, `tasks/reference/`, and `tasks/archive/` stay PROJECT-KEYED — do NOT add a family
   level there.** Rationale: the tasks system keys off the **project name** (task docs are
   project-prefixed like `ocarina-*`; reference docs live at `tasks/reference/<project>/`; the local
   archive override is `tasks/archive/<project>/<YYYY>/<MM>/<DD>/`), and project names stay unique
   (`osbooks-*` cannot collide with N64 game names). Mirroring the family level into `tasks/` would
   be pure churn + verbosity (`tasks/reference/n64/ocarina/`, prefixes like `n64-ocarina-*`) for no
   discoverability gain — the folder tier and `n64/CLAUDE.md` already express the family grouping.
   The **only** `tasks/`-related edit is one clarifying clause in the master `CLAUDE.md` (see step 4):
   `<project>` is the reference/archive key **regardless of which family folder the project sits in**.
   (Escape hatch: if a future name collision ever occurs, prefix only that one project — not the
   whole scheme.)
3. **Re-tier `CLAUDE.md`** (the real work): the master keeps only the **cross-family** contracts; a
   new **`n64/CLAUDE.md`** absorbs the N64/HarbourMasters-specific material. See step 3 for the exact
   split.
4. **The per-project folder contract is somewhat N64-flavored** (podman AppImage, CI-mirror
   Dockerfile). Generalize: the master states the *generic* self-contained-folder principle (docs in
   imps, patches carry code, a project is a self-contained folder with its own fetch/apply/build/run
   + docs); each **family** `CLAUDE.md` specifies that family's concrete build/patch contract. The
   HarbourMasters-port contract (fetch pristine upstream at a pin, `git am` the series, podman
   AppImage) moves to `n64/CLAUDE.md`; openstax will state its own when it arrives.

## Move-safe — verified 2026-09-02; the executor need NOT touch these

- **Scripts** (`fetch.sh`/`apply.sh`/`build.sh`/`run.sh`): all start `cd "$(dirname "$0")"` and use
  only paths inside their own project folder (the sole `../` is `run.sh`'s `cd runDir &&
  ../bldInstall/...`, siblings inside the project). None reach the imps root → unaffected by the move.
- **`.gitignore`**: per-project (each dir + each checkout has its own; there is no root `.gitignore`
  with project-path patterns) → unaffected.
- **`patches/`**: apply inside the checkout, which lives inside the project folder wherever it sits →
  unaffected. **No patch regeneration is needed.**

## Plan (execute in order)

1. **Create `n64/` and move the projects** (one `git mv` each; the checkouts/build dirs are untracked
   and move with the folder on disk, or are simply re-fetched):
   `git mv OcarinaOfTime MajorasMask SuperMario64 BanjoKazooie libultraship n64/`
   (Note: untracked `Shipwright/`, `build-cmake/`, `runDir/`, etc. are not moved by `git mv` — move
   them on disk with a plain `mv` if you want to preserve a built checkout, or just let `fetch.sh`
   re-clone. Either is fine; nothing tracked depends on them.)
2. **Fix the ~36 relative doc cross-links** (`grep -roE '\]\(\.\./[^)]+' n64/*/CLAUDE.md tasks/`
   after the move to enumerate). Two kinds:
   - a per-project `CLAUDE.md` linking `../tasks/...` → now `../../tasks/...` (the project got one
     level deeper);
   - any doc linking to a **project path** → gains the `n64/` segment (`../../OcarinaOfTime/` →
     `../../n64/OcarinaOfTime/`, etc.).
   Do it with a reviewed script (save it under `tasks/adhoc/imps-family-folder-restructure/`), and
   **verify every rewritten link resolves** (`test -f` each target) before committing — imps docs are
   heavily cross-linked and a broken relative link is exactly the kind of rot to avoid.
3. **Re-tier `CLAUDE.md`.** Create **`n64/CLAUDE.md`** and MOVE these master sections into it (they
   are entirely N64/HarbourMasters-specific):
   - the **"Derived artifacts — where drift occurs"** table (all HarbourMasters CI workflows, SDL/
     tinyxml2/libzip versions, libultraship pins);
   - the **"Never build a checkout from a foreign toolchain via a bind mount"** gotcha (a
     libultraship-artifact-pollution issue);
   - the **podman-build** half of the per-project folder contract (Dockerfile/Makefile CI-mirror
     AppImage template, `VARIANT` switch);
   - the **libultraship** engine paragraph + the **Projects** index for the 5 N64 folders.
   The master **keeps** (generalized to be family-agnostic): what imps is; the doc-tier design (now
   **four** tiers — add the family tier and explain the ancestor-loading benefit); the *generic*
   self-contained-folder principle (docs in imps, patches carry code); the **patch philosophy**
   (upstream-first); the **unsigned-commits** rule; the **tasks/archive** convention (+ the step-2
   project-keyed clause); and a **family index** (`n64/` → `n64/CLAUDE.md`; `openstax/` → later).
   The master's per-project *folder contract* becomes: "each family defines its concrete
   build/patch contract in its family `CLAUDE.md`; the N64 contract is in `n64/CLAUDE.md`."
4. **Update `README.md`**: group the per-project sections under `## N64 ports (HarbourMasters)` and a
   stub `## OpenStax` ("coming — the `osbooks-*` textbook repos"); update the quick-start paths
   (`cd OcarinaOfTime` → `cd n64/OcarinaOfTime`).
5. **Fix prose path references** (`OcarinaOfTime/` → `n64/OcarinaOfTime/`, etc.) in the master
   `CLAUDE.md`, `README.md`, and the ~5 task docs that name project paths (the
   `*-upstream-container-ci.md` set + `ocarina-save-generator-story-flags.md`). Match the **path**,
   not the bare project name (don't rewrite "OcarinaOfTime" used as a proper noun).

## Verification (before staging)

- **A project still works from its new path**: `cd n64/OcarinaOfTime && ./fetch.sh` (or confirm the
  moved checkout is intact) then `./apply.sh` succeeds — proving the scripts are path-independent as
  claimed. (A full `./build.sh` is the strongest check but slow; at minimum fetch+apply.)
- **No broken relative links**: the step-2 checker reports every `](../…)` target resolving.
- **`git grep -n 'OcarinaOfTime/\|MajorasMask/\|SuperMario64/\|BanjoKazooie/\|libultraship/'`** on the
  docs shows only `n64/`-prefixed paths remain (no stale top-level project paths in prose/links).
- **Doc-tier sanity**: open a shell in `n64/OcarinaOfTime/` and confirm the intended
  master→`n64/`→project `CLAUDE.md` chain is what an agent would load (ancestors from cwd to root).

## Notes / gotchas for the executor

- This is a **structural doc change, not a patch change** — `patches/` are untouched and need no
  regeneration; do NOT run `git format-patch`.
- Save the link-rewrite script under `tasks/adhoc/imps-family-folder-restructure/` (per the ad-hoc
  convention) so the mechanical link surgery is reproducible and reviewable.
- When done, this task archives to `tasks/archive/imps/<YYYY>/<MM>/<DD>/` (repo-wide task → `imps`
  project bucket, per the master `CLAUDE.md`).

## OpenStax family — survey findings (2026-09-02; drives a follow-on task)

The motivating second family is concrete: **16 `osbooks-*` repos** under `/foo/opt/openstax`, each
currently checked out on a **`latex` branch**. Upstream is the OpenStax content repo (Pi-mirrored,
e.g. `pi@…/openstax/science/osbooks-anatomy-physiology.git`); the pin is the **merge-base where
`latex` diverges from `main`**, and the `latex`-branch commits are the maintainer's delta.

**What the `latex` delta contains** (surveyed 2026-09-02):
- **A shared CNXML→LaTeX porting toolchain — ~27 hand-authored files, near-identical across all 16
  books:** `tools/cnxml2tex/` (converter), `latex/osbook.cls`+`osbook-*.sty`, the container build
  (`Dockerfile`/`Makefile`/`pyproject.toml`/`entrypoint/*.sh` → HTML/PDF/EPUB), `tools/pandoc/`
  templates, `tools/tests/`. This is the real hand-authored code.
- **Plus, for some books, thousands of FETCHED/GENERATED assets** produced by the toolchain's own
  fetch scripts: e.g. organic-chemistry's delta is 4062 files = 2076 `.jpg` + 1959 exercise `.json`
  (653k insertions) pulled by `fetch-exercises.sh`/`convert.py`. Delta sizes: 6 books are
  toolchain-only (~27 files); the rest add fetched assets up to ~4062 files.

**Maintainer decision (2026-09-02, mid-investigation):** the fetched content **is wanted tracked** —
*"a book should have all of its content"* — **plus a script to redownload/refresh it.** So it is NOT
out-of-scope like the N64 ROM/`o2r`. That reframes the question from *whether* to carry it to *how*:
the ~27-file hand-authored toolchain is a clean `format-patch` series, but the books that downloaded
content have **thousands of binary images**, an awkward fit for `git am` patches (bulky base85 binary
diffs). Also the toolchain is **shared** across all 16 books, so 16 near-identical copies-as-patches
is a smell. Both are open design questions below.

**Contract differences from N64** (for the eventual `openstax/CLAUDE.md`): a LaTeX conversion is
**never upstreamed to OpenStax**, so the family is *all personal patches* — no upstream-submission
tier. The "build" is the container `latexmk`→PDF the toolchain already provides.

**Populating `openstax/` is a SEPARATE follow-on task**, gated on the maintainer's answers to the
questions below (which decide toolchain-vs-assets scope and shared-vs-per-book layout). This
restructure task only establishes the `openstax/` family folder + family-generic master docs.

## Open questions

For THIS restructure task: none blocking — recommendations blessed, discretion granted (2026-09-02).

For the OpenStax follow-on (must be answered before that task is written/executed):
1. **Carrier for the tracked downloaded content** (maintainer wants it tracked + a redownload
   script). `git am` patches are a poor fit for thousands of binary images, so: **(a)** carry
   EVERYTHING (toolchain + assets) as the `format-patch` series anyway — purest imps model, bulky
   binary patches but `git am` handles them; or **(b)** carry the hand-authored toolchain as patches
   and the downloaded assets as a **committed subtree** in the book folder (clean patches; content
   tracked directly in imps). Both paired with a redownload/refresh script in the toolchain.
   Recommend **(b)**. Either way, a **redownload script is a required deliverable** per the maintainer.
2. **Shared vs per-book toolchain** — the ~27 toolchain files are near-identical across all 16 books;
   hoist them once to `openstax/` (shared) with each book folder carrying only its thin per-book
   delta (pin + book-specific config), or keep each book self-contained with its own copy (matching
   the N64 self-contained-folder contract)?
3. **Build contract** — do OpenStax book folders get the full fetch/apply/**build** contract (the
   container `make pdf`/`html`/`epub`), or just fetch/apply/patches?
4. **Scope/sequencing** — all 16 at once, or land the structure + one small book (e.g.
   anatomy-physiology, toolchain-only) as the pattern first, then fan out?
