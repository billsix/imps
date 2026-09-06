# BanjoKazooie: graphics/math reference-doc set (umbrella)

**Status:** proposed — needs go-ahead
**Priority:** 7
**Difficulty:** 7

## BLUF

Produce the same teaching-oriented graphics/math reference set for **Lighthouse (Banjo-Kazooie)**
(BanjoKazooie) that the mario64 initiative produced for Super Mario 64 — the topics
the maintainer's courses (`modelviewprojection`, `geometricalgebra`) don't
cover, each compared to how he teaches it, at layered levels of detail (L0
capsule / L1 orientation / L2 mechanism / L3 source). This umbrella sets
direction; it does NOT itself write the docs. Done when this game's reference
set exists under `tasks/reference/banjo/` with a map/index.

## Context — read the mario64 umbrella first

**The vision, gap analysis, house style, levels-of-detail system, and the
two-lane patch model are ALL in `tasks/mario64-graphics-refdocs.md` — reuse
them, do not re-derive.** This doc records only what is DIFFERENT for BanjoKazooie.
The mario64 set at `tasks/reference/mario64/` (23 topics, L0-L2, a `README.md`
map) is the worked exemplar to imitate for voice and structure.

- **Code under study:** `n64/BanjoKazooie/Lighthouse/` at pin `6d30df9a` (read the exact
  SHA + upstream from `n64/BanjoKazooie/fetch.sh`; upstream `https://github.com/HarbourMasters/Lighthouse`), three bodies of
  code — the game decomp, the port layer (`src/`), and **this game's own
  pinned libultraship submodule** at `2917d0f4 (1.3.1-482)`. Study THAT submodule.
- **Existing reference docs:** `tasks/reference/banjo/` (per `n64/BanjoKazooie/CLAUDE.md`) —
  architecture/orientation docs the new topic docs cross-link, never
  duplicate.

## What differs from mario64 (per-game)

- **Different decomp.** Lighthouse (Banjo-Kazooie) has its own actor, scene, collision, animation,
  camera, and effect systems — the file:line anchors WILL differ from SM64's.
  **The FIRST sub-step is a per-game seam-map survey** (fan out readers,
  verify, distinguish live/dead) before writing docs.
- **Different libultraship pin** (`2917d0f4 (1.3.1-482)`). Pipeline/shader/texture/audio
  topics are shared-engine, so their PROSE can largely be reused from mario64,
  but the anchors differ (older mainline LUS here, NOT the SM64 1.3.1-544
  fork), so re-verify every LUS anchor against THIS submodule. Fork-only
  features (Vulkan backend, HD mip/alt-assets, generated Vulkan shaders) may
  be ABSENT at this older pin — document the absence.
- **Its own two-lane patch model** (game tree + THIS game's libultraship
  submodule), per `n64/CLAUDE.md`. Doc-region markers authored for SM64's LUS
  may need re-anchoring here via `git am`/rebase (different LUS pin).

## Method (mirror mario64's steps, re-scoped)

1. **Seam-map survey** for this game's topics (same gap list, different
   locations).
2. **Foundation:** a `tasks/reference/banjo/README.md` map + template, re-anchor stale
   existing docs, an `absent-topics.md` (what's absent AT THIS PIN — likely
   more than SM64, given older LUS).
3. **Content docs** by lane (math/transforms, camera/projection,
   pipeline/shaders, textures/assets, appearance, engine systems) —
   deepest-first, halve upward, compare to the course, at L0-L2.
4. **Doc-region patch pass** (both lanes) once content exists.

## Cross-game reuse

Shared-engine topics can share prose and doc-region region-names across games,
ported across differing LUS pins with `git am`/rebase. Game-specific topics
(each title's camera, animation, collision, water/skybox equivalents) are
bespoke. The eventual `tasks/reference/` shared index ties all four games'
sets to the course gaps.

## Related

- Exemplar + shared rationale: `tasks/mario64-graphics-refdocs.md`,
  `tasks/reference/mario64/`.
- This game's facts: `n64/BanjoKazooie/CLAUDE.md`. Family contract: `n64/CLAUDE.md`.
