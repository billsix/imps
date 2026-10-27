# Tier-2 sweep: update historical docs for the upstreamable-<slug> stream rename

**Status:** proposed — needs go-ahead
**Priority:** 6
**Difficulty:** 3

## BLUF

The 2026-10-27 stream reorg (`tasks/archive/imps/2026/10/27/imps-upstreamable-stream-reorg.md`) renamed the patch streams
(`standard-c` → `upstreamable-standard-c`, `personal` → `upstreamable-rename-decomp`, and
`upstream-candidates/` split into one `upstreamable-<slug>/` per PR). The convention + operational docs
were updated in that change; this task is the **deferred Tier-2 pass** over the remaining historical task
docs and reference docs that still use the old stream names. **Done =** every stale `patches/<old>/` path
citation (a broken link) is repointed to the new folder, consistently, and staged.

## Context

Deliberately deferred from the reorg to keep that change focused on the convention + operational docs
(master/family/per-project `CLAUDE.md`, `apply.sh`, READMEs, `patch-streams-design.md`, the appimage task
doc). The remaining references are mostly in historical/archival-adjacent docs.

**Scope distinction:** fix **path citations** — `patches/standard-c/`, `patches/personal/`,
`patches/upstream-candidates/` — because those are now broken links to folders that moved. A bare
*conceptual* mention of "standard-c" (e.g. the asmdiff tooling's "standard-c stream" as a category, or
narration of the 2026-09-22 work) can stay, or get a one-time note, at the editor's discretion — it is not
a broken artifact. Do not rewrite historical narrative wholesale.

## Where to look

`grep -rlnE 'standard-c|upstream-candidates|patches/personal' tasks/ --include='*.md'`, minus
`tasks/archive/` and `tasks/adhoc/`. As of 2026-10-27 the candidates were:

- Task docs (mario64/ocarina lines of work): `tasks/mario64-decomp-rename-and-cleanup.md`,
  `tasks/mario64-standard-c-explained-diffs.md`, `tasks/mario64-standard-c-naming.md`,
  `tasks/mario64-surface-collision-dangling-pointer.md`, `tasks/mario64-upstream-standard-c.md`,
  `tasks/ocarina-decomp-bugs-found-by-survey.md`, `tasks/ocarina-rename-personal-stream-to-renaming.md`,
  `tasks/ocarina-review-recut-rename-patches.md`, `tasks/ocarina-standard-c-explained-diffs.md`,
  `tasks/ocarina-standard-c-naming.md`, `tasks/ocarina-upstream-standard-c.md`,
  `tasks/papermario-upstream-patches.md`, `tasks/imps-check-upstreams-and-rebase-patches.md`.
- Reference docs: `tasks/reference/imps/standard-c-tooling.md`,
  `tasks/reference/imps/recutting-a-stream-under-a-new-base.md`,
  `tasks/reference/imps/game-port-history.md`, `tasks/reference/imps/derived-artifact-drift.md`,
  `tasks/reference/mario64/assembly-isms-in-the-decomp.md`,
  `tasks/reference/ocarina/assembly-isms-in-soh.md`,
  `tasks/reference/papermario/rom-import-investigation.md`.
  (`tasks/reference/gzdoom/*` and `tasks/ripgrep-refdocs-and-book.md` matched on unrelated "standard-c"
  text — verify, likely leave.)

Note `tasks/ocarina-rename-personal-stream-to-renaming.md` may now be moot — the `personal` stream was
renamed to `upstreamable-rename-decomp` by the reorg; check whether that task is satisfied/obsolete.

## Open questions

1. Any reference doc that is pinned to a dependency version or describes a point-in-time crawl
   (`game-port-history.md`) — update only the path citations, or also reconcile other drift found in
   passing? (Recommend: only the path citations here; broader reconciliation is its own job.)
