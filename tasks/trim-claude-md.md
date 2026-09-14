# Trim imps's CLAUDE.md files (root 14 KB + n64/ 19.9 KB, loaded every session)

**Status:** Done — trimmed 2026-09-13 (pending archive after the work commit)
**Priority:** 3
**Difficulty:** 3

## Result — before → after (measured 2026-09-13)

Target applied: **MODERATE** (operational/quick-reference kept inline; rationale,
history, deep mechanics, and post-mortems relocated). Per the maintainer's
override, per-game history went to a NON-loaded reference doc
(`tasks/reference/imps/game-port-history.md`), NOT into the ancestor-loaded tier-3
`n64/<Game>/CLAUDE.md` files.

| File | Before | After | Δ |
|---|---|---|---|
| `CLAUDE.md` (root) | 14,056 B | 10,922 B | −3,134 B (−22%) |
| `n64/CLAUDE.md` | 19,904 B | 9,684 B | −10,220 B (−51%) |
| **combined** | 33,960 B | 20,606 B | −13,354 B (−39%) |

A session under a game folder now loads ~20.6 KB of ancestor CLAUDE.md (root +
n64) before its tier-3 file, down from ~34 KB. (Root sits above the ~8.5 KB
projection because the `runDir/` IS SACRED rule + its 3 invariant bullets were
judged safety-operational and kept inline, per MODERATE.)

### What moved, to which reference doc (all prose copied verbatim first)

- **root → `tasks/reference/imps/documentation-structure.md`** (new): the
  dividing-principle full statement, the ancestor-loading rationale + full tier
  descriptions, the why-family-tier reasoning, the tasks/-keying + per-project
  archive-override decision, and the `runDir/` structural-safety proof.
- **root → `tasks/reference/imps/patch-philosophy.md`** (new): the full ranked-goal
  statements, the "what imps actually buys" list, the upstream-vs-pin-bump
  tradeoff, and the patch-lifecycle consequence.
- **n64 → `tasks/reference/imps/patch-streams-design.md`** (new): the two-lane
  origin aside, "why streams exist", the two live ORDER cases (Ocarina, SM64), the
  `apply.sh` internals, and the book-stream comment-only proof mechanics (gcc
  `-fpreprocessed`, `--allow-line-shift`).
- **n64 → `tasks/reference/imps/derived-artifact-drift.md`** (new): the full
  derived-artifact ↔ source-of-truth drift table.
- **n64 → `tasks/reference/imps/n64-build-gotchas.md`** (new): the
  foreign-toolchain-via-bind-mount post-mortem + recovery.
- **n64 → `tasks/reference/imps/game-port-history.md`** (new): the four per-game
  detailed status paragraphs + the libultraship crawl-history detail.
- **Updated:** `tasks/reference/imps/family-tier-and-move-safety.md` — its pointer
  for the four-tier design now names `documentation-structure.md` as well as the
  master CLAUDE.md summary.

Each trimmed section left a 1-2 line pointer (repo-relative path). Not staged,
committed, or archived per the task instructions.

## BLUF
Both of imps's auto-loaded CLAUDE.md files carry durable design rationale, drift
tables, and per-project history that belong in `tasks/reference/` (or the tier-3
per-project CLAUDE.md files that already exist), not in context every session.
Move that detail out and leave one-line pointers, cutting the root from ~14 KB to
~8.5 KB and `n64/CLAUDE.md` from ~19.9 KB to ~9 KB (a working session under a game
folder loads BOTH, so today it pays ~34 KB / ~8.5K tokens of ancestor CLAUDE.md
before any per-project or reference file).

## Context
- Why: `CLAUDE.md` (and every ancestor `CLAUDE.md` on the path from cwd to the
  repo root — so a session under `n64/<Game>/` loads root + `n64/` + the game's
  tier-3 file) is spliced into the model's context on every turn. Method/numbers:
  runCrushInContainer `tasks/reference/crush-context-assembly.md`.
