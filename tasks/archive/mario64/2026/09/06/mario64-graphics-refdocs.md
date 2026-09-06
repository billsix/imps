# SuperMario64: graphics/math reference-doc set (umbrella)

**Status:** DONE — 2026-09-06. The reference set was built: 23 topics under
`tasks/reference/mario64/` at levels of detail (L0 map capsules, L1 orientation
where warranted, L2 anchored mechanism), each compared to the maintainer's
courses. Steps 1-9 completed; step 7b (doc-region markers) was prepped and
handed to the Sphinx-book effort. Archived 2026-09-06.
**Priority:** 2
**Difficulty:** 7

## BLUF

Produce a large set of **teaching-oriented reference documents** on the
Super Mario 64 (Ghostship) source — game/port code AND its pinned
libultraship fork — covering the graphics and applied-math topics the
maintainer's two courses (`modelviewprojection` and `geometricalgebra`)
do **not** cover, or cover only thinly. The maintainer teaches a graphics
course and wants Mario 64 as a worked source of real-engine examples for
the gaps: lighting, textures, camera-as-a-system, animation, collision,
transparency/skybox/water, the color-combiner→shader path, sound, and
more. **Every doc explicitly compares the engine's approach to how the
maintainer already teaches the topic** (e.g. SM64 Euler binary-angle
rotation vs. the course's geometric-algebra rotors). This is the
**first pass: reference docs only**; a later pass may add Sphinx
`doc-region` markers as patches so the docs can feed a Sphinx book. The
last step scaffolds sibling task docs for the other three games. Done
when the mario64 reference-doc set (steps 1-7) exists, is verified against
the current pin, and the sibling-game tasks (step 8) are filed.

## Outcome (retrospective)

The initiative produced a 23-topic teaching reference set that maps the SM64
(Ghostship) source to the maintainer's graphics-course gaps, each doc written
deepest-first (L2) then summarized upward into an L0 capsule (and an L1 when
the mental model was non-obvious and self-contained). The `README.md` map
aggregates every capsule. The rotation doc (Euler binary angles vs GA rotors)
was the showpiece. The levels-of-detail method and its calibration rule were
proven and logged for step 9 to codify. The doc-region patch pass (step 7b)
was fully prepared — a 39-region worklist, both lanes set up — and folded into
the Sphinx-book initiative (`tasks/mario64-sphinx-book.md`), where markers get
added per-chapter as `literalinclude` needs them. Sibling-game umbrellas and
the capability-codification tasks were scaffolded.

## Context — read first

- **This is an imps step-task umbrella.** It holds the vision, the
  shared contract, the doc inventory, and the ordered step index. Each
  step is its own cold-readable task doc
  (`tasks/mario64-graphics-refdocs-step-N-*.md`) carrying the detailed
  source anchors for its docs. Read the imps master `CLAUDE.md` and
  `n64/CLAUDE.md` for the repo/family contracts, and
  `n64/SuperMario64/CLAUDE.md` for the project's pin and gotchas.
- **The code under study** is `n64/SuperMario64/Ghostship/` at pin
  `49c5312a` (GitHub develop tip, 2026-09-01), three bodies of code:
  the SM64 decomp (`src/game/`, `src/engine/`, `src/audio/`), the C++
  port layer (`src/port/`), and **the game's own pinned libultraship
  submodule** (`Ghostship/libultraship/`, `c151cc91` = the 1.3.1-544
  KiritoDv fork with a real Vulkan backend). Study THAT submodule, not
  Kenix3 mainline or any other checkout.
- **Existing reference docs** at `tasks/reference/mario64/` are
  ARCHITECTURE/orientation docs ("where does X live"):
  `architecture-overview`, `decomp-map`, `port-layer`,
  `libultraship-integration`, `asset-pipeline`, `frame-interpolation`
  (deep — the framerate topic is already documented in detail),
  `build-system`, plus the cheats plan. The new docs are
  TOPIC/CONCEPT-oriented and **cross-link into these, never duplicate
  them.**
- **The existing docs' libultraship paths are STALE.** They were authored
  around base `67e561c6` with LUS `e0c1b1fc` (1.3.1-399); the pinned LUS
  here is the newer fork, split into `libultraship/src/fast/` (Fast3D) +
  `src/ship/` + `src/libultraship/` with a Vulkan backend. Decomp/port
  paths in the old docs still hold; LUS paths do not. Step 1 re-anchors
  the LUS-touching docs.

### The gap analysis (why these topics) — synthesized from the two courses

`modelviewprojection` (github.com/billsix/modelviewprojection) teaches
linear algebra through an OpenGL model-view-projection pipeline; it
**covers well**: vectors, matrices, the transform math (translate/rotate/
scale, composition, change of basis), the view transform, perspective
projection, NDC/viewport, depth buffer, the pipeline stages, and vertex/
fragment shaders. `geometricalgebra`/gacalc
(github.com/billsix/geometricalgebra) teaches the coordinate-free algebra
of transforms and **stops exactly at the model matrix** (it explicitly
refuses the non-linear perspective step). Rotation in both is taught via
**GA rotors**, not matrices-only and not quaternions.

**What both LACK — the target list, ranked by teaching value:**

1. **Lighting, illumination, reflection, surface shading** — the single
   most explicit hole (the book says outright it omits lighting).
2. **Textures, texture mapping, sampling/filtering** — explicitly
   excluded in the book.
3. **Camera as a SYSTEM** — the courses teach the view-transform *math*;
   neither has a follow/orbit/collision-aware camera controller. The
   maintainer flagged this as directly relevant to his book.
4. **Animation** — the courses have only keyboard-nudged motion + a
   60 Hz cap; no keyframes, interpolation, easing, or delta-time. The
   maintainer said he barely covers it.
5. **Collision detection** — entirely absent from both.
6. **Transparency/alpha blending, skyboxes, water/reflective effects** —
   all absent, all present in SM64 (incl. the wobbling paintings).
7. **Scene / spatial data structures** — the courses have transform
   stacks only; no scene graph.
8. **The color-combiner → generated-shader path and GPU backends** — how
   N64 rendering actually reaches modern GL/Vulkan hardware.
9. **Sound processing** — absent from both.
10. **Orthographic projection** — named but never implemented in the
    book; SM64's HUD/ortho path illustrates it.

**Genuinely absent in the ENGINE too (document the absence, don't hunt):**
ray tracing (the fork has NO RT64/path tracer — "RT64 mipmapping" is just
auto-mipmap + trilinear sampling) and implicit modeling (no SDF/metaballs
anywhere). Per the maintainer's reference-authoring conventions, state
what is NOT here and why, so nobody re-searches for it.

**Rotation is covered thoroughly by the course via GA rotors, but the
maintainer explicitly wants it covered here as a COMPARISON** — SM64's
fixed-point 16-bit Euler "binary angles" + sine/cosine lookup tables +
fixed-axis-order matrix construction, contrasted with the course's
half-angle rotors and the sandwich product: where they agree (same
SO(3) rotation), where they differ (Euler order-dependence / gimbal vs.
coordinate-free rotor composition), and how each interpolates.

## House style — the contract for EVERY reference doc

1. **Compare to how the maintainer teaches it.** Each doc ends with (or
   threads through) a "How this relates to the course" section naming the
   specific `modelviewprojection` chapter or `gacalc` concept, and
   whether the engine's approach matches, differs, or fills a gap. This
   is the whole point of the set — it is not optional.
2. **Anchor to the CURRENT pin.** Every claim carries a `file:line`
   anchor verified against Ghostship `49c5312a` / libultraship
   `c151cc91`. Cite the game/port tree for decomp/port topics and the
   pinned submodule for LUS topics.
3. **Provenance banner** at the top of each doc: the Ghostship pin, the
   LUS submodule SHA, and the authoring date — so a future pin bump can
   detect drift (the same discipline the existing docs use).
4. **Verify before asserting** (the maintainer's reference-authoring
   rule): a reference doc is trusted later without re-checking, so
   confirm anything a reader will trust — especially "X is unused/absent"
   — by grep + reading, not one agent pass. Distinguish live code from
   dead/absent explicitly.
5. **Cross-link, don't duplicate.** Point at the existing architecture
   docs for "where the code lives"; the new docs explain the *concept*
   as the code illustrates it.
6. **`doc-region` markers become the durable anchor (revised 2026-09-06 at
   the maintainer's request).** Line numbers drift (`GfxSpMatrix` moved
   1065→2251 between the old docs and this pin); named regions don't. So
   there is a dedicated **doc-region patch pass** (a real step below) that
   adds `// doc-region-begin <name>` / `// doc-region-end <name>` comments
   into the source as patches (two lanes — game tree + libultraship
   submodule) and converts the docs to cite regions **by name**, keeping
   `file:line` only as a secondary "as of pin `49c5312a`" aid. Until that
   pass runs, each doc's **"Candidate doc-region spans"** section is the
   authoritative shopping list; do NOT cite a region name before its marker
   exists (that would dangle). Doing it as ONE batch (not per topic) avoids
   regenerating the two patch series on every doc.

## Levels of detail — the layered-summary system

(Added at the maintainer's request, 2026-09-06.) Understanding a topic
means seeing it at the right level — from a one-paragraph capsule up to
the source itself. So a topic is **not one doc but a column of docs at
decreasing abstraction**, and a big topic gets up to four levels:

- **L0 — Capsule** (≤1 paragraph / ~5 sentences): the whole topic in a
  breath. All L0s aggregate into one top-level MAP doc so the set is
  graspable at a glance — the same exercise as summarizing the entire
  `modelviewprojection` book in five paragraphs (done 2026-09-06; that
  summary is the template for an L0's voice).
- **L1 — Orientation** (½–1 page, NO code): the mental model — what the
  subsystem does, its key mechanism, and how it maps to the course. Read
  this to "get it" without reading code.
- **L2 — Mechanism** (the main reference, `file:line`-anchored): the
  actual algorithm and data flow. Most of the inventory below is L2.
- **L3 — Source-linked** (finest): pointers into the code and, in the
  later pass, the `doc-region` markers that let Sphinx `literalinclude`
  pull the exact spans — the source IS the finest level.

Rules: every topic has an **L0 and an L2 always**; add **L1** when the
mental model is non-obvious; add **L3/doc-regions** in the later Sphinx
pass. Small topics may fuse L0+L1 or L1+L2. Each doc links UP to its
capsule and DOWN to its detail; the top map doc holds every L0. **Where
the levels split, how big each should be, and how they cross-reference is
itself a deliverable** — once it stabilizes across the mario64 set, step 9
codifies it as a reusable sandbox capability.

**How to generate the levels (the method, William Emerison Six
<billsix@gmail.com>, 2026-09-06):** write the **extreme-detail L2 first**
(you can only summarize what you already hold completely), then compress
**upward**, each level targeting **~half the lines of the level below**,
until you reach a few paragraphs (L0). The halving is a **size budget and
forcing function**, not a literal delete-half: write each level *fresh at
its altitude* so an L0 reads as a clean capsule, not a shrunken mechanism
doc. Halving yields more rungs than we ship (600→300→150→75→~20); keep the
3–4 that land at natural reading stances — **L0** a glance (~15–25 lines),
**L1** understand-without-code (~1 page, ~120–160 lines), **L2** full
anchored depth, **L3** the source — and discard the in-between rungs. The
book-summary done 2026-09-06 is a worked L0.

**The scheme is a hypothesis, and evolvable by standing permission**
(William Emerison Six <billsix@gmail.com>, 2026-09-06): the rung count,
sizes, and split points above are a starting point, not fixed law. I am
authorized to change them **during or after** the work if the source
proves a topic wants a different shape — "we are learning together."
Flag each change and its reason so the pattern's convergence is visible;
whatever the scheme has settled into by the end is what step 9 codifies.

## Working mode — commit as you go, squash after

(Authorized by William Emerison Six <billsix@gmail.com>, 2026-09-06.)
Execution commits freely as it goes (quick-saves, one per doc or small
cluster), **gpg signing disabled repo-locally** (`git config
commit.gpgsign false`, never global — and inside the libultraship
submodule too when the later patch pass commits there), **never pushing**.
At the end of a step (or the initiative), **squash** the quick-saves into
logical units per the imps squash workflow, harvesting the reasoning into
the step/umbrella docs before flattening.

## The patch model (for the later doc-region pass, and all future edits)

(Confirmed with William Emerison Six <billsix@gmail.com>, 2026-09-06.)
Everything lives as patches, the standard imps model, in **two lanes**:

- **Game-tree lane** — patches on the Ghostship tree (the existing
  `n64/SuperMario64/patches/` series), base = the Ghostship pin.
- **libultraship lane (new for imps)** — a SEPARATE patch series applying
  INSIDE `Ghostship/libultraship/`, base = the pinned submodule SHA
  `c151cc91`, with its own apply step. The submodule is its own git repo,
  so signing must be disabled in ITS config too.

Working terms: **commit yes** (disable gpg signing repo-locally —
`git config commit.gpgsign false`, never global — in whichever repo you
commit in, including the submodule), **never push**, free rein on the
patches. The deliverable is the regenerated `patches/` series, not
checkout state. On a Ghostship pin bump: replay both lanes with
`git am --3way` / rebase; the `doc-region` markers are NAMED, so Sphinx
`literalinclude` is immune to line drift even though a rebase can still
conflict on co-edited lines.

**This two-lane model is a family-level contract** — it applies to
Ocarina, Majora's Mask, and Banjo too, each keyed to that game's own
libultraship pin (which differs per game: Ocarina/MM on older mainline,
Banjo on -482, Mario 64 on the -544 fork). It belongs in `n64/CLAUDE.md`;
step 1 records it there.

## Reference-doc inventory (the deliverable)

The table lists the **L2 mechanism doc** for each topic — the anchored
core. Per "Levels of detail" above, each also gets an **L0 capsule**
(aggregated into a top map doc) and, where the mental model is
non-obvious, an **L1 orientation** doc; **L3/doc-regions** come in the
later Sphinx pass. So the ~22 rows below imply more files once the L0/L1
layers are added — that layering is deliberate, not scope creep. Body =
which code: **D** decomp (`src/game`/`src/engine`/`src/audio`), **P** port
(`src/port`), **L** libultraship (pinned submodule). Detailed `file:line`
anchors live in each step-task.

| Doc (new) | Body | Course gap it fills | Step |
|---|---|---|---|
| `vectors-and-vector-math.md` | D | vs course Vector class | 2 |
| `matrices-and-linear-algebra.md` | D+P | fixed-point matrices, matrix pools | 2 |
| `transformations.md` | D | transform composition in a geo stack | 2 |
| `rotation-euler-vs-rotors.md` | D | **the rotation comparison doc** | 2 |
| `camera-system.md` | D+P | camera-as-system (Lakitu) — flagged | 3 |
| `field-of-view-and-projection.md` | D | FOV, perspective + the ortho gap | 3 |
| `curves-and-splines.md` | D | splines (cutscene camera); surfaces absent | 3 |
| `graphics-pipeline.md` | P+L | DL→Fast3D→GPU (extends frame-interp) | 4 |
| `shaders-and-gpu.md` | L | combiner→GLSL/SPIR-V, GL+Vulkan backends | 4 |
| `color-combiner-and-surface-shading.md` | L | CC mux semantics / surface shading | 4 |
| `textures-and-texture-mapping.md` | L | textures/UV/tiles/TLUT — absent in course | 5 |
| `sampling-and-mipmapping.md` | L | filtering, autoMipmap, mip chain | 5 |
| `alternate-and-hd-assets.md` | L | the alt/HD asset path ("they look great!") | 5 |
| `lighting-illumination-reflection.md` | D+L | lighting/reflection — the #1 gap | 6 |
| `transparency-and-blending.md` | D+L | alpha layers/blending — absent in course | 6 |
| `skyboxes.md` | D | skybox drawing/scroll — absent in course | 6 |
| `water-and-moving-textures.md` | D | movtex water, pseudo-refraction | 6 |
| `painting-wobble.md` | D | the rippling paintings — asked by name | 6 |
| `collision-detection.md` | D | surface collision — absent in course | 7 |
| `animation.md` | D+P | skeletal/geo animation — barely covered | 7 |
| `scene-graph-and-data-structures.md` | D | geo tree + display-list buckets | 7 |
| `sound-processing.md` | D+L | decomp synth → LUS audio player | 7 |
| `absent-topics.md` (short) | — | ray tracing + implicit modeling are ABSENT | 1 |

## Step index

Each step is a `tasks/mario64-graphics-refdocs-step-N-<slug>.md`. Content
steps 2-7 depend only on step 1 (the template + re-anchoring); they are
otherwise independent and may run in any order. Step 8 depends on the
mario64 template being proven (do it last).

- [x] **Step 1 — Foundation** (`-step-1-foundation.md`): write the doc
  template/house-style, re-anchor the LUS-touching existing docs
  (`libultraship-integration`, `frame-interpolation`) to the current pin,
  write the short `absent-topics.md`, and record the two-lane patch model
  in `n64/CLAUDE.md`. **P2** (next).
- [x] **Step 2 — Math & transforms** (`-step-2-math-transforms.md`):
  4 docs incl. the rotation comparison. **P4**, after step 1.
- [x] **Step 3 — Camera, projection & curves**
  (`-step-3-camera-projection.md`): 3 docs. **P4**, after step 1.
- [x] **Step 4 — Pipeline, shaders & surface shading**
  (`-step-4-pipeline-shaders.md`): 3 docs. **P4**, after step 1.
- [x] **Step 5 — Textures, sampling & alternate assets**
  (`-step-5-textures-assets.md`): 3 docs. **P4**, after step 1.
- [x] **Step 6 — Appearance: lighting, transparency, skybox, water,
  paintings** (`-step-6-appearance.md`): 5 docs. **P3** (the biggest
  course gap), after step 1.
- [x] **Step 7 — Engine systems: collision, animation, scene graph,
  sound** (`-step-7-engine-systems.md`): 4 docs. **P4**, after step 1.
- [ ] **Step 7b — Doc-region patch pass (both lanes)**
  (`-step-7b-doc-region-patches.md`): after the content docs (steps 2-7)
  exist, add `// doc-region-begin/end <name>` markers into the source for
  every "Candidate doc-region spans" entry, as patches — game-tree markers
  append to `n64/SuperMario64/patches/`, libultraship markers become the
  first entries of a NEW `n64/SuperMario64/patches-libultraship/` series
  (base = submodule `c151cc91`, signing off in the submodule). Then convert
  each doc to cite regions by name. Verify the build still succeeds
  (comments only). **P5**, after step 7.
- [x] **Step 8 — Scaffold sibling-game task docs**
  (`-step-8-sibling-games.md`): create the same-shape umbrella+intent for
  Ocarina, Majora's Mask, Banjo. **P7**, after the mario64 set proves the
  template.
- [x] **Step 9 — Codify the multi-LoD documentation capability**
  (`-step-9-lod-doc-capability.md`): once the L0-L3 structure has proven
  itself across the mario64 set, create tasks in **runClaudeInContainer**
  and **runCrushInContainer** to add the layered-reference-doc system as
  a **CLAUDE.md convention plus a command-system entry** (a
  `/new-reference` enhancement or a new command that scaffolds an L0-L3
  set with cross-links). **P8**, after step 8 — this is the "learn by
  doing, then codify" deliverable.

## Cross-cutting risks

- **LUS fork drift.** The pinned LUS is a fork, not mainline; the crawl
  docs at `tasks/reference/libultraship/` describe mainline tags. Verify
  LUS claims against THIS submodule's code, not the crawl.
- **Live vs. dead code.** The fork carries paths that may be inert (the
  frame-interp doc already found dead recorders). Confirm callers exist
  before documenting a path as "how it works."
- **Scope creep into re-teaching.** These docs illustrate gaps; they must
  not re-teach what the courses already cover well (the transform math,
  the MVP pipeline). Reference the course; spend words on the delta.
- **Over-granular docs.** ~22 docs is deliberate breadth; if two collapse
  naturally (e.g. transparency into water), merge rather than pad.

## Verification (per step and overall)

- Every `file:line` anchor resolves in the pinned checkout at authoring
  time (spot-check by opening it).
- Every doc has the provenance banner and a course-comparison section.
- "Absent/dead" claims are grep-confirmed, not assumed.
- No new doc restates an existing architecture doc; it links instead.
- Docs are staged (imps convention: reference docs are committable);
  committing is the maintainer's, except where he has authorized commits
  for this work.

## Lifecycle

Reference docs are NEVER archived (they are living knowledge). Each
**step-task** archives on its own completion to
`tasks/archive/mario64/<YYYY>/<MM>/<DD>/`. This **umbrella** archives when
step 9 lands; at that point harvest the initiative's rationale (the gap
analysis) into a standing `tasks/reference/mario64/` index doc — which
doubles as the **top L0 map doc** — that ties the set to the course gaps.

## Deviations log (autonomous run started 2026-09-06)

The maintainer authorized changing the steps/LoD scheme as I go, away from
keyboard, and asked me to log deviations here.

- **2026-09-06, step 1:** the existing `frame-interpolation.md` cites
  `interpreter.cpp` INTERNAL line numbers from the old checkout that have
  drifted badly (e.g. `GfxSpMatrix` `:1065`→`:2251`). Fully re-mapping
  interpreter internals is step 4's job (the pipeline/shader docs), so
  step 1 fixed only the port ENTRY points (`ProcessGfxCommands`,
  `RunCommands`), the fork identity, and the banners, and flagged the
  internals as "approximate until step 4." Rationale: keep step 1
  foundational; don't front-load step 4's deep interpreter mapping.
- **2026-09-06, LoD naming:** settled the file convention as L2 =
  `<topic>.md`, L1 = `<topic>-overview.md` (only when warranted), L0 =
  a row in `README.md` (not its own file). Recorded in `_TEMPLATE.md`.
- **2026-09-06, step 2, the L1 calibration (a real process finding):**
  whether a topic earns an L1 turned out to hinge on **whether its mental
  model is BOTH non-obvious AND self-contained**, not on the topic's size.
  Worked examples: *vectors* → L2+L0 (mental model trivial: mutable arrays);
  *matrices* → L2+L1+L0 (dual float/fixed-point + transposed convention is
  non-obvious and self-contained → L1 pays); *transformations* → L2+L0
  (the composition model is non-obvious but NOT self-contained — it bleeds
  into the scene-graph doc, so an L1 would duplicate it; cross-link
  instead); *rotation* → L2+L1+L0 (the Euler-vs-rotor contrast is the whole
  point → L1 carries it prose-only). **Rule of thumb adopted:** write L1
  only when a reader could hold the whole idea from it AND that idea isn't
  another topic's job. This is the kind of finding step 9 codifies.
- **2026-09-06, doc-regions pulled forward (maintainer, mid-run):** the
  maintainer noted the docs lean on line numbers and asked me to add
  `doc-region` markers as patches and cite regions by name, since I have
  patch permission. Decision: keep drafting content docs with verified
  `file:line` + a candidate-spans list, then do ONE **doc-region patch
  pass** (new step 7b) across both lanes rather than per-topic (which would
  regenerate two patch series repeatedly). Docs then switch to named-region
  references; line numbers stay as an "as of pin" aid. This also
  retroactively covers steps 1-6's docs, whose candidate-spans lists are
  the pass's worklist. Rationale: "keep the goal in sight" — the content
  docs are the deliverable; the marker pass is a mechanical transform of
  lists already being built, best batched.
- **2026-09-06, method for steps 3-7 (pending):** steps 1-2 were done by
  hand to set the voice + the L1 rule. For the more independent subsystems
  in steps 3-7 I intend to fan out one reader-subagent per topic to draft
  the L2 (following `_TEMPLATE.md` + these exemplars), then VERIFY anchors
  myself and write the L0/L1 (the summarization is where the LoD judgment
  lives and stays with me). Will log the outcome.

## Open questions

See the closing numbered list in the report that accompanies this task.
