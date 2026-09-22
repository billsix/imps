# Reference: assembly-isms in Ship of Harkinian's OoT decomp — what they are, what was rewritten, what remains

> **Provenance:** written 2026-09-23 from the survey and first cut of
> `tasks/ocarina-de-disassemble-ugly-c.md` (2026-09-22, pin `acdbc651d`). The four reader reports
> under `tasks/adhoc/ocarina-assembly-isms/reports/` hold the per-site tables and grep commands;
> this is the durable summary. The patterns and semantic rules shared with SM64 are in
> `tasks/reference/mario64/assembly-isms-in-the-decomp.md` — read that first; this doc records only
> what is *different* in SoH and what the cut found.

## What "upstream" and "compiled" mean here

- `soh/src/` is the zeldaret/oot decomp as SoH carries it, with **SoH's own enhancement code
  interleaved** (`CVarGetInteger(...)` guards, `GameInteractor` hooks, whole SoH-authored actors
  such as `En_Partner`). A rewrite never touches those lines; `git blame` tells them apart, and the
  readers listed the SoH-authored constructs class by class (9 gotos, 3 `== true`, 24 mechanical
  rename touches of decomp constructs that are still decomp).
- The port compiles the decomp as **C23 with GCC at `-O2`, `-fno-fast-math -ffp-contract=off`,
  no LTO on Linux** — so a per-file gate is faithful, and unlike SM64's `-O1` a byte loop could in
  principle fold to `memcpy` (not attempted in the first cut). **117 of 804 `.c` files are not
  compiled** (`libultra/`, `dmadata/`, `elf_message/`; `data/uncompiled.txt`): they cannot be
  gated, so they are left alone — which is why the `register` class (48 declarations, all in
  `libultra/`) is empty for OoT.
- `-w` is in the flags: `-Wshadow`, `-Wunused` and friends are silent. A rename or deletion must
  be checked by grep and by the gate, not by warnings.

## What SoH has that SM64 does not (and the verdicts)

