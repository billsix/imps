# Mario 64: the "how a production game is built" Sphinx book (UMBRELLA)

**Status:** proposed — needs go-ahead; this is a large multi-phase
initiative that will spawn many child tasks over time.
**Priority:** 3
**Difficulty:** 9

## BLUF

Build a **definitive, student-facing book** — a Sphinx document in the style
of the maintainer's `modelviewprojection` (github.com/billsix/modelviewprojection),
buildable to **HTML, PDF, and EPUB** — that teaches, from the real Super
Mario 64 (Ghostship) source, **how a production game is actually made**: the
math, the graphics pipeline, lighting, textures, camera, animation, collision,
sound, and the systems that tie them together. It uses **`literalinclude` code
references** (pulling exact spans by *named doc-region*, not line numbers),
**Graphviz diagrams**, and **ASCII art**, and it is grounded in the reference
set already built at `tasks/reference/mario64/`. This is a **coordination-heavy,
many-child umbrella**; it will keep producing **new reference docs and new
levels of detail** as knowledge is extracted for the book. Done when a
student can read it front to back and understand how to build a real 3D game.

## Context — read first

- **The reference set is the raw material, not the book.** `tasks/reference/mario64/`
  holds 23 topics at levels L0-L2 (see its `README.md` map) plus the
  architecture docs. Those are the maintainer-facing *knowledge*; the book is
  the polished, sequenced, student-facing *narrative* distilled from them. The
  book will send us back into the code to write MORE reference docs and deeper
  levels of detail as gaps surface — that extraction is expected and ongoing
  (maintainer, 2026-09-06).
- **The model to imitate:** `modelviewprojection` — a Sphinx book built around
  one running example, one concept per chapter, each motivated concretely,
  buildable to HTML/PDF/EPUB. Study its `book/docs/` structure, `conf.py`, and
  its `# doc-region-begin/end` + `literalinclude` mechanism (the same markers
  this book needs; the L0 capsule of mvp is in `tasks/reference/mario64/`'s
  sibling work / the umbrella `mario64-graphics-refdocs.md`).
- **Code references need doc-regions.** The book's `literalinclude` directives
  pull code by **named region** (`:start-after: // doc-region-begin foo` /
  `:end-before: // doc-region-end foo`), so the markers must exist in the
  (patched) Ghostship + libultraship source. The initial 39 regions are seeded
  by `mario64-graphics-refdocs-step-7b-doc-region-patches.md`; **the book will
  drive MANY more** — doc-region creation is a continuous activity under this
  umbrella, in the imps two-lane patch model (`n64/CLAUDE.md`).
- **Build dependency to design around:** `literalinclude` reads the source at
  a path, and the doc-region markers only exist in the **patched** checkout
  (pin + patches). So building the book requires the patched Ghostship tree
  present — a real architectural constraint (see Open questions).

## Vision — what "definitive" means here

A reader who finishes it should understand, with real code in front of them:
- the applied math (vectors, matrices, transforms, rotation) as a shipping
  engine uses it — and how it relates to the GA/linear-algebra they may know;
- the full graphics pipeline from N64 display list to modern GPU, including
  generated shaders, textures, sampling, and the color combiner;
- how a scene is structured (scene graph), lit, animated, and made to collide;
- the effects that give a game life (skybox, water, transparency, the
  wobbling paintings) and how cheap the tricks really are;
- and the engineering seams (translation layers, caches, backends, asset
  replacement) that make a cross-platform port possible.
It should be the book the maintainer wishes existed when learning to build a
production game.

## Ingredients (the "how")

- **Sphinx** (furo theme, `myst-nb`/`nbsphinx` as mvp uses) → HTML; **LuaLaTeX**
  → PDF (Unicode math, per the sandbox's book toolchain); EPUB.
- **`literalinclude`** with named doc-regions for every code reference — never
  pasted code that can drift.
- **Graphviz** (`.. graphviz::` / `.. digraph::`) for pipelines, the scene
  graph, data-flow, state machines (camera modes, painting ripple states).
- **ASCII art** for layered/box diagrams inline where a figure is overkill.
- **The reference docs** as the per-topic source of truth and the place deeper
  detail lives; the book cites/derives from them.

## Shape (initial, to be refined together)

This will become a **step-task umbrella** with children. Likely early phases
(each its own task doc when we commit to it):
1. **Book scaffold** — decide the book's home (Open questions), stand up the
   Sphinx project (conf.py, toctree, build to HTML/PDF/EPUB green on a
   trivial page), wire it to the patched Ghostship source for `literalinclude`.
2. **Chapter outline** — sequence the 23+ topics into a teachable arc (the
   mvp move: one running thread, concept per chapter, motivated concretely).
3. **Per-chapter authoring** — one child task per chapter (or cluster),
   each: write the narrative from the reference doc, add the doc-regions the
   chapter needs (patch pass), draw the Graphviz/ASCII figures, build-verify.
4. **Doc-region expansion** — ongoing; `-step-7b-` is the seed set.
5. **New reference docs / deeper LoD** — spawned as authoring finds gaps.

## Relationship to existing work

- **Feeds on:** `mario64-graphics-refdocs.md` (the reference set + LoD system +
  the two-lane patch model) and its `-step-7b-` doc-region seed.
- **Will extend:** the reference set (new topics, new L0/L1/L2, per the
  evolvable-LoD standing permission).
- **Sibling books:** once proven for Mario 64, the same could apply to the
  other three games (their reference umbrellas exist:
  `{ocarina,mm,banjo}-graphics-refdocs.md`), but that is out of scope here.

## Open questions (for the maintainer — see the closing list at report time)

1. **Where does the book live?** — a NEW dedicated repo (like
   `modelviewprojection` is its own repo), or a directory inside imps (e.g.
   `n64/SuperMario64/book/`)? This drives the whole scaffold and the
   literalinclude-from-patched-source build design.
2. **Build environment** — its own container-per-project template (Dockerfile +
   Makefile like mvp), or reuse the sandbox's Sphinx/LuaLaTeX toolchain?
3. **Scope of the running example** — mvp uses ONE running example throughout;
   should this book pick a single spine (e.g. "follow one triangle / one frame"),
   or be topic-organized like the reference set?