- Sizes: `/foo/opt/imps/CLAUDE.md` 14,056 B ≈ 3.5K tok; `/foo/opt/imps/n64/CLAUDE.md`
  19,904 B ≈ 5.0K tok. **@-imports: none** (neither file has a bare `@path` import
  line — nothing to relocate on that front).
- Convention: `CLAUDE.md` stays lean and operational (loads every session);
  durable detail moves to `tasks/reference/<slug>.md` and is pointed at, not
  `@`-imported. imps namespaces reference docs per project:
  `tasks/reference/imps/<slug>.md` for repo-wide topics.
- This repo already practices the split: three imps reference docs exist and are
  pointed at from CLAUDE.md rather than inlined. This task extends that to the
  rationale/history still sitting inline.
- Existing `tasks/reference/imps/` docs: `family-tier-and-move-safety.md`,
  `splitting-a-patch-series.md`, `squashing-a-produced-series-for-review.md`.
  Note: `family-tier-and-move-safety.md` explicitly says the four-tier design
  "is described in the master CLAUDE.md" — so if that rationale moves to a new
  reference doc, update that pointer in the same change.
- Tier-3 per-project CLAUDE.md files already exist for all four games
  (`n64/{OcarinaOfTime,MajorasMask,SuperMario64,BanjoKazooie}/CLAUDE.md`), so the
  detailed per-project history in `n64/CLAUDE.md` "Projects" has a natural home
  already — it need not create new docs, just relocate into (and dedupe against)
  those tier-3 files, leaving a one-line index at tier 2.

## Stay vs move — root CLAUDE.md

| section | ~bytes | Verdict | Destination |
|---|---|---|---|
| Header + "what this is" (patch-carrier one-para) | ~450 | STAY | CLAUDE.md |
| "Documentation structure — four tiers" | ~2,800 | TRIM | keep the 4-item tier list + family index (~700 B) in CLAUDE.md; MOVE the ancestor-loading rationale, the "why the family tier sits between" reasoning, and the tasks/-keying/archive-override decision → `tasks/reference/imps/documentation-structure.md` |
| "Per-project folder contract" (fetch/build/run/apply/patches) | ~1,600 | STAY | CLAUDE.md (operational — followed while working) |
| "`runDir/` IS SACRED" incl. structural-safety proof | ~1,300 | TRIM | keep the rule + the 3 bullets that state the invariant (~600 B); MOVE the "why it is structurally safe today" prose into `documentation-structure.md` or the folder-contract reference (or drop — it restates the bullets) |
| "Patch philosophy — must keep working" (goals 0/1/2, "what imps buys", lifecycle consequence) | ~3,400 | TRIM | keep the ranked-goals summary (goal 0 primary, upstream-where-it-fits, personal-carried) + the `check_patches_apply.sh` gate command (~900 B); MOVE the "what imps actually buys" list, the upstream-vs-pin-bump tradeoff prose, and the lifecycle-consequence paragraph → `tasks/reference/imps/patch-philosophy.md` |
| "Working on a project — agent contract" | ~1,400 | STAY | CLAUDE.md (operational: assume-applied, deliverable-is-patches, pin-bump op) |
| "Rules" (cd/relative, pin discipline, ROM out-of-scope, unsigned commits) | ~1,100 | STAY | CLAUDE.md (invariant conventions) |
| "Families" index | ~900 | STAY | CLAUDE.md |

Biggest root MOVE candidates: the four-tier documentation-structure rationale
(~2.1 KB net) and the patch-philosophy rationale (~2.5 KB net).

## Stay vs move — n64/CLAUDE.md

