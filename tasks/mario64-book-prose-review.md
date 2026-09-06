# Mario 64 book: prose review & coordination

**Status:** proposed — the maintainer drives this (his book, his voice)
**Priority:** 3
**Difficulty:** 5
**Part of:** `mario64-sphinx-book.md` (umbrella)

## BLUF

Review and polish the book's first full draft (`n64/SuperMario64/book/`, 13
chapters + intro + 5 appendices) with the maintainer — his book, his voice, his
students. This is the "coordinate back and forth a lot" pass he asked for. The
draft is a scaffold to react to, not a finished text: chapters can deepen,
reorder, split, or be rewritten. Done when the maintainer is satisfied the book
reads the way he wants for a student who finished `modelviewprojection`.

## Context

- The draft was written autonomously 2026-09-06 from the reference set
  (`tasks/reference/mario64/`), in the black-box/white-box structure the
  maintainer chose (the pipeline chapter is the black-box spine; chapters link
  out to detail and down to the reference notes). It builds to HTML/EPUB/PDF.
- Every code snippet is a real `literalinclude` by named doc-region, so editing
  prose never risks the code samples.
- The maintainer said authoring may spawn NEW reference docs and deeper levels
  of detail as review finds gaps — expected, not scope creep.

## How to review (suggested)

Go chapter by chapter (the toctree order in `docs/index.rst`). For each:

1. **Voice & level** — does it sound like the maintainer, and is it pitched
   right for a post-`modelviewprojection` student? Trim or expand.
2. **The compare-to-your-course framing** — is the "you learned X; here's what a
   real game does" hook landing, or forced?
3. **Black-box/white-box links** — are the `:doc:` cross-references sending the
   reader to the right place at the right moment?
4. **Figures** — are the Graphviz diagrams and ASCII art helping? More? Fewer?
5. **Depth** — what got glossed that should be a chapter section, and what
   should move to an appendix or the reference set?
6. **Code snippets** — is each `literalinclude` the right span? (If not, adjust
   the doc-region marker in the source — grows patch 0005 / the LUS lane.)

Capture decisions here as they're made; spin off child tasks for anything big
(a rewrite, a new chapter, a new reference doc).

## Chapters to review

Part I: rotation, engine-math, camera, projection.
Part II: pipeline (the black-box hub), shaders, textures, lighting.
Part III: animation, collision, effects, frame-interpolation, sound.
Appendices: A fixed-point matrices, B binary-angle table, C geo bytecode,
D curves/splines, E the reference set.



## Self-review pass 1 — intro + rotation (2026-09-06)

Did a self-review of the first two chapters and applied the safe improvements;
the judgment calls below are for the maintainer.

**intro.rst — changed:**
- Rewrote "The plan" to reflect the ACTUAL structure (Parts I/II/III, all 13
  chapters) and to introduce the book's organizing idea up front: the black-box
  "one frame's journey" spine with white-box links. The old version listed five
  vague bullets and never mentioned the spine.
- Fixed "margin notes" → "Go deeper boxes" (there are no margin notes; they are
  `.. admonition:: seealso` blocks).

**rotation.rst — changed:**
- Fixed the ASCII binary-angle circle: the old one labelled 0x0000 "east" and
  0x8000 "west" (a muddled compass); replaced with a clean clock (0° top, 90°
  right, 180° bottom, 270° left) labelled by angle only.
- Added a cross-link to :doc:`engine-math` where the matrix's transposed layout
  is explained, and to the new :doc:`appendix-binary-angles` for the sine-table
  trick.

**Judgment calls for the maintainer (I did NOT change these):**
1. Tone/voice — does the intro's "you already know X; here's what a real game
   does" hook sound like you, or too breezy?
2. The rotation `literalinclude` shows the whole ~30-line matrix builder. Keep
   it whole (shows the hand-multiplied Euler product), or trim to a few rows?
3. Do you want the ASCII diagrams at all, or would you rather these be Graphviz
   (consistent with the rest) or dropped?
4. Reading order — is putting rotation FIRST (as the warm-up) right, or should
   the black-box "one frame" overview come first so the reader sees the whole
   shape before any detail?

## Related

- The book: `mario64-sphinx-book.md`. The arc: `mario64-book-chapter-outline.md`.
- The backing detail: `tasks/reference/mario64/`.
