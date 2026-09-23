# SuperMario64: the assembly-ism rewrites deliberately left OUT of `standard-c` (codegen changes)

**Status:** proposed — needs go-ahead (William Emerison Six <billsix@gmail.com> asked 2026-09-22
for the deliberate omissions to be their own task; the go-ahead here is per item or per group,
after the identical set has been reviewed and played)
**Priority:** 5 · **Difficulty:** 5 (each item is small; the cost is that none can be proven by
the gate, so every one needs the maintainer's in-game oracle)
**Project key:** mario64
**Depends on:** `tasks/archive/mario64/2026/09/23/mario64-assembly-isms-to-standard-c.md` (its Phase B.11 — this task is that
list, promoted); stream and tools there.

## BLUF

Everything in the assembly-isms catalogue that is behaviour-preserving **by argument** but changes
the generated code — so the `standard-c` stream's rule ("byte-identical assembly or it does not go
in") excluded it. Done = each item below is either landed as its own commit whose message carries
the explained diff (in a separate stream, `patches/standard-c-explained/`, listed in `ORDER`
right after `standard-c`), verified in-game by the maintainer, or declined here with a reason.

## Context

- The first cut's rule and why it matters: `tasks/reference/mario64/assembly-isms-in-the-decomp.md`
  ("What the first cut found"): "assembly-identical" is stricter than "behaviour-identical", and
  the gap is exactly the compiler's knowledge — an `s32` field only ever assigned 0/1 is a boolean
  to the reader but not to GCC.
- Gate: `ASMDIFF_BUILD=<configured cmake tree> bash tools/asmdiff.sh
  <file> HEAD` prints the differing hunks; the commit message quotes them and says why they are
  the same program. The maintainer's host build + play of the affected area is the oracle.
- Keep this a **separate stream**, not a tail of `standard-c`: the identical set is upstream-bound
  as-is (`tasks/mario64-upstream-standard-c.md`); these are a harder sell and must be droppable
  independently.

## The list (reverted during the first cut; worklogs under `tasks/adhoc/mario64-assembly-isms/data/`)

| # | site | rewrite | why codegen differs | risk |
|---|---|---|---|---|
| 1 | `mario_actions_cutscene.c` (`<< 16 >> 16` ×2, the NPC-turn and jumbo-star angle differences) | `(s16)(a - b)` | GCC then knows only the low 16 bits matter: `movzwl` + `subl %r14d` instead of two `movswl` + `subl` — same low-16 result | none; **removes UB** (left shift of a negative int). Best first item. |
| 2 | 40 files, ~130 sites of `== TRUE` / `!= FALSE` / `== FALSE` on plain `s32` object fields and globals (`tasks/adhoc/mario64-assembly-isms/data/batch5_bool_deferred.txt`; regenerate with `tools/standard-c/drop_true_false_cmp.py` and keep only what the gate says differs) | `x` / `!x` | `cmp $1` → `test` | the survey read every field: each is only ever assigned TRUE/FALSE; a value of 2 would change behaviour (`== TRUE` false vs `x` true). Hot: `menu/file_select.c` (40). |
| 3 | `behaviors/spindel.inc.c` speed ladder | `switch` with stacked cases | GCC emits a jump table (2560 lines move) | none; equivalent by inspection. |
| 4 | `menu/file_select.c` `print_menu_cursor` two complementary `if`s | `if/else` | the compiler must re-read the static between the two `if`s (the `gSPDisplayList(gDisplayListHead++ …)` write could alias it); the rewrite removes the re-read | none unless `sCursorClickingTimer` aliases the display-list head, which it does not. |
| 5 | `behaviors/bowser.inc.c` `switch (oBowserIsReacting)` | `if/else` | block layout (3869 lines move) | field is only ever TRUE/FALSE after `standard-c` #43 (`++` → `= TRUE`). |
| 6 | `game/print.c` digit-counter loop (test hoisted into the body) | `while ((powBase = int_pow(base, numDigits)) <= (u32) n) numDigits++;` | GCC lays the loop out differently (306 lines) | low value, equivalent. |
| 7 | goddard open-coded byte loops: `objects.c` zeroing loop, `renderer.c` ×3 (`dest[i] = src[i]`, `((u8 *) p1cont)[i] = 0`, `str[i] = buf[i]`), `joints.c:891`, `dynlist_proc.c copy_bytes` | `memset` / `memcpy` | the port builds at `-O1`; GCC only turns byte loops into libc calls at `-O2`+ (`-ftree-loop-distribute-patterns`) | none; needs `<string.h>` and the dead loop locals removed. |
| 8 | `behaviors/heave_ho.inc.c` two-exit search loop | `for` + `return` | loop shape | read the two exits carefully (`i` is used after). |
| 9 | action ladders (`express_elevator.inc.c`, `bowser.inc.c` ×6, …) | `switch` | jump tables | only after proving no arm's write makes a later arm's test true — per site. |
| 10 | `DEGREES()` for the safe multiples of 5.625° (`+ 0x8000` → `DEGREES(180)`, `±0x4000`, the 42 `-0x8000` yaw args in `file_select.c`) | macro | none expected — but `DEGREES` is scoped to camera code; first patch moves it to `macros.h` | exact iff `x*65536 % 360 == 0`; `camera.c:5090` `0x22AA` is NOT one. |
| 11 | `!= 0` / `== 0` on verified booleans (~60, capped) | drop | as #2 | as #2. |

## Plan

- [ ] Maintainer picks the first group (recommend #1 + #3 + #4 + #7: no invariant needed, pure
      compiler-layout diffs plus a UB fix).
- [ ] Per item: commit on a branch `imps-standard-c-explained` at the tip of the applied
      `standard-c` stream; message = rule + the quoted asm hunks + the argument; export to
      `patches/standard-c-explained/`; add the stream to `patches/ORDER` after `standard-c`;
      `tools/check_patches_apply.sh SuperMario64`.
- [ ] Maintainer host build + play of the affected area per group; record the verdict here.

## Notes / decisions

## Open questions

1. Start with the no-invariant group (#1, #3, #4, #7) — yes/no? Recommendation: yes.