| section | ~bytes | Verdict | Destination |
|---|---|---|---|
| Header + "what this is" (N64 family, libultraship) | ~900 | STAY | n64/CLAUDE.md |
| "N64 build/patch contract" (HarbourMasters shape, podman build) | ~1,200 | STAY | n64/CLAUDE.md (operational) |
| "Patches live in TWO lanes" | ~1,300 | STAY (trim) | keep the two-lane contract; drop the origin/mario64-initiative aside |
| "Patches grouped into purpose STREAMS" (stream list, ORDER rule, why-streams, two live cases, apply.sh walk) | ~3,600 | TRIM | keep the stream-folder list + the "within a stream ordered, across streams disjoint" rule + the `ORDER` one-liner (~1,200 B) in n64/CLAUDE.md; MOVE the "why streams exist" rationale, the Ocarina + SuperMario64 worked cases, and the apply.sh internals → `tasks/reference/imps/patch-streams-design.md` |
| "The series must still apply — gated" | ~700 | STAY (trim) | keep the gate command + what it does; drop the dated per-project verification counts |
| "A `book/` stream is comment-only BY CONTRACT — gated" | ~1,700 | TRIM | keep the two gate commands + the one-line contract (~600 B); MOVE the gcc `-fpreprocessed` proof mechanics and the `--allow-line-shift` reasoning → `patch-streams-design.md` (same doc, book-stream section) |
| "Never build a checkout from a foreign toolchain via a bind mount" | ~900 | MOVE | post-mortem gotcha → `tasks/reference/imps/n64-build-gotchas.md`; leave a one-line pointer ("copy source into the throwaway container; don't bind-mount — see …") |
| "Derived artifacts — drift table" | ~3,600 | MOVE | the whole table is pin-bump-time reference, not per-session → `tasks/reference/imps/derived-artifact-drift.md`; keep a one-line pointer + the standing rule "re-verify every derived artifact at each pin bump" |
| "libultraship — the shared engine" | ~1,100 | TRIM | keep 2 lines (docs-only project; crawl complete; current pin) + pointer to `tasks/reference/libultraship/`; drop the crawl-history detail |
| "Projects" (four per-game status paragraphs + libultraship) | ~5,200 | TRIM | keep a one-line-per-project index (upstream URL, pin SHA, one-line status) in n64/CLAUDE.md; MOVE the detailed patch-count/verification-date/fork-migration history into each game's existing tier-3 `n64/<Game>/CLAUDE.md` (dedupe against what's already there) |

Biggest n64 MOVE candidates: the "Projects" history (~4 KB, relocates to the four
existing tier-3 files) and the derived-artifact drift table (~3.6 KB → new
`derived-artifact-drift.md`).

## Projected result
- Root `CLAUDE.md`: ~14,056 B → **~8,500 B** (~2.1K tok).
- `n64/CLAUDE.md`: ~19,904 B → **~9,000 B** (~2.25K tok).
- A session under a game folder drops from ~34 KB to ~17.5 KB of ancestor
  CLAUDE.md (before its tier-3 file and any reference doc).
- New reference docs: `tasks/reference/imps/documentation-structure.md`,
  `tasks/reference/imps/patch-philosophy.md`,
  `tasks/reference/imps/patch-streams-design.md`,
  `tasks/reference/imps/derived-artifact-drift.md`,
  `tasks/reference/imps/n64-build-gotchas.md`.
- Updated: `tasks/reference/imps/family-tier-and-move-safety.md` (its pointer to
  "the master CLAUDE.md" for the four-tier design → the new
  `documentation-structure.md`); the four existing tier-3
  `n64/<Game>/CLAUDE.md` files (absorb the relocated per-project history).

## Open questions (for the maintainer)
1. The book-stream comment-only gate mechanics — fold them into
   `patch-streams-design.md` (recommended: streams and the book gate are one
   topic) or give them their own `book-stream-comment-only-gate.md`?
2. Per-project history relocation target — into the four existing tier-3
   `n64/<Game>/CLAUDE.md` files (recommended, matches the doc-tier design) or a
   `tasks/reference/imps/project-history.md`? The tier-3 files are ancestor-loaded
   for that game's own sessions, so putting long history there re-bloats those
   sessions; if that's a concern, prefer the reference doc.

## Related
- runCrushInContainer `tasks/reference/crush-context-assembly.md` — measurement + method.
- `tasks/reference/imps/family-tier-and-move-safety.md` — existing doc that points
  at the master CLAUDE.md for the four-tier design (pointer to update).
