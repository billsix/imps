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

## Open questions

None at filing — the execution mode is decided (autonomous, stop-and-log). New open questions get
appended here *during* the sweep for any item that needs the maintainer's call.
