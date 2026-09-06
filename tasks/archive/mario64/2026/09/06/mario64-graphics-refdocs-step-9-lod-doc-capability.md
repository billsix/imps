# SM64 refdocs — Step 9: codify the multi-level-of-detail doc capability

**Status:** done — 2026-09-06 (capability task staged in runClaudeInContainer + runCrushInContainer). Archived same day.
**Priority:** 8
**Difficulty:** 4
**Part of:** `mario64-graphics-refdocs.md` (umbrella)
**Depends on:** the mario64 doc set proving the L0-L3 structure (do this LAST, once the pattern is stable)

## BLUF

After the layered-detail structure (L0 capsule / L1 orientation / L2
mechanism / L3 source-linked) has proven itself across the mario64
reference set, make it a **native capability** in the maintainer's two
sandbox repos — **runClaudeInContainer** and **runCrushInContainer** — so
future sessions produce layered reference docs by default. Per the
maintainer (2026-09-06), it lives in **the nested `CLAUDE.md` convention
plus the command system**, not as loose docs. Done when both repos carry
the convention and a command that scaffolds a layered doc set.

## Context

Read the umbrella's "Levels of detail" section — that is the design this
step promotes from practice to convention. Do NOT invent the scheme here;
harvest what actually worked across steps 1-7 (where the levels split, how
big each was, how they cross-referenced, when L1 earned its place). The
maintainer's existing doc conventions already define single-level
reference docs (`tasks/reference/`, the `/new-reference` command / skill);
this EXTENDS that with the level dimension.

These are OTHER repos. Confirm they are mounted and read their layout
first: runClaudeInContainer holds the shared `entrypoint/dotfiles/.claude/
CLAUDE.md` + `commands/` (the tracked convention + slash-command layer);
runCrushInContainer is the sibling client with its own equivalent. The
deliverable is a task doc IN EACH repo (not in imps), cross-linked back to
this umbrella as the origin/worked-example.

## Deliverables — one task per sandbox repo

For each of runClaudeInContainer and runCrushInContainer, create a task
that adds:

1. **A `CLAUDE.md` convention section** — "Layered reference documents
   (levels of detail)": the L0-L3 definitions, the size budget per level,
   the naming/placement scheme, the up/down cross-linking rule, and the
   "top map doc aggregates every L0" rule. Written generically (not
   Mario-64-specific), citing the mario64 set as the worked example.
2. **A command-system entry** — extend `/new-reference` (or add a sibling
   command / skill) to scaffold a layered set for a topic: generate the
   L0 capsule stub, the L1 orientation stub, and the L2 mechanism stub
   with the banner + course-comparison + cross-links pre-wired, and
   register the topic in the top map doc. Match the existing command
   conventions in each repo.
3. **Consistency across both repos** — the convention and command should
   be the same shape in both (they share the dotfiles/command lineage);
   note any deliberate divergence.

Keep each task `proposed — needs go-ahead`; the maintainer approves
changes to the sandbox conventions/commands themselves (per his
"confirm before acting" rule — the sandbox command/convention layer is
his to approve).

## Verification & done-state

Two task docs exist (one per repo), each cold-readable, harvesting the
proven L0-L3 scheme into a generic convention + command spec, cross-linked
to this umbrella. On their creation, this step and the whole initiative
archive; harvest the gap analysis + the LoD scheme into the standing
`tasks/reference/mario64/` map/index doc per the umbrella's lifecycle.
