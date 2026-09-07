# Ocarina: deduce names for the symbols zeldaret/oot also leaves address-named

**Status:** proposed — needs go-ahead before the first batch
**Priority:** 5
**Difficulty:** 8
**Started:** 2026-09-07

## BLUF

The zeldaret/oot oracle is **exhausted**: 765 of 4,235 address-named symbols
(18.1%) now carry upstream names, and every remaining candidate has been
checked. **2,565 of the 3,470 that remain are address-named in oot too**, so
there is no authoritative name left to adopt — each needs one *deduced* from its
body and callers, marked `[LLM:HIGH]` or `[LLM:GUESS]` with the evidence. This
task is that work. "Done" is not realistically all 3,470; done is a sustainable
batch loop that keeps the tree compiling and every name traceable, run until the
maintainer calls it.

## Context

### Read first

- **[`tasks/reference/ocarina/decomp-renaming.md`](reference/ocarina/decomp-renaming.md)**
  — the governing conventions: the provenance-comment forms, the declaration
  tag, one rename per commit, the safe-rename mechanic, and the gotchas that
  have actually bitten. **Do not deviate from it.**
- **[`tasks/ocarina-decomp-rename-and-cleanup.md`](ocarina-decomp-rename-and-cleanup.md)**
  — the parent effort, including the 2026-09-07 oracle batches and how to
  rebuild in-sandbox. This task is its remainder.
- **`tasks/adhoc/ocarina-decomp-rename-and-cleanup/oracle.tsv`** — the work-list.
  Filter `verdict == BOTH`; those are the ones needing deduction.
- **[`tasks/reference/ocarina/decomp-map.md`](reference/ocarina/decomp-map.md)**
  — where OoT subsystems live; essential for guessing what a function does.

### Current state (2026-09-07)

- The `personal` stream is **784 patches**, one rename per commit, applying
  clean onto pin `acdbc651d`.
- The patched tree **compiles**: `soh.elf` links, 0 errors.
- Every name currently in the tree is either upstream-sourced (597, verified) or
  an LLM guess from the maintainer's 2026-07-31 batch (142). **Nothing in this
  task's scope has been guessed yet** — that starts here.

### What remains, and why the oracle cannot help

| Verdict | Count | Meaning |
|---|---|---|
| `BOTH` | **2,565** (2,268 func + 297 data) | Address-named in oot too. **This task.** |
| `UNSAFE` | 76 | Alignment found no safe mapping through drift |
| `MISMATCH` | 66 | Bodies diverged past both the literal and structural thresholds |
| `NOFILE` | 4 | No oot counterpart (`padutils.c`, `system_heap.c`, `code_800FBCE0.c`, kaleido) |
| `ADOPT` | 1 | `EnDivingGame_TalkDuringMinigame` — oot's name is already taken by a different SoH function; needs a hand-picked alternative |

The 146 non-`BOTH` rows are worth a second look **before** guessing: they failed
for mechanical reasons, not because upstream lacks a name, so a better path
mapping or a closer oot revision could still yield authoritative names. That is
cheaper and safer than deduction.

### Decisions already made

- **Guessed names are acceptable, provided each is marked with its confidence
  and reason** (William Emerison Six <billsix@gmail.com>, 2026-09-07). Form:
  `// LLM generated name (HIGH|GUESS), was <addr>: <reason from the code>` at
  the definition, plus the short `// was <addr> [LLM:HIGH]` tag at every header
  declaration.
- **A name invented without reading the function is the one outcome that
  actively damages a decomp.** Bulk-generating plausible names would poison the
  tree with confident wrong labels that later readers trust. Read the body and
  the callers, or leave the symbol alone.
- **One rename per commit**, so a wrong guess costs one `git revert`.
- `code_800FBCE0.c` (RCP) was deliberately skipped by the 2026-07-31 batch —
  oot leaves its two functions address-named too and there is no oracle. Skip it
  again unless someone genuinely understands the code.

### Shape of the work

153 files hold the 2,565. The distribution is extremely skewed:

- 4 files have exactly 1; ~30 have ≤3 — **start here** (richest context per
  symbol, lowest risk, per the documented method).
- The tail is brutal: `z_player.c` alone has **390**, `z_en_zl3.c` 201,
  `z_en_zl2.c` 118. Those three are ~28% of the work and should come last, if at
  all — `z_player.c` is 16.6k lines and its action machine is the hardest code
  in the game to name confidently.

## Goal

Give meaningful names to the decomp symbols that upstream also leaves
address-named, working file-by-file from the smallest, deducing each name from
the function's body and callers rather than its shape, marking every one with
its confidence and the reason, and keeping the tree compiling throughout. The
measure of success is not the count renamed but that a later reader can trust —
or overturn — every name, because the evidence for it is recorded next to it.

## Plan

- [ ] **0. Harvest the remaining oracle-backed names first** (146 rows: 76
      UNSAFE, 66 MISMATCH, 4 NOFILE). Try a closer oot revision than `main` to
      collapse drift, and hand-map the 4 NOFILE paths. Authoritative names are
      always preferable to deduced ones.
- [ ] **1. Pick the smallest-file batch** (`oracle.tsv`, `verdict == BOTH`,
      fewest per file). Roughly 30 files at ≤3 symbols each.
- [ ] **2. For each symbol: read the body and every caller.** Name it for what
      it does. `HIGH` when the body makes it unambiguous; `GUESS` when the name
      is inference. If neither, leave it.
- [ ] **3. Apply with the safe-rename mechanic** — scope to the files holding
      the old name, collision-check, one commit per symbol, declaration tags in
      the same commit.
- [ ] **4. Gate:** `n64/OcarinaOfTime/tools/check_renames.py all`.
- [ ] **5. Build** (see the parent task for the in-sandbox recipe — copy the
      checkout out of the repo first).
- [ ] **6. Regenerate the stream** and re-run
      `tools/check_patches_apply.sh OcarinaOfTime`.
- [ ] **7. Log the batch here**, then repeat from step 1.

## Notes / decisions

**Why this is separated from the parent task.** Everything before it was
*adoption* — mechanical, verifiable against upstream, and safe to run in bulk to
a fixpoint. This is *deduction*: irreducibly per-symbol, unverifiable except by
reading, and the place where a bad batch does lasting harm. Mixing the two would
have let the safe work's momentum carry into the unsafe part.

**Throughput is the real constraint, not tooling.** The tools already exist and
are gated. 2,565 symbols means reading 2,565 functions; there is no shortcut
that is not fabrication.

**A note on `z_player.c`.** Its 390 un-named functions are mostly
`Player_Action_*`-adjacent state machine internals. oot leaves them
address-named after years of effort, which is itself evidence they are hard to
name confidently. Treat as the last resort.

## Open questions

1. **How far down the confidence scale should this go?** I would set the bar at:
   name it only when the body supports a specific claim about what it does, and
   otherwise leave the symbol address-named. That yields fewer names of higher
   quality. The alternative — name everything, leaning on `[LLM:GUESS]` to carry
   the doubt — covers more ground but fills the tree with labels nobody should
   trust. Which do you want?
2. **Should the three huge files (`z_player.c` 390, `z_en_zl3.c` 201,
   `z_en_zl2.c` 118 — ~28% of the work) be attempted at all,** or explicitly
   declared out of scope so the effort stays on code where names can be
   defended?
