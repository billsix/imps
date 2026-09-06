# Reference: <TOPIC> — <one-line what-it-is>

> **Provenance:** authored <DATE> against Ghostship pin `49c5312a` (GitHub
> develop tip 2026-09-01) and its libultraship submodule `c151cc91`
> (1.3.1-544, the KiritoDv fork). `file:line` anchors are valid at this
> pin; a pin bump must re-verify them. This is a **teaching** doc in the
> mario64 graphics/math set — see the map at
> [`README.md`](README.md) and the umbrella task
> `tasks/mario64-graphics-refdocs.md`.

<!--
  HOUSE STYLE — delete this comment block when filling the template.

  This set has ONE job: show the maintainer's graphics-course topics as a
  real engine implements them, and COMPARE to how he already teaches each
  (modelviewprojection = github.com/billsix/modelviewprojection; gacalc =
  github.com/billsix/geometricalgebra). Every doc:

  - Anchors every claim with file:line at the current pin. VERIFY before
    asserting — a reference doc is trusted later without re-checking.
  - States what is ABSENT/dead explicitly (grep-confirmed), never implied.
  - Cross-links, never duplicates, the architecture docs
    (architecture-overview / decomp-map / port-layer /
    libultraship-integration / asset-pipeline / frame-interpolation /
    build-system).
  - Ends with a "How this relates to the course" section naming the
    specific mvp chapter / gacalc concept and whether the engine matches,
    differs, or fills a gap.
  - Notes candidate `// doc-region-begin <name>` / `// doc-region-end
    <name>` spans for the later Sphinx literalinclude pass (do NOT add the
    markers yet — first pass is prose + inline anchors).

  LEVELS OF DETAIL — a topic is a COLUMN of docs at decreasing detail.
  Generate them DEEPEST-FIRST, then compress UPWARD, each level ~half the
  lines of the one below (a size budget, not delete-half: write each level
  fresh at its altitude). Ship the rungs at natural reading stances:

    L2  <topic>.md            full anchored mechanism (this file; write first)
    L1  <topic>-overview.md   ~1 page, NO code — the mental model
    L0  (a paragraph)         lives in README.md's capsule list, not its own file

  Every topic has L0 + L2; add L1 when the mental model is non-obvious.
  Small topics fuse levels. L0 links down to L1/L2; L1 links up to L0 and
  down to L2; L2 links up. The scheme is evolvable (maintainer's standing
  permission, 2026-09-06) — flag any change in the umbrella's deviations
  log.
-->

## TL;DR

<2-4 sentences: the mechanism in a breath. This is denser than the L0
capsule; the L0 in README.md is written by halving this further.>

## <mechanism sections, file:line-anchored>

...

## How this relates to the course

<Name the mvp chapter / gacalc concept. State: same idea / differs how /
fills which gap. This section is the whole point of the doc.>

## Candidate doc-region spans (for the later Sphinx pass — not yet added)

- `<path>` around `<function>`: region name `<name>` — <why it's a good
  literalinclude for the book>.