| idiom | verdict | why |
|---|---|---|
| `if (1) {}` / `if (0) { rodata strings }` / `if (x) {}` matching blocks | empty `if (<read>) {}` DONE (72); `if (1) {` unwrapped (8); `if (0)` string blocks LEAVE | the `if (0)` blocks are the only record of the retail debug prints; a port has no rodata contract but the text is documentary |
| `s32 pad;` function-local padding (never `UNUSED`) | DONE: 1 710 declarations, 461 files | the census regex missed every bare `s32 pad;` — the naming reader rebuilt the worklist per function (`data/filler_function_local_unreferenced.txt`); 14 locals named `pad` are real variables and are not on it |
| `pad*`/`unk_XX` struct members | LEAVE | `SaveManager.cpp` and `savestates.cpp` memcpy whole structs; layout is load-bearing |
| `PARAMS_GET_U/S/NOMASK/NOSHIFT` exist (`z64actor.h`) but ~1 050 raw `params` masks remain in 190 actors | CARE, not done | pure macros, identical by construction, but a per-actor naming job (`ENXXX_GET_*` in each `.h`); **never** turn the sign-extending `(p & 0xFF00) >> 8` into the zero-extending `(p >> 8) & 0xFF` |
| angles: no integer `DEG_TO_BINANG`; `DEGF_TO_BINANG(180.0f)` is `(s16)32768.0f` = UB; `BINANG_ROT180` is `(s16)(x - 0x7FFF)`, off by one from `+ 0x8000` | LEAVE the whole class | the SM64 `DEGREES()` rows have no exact OoT equivalent; a new integer macro would be the first patch |
| `GET/SET_EVENTINF_HORSES_*` macros exist; the raw `eventInf[0] & 0xF` sites did not use them | DONE (15 sites) | pure macros; `Flags_UnsetEventChkInf` is a *function*, so the `eventChkInf[11] &= ~bit` sites (7) are an explained diff |
| `(uintptr_t)ptr + N` passed to a pointer parameter | DONE (`(u8*)`) | compiles only under `-Wno-int-conversion`; GCC 16 rejects it without the flag — a real portability fix, not taste |
| `switch (bool)` with `case false:`/`case true:` and no `default` | CARE (8 sites) | `if/else` gains behaviour for values ≠ 0/1 and moves the layout |
| `(s16)frameCount` on an `f32` holding an integer (22) | explained diff | numerically a no-op, `cvttss2si`+`cvtsi2ss` differ |
| "missing return" `//!` notes (`z_camera.c` ×4, …) | LEAVE / explained | legal C because every caller ignores the value; adding `return` changes the epilogue |
| `//!` annotations (121 distinct) | almost all C1 (shipped behaviour, preserve) | one dead block deleted (En_Ossan's `> 10 && < 0`), six stale notes reworded |

## What the first cut did (36 patches, all codegen-identical)

booleans on 0/1 operands (14 files); the 72 empty ifs; `goto`→`return`/`continue`; self-assignments,
fake temps, dead locals/stores, aliases, `(*p).f`, `((void)0, x)`, `& 0xFFFFFFFF`; `if (1) {`
unwraps; empty arms + the ucode_disas inversion; unreachable `break` / stray `;`; the seven
`z_parameter.c` `else if` tails; `isMaterialApplied++`; `? true : false`, `!! == 0`, a result
temp; `== 1` on bitfields; En_Ossan's dead block; `& 0xFFFF` before 16-bit stores (15 files);
En_Wood02's UB left shifts; `(f32)Animation_GetLastFrame` ×32; `(s32)` promotion no-ops ×7;
`fwork[GDF_FWORK_1]`; the horse-race macros; `(u8*)` arithmetic; the pad sweep; nine test-first
loops; stale notes; Yoda flips and nested-if merges (63 files). Full per-batch log: the task.

**Gate results that were not what the reader expected** (and are now rules): `if (c) return true;
return false;` → `return c;` differs at `-O2` (a branch pair vs `setcc`); a `goto` to the very
next statement anchors a basic block (deleting it re-laid out a 418-line TU); a self-store spelled
through a pointer (`En_Ma3`) survives as a real store; three `return 1` replacing three `goto
block_2` stop tail-merging; two digit loops in `z_file_choose.c` differ once the test is in the
header. All are semantically identical and sit in `tasks/ocarina-standard-c-explained-diffs.md`.

## What remains (by size)

1. **Explained diffs** — 18 items, `tasks/ocarina-standard-c-explained-diffs.md`.
2. **Naming** — 1 988 stack-slot / `temp_` / `phi_` declarations in 748 functions (~85% nameable;
   8 two-meaning slots need a second variable, 5 loop-carried `phi_` groups are rename-only), 172
   `argN` definitions in `code/` (~110 nameable; never the `z64audio.h` `u8 arg0/1/2` fields; rename
   call chains together), the per-actor `params` macros. Tool: `tools/standard-c/rename_in_function.py`;
   compile touched files with `-Wshadow` besides the gate.
3. **Bugs** — `tasks/ocarina-decomp-bugs-found-by-survey.md` (uninitialised `getItemId`/`fairyType`,
   the `sOwEntranceFlag[20]` overread, the 32-bit sentinel in `z_en_horse.c`).
4. **Upstream** — `tasks/ocarina-upstream-standard-c.md`.

## Relationship to the rename stream

The 488-patch `personal` rename stream now sits **on top of** `standard-c` (`patches/ORDER`), so
every new rewrite is written against the pin's address-named tree and the renames are re-cut over
it (`tasks/reference/imps/recutting-a-stream-under-a-new-base.md`). Practical consequence: a site
in this doc is named by its pin-time name (`func_808AC22C`), while the applied checkout shows the
renamed one (`BgSpot01Objects2_GetPathPoint`); `git grep` on branch `imps-standard-c` for the
former, `imps-applied` for the latter.
