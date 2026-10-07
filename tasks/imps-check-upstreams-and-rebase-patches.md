# imps — check upstreams for updates and rebase our patch series onto them

**Status:** proposed — needs go-ahead (filed 2026-10-07 at the maintainer's request).
**Priority:** 5
**Difficulty:** 6 (the N64 decomp ports carry most of it; a HarbourMasters bump can be a large refactor, not line drift)
**Created:** 2026-10-07 (William Emerison Six <billsix@gmail.com>: "look to see for updates to upstream sources, see what's changed, and see if we can rebase our local patches on top. … some of the projects may have taken part of my github pull requests … use your discretion")

## BLUF

For every imps-carried upstream, compare our pinned base SHA against the upstream's current
branch head, summarize what changed, and **attempt the pin-bump operation** (re-fetch at the
new head, replay our `patches/` series with `git am --3way`, resolve, build, run) where it's
clean enough to be worth it. A first-class goal of this pass: **detect where upstream has
merged (part of) the maintainer's GitHub pull requests** — those patches now apply empty or
conflict because the code is already upstream, and the right move is to **drop/trim them**, not
force them. Done = a per-upstream drift+PR-absorption report, plus, for each upstream we
actually bump, an updated `PIN_SHA` in `fetch.sh` + regenerated `patches/` + refreshed docs,
staged as one unit per upstream, `tools/check_patches_apply.sh` green. Recon is read-only;
moving any pin waits for the maintainer's go-ahead per upstream (see Open questions).

## Context

- **The pin-bump operation is already defined** in the master `CLAUDE.md` ("Working on a
  project — agent contract" → *Pin bumps are a defined operation*): fetch upstream, `git am
  --3way` the series onto the candidate SHA on a branch, resolve conflicts, check for
  **non-textual** breakage (upstream-added references to symbols our series renames), build +
  run, then update `PIN_SHA` in `fetch.sh` (that variable name in every project), regenerate
  the series, and refresh pin references + provenance banners in the docs — **one staged unit**.
  Re-verify every derived artifact against its source (the drift table in `n64/CLAUDE.md`).
- **Moving a pin is a deliberate act** (master `CLAUDE.md` Rules): re-verify the series applies
  and the project builds before the new SHA is committed. The agent **stages**; the maintainer
  commits (and imps itself is **never** configured unsigned — do not touch `imps/.git/config`'s
  `commit.gpgsign`; see the Rules section of the master `CLAUDE.md`).
- **The gate:** `tools/check_patches_apply.sh [project]` resets each project to its pin and runs
  its own `apply.sh` (real path: stream order, both lanes, pin guard), reporting the per-lane
  commit count. A failure IS the pin-bump conflict surfacing early. It leaves each checkout on
  the fully-applied series and never touches `runDir/` (a sibling of the checkout — **sacred**,
  never deleted/rewritten).
- **standard-c streams have an extra gate:** any replayed rewrite of a decomp's assembly-isms
  must still compile byte-identically — `tools/asmdiff.sh` / `tools/asmdiff_tree.sh`
  (`tasks/reference/imps/standard-c-tooling.md`). After a base bump, re-run the asmdiff gate;
  if upstream changed a touched file, a rename stream may need re-cutting under the new base
  (`tools/resolve_rename_conflicts.py`; `tasks/reference/imps/recutting-a-stream-under-a-new-base.md`).
- **Comment-only (docs/book) streams** have `tools/check_comment_only_streams.sh` — re-prove
  after a bump.

### The upstreams today (pin → upstream; read current pins from each `fetch.sh`, these are 2026-10-07)

**n64/ (HarbourMasters PC ports + engine) — code-patch family, `n64/CLAUDE.md`:**

| project | upstream | pin (PIN_SHA) |
|---|---|---|
| OcarinaOfTime | github.com/HarbourMasters/Shipwright | `acdbc651` |
| MajorasMask | github.com/HarbourMasters/2ship2harkinian | `04a1a431` |
| SuperMario64 | github.com/HarbourMasters/Ghostship | `49c5312a` |
| BanjoKazooie | github.com/HarbourMasters/Lighthouse | `6d30df9a` |
| PaperMario | github.com/HarbourMasters/PaperBoat | `424c220f` |
| libultraship | github.com/Kenix3/libultraship | `c151cc91` |

**games/ (`games/CLAUDE.md`):** gzdoom — github.com/ZDoom/gzdoom `99aa489d` + its ZMusic dep
github.com/ZDoom/ZMusic `95efd37c` (two pins in one `fetch.sh`).

**unixutils/ (doc-only carriers, `unixutils/CLAUDE.md`):** ripgrep — github.com/BurntSushi/ripgrep
`4649aa97`; dash — kernel.org primary, mirror github.com/tklauser/dash `037bbdfd` (v0.5.13.5).

**android/ (doc-only, `android/CLAUDE.md`):** fossify — **multi-repo**, pins in the `repos`
manifest (`android/fossify/repos`, one `url sha` line per repo), not a single `PIN_SHA`.

### Where the maintainer's merged PRs matter most

The maintainer has open/merged PRs against several of these (the `*-upstream-*` tasks are the
submission side: `tasks/papermario-upstream-patches.md`, `tasks/ocarina-upstream-standard-c.md`,
`tasks/mario64-upstream-standard-c.md`). **Upstream may have merged some without our knowing.**
During recon, for each upstream check whether our patch subjects / the maintainer's authored
commits already appear in `PIN_SHA..head` (`git log --author=billsix`, subject match,
`git log --grep`), and when replaying, treat an **empty `git am` patch** ("No changes — did you
forget to use 'git add'?") or a conflict-that-is-already-applied as **evidence upstream absorbed
it** → drop that patch from the series, note it in the per-project `CLAUDE.md` patch list, don't
force it.

## Plan

1. **Recon (read-only), per upstream** — `git ls-remote <url>` for the head; shallow-fetch and
   `git log --oneline <PIN_SHA>..<head>` for the changelog; count commits, flag big refactors
   (HarbourMasters rewrites are not line drift). Detect PR absorption (above). Produce a report:
   per upstream — commits behind, headline changes, PRs absorbed, rebase risk (clean / conflicts
   / needs re-cut), recommendation.
2. **Report and get per-upstream go-ahead** (Open question 1). Do not move pins in recon.
3. **Per approved upstream, do the pin-bump operation** (defined above): branch at the candidate
   SHA, `git am --3way` the series, resolve, drop absorbed patches, re-run the family gates
   (`check_patches_apply.sh`, asmdiff for standard-c, comment-only for docs/book), **build + run**
   (host scripts; podman where it exists), then update `PIN_SHA`/`repos`, regenerate `patches/`,
   refresh pins + provenance banners + drift tables, and **stage** the unit. One upstream per unit.
4. **Report exceptions afterward** (bulk done / opted-out / outright-skipped and why), per the
   "use your discretion" contract.

## Recon results (2026-10-07, overnight run — read-only `git ls-remote` vs each `PIN_SHA`)

**All 10 upstreams are BEHIND** their default-branch head:

| project | upstream | pinned | head (default branch) |
|---|---|---|---|
| OcarinaOfTime | HarbourMasters/Shipwright | `acdbc651` | `ecd889c2` |
| MajorasMask | HarbourMasters/2ship2harkinian | `04a1a431` | `e8757c14` |
| SuperMario64 | HarbourMasters/Ghostship | `49c5312a` | `40eef138` |
| BanjoKazooie | HarbourMasters/Lighthouse | `6d30df9a` | `5c948c59` |
| PaperMario | HarbourMasters/PaperBoat | `424c220f` | `089ffd17` |
| libultraship | Kenix3/libultraship | `c151cc91` | `759b1340` |
| gzdoom | ZDoom/gzdoom | `99aa489d` | `c26ce2e6` |
| ZMusic | ZDoom/ZMusic | `95efd37c` | `d3b73079` |
| ripgrep | BurntSushi/ripgrep | `4649aa97` | `3fce3b5b` |
| dash | tklauser/dash | `037bbdfd` | `057cd650` |

Note: `ls-remote HEAD` is the default branch; some pins were taken from a specific branch (see each
`fetch.sh` comment) — confirm the right branch before computing the commit delta for a bump.

**Correction — the tag-pinned projects were re-checked against their latest RELEASE TAG, not HEAD:**
- **gzdoom** (pin `g4.14.2`): latest stable tag is `g4.14.2` (`g4.15pre` is a pre-release) → **UP-TO-DATE**.
- **ZMusic** (pin `1.3.0`): latest tag `1.3.0` → **UP-TO-DATE**.
- **dash** (pin `v0.5.13.5`): latest kernel.org tag `v0.5.13.5` (the GitHub mirror has no tags) → **UP-TO-DATE**.
- **ripgrep** (pin `14.1.1` commit): latest release `15.2.0` (commit `e89fff89`) → **BEHIND, major-version jump 14→15**.

So the real behind set is: **ripgrep** (→15.2.0), the five HarbourMasters games (develop-branch HEADs),
and the standalone **libultraship** carrier. gzdoom/ZMusic/dash need no bump.

## Rebase-feasibility probe results (2026-10-07, overnight run)

Method: in each existing checkout, `git fetch --depth 1` the new upstream head, detach to it, and
`git am --3way` the patch series (by `patches/ORDER`). Pure feasibility test — no build. Every checkout
was **restored to its prior applied state** afterward; no pins were moved.

| project | target | series | rebase result |
|---|---|---|---|
| **PaperMario** | develop `089ffd17` | 2 (upstream-candidates) | **CLEAN** — both apply, still unmerged upstream |
| **BanjoKazooie** | develop `5c948c59` | 4 (upstream-candidates) | **CLEAN** — all apply, still unmerged |
| **SuperMario64** | develop `40eef138` | 51 (standard-c 46 + cheats 3 + book 1 + cand 1) | **CLEAN textually** — all 51 apply; the standard-c codegen-identity (asmdiff) invariant still needs a build to re-verify |
| **ripgrep** | tag `15.2.0` (`e89fff89`) | 3 (docs) | **CONFLICT** — 0001/0002 apply, 0003 conflicts in `crates/searcher/src/searcher/glue.rs` (code restructured 14→15) |
| **MajorasMask** | develop `e8757c14` | 2 (upstream-candidates) | **CONFLICT** — 0001 (audio crash fix) conflicts in `mm/src/audio/lib/playback.c` |
| **OcarinaOfTime** | develop `ecd889c2` | 524 (standard-c 36 + personal 488) | **CONFLICT** — standard-c conflicts ~20 patches in, at `z_kaleido_collect.c`; and the 488-patch `personal` rename stream would still need re-cutting on the new standard-c tip |
| gzdoom / ZMusic / dash | — | — | **UP-TO-DATE** (latest release tag already pinned) |
| libultraship (carrier) | — | — | **out of scope** — a tag-by-tag documentation crawl (no patch series), advanced deliberately by the maintainer, not a rebase target |

**Merged-PR check:** every clean patch applied as a real change (non-empty `git am`), so upstream has
**not** absorbed any of the maintainer's `upstream-candidates` yet — nothing to drop.

**Why no pins were bumped:** completing an n64 pin bump requires (a) re-verifying the derived artifacts
(`Dockerfile`/`installdependencies.sh`/`build.sh`/`run.sh`) against the new upstream's CI/docs/LUS per
`tasks/reference/imps/derived-artifact-drift.md`, (b) for standard-c, re-running `tools/asmdiff.sh` per
patch against the new compile flags, and (c) a **build + play-test**, which is the maintainer's and
cannot be done autonomously. So the three clean games are **ready to bump pending that verification** —
the rebase (the hard, conflict-prone part) is confirmed clean. See the open questions.

## Decisions (William Emerison Six <billsix@gmail.com>, 2026-10-07)

- **Run autonomously:** after the read-only recon, proceed and bump every upstream whose rebase is
  clean — dropping/trimming PR-absorbed patches — without asking per upstream. **But when an item
  requires too much discretion, STOP on that item and log it in this task as a new open question**
  (don't guess, and don't force it); keep going on the rest. A standard-c re-cut, a large
  HarbourMasters refactor, or an ambiguous "did upstream really absorb this patch?" call are the
  typical stop-and-log cases.

## Notes / decisions (my discretion, adjustable)

- **Recon spans all families**, but the **rebase effort is ranked**: the code-patch families
  (n64, games) first — that's where "rebase our local patches" bites and where PRs get merged —
  then the doc-only carriers (unixutils, android), whose streams are comment-only and cheaper.
- **libultraship is shared** by the n64 games; bump it coherently with the game(s) that consume
  it, not in isolation (a game's pin and its LUS submodule move together).
- ROM/asset acquisition stays out of scope; `runDir/` is sacred and untouched throughout.

## Next actions (DECIDED 2026-10-08 by the maintainer — all "yes"; NOT started)

1. **Bump the three clean-rebasing games — PaperMario, BanjoKazooie, SuperMario64 — the agent does it**
   ("yes you do it"). Per game: set the new `PIN_SHA` in `fetch.sh` (+ pin comment), replay the series
   (`git am --3way`), `git format-patch --no-cover-letter --base=<new> <new>..HEAD -o patches/<stream>/`
   to regenerate, re-verify the derived artifacts against the new upstream
   (`tasks/reference/imps/derived-artifact-drift.md`: Dockerfile vs new CI, `installdependencies.sh` vs
   new docs, `build.sh`/Makefile target names, `run.sh` OpenGL-seed vs the new LUS enum + ROM hashes),
   refresh the per-project `CLAUDE.md`, and **stage** it. **SM64 additionally:** re-run `tools/asmdiff.sh`
   per standard-c patch (needs a build) to re-prove codegen-identity. The **build + play-test is the
   maintainer's** — the agent hands over a staged, derived-artifact-checked bump; the maintainer confirms
   by building/playing. Targets: PaperMario `089ffd17`, BanjoKazooie `5c948c59`, SuperMario64 `40eef138`.
2. **ripgrep 14.1.1 → 15.2.0 — the agent resolves and bumps it** ("yes"). Patches 0001/0002 apply; 0003
   conflicts because `crates/searcher/src/searcher/glue.rs` was restructured 14→15. Re-place the "three
   search strategies" doc comment in the new code, re-prove comment-only
   (`tools/check_comment_only_streams.sh ripgrep`), regenerate the docs stream, bump the pin + comments to
   `15.2.0` (`e89fff89`), update the ripgrep reference docs, stage.
3. **MajorasMask and OcarinaOfTime get their own dedicated pin-bump tasks** ("yes, write it as a todo").
   Filed: `tasks/mm-pin-bump.md` and `tasks/ocarina-pin-bump.md` (both `proposed — todo`). MM's audio-crash
   fix collides with upstream's reworked `playback.c`; OoT's standard-c collides at `z_kaleido_collect.c`
   and its 488-patch `personal` rename stream then needs re-cutting — a substantial task each.

## Open questions

None open — all three decisions are answered above and queued (1 and 2 for the agent to execute next; 3
filed as their own task docs).
