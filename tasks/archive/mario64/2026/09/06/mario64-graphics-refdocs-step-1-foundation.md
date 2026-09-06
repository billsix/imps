# SM64 refdocs — Step 1: foundation (template, re-anchor, absent-topics)

**Status:** done — 2026-09-06 (template, map, absent-topics, two docs
re-anchored, family contract recorded). Archived same day.
**Priority:** 2
**Difficulty:** 3
**Part of:** `mario64-graphics-refdocs.md` (umbrella)
**Next:** `mario64-graphics-refdocs-step-2-math-transforms.md`

## BLUF

Lay the foundation the content steps lean on: (1) a **doc template /
house-style** for the teaching reference docs; (2) **re-anchor** the two
existing LUS-touching docs to the current pin (their libultraship paths
are stale); (3) write the short **`absent-topics.md`** recording that ray
tracing and implicit modeling are genuinely absent; (4) record the
**two-lane patch model** in `n64/CLAUDE.md`. Done when the template
exists, the two docs resolve against the current LUS, `absent-topics.md`
is written, and the family contract is updated.

## Context

Read the umbrella first for the house-style rules and the patch model.
Code under study: `n64/SuperMario64/Ghostship/` at `49c5312a`, LUS
submodule `Ghostship/libultraship/` at `c151cc91` (the 1.3.1-544 fork).

**Why re-anchor now:** the seam-map found the fork split LUS into
`libultraship/src/fast/` (Fast3D interpreter + backends) + `src/ship/` +
`src/libultraship/`, with a real Vulkan backend. The existing
`libultraship-integration.md` and `frame-interpolation.md` cite the old
`e0c1b1fc`/1.3.1-399 layout — stale for LUS, fine for decomp/port. Steps
4-6 build on these, so fix them first.

## Deliverables

1. **`tasks/reference/mario64/_TEMPLATE.md`** (or a "house style" note in
   the umbrella's companion): the provenance-banner block, the required
   "How this relates to the course" section, the anchor/verify rules, and
   the "note candidate `doc-region` spans" convention. **Also define the
   Levels-of-Detail scheme concretely** (L0 capsule / L1 orientation / L2
   mechanism / L3 source-linked, per the umbrella): the size budget for
   each level, the naming/placement (how an L0/L1/L2 for one topic are
   named and cross-linked up/down), and stub the **top L0 map doc**
   (`tasks/reference/mario64/README.md` or `_map.md`) that will aggregate
   every topic's capsule. This scheme is what step 9 later codifies into
   the sandbox repos, so record decisions as you make them.
2. **Re-anchor `libultraship-integration.md`** — update its §4 (graphics)
   and file paths to the fork. New anchors from the seam-map: interpreter
   `libultraship/src/fast/interpreter.cpp` (`Run` at `:6644`,
   `DrawTriangles` at `:146`), backends
   `libultraship/src/fast/backends/gfx_{opengl,vulkan}.cpp`. Keep the
   provenance banner but bump it to the current pin.
3. **Re-anchor `frame-interpolation.md`** — its decomp/port anchors hold;
   fix only the LUS consumption side (the interpreter `Run(... mtx
   replacements ...)` at `interpreter.cpp:6644`, `Engine.cpp:1352`). Note
   the doc is otherwise deep and correct.
4. **`tasks/reference/mario64/absent-topics.md`** (short): ray tracing is
   ABSENT — grep of `libultraship/src/fast/` for `RT64`/`rt64` is empty;
   what people call "RT64 mipmapping" is the auto-mipmap + trilinear
   sampler path (`interpreter.cpp` `UploadMipChain:1950`,
   `gfx_vulkan.cpp` `GetSampler(...autoMipmap)` `:532`), not a tracer.
   Implicit modeling (SDF/metaballs) is ABSENT everywhere. State it so
   nobody re-searches.
5. **`n64/CLAUDE.md`** — add the two-lane patch model (game tree +
   libultraship submodule series) as a family contract, noting each
   game's LUS pin differs.

## Verification

- Open each cited LUS anchor in the pinned submodule and confirm it
  resolves.
- `grep -ri rt64 Ghostship/libultraship/src/fast/` returns nothing
  (proves the absent-topics claim).
- The template renders the banner + course-comparison section other steps
  will copy.

## Done-state

Template written; both docs re-anchored with bumped banners;
`absent-topics.md` staged; `n64/CLAUDE.md` records the two-lane model.
Archive this step to `tasks/archive/mario64/<date>/` on completion.
