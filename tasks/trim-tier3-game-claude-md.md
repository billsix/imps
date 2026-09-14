# Trim the tier-3 per-game CLAUDE.md files (n64/<Game>/CLAUDE.md)

**Status:** Done — trimmed 2026-09-14 (pending archive after the work commit)
**Priority:** 3
**Difficulty:** 2

## BLUF
The four tier-3 per-game `n64/<Game>/CLAUDE.md` files are ancestor-loaded whenever
a session works under that game's folder, so their long production/verification
narrative wasted per-turn context every session. Trimmed them to MODERATE
(operational: what the port is, its patch/stream list, build/run commands,
build-time gotchas kept inline) and moved history / verification narrative /
podman-build post-mortems into the non-loaded reference doc
`tasks/reference/imps/game-port-history.md`. Combined tier-3 dropped from
40,646 B to 32,646 B (−8,000 B, −20%).

## Context
- Follow-on to `tasks/trim-claude-md.md` (root + `n64/CLAUDE.md` trim, 2026-09-13),
  which deliberately moved per-game history OUT of the tier-3 files into
  `tasks/reference/imps/game-port-history.md` and left `n64/CLAUDE.md` a
  one-line-per-game index. This task extends that trim to the tier-3 files
  themselves.
- Why ancestor-loading costs context: a session under `n64/<Game>/` auto-loads
  root + `n64/` + the game's tier-3 CLAUDE.md every turn. Method/numbers:
  runCrushInContainer `tasks/reference/crush-context-assembly.md`.
- Target = **MODERATE**: keep inline what's needed WHEN WORKING ON THAT GAME;
  move rationale / history / post-mortems / deep mechanics / verification
  narrative. Per-game history → the EXISTING `game-port-history.md` (not back into
  a tier-3 file — they're ancestor-loaded, defeating the point).
- Cross-game mechanism docs already exist and were consulted so nothing is
  duplicated: `patch-streams-design.md`, `n64-build-gotchas.md`,
  `derived-artifact-drift.md`. The tier-3 files now point at those for stream
  internals, the foreign-toolchain post-mortem, and the drift table respectively.

## Result — before → after (measured 2026-09-14)

| File | Before | After | Δ |
|---|---|---|---|
| `n64/OcarinaOfTime/CLAUDE.md` | 13,906 B | 10,081 B | −3,825 B (−28%) |
| `n64/SuperMario64/CLAUDE.md` | 13,103 B | 10,868 B | −2,235 B (−17%) |
| `n64/BanjoKazooie/CLAUDE.md` | 7,707 B | 6,928 B | −779 B (−10%) |
| `n64/MajorasMask/CLAUDE.md` | 5,930 B | 4,769 B | −1,161 B (−20%) |
| **combined** | 40,646 B | 32,646 B | −8,000 B (−20%) |

OcarinaOfTime and SuperMario64 carried the bulk of the narrative and saw the
biggest cuts; BanjoKazooie and MajorasMask were already fairly lean, so their
trims are modest (verification narrative only).

## What moved, to which reference doc

All moved prose was appended VERBATIM to
`tasks/reference/imps/game-port-history.md` (new section "Per-game tier-3 detail
(relocated 2026-09-14)", one `###` subsection per game) BEFORE removal, and
verified present. Each trimmed tier-3 section left a 1-2 line pointer.

- **OcarinaOfTime → `game-port-history.md`**: the decomp-rename production &
  verification history (squash from 3,799 one-rename-per-commit patches,
  provenance counts 665/2,844/272, the split from a 6,854-line commit, the
  original fork port + conflict resolution, container/on-host build-and-run
  verification, the illegible-save-text oddity, the Co-Authored-By/no-session-URL
  note) and the podman-build history (the three runner-provides-it gaps, nested +
  on-host verification). Kept inline: the patch/stream-order rule, the provenance
  comment convention, the four remaining unnamed symbols, the `check_renames.py`
  gate, the tools list, the architecture-reference index, the concise podman
  description.
- **SuperMario64 → `game-port-history.md`**: the cheat-series porting history
  (fork topic branches linearized across the hooks→events restructure, per-patch
  port notes), the libultraship KiritoDv-fork-topology detail, and the
  podman-build history (COPY-vs-bind-mount SELinux rationale, the shaderc/spirv
  skew + compat symlink, nested + on-host verification, the OpenGL-seed
  reasoning). Kept inline: the patch/stream list, the stream-ORDER rule, "how to
  add a cheat", the LUS-fork one-liner + pointer, build-time sandbox deps, the
  RADV Vulkan-hang run gotcha, libtcc rpath, the architecture index, the book +
  LUS doc-region lane.
- **BanjoKazooie → `game-port-history.md`**: the patch-series export history
  (fixOnFedora export, patch 0002 subject repair, byte-identical verification)
  and the podman-build verification narrative. Kept inline: the patch list
  (incl. the freeze-fix explanation), the upstream-PR retirement note, version
  notes, the architecture index, the podman description + the USERNS_FLAG
  deviation.
- **MajorasMask → `game-port-history.md`**: the patch export/verification
  narrative and the podman porting/verification history (from the
  `podmanBuildAppImage` branch). Kept inline: the patch descriptions (audio-fix
  detail (a)-(e)), version notes, and the podman two-variant operational
  description (this folder is the N64 podman reference implementation).

No content was folded into `patch-streams-design.md` / `n64-build-gotchas.md` /
`derived-artifact-drift.md` — the tier-3 files already pointed at those (or gained
pointers); the per-game narrative belonged in `game-port-history.md`.

Not staged, committed, or archived (per instructions).

## Related
- `tasks/trim-claude-md.md` — the root + `n64/` trim this extends.
- `tasks/reference/imps/game-port-history.md` — destination for all moved prose.
- runCrushInContainer `tasks/reference/crush-context-assembly.md` — ancestor
  CLAUDE.md loading, measurement + method.
