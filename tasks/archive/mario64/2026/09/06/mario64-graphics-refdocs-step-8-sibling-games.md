# SM64 refdocs — Step 8: scaffold sibling-game reference-doc tasks

**Status:** done — 2026-09-06 (three sibling umbrellas: ocarina/mm/banjo). Archived same day.
**Priority:** 7
**Difficulty:** 3
**Part of:** `mario64-graphics-refdocs.md` (umbrella)
**Depends on:** the mario64 doc set (steps 2-7) proving the template
**Next:** `mario64-graphics-refdocs-step-9-lod-doc-capability.md`

## BLUF

Once the Mario 64 reference-doc set exists and has proven the template,
create the same-shape umbrella task for each of the other three games —
**Ocarina of Time, Majora's Mask, Banjo-Kazooie** — so a later session can
produce their graphics/math reference docs in the maintainer's teaching
style. This step SETS DIRECTION; it does not write the sibling docs.

## Context

Read the mario64 umbrella (`mario64-graphics-refdocs.md`) — the sibling
tasks mirror it. The three games are HarbourMasters ports sharing
libultraship but each pins a DIFFERENT LUS commit (Ocarina/MM on older
mainline, Banjo `1.3.1-482`, verify each from the game's `fetch.sh`), so
per-game seam anchors differ and each has its OWN two-lane patch model
(game tree + that game's libultraship submodule series). Each game's
existing reference docs live at `tasks/reference/{ocarina,mm,banjo}/` (see
each project's `CLAUDE.md` index).

## Deliverables — one umbrella task per game

For each of Ocarina, Majora's Mask, Banjo, create
`tasks/<game>-graphics-refdocs.md` (`proposed — needs go-ahead`) that:

1. **Reuses the mario64 gap analysis** (same two courses, same target
   topic list) — reference it, don't re-derive it.
2. **Names the game's own code** — its decomp differences (Zelda games:
   different actor/scene/collision systems; Banjo: its own decomp
   lineage), its port layer, and its OWN pinned libultraship submodule
   SHA (read from `n64/<Game>/fetch.sh`).
3. **Flags per-game seam-mapping as the first sub-step** — the file:line
   anchors WILL differ; each game needs its own seam-map survey (fan out
   readers, verify, distinguish live/dead) before writing docs.
4. **Carries the two-lane patch model** and the doc-region-later-pass
   plan, per the family contract recorded in `n64/CLAUDE.md`.
5. **Notes cross-game reuse opportunities** — shared-engine topics
   (libultraship pipeline/shaders/textures/audio) can share prose and
   `doc-region` markers, ported across the games' differing LUS pins with
   `git am`/rebase; game-specific topics (each title's camera, animation,
   collision, water/skybox equivalents) are bespoke.

Also: propose a short `tasks/reference/` shared index tying all four
games' doc sets to the course gaps (the harvest target when this umbrella
archives).

## Verification & done-state

Three sibling umbrella tasks exist, each cold-readable and cross-linked to
the mario64 umbrella and to its game's `CLAUDE.md`. This step (and the
whole initiative) then archives; harvest the mario64 gap analysis into a
standing `tasks/reference/` index doc per the umbrella's lifecycle note.
