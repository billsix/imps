# Assembly-isms in Ship of Harkinian (OoT) — control flow and matching-comment classes

Checkout: `n64/OcarinaOfTime/Shipwright`, branch `imps-standard-c` at the pristine pin
`acdbc651d4b11e29518442d6875a3ec181414cfc` ("Fix compat issues loading pre-9.1 saves on 9.2+ (#7132)").
Survey date 2026-09-22. Read-only: every claim below comes from reading the cited lines at this pin; all
paths are relative to the checkout root, line numbers are current. Census logs:
`tasks/adhoc/ocarina-assembly-isms/data/*.txt` (63 goto, 357 labels, 71 infinite loops, 0 do-while-0,
75 empty then-blocks, 9 `if (1)`, 397 else-if ladders, 91 matching comments, 14 AVOID_UB, 15 volatile).

## Build facts that decide what the gate can prove

- **C23, GCC** (`soh/CMakeLists.txt:8` `CMAKE_C_STANDARD 23`). Decomp-file flags include
  `-fno-fast-math -ffp-contract=off -msse2 -mfpmath=sse` (good: float rewrites are not muddied by FMA).
- **The optimisation level is NOT fixed at -O2 — it depends on which build the gate copies flags from.**
  `Shipwright/CMakeLists.txt:150-151` forces `CMAKE_BUILD_TYPE=Debug` when none is given, and the imps
  host `build.sh:19` gives none, so the local `build-cmake/` (CMakeCache `CMAKE_BUILD_TYPE=Debug`) compiles
  every `soh/src` object with `-g` and **no `-O` flag (-O0)**: `build-cmake/build.ninja:15597-15600`
  (`z_camera.c.o`) has `FLAGS = -g -fno-fast-math -ffp-contract=off -Wall … -w`. The podman `Makefile:77`
  configures Release, which is `-O2 -DNDEBUG` (`Shipwright/CMakeLists.txt:137`).
  Consequence: **run the asmdiff gate from a Release configure**. At -O0 GCC emits the load+compare for
  `if (x) {}`, the load/store for `x = x;`, and the store for an unused initialised local, so every
  deletion in classes 3 and 5 would show a DIFF that means nothing about the shipped binary. Also
  `-DNDEBUG` changes `OPEN_DISPS`/`CLOSE_DISPS` (`soh/include/macros.h:205-238`: only the non-NDEBUG
  arm calls `Graph_OpenDisps/CloseDisps(…, __FILE__, __LINE__)`), which matters for the one `goto` whose
  rewrite duplicates `CLOSE_DISPS`.
- `AVOID_UB` is never defined; SoH hard-codes the AVOID_UB variants (`soh/include/macros.h:15-23`,
  `BAD_RETURN(type)` is `void`; `__osMalloc.c:10` `#define OOT_DEBUG 1`). There are no `#ifdef AVOID_UB`,
  `NON_MATCHING` or `NON_EQUIVALENT` regions in `soh/src` — the 14 `avoid_ub.txt` hits are all `OOT_DEBUG`
  in one file (section 6).
- SoH authorship: `git blame` on every site. Commit `39cc86c2` (2022-03-22) is the initial import = decomp
  text. Lines attributed to `99260aca` ("Use PlayState instead of GlobalContext"), `8f126344` (clang-format),
  `b5c6545d` (z_player doc rename), `50837308` (z_en_holl decomp resync) are renames of decomp constructs,
  not new SoH code; I only call a construct SoH's when the surrounding block is port-authored.

## 1. `goto` — 63 hits, 63 real statements, 41 labels

Labels: `labels.txt` yields 39 real labels once `default:`/`case`/prose lines are dropped; its regex misses
the two `label:;` forms (`soh/src/code/audio_playback.c:309 skip:;`, `soh/src/code/graph.c:494 nextFrame:;`),
so the true set is 41 labels for 63 gotos. Three gotos are in `#if 0` text (dead): `fault.c:130`, `:203`
(`#if 0` at `fault.c:118/191`), `z_kaleido_manager.c:99` (`#if 0` at `:88`). Nine are port-authored:
`graph.c:445` (SoH's `RunFrame` coroutine), `z_play.c:1602` (Archez 2024, "SOH [Port]"), `audio_synthesis.c:889`
(inside the "2S2H [Port] [Custom audio]" `CODEC_S16/CODEC_OPUS` case), `z_kaleido_equipment.c:570-617` ×6
(inside "#Region SoH [Enhancements] EquipmentCanBeRemoved"; labels `RESUME_EQUIPMENT*`/`EQUIP_FAIL` added by
Archez 2025 / louist103 2022). Every label below was grepped (`grep -nE '\b<label>:|goto <label>;'`) — the
"unreferenced otherwise" claims are from those greps.

| kind | sites (`goto` → label) | verdict | exact rewrite | why behaviour-preserving | gate |
|---|---|---|---|---|---|
| goto-as-`return` | `soh/src/code/z_player_lib.c:916` → `:922 return_neg:` | **DO** | `goto return_neg;` → `return -1;`; delete `:922-923` | label body is exactly `return -1;`; label referenced only at 916/922 | IDENTICAL |
| goto-as-`return` | `soh/src/code/db_camera.c:1834`, `:1874`, `:2007` → `:1893 block_2:` | **DO** | each → `return 1;`; delete the `block_2:` line (its own `return 1;` at `:1894` stays as the MENU_ERROR arm's tail) | label body is exactly `return 1;`; refs only 1834/1874/1893/2007 | IDENTICAL (three returns of a constant tail-merge at -O2 as the goto did) |
| goto-as-`return` + `if (0)` label home | `soh/src/code/audio_heap.c:442`, `:449` → `:456 fail:` | **DO** | each → `return NULL;`; delete `:455-459` `if (0) { fail: /*comment*/ return NULL; }` (keep the comment "Both sides are being loaded into." on the returns) | label body is `return NULL;`; refs only 442/449/456; the `if (0)` wrapper existed only to give the label a home | IDENTICAL |
| goto-as-`continue` | `soh/src/code/audio_playback.c:239` → `:309 skip:;` | **DO** | `goto skip;` → `continue;`; delete `:309` | `skip:;` is the last statement of the `if (playbackState->priority != 0) {` block (`:220`, closes `:310`), and that block is the last statement of the `for (i…numNotes)` body (closes `:311`) — nothing runs between label and loop end; refs only 239/309 | IDENTICAL |
| goto to the next statement | `soh/src/overlays/actors/ovl_Boss_Dodongo/z_boss_dodongo.c:1290` → `:1292 block_1:` | **DO** | delete `:1286-1292` entirely (`// required for matching`, `if ((limbIndex == 6) \|\| (limbIndex == 7)) { if (this->unk_25C) {} goto block_1; }`, `block_1:`) | the `goto` targets the statement that follows the `if` anyway; the inner `if (this->unk_25C) {}` is a side-effect-free read of a non-volatile field; refs only 1290/1292 | IDENTICAL at -O2 (dead load removed); DIFFERS at -O0 |
| goto-as-cleanup, one macro | `soh/src/code/z_skin.c:211` → `:237 close_disps:` | CARE | `goto close_disps;` → `CLOSE_DISPS(gfxCtx); return;`; delete `:237` | label body is `CLOSE_DISPS(gfxCtx);` then `}`; refs only 211/237 | likely IDENTICAL under `-DNDEBUG` (macro is one call, tail-merged); the non-NDEBUG macro embeds `__LINE__`, so a Debug gate shows a string diff — normalise or leave |
| backward goto = `do/while` | `soh/src/code/audio_load.c:201` → `:180 again:` | CARE | `i = 0; again: … dma = gAudioContext.sampleDmas + i++; if (i <= gAudioContext.sampleDmaListSize1) goto again;` → `i = 0; do { … dma = gAudioContext.sampleDmas + i++; } while (i <= gAudioContext.sampleDmaListSize1);`; delete `again:` (refs only 180/201) | same statements in the same order; the `return` inside stays | likely IDENTICAL (same CFG), but SM64 saw one loop rewrite reschedule — gate it |
| shared tail of two `case`s | `soh/src/code/code_800E4FE0.c:643` → `:646 block_11:` (in `func_800E6128`, `switch (cmd->op)` at `:619`) | CARE (explained diff) | `case 0x4A: case 0x4B: fadeVolume = (cmd->op == 0x4A) ? (s32)cmd->arg1 / 127.0f : ((s32)cmd->arg1 / 100.0f) * seqPlayer->fadeVolume;` then the shared body; delete `block_11:` | `cmd` is a pointer parameter not written in the function, so re-reading `cmd->op` is pure; both arms compute the same float | likely differs (one extra compare) |
| labelled break out of a `switch` inside `while (true)` | `soh/src/code/audio_seqplayer.c:1039`, `:1442` → `:1484 exit_loop:` (+ `:988`, `:997` pre-loop guards) | LEAVE | none without a flag | C has no multi-level break; the two pre-loop gotos could become an `if` around the 480-line loop but the label must stay for 1039/1442 | — |
| labelled break out of nested `for`s | `soh/src/code/ucode_disas.c:637` → `:644 block_1:`, `:679` → `:687 block_2:` | LEAVE | found-flag or helper | the goto skips the fallback `DISAS_LOG` after the double loop | would differ |
| jump over the rest of an `else` | `soh/src/code/audio_heap.c:392`, `:406`, `:419`, `:432` → `:461 done:` | LEAVE | two search loops would need hoisting into predicates | — | — |
| jump over the rest of a then-block | `soh/src/code/audio_playback.c:194`, `:207` → `:219 out:` | LEAVE | a 5-arm `if/else if` chain where arms 2 and 4 fall into a shared release block; restructuring duplicates the block or reorders pointer tests | — | — |
| two-statement error tail | `soh/src/code/audio_playback.c:881`, `:893`, `:902`, `:916` → `:920 null_return:` (`layer->bit3 = true; return NULL;`) | LEAVE | inline ×4 or a helper | not "trivially a return" | — |
| jump over the ADPCM block from inside a `switch` | `soh/src/code/audio_synthesis.c:852`, `:889` → `:981 skip:` | LEAVE | wrap ~90 lines in `else` | `:889` is in port-added code | — |
| error tail with cleanup | `soh/src/boot/z_std_dma.c:79`, `:109` → `:117 end:` (`osInvalICache; osInvalDCache; return ret;`) | LEAVE | — | three statements ×2 | — |
| skip the post-loop reset | `soh/src/code/fault.c:850`, `:854`, `:857` → `:870 end:` | LEAVE | — | the `break` path at `:862` runs `sp = pc = ra = 0` (`:866-868`) which the gotos skip; a flag or ×3 duplication | — |
| dead (`#if 0`) | `fault.c:130`, `:203`, `z_kaleido_manager.c:99` | LEAVE | — | never compiled; a gate on them is meaningless | — |
| SoH coroutine | `soh/src/code/graph.c:445` → `:494 nextFrame:;` (jumps into the `while (GameState_IsRunning)` body) | LEAVE | — | port's own frame-resume state machine | — |
| jump into another `case`'s body | `soh/src/code/z_camera.c:3337`→`:3340 cont:`, `:5528`→`:5536 setEyeNext:`, `:5569`→`:5580 setAtFOVRoll:`, `:5958`→`:5971 skipeyeUpdate:`; `ovl_Boss_Ganon/z_boss_ganon.c:1058`→`:1066`, `:1479`→`:1494` | LEAVE | none in C (fallthrough only reaches the physically next label) | — | — |
| label stacked on a `case` label, goto from inside the previous case | `ovl_Boss_Mo/z_boss_mo.c:825`→`:829 tent_shake:`, `ovl_En_Clear_Tag/z_en_clear_tag.c:387`→`:524 state_crashing:`, `ovl_Fishing/z_fishing.c:3866`→`:3870 hoistCatch:`, `ovl_En_Bb/z_en_bb.c:1168`→`:1181 block_15:` (into `default:`, carries a `//! @bug` note) | LEAVE | none (the goto site is nested under `if`s that otherwise `break`) | — | — |
| guard inversion over ~150 lines | `soh/src/code/z_play.c:1429`, `:1455` → `:1610 Play_Draw_DrawOverlayElements:` | LEAVE | wrap the skybox/world/actor draw in a condition | SoH hooks (`GameInteractor_ExecuteOnPlayDrawEnd`, CVar reads) are interleaved in the skipped region | — |
| skips one debug macro | `soh/src/code/z_play.c:1255` → `:1261 skip:` (skips only `PLAY_LOG(3799)`, a `do{ if (1 & HREG(63)) … } while (0)` macro, `z_play.c:42-47`) | LEAVE | duplicate the macro in two arms | value ≈ 0 | — |
| SoH's | `z_play.c:1602`, `z_kaleido_equipment.c:570/584/593/602/610/617` | LEAVE | — | port enhancement code | — |
| two-statement cleanup | `soh/src/code/z_eff_spark.c:182`, `:271` → `:284 end:` (`CLOSE_DISPS; FrameInterpolation_RecordCloseChild();`) | LEAVE | — | the `:270` `RecordCloseChild()` before the second goto is port-added (Kenix3 2022-08-03) — nesting is easy to get wrong | — |
| goto INTO an `else` block | `soh/src/code/audio_load.c:166` → `:177 search_short_lived:` | LEAVE | hoist the else body into a helper | the label is the first statement inside `} else {` (`:176-177`) | — |

**Look-alikes that are NOT safe:** `audio_heap.c:392-432` look like early-outs but `done:` is not the end
of the function; `fault.c:850-857` look like breaks but skip three stores; `z_std_dma.c` `goto end` is not a
plain return (the invalidations must run); `db_camera.c:1898 goto block_1` sits next to the DO `block_2`
sites but jumps into the middle of `default:` (`:1912`) — leave it in the same patch that fixes `block_2`.

## 2. Infinite loops — 71 hits, 70 real (`audioMgr.c:57` is a comment)

| bucket | sites | verdict |
|---|---|---|
| deliberate halts (empty body) | `boot/idle.c:88`, `boot/is_debug.c:87`, `libultra/os/initialize.c:74`, `code/code_800D31A0.c:8` (sleep forever) | LEAVE |
| thread/event loops (`osRecvMesg` + dispatch) | `boot/z_std_dma.c:311`, `code/main.c:143`, `code/sched.c:438`, `code/fault.c:83`, `:305`, `:984`, `libultra/io/devmgr.c:17`, `:34`, `libultra/io/vimgr.c:72`, `libultra/os/timerintr.c:31`, `code/code_800E4FE0.c:494` | LEAVE |
| script interpreters / parsers | `code/audio_seqplayer.c:482`, `:1000`, `:1542`, `code/z_elf_message.c:120`, `code/z_scene.c:180` (prints before testing), `code/z_message_PAL.c:1027`, `:1366`, `:1899`, `:2282`, `libultra/rmon/xprintf.c:38`, `code/z_jpeg.c:127` (see DO below) | LEAVE (except z_jpeg) |
| linked-list walks, exit tested after the first statement | `code/z_bgcheck.c:484, 543, 690, 771, 882, 941, 1029, 3045, 3242, 3315, 3476, 3576, 3709, 4420, 4522` | LEAVE (the exit is `if (curNode->next == SS_NULL) break; curNode = …` at the bottom, not test-first) |
| multi-exit / exit mid-body | `boot/logutils.c:39`, `:54` (test last), `code/jpegutils.c:39`, `:40`, `code/code_800FCE80.c:45`, `code/z_effect_soft_sprite.c:110` (flag + wrap-around), `ovl_Boss_Ganon2/z_boss_ganon2.c:2329`, `:2405`, `ovl_kaleido_scope/z_kaleido_equipment.c:371`, `:419`, `z_kaleido_item.c:538`, `:574`, `z_kaleido_scope_PAL.c:1230`, `:3332` (exit at `:3373`) | LEAVE |

Test-first search loops (the SM64 pattern-2 rule: only when the exit is the FIRST statement and the negated
test is exact):

| site | rewrite | why exact | gate |
|---|---|---|---|
| `soh/src/code/audio_load.c:958-967` | `while (size >= 0x400) { AudioLoad_Dma(…); osRecvMesg(…); size -= 0x400; … }` | `size` is `size_t` (`:951`); `!(size < 0x400)` ≡ `size >= 0x400` | expected IDENTICAL |
| `soh/src/code/audio_load.c:2020-2041` | `while (gAudioContext.preloadSampleStackTop > 0) { … }` | `s32` (`z64audio.h:844`); the body's `continue` re-tests either way | expected IDENTICAL |
| `soh/src/code/z_jpeg.c:127-130` | `while (!exit) { … }` | `u32 exit` flag; the `break`s at `:137-:210` are `case` breaks inside the inner `switch`, not loop exits | expected IDENTICAL |
| `soh/src/code/z_map_mark.c:113-116` | `while (mapMarkIconData->markType != MAP_MARK_NONE) {` | enum compare; no `continue` in the body (grep) | expected IDENTICAL |
| `soh/src/overlays/misc/ovl_kaleido_scope/z_lmap_mark.c:62-65` | `while (mapMarkData->markType != PAUSE_MAP_MARK_NONE) {` | same; the `break`s at `:115/:118` are inside an inner `switch`/`if` — re-check they are not loop exits before patching | expected IDENTICAL |
| `soh/src/libultra/io/pfsfilestate.c:34-37` | `while (page.ipage >= pfs->inodeStartPage) {` | integer compare, same promotions | expected IDENTICAL |
| `soh/src/overlays/gamestates/ovl_file_choose/z_file_choose.c:241-247`, `:249-255` | `while (*ones >= 100) { (*hundreds)++; *ones -= 100; }` / `while (*ones >= 10) { (*tens)++; *ones -= 10; }` | `*ones` is `s16` promoted to `int`; `(*ones - 100) < 0` ≡ `*ones < 100` with no overflow | expected IDENTICAL |
| `soh/src/overlays/actors/ovl_Bg_Spot16_Bombstone/z_bg_spot16_bombstone.c:295-298` | `while ((u32)this->unk_158 < ARRAY_COUNTU(D_808B5EB0) && this->unk_154 >= D_808B5EB0[this->unk_158][0]) {` | De Morgan on integer tests; `&&` keeps the bounds check before the indexed read exactly as `\|\|` did | expected IDENTICAL |
| `soh/src/code/code_800EC960.c:5419-5423` | `while (func_800F6BB8()) { }` | the function is `void`; `return` on the false branch ≡ falling off the end | expected IDENTICAL |
| `soh/src/code/jpegutils.c:52-56` | `do { code <<= 1; } while (codesLengths[idx] != ++lastLen);` | the comma expression evaluated `code <<= 1` then the test; `do/while` keeps that order | CARE (loop-shape) |
| `soh/src/code/z_eff_blure.c:335-359` | `while (this->elements[0].state == 0) { …shift…; this->numElements--; if (this->numElements <= 0) { this->numElements = 0; return 0; } }` | the loop is `if (c) { body } else { break; }` — pure inversion; `state` is re-read each iteration in both forms | expected IDENTICAL |
| `soh/src/code/z_effect_soft_sprite.c:136-140` | `while (!((priority <= t[i].priority) && !((priority == t[i].priority) && (t[i].flags & 1)))) {` | exact negation of an integer test; ugly — only if the reader wants it | CARE |
| `soh/src/code/audio_playback.c:653-660` | `while ((cur = source->next) != source && cur != NULL) { … }` | assignment moves into the condition; same order | CARE |

**Not safe:** `soh/src/code/z_bgcheck.c:1698-1700` (`if (checkPos.y < colCtx->minBounds.y) break;`) is a
float compare — `while (checkPos.y >= min)` exits on NaN where the original continues; only
`while (!(checkPos.y < …))` is exact, and that reads worse than the original. LEAVE.

## 3. `if (1) {}`, `if (0) {}`, empty then-blocks — 75 + 9 + 11 hits

**`empty_then.txt` (75):** 2 are commented-out lines (`z_camera.c:3615`, `ovl_En_Sa/z_en_sa.c:677` — delete
the line, and `z_camera.c:3614 // needed to match` with it); 1 is an inversion; 72 are live empty
`if (<read>) {}` statements. None hold a comment worth keeping — every comment names the matching hack
("Needed to match", "helps the compiler store play2 into s1", "Must be 'play'", "these ifs cannot just
contain a constant", "One way of fake-matching", "fixes regalloc, may be fake", "Very fake, but needed to
get the s registers right") and dies with it.

| kind | sites | verdict | rewrite | gate |
|---|---|---|---|---|
| plain read, no side effect (params, locals, fields, globals, array elements, `&x`, `0 * i`, `size && size`) | all 72 live sites, e.g. `code/audio_load.c:1907`, `:1959`, `:2170`, `code/audio_seqplayer.c:1574`, `code/code_800E4FE0.c:115-116`, `code/code_800FC620.c:161`, `:168`, `code/db_camera.c:1233` (`if (&dbCamera->at) {}`), `code/z_lifemeter.c:248` (`if (1) {}`), `code/z_message_PAL.c:2536`, `code/z_onepointdemo.c:61`, `code/z_skin_matrix.c:374`, `:436`, `code/z_view.c:61`, `ovl_Bg_Jya_Cobra:354`, `ovl_Bg_Mizu_Bwall:383`, `ovl_Bg_Spot00_Hanebasi:155`, `ovl_Bg_Spot16_Bombstone:433`, `ovl_Bg_Spot18_Basket:106`, `ovl_Boss_Dodongo:1117`, `:1289` (with its goto, §1), `ovl_Boss_Mo:963`, `ovl_Boss_Tw:2820` (`if (&this->subCamEye) {}`), `ovl_Demo_Ec:323`, `:830`, `:903`, `ovl_Demo_Effect:1761`, `ovl_Demo_Gj:590`, `:654`, `:910`, `ovl_Demo_Kankyo:278`, `:870`, `ovl_Eff_Dust:346`, `ovl_En_Ani:154`, `ovl_En_Anubice:164`, `:425`, `ovl_En_Box:136`, `ovl_En_Dekubaba:534`, `ovl_En_Ex_Item:490`, `ovl_En_Fish:296`, `ovl_En_Floormas:546`, `ovl_En_Gb:395`, `:398`, `ovl_En_Holl:246`, `:248`, `ovl_En_Horse:699`, `ovl_En_Horse_Game_Check:254`, `ovl_En_In:270`, `ovl_En_Insect:360`, `ovl_En_Kz:535`, `ovl_En_Nwc:110`, `ovl_En_Owl:1259`, `ovl_En_Ssh:486`, `ovl_En_Torch2:279`, `:521`, `ovl_En_Tp:165`, `:182` (`if (0 * i) {}`), `ovl_En_Viewer:809`, `ovl_En_Xc:549`, `ovl_En_Zl3:1852`, `ovl_Fishing:5109`, `ovl_Obj_Bean:649`, `ovl_player_actor/z_player.c:6324`, `ovl_Effect_Ss_G_Ripple:74`, `ovl_kaleido_scope/z_kaleido_equipment.c:312`, `:881`, `z_kaleido_item.c:450`, `:451`, `z_kaleido_scope_PAL.c:2911` | **DO** delete the statement and its trailing comment (and the preceding comment line at `ovl_Eff_Dust:345`, `ovl_En_Floormas:545`, `z_kaleido_item.c:449`) | — | IDENTICAL at -O2; DIFFERS at -O0 (each is a real load there) |
| dead local kept alive by the empty `if` | `ovl_En_Anubice/z_en_anubice.c:360` `f32 zero;`, `:424` `zero = 0.0f;`, `:425` `if (zero) {}` | **DO** delete all three (only references) | — | IDENTICAL at -O2 |
| unreachable statement between `switch (…) {` and the first `case` | `ovl_En_Go/z_en_go.c:210` `if (play) {}` | **DO** delete | never executed | IDENTICAL |
| inversion `if (x) {} else { S }` | `soh/src/code/ucode_disas.c:227-228` | **DO** → `if (this->enableLog != 0) { osSyncPrintf("\nGBL_c1(…)", …); }` and drop the `// clang-format off/on` fence at `:226/:229` (it protects only this one-liner); `:231` already uses `if (this->enableLog)` for the twin | same test, same body | IDENTICAL |
| warning suppressor with a real reason | `soh/src/libultra/os/settimer.c:41` `if (time) {} // suppresses set but unused warning` | CARE → `(void)time;` (the standard idiom; the build passes `-w` anyway) | — | IDENTICAL |

SoH-touched lines in this class (blame): 24 lines were last touched by SoH commits, all mechanical
(`99260aca` GlobalContext→PlayState rename ×17, `8f126344` clang-format, `b5c6545d` rename, `50837308`
resync, `274c12f3` moved `z_lifemeter.c:248`); two sit in port-rewritten blocks and deserve a look before
deleting: `z_kaleido_scope_PAL.c:2911 if (colorIndex) {}` (`4bdb5098` "Colors 1") — the construct is still the
decomp's, the block around it is SoH's.

**`if (1) {` with a body (9 hits in `if_1.txt`, 8 non-empty):** `boot/z_std_dma.c:350`,
`code/code_800EC960.c:3349`, `code/z_actor.c:3782`, `code/z_player_lib.c:2147` (+ `s32 pad[2];` and the
comment at `:2146`), `ovl_Bg_Hidan_Hrock:105`, `ovl_Boss_Fd:1389` (declares `emberVel`/`emberAccel`/…),
`ovl_Boss_Ganon2:808` (declares `effect`), `ovl_Demo_Go:64` — **DO**: unwrap; where the block declares
locals keep a bare `{ … }` scope (or hoist the declarations). IDENTICAL (constant condition folds at any -O).

**`if (0) {` with a body (11 sites, grep):** `audio_heap.c:455` (the `fail:` home, handled in §1);
`sched.c:156`, `:163` (dead `assert`s); `z_prenmi.c:14`, `ovl_Fishing/z_fishing.c:5204`, `boot/z_std_dma.c:238,
261, 283, 300, 318, 325` — "Strings existing only in rodata": the decomp keeps the original debug prints under
`if (0)` to reproduce `.rodata`. The port has no rodata contract, so they are deletable no-ops, but they are the
only record of what the retail build once printed. LEAVE (documentary; codegen IDENTICAL either way).

Empty arms found by the wider grep and not in the census: `soh/src/code/audio_synthesis.c:745-750`
(`if (a && b) {} else if (c && d) {} else {}` with the comment "Partially-optimized out no-op ifs required for
matching") and `ovl_Bg_Treemouth/z_bg_treemouth.c:243-244` (`} else { // neeeded to match` `}`) — **DO**
delete both blocks with their comments; all conditions are pure reads. IDENTICAL at -O2.

## 4. `} else if (x == k)` ladders — 397 hits

(a) **Redundant tails: exactly 7 in the tree, all in one function** (`Interface_Update`,
`soh/src/code/z_parameter.c`). The scanner walked each hit back to its chain head; the inverse forms
(`if (x == k) … else if (x != k)`, `if (!x) … else if (x)`) return 0 hits, so "20 clearest" cannot be met —
there are seven.

| head `if (X != 0)` | tail `} else if (X == 0)` | X |
|---|---|---|
| `z_parameter.c:1120` | `:1131` | `interfaceCtx->restrictions.bottles` |
| `:1144` | `:1161` | `…restrictions.tradeItems` |
| `:1174` | `:1185` | `…restrictions.hookshot` |
| `:1198` | `:1209` | `…restrictions.ocarina` |
| `:1222` | `:1233` | `…restrictions.farores` |
| `:1245` | `:1256` | `…restrictions.dinsNayrus` |
| `:1269` | `:1296` | `…restrictions.all` |

**DO**: each tail → `} else {`. Behaviour-preserving: no statement in `:1100-1300` writes any
`interfaceCtx->restrictions.*` field (grep count 0); the arms write only `gSaveContext.buttonStatus[]` and
the local `sp28`. SoH commits (`fd06827e` DPad items, `4173eada` C-button tunics) edited lines inside the arms,
not the chain heads. Gate: IDENTICAL (GCC folds the provably-true second test; SM64's identical class).

(b) **Switch candidates** — chains over one discriminant with ≥3 distinct constant arms, no arm writes the
discriminant, no condition has side effects, every arm is assignments or calls that do not touch the
discriminant. Scanner found ~40 unique chains; the clearest, verified by reading:

| site | discriminant | arms | note |
|---|---|---|---|
| `soh/src/code/z_camera.c:5978-5992` | `anim->animFrame` | 7 (1, 2, 0x94, 0x9E, 0x9F, 0xA8, 0xE4) | each arm assigns `camera->animState`; `animFrame++` happens at `:5976`, before the chain |
| `soh/src/code/z_vimode.c:81-105` | `type` (param) | 3 | seven register-field stores per arm |
| `soh/src/code/z_fbdemo_triforce.c:39-47` | `this->state` | 4 | one `transPos` assignment per arm, inside a `for` |
| `soh/src/code/z_kankyo.c:375-383` | `gWeatherMode` | 3 | |
| `soh/src/code/z_message_PAL.c:2308-2314` | `numLines` | 3 | |
| `ovl_Boss_Ganon2/z_boss_ganon2.c:2624-2636` | `limbIndex` | 6 | `Matrix_MultVec3f` calls |
| `ovl_Boss_Dodongo/z_boss_dodongo.c:1350-1359` | `limbIndex` | 3 | |
| `ovl_Fishing/z_fishing.c:4278-4284` | `limbIndex` | 3 | |
| `ovl_En_Dha/z_en_dha.c:422-431`, `ovl_En_Po_Field/z_en_po_field.c:895-901` | `limbIndex` | 3 | |
| `ovl_Bg_Jya_Bigmirror/z_bg_jya_bigmirror.c:49-55` | `play->roomCtx.curRoom.num` | 3 | |
| `ovl_Bg_Hidan_Hrock/z_bg_hidan_hrock.c:119-126` | `thisx->params` | 3 | |
| `ovl_En_Po_Relay/z_en_po_relay.c:252-260` | `this->pathIndex` | 4 | `pathIndex++` at `:250` precedes the chain |

Verdict **CARE / explained diff** for all of (b): a `switch` with 4+ dense arms becomes a jump table or a
different compare tree, so the gate will differ (the SM64 lesson). Behaviour is identical by the pattern-5
rule (discriminant read once vs per arm gives the same value because nothing in the chain writes it).

(c) **LEAVE** — arms write the discriminant: `ovl_select/z_select.c:890-916`, `:918-944`
(`gSaveContext.cutsceneIndex`, 13 arms; also SoH-modified file), `ovl_Boss_Fd/z_boss_fd.c:1086-1118`
(`this->fogMode`), `ovl_En_Dekubaba/z_en_dekubaba.c:760-832` (`this->timer`),
`ovl_file_choose/z_file_nameset_NES.c:786-798` (`this->charPage`). Also
`ovl_kaleido_scope/z_kaleido_scope_PAL.c:2331-2343` is SoH's (`274c12f3`, `for (s16 i …)`) — not a decomp ladder.

## 5. Matching comments — 91 hits

19 are the ordinary sense of "match" (noise): `audio_load.c:1348`, `z_moji.c:30`, `code_800EC960.c:4362`
(SoH randomizer; note both arms assign the same value — SoH's oddity, not ours), `:5534`, `audio_synthesis.c:358`,
`ovl_Bg_Spot06:564`, `ovl_Bg_Spot08:159`, `ovl_Boss_Dodongo:213`, `ovl_Demo_Effect:1714`, `ovl_Demo_Gj:197`,
`ovl_Door_Killer:116`, `ovl_En_Heishi1:501`, `z_file_choose.c:351/1585/2716`, `z_select.c:1228`,
`z_player.c:8640/11166/11167`. The rest excuse a construct; each was read and its variable grepped.

| construct excused | sites | still there? | verdict / rewrite | gate |
|---|---|---|---|---|
| lone `;` | `soh/src/code/code_800EC960.c:3700` (`; // might be a fake match?`) | yes | **DO** delete | IDENTICAL |
| stray block | `ovl_Boss_Dodongo/z_boss_dodongo.c:1337` `{ s32 pad; } // Required to match` | yes | **DO** delete | IDENTICAL |
| self-assignment | `code/z_eff_blure.c:493` `sp30 = sp30;`, `ovl_Bg_Hidan_Hamstep:106` `pos = pos;` (Vec3f), `ovl_Mir_Ray:431` `spE8 = spE8;`, `:441` `normalVec = normalVec;` | yes | **DO** delete + comment | IDENTICAL at -O2; -O0 emits the copies |
| self-assignment via pointer (not in the census — found reading `ovl_En_Ma3`) | `ovl_En_Ma3/z_en_ma3.c:79` `s16* timerSecondsPtr;`, `:84`, `:86` `gSaveContext.timerSeconds = gSaveContext.timerSeconds;`, `:93` `gSaveContext.timerSeconds = *timerSecondsPtr;` | yes | **DO** delete all four lines (`timerSeconds` is a plain `s16`; both stores write the value just read) | IDENTICAL at -O2 |
| `u64 temp = CONST; g = temp;` | `code/irqmgr.c:104-106`, `:130-131` (`gIrqMgrResetStatus` is `vu32`, `irqmgr.c:4`) | yes | **DO** `gIrqMgrResetStatus = STATUS_PRENMI;` / `= STATUS_NMI;` | IDENTICAL (one 32-bit store either way) |
| `u64 temp = 0;` used as a 0 | `code/z_kaleido_setup.c:73`, `:102-103` | yes | **DO** write `0`, delete `temp` | IDENTICAL |
| `s32 one; one = 1; D = one;` | `ovl_En_Nb/z_en_nb.c:207/218/220`, `ovl_En_Ru2/z_en_ru2.c:197/209/211` | yes | **DO** `D_80AB4318 = 1;` / `D_80AF4118 = 1;` | IDENTICAL |
| unused local | `code/z_bgcheck.c:4267` `waterBoxList`, `ovl_En_Trap:69` `unused`, `ovl_En_Zl3:2590` `Actor* thisx` (only reference in that function) | yes | **DO** delete | IDENTICAL |
| dead initialiser | `ovl_Bg_Ice_Objects:85` `s16 z16 = 0;` (assigned at `:92`/`:99` before every read) | yes | **DO** drop `= 0` + comment | IDENTICAL |
| dead store in an `else` arm | `code/z_skin_matrix.c:354` `xz = sinZ;`, `:419` `xy = sinY;` (both locals are re-assigned at `:365`/`:429` before their next read; the `mf->xz`/`mf->xy` stores in between are fields, not the local) | yes | **DO** delete + comment | IDENTICAL |
| redundant alias | `ovl_En_Ru1:1456` `EnRu1* thisx = this;` (one use, `:1464` `thisx->bobDepth`); `:1961/1967/1968` `csCmdNPCAction2` (only refs) → `csCmdNPCAction = play->csCtx.npcActions[3];`; `ovl_Obj_Mure:180` `ac = (ActorContext*)play` (overwritten at `:190` before the use at `:192`) → `ActorContext* ac;`; `ovl_En_Elf:1371/1440/1441` `unk2C7` → `if (this->unk_2C7 > 0) { this->unk_2C7--; }` | yes | **DO** | IDENTICAL |
| `((void)0, expr)` | `ovl_En_GeldB:1273`, `ovl_En_Horse:3150` `((void)0, this->actor.world).rot.y` | yes | **DO** drop the comma operand | IDENTICAL |
| `(*p).f` | `ovl_En_Fr:842` `(*msgCtx).lastOcaNoteIdx`, `code/z_bgcheck.c:2898/2900` `(*newPoly).flags_vIA` (+ the "my God, it matches" comment at `:2897`) | yes | **DO** `->` | IDENTICAL |
| always-true guard inside its own loop | `ovl_Boss_Fd:788-789` `for (i1 = 0; i1 < sp150; i1++) { if (sp150) {` | yes | **DO** unwrap (`i1 < sp150` with `i1 >= 0` ⇒ `sp150 != 0`) | likely IDENTICAL (VRP proves it) |
| dead `if (zero)` | `ovl_Boss_Tw:2727` `s32 zero = 0;`, `:2739-2742` `if (zero) { accel.x *= 2.0; }` (only refs) | yes | **DO** delete both | IDENTICAL at -O2 |
| `& 0xFFFFFFFF` on an `int` | `code/game.c:126-127` (`hexDumpSize` is `s32`, `:86`) | yes | **DO** drop the mask + comment (same 32 bits stored) | IDENTICAL |
| `if (1) { pad; S }` | `code/z_player_lib.c:2146-2150` | yes | **DO** (see §3) | IDENTICAL |
| commented-out hack | `code/z_camera.c:3614-3615` | yes | **DO** delete both lines | IDENTICAL (comment) |
| empty arms | `code/audio_synthesis.c:745-750`, `ovl_Bg_Treemouth:243` | yes | **DO** (see §3) | IDENTICAL |
| stale comment only | `code/audio_load.c:558-562` ("Intentionally missing return" above `return 1;`), `ovl_Bg_Gnd_Soulmeiro:120` (`!x` vs `== 0`), `ovl_Bg_Ydan_Maruta:93`, `ovl_Demo_Ik:178`, `ovl_En_Zl4:1125` ("no break … for matching" on a last `case`), `code/z_actor.c:1962`, `code/z_en_item00.c:1553` ("single if … to match"), `z_kaleido_item.c:668`, `ovl_Demo_Effect:1025`, `ovl_player_actor/z_player.c:1583` (`BAD_RETURN` is already `void`, `macros.h:15-23`), `code/z_lights.c:200` | — | **DO** delete/reword the comment only; leave the code (`z_lights.c` return type is API, `z_player.c` macro is tree-wide) | IDENTICAL |
| struct copy spelled as 3 stores | `ovl_Demo_Effect:558-561` | yes | CARE → `this->actor.world.pos = this->actor.parent->world.pos;` | likely IDENTICAL |
| `x = x + (s16)(…)` | `ovl_En_Horse:3557-3560` | yes | CARE → `+=` (keep the `(s16)` cast — it truncates the addend, pattern 10) | IDENTICAL |
| named temps that are used | `ovl_En_Ossan:1973-1974`, `z_file_choose.c:602-603` (`new_var2`/`new_var3`, used ×3 each), `ovl_En_Dodongo:748` (`a b c d` indices), `ovl_En_Tp:502` `temp_v0`, `code/z_scene.c:40` `play2` (used throughout) | yes | CARE (rename/inline is identical but wide); `z_message_PAL.c:1954` `(curChar * 32) << 2` → `* 128` is exact for the non-negative `curChar` — comment-only unless wanted | — |
| dead code after `return;` | `code/audio_heap.c:1329-1355` (`fakematch`; the function returns at `:1332`, SoH stub) | yes | LEAVE (dead) | — |
| double literal | `code/z_actor.c:2477` `* 0.2` | yes | LEAVE (pattern 13: adding `f` changes bits — the comment is right) | — |
| `//! @bug` + UB note | `code/z_camera.c:7250` | yes | LEAVE | — |
| `temp = 0.1f; if (!sp1CF) temp = 1.0f;` | `ovl_Boss_Fd:492-497` | yes | LEAVE (the comment claims `sp1CF` is always false here; not verified, and 0.1 vs 1.0 is a visible camera-shake step) | — |
| data layout | `ovl_En_Tr:71` ("1-dimensional to match") | yes | LEAVE | — |
| chained assignment style | `z_file_copy_erase.c:983`, `code_800EC960.c:5534` | yes | LEAVE | — |

**Look-alikes NOT safe:** `ovl_En_Fr:842`'s comment says "possibly an array?" — only the `(*p).` spelling is
the ism, the compare is real; `code/z_bgcheck.c:2898` the `& 0xE000` mask is a real field split (keep it);
`ovl_En_Horse:3557` the `(s16)` casts are truncation, not residue.

## 6. `volatile` and AVOID_UB

`volatile_kw.txt` (15, all declarations in two files). Readers/writers grepped tree-wide (`soh/src`,
`soh/include`, `soh/soh`):

| variable | writers | readers | verdict |
|---|---|---|---|
| `code/irqmgr.c:6 gIrqMgrRetraceTime` | `irqmgr.c:159` (IRQ manager thread) | `speed_meter.c:59`, `:67` (graph thread) | LEAVE — live cross-thread |
| `code/speed_meter.c:4-14, 16` (`D_8016A520…D_8016A558`, `gRSP*TotalTime`, `gRDPTotalTime`) | `audioMgr.c:32-39`, `sched.c:363-408`, `graph.c:181-221`, `:398-406` | `speed_meter.c:20-22` table (drawn by the graph thread) | LEAVE — audio/scheduler/graph threads |
| `code/irqmgr.c:5 sIrqMgrResetTime` | `irqmgr.c:108` only | none anywhere | dead (write-only); CARE — deleting the variable and its store is behaviour-free but the store is emitted, so the gate differs |
| `code/speed_meter.c:15 D_8016A578` | none | none | dead; **DO** delete (no `extern` in `variables.h`, 0 refs) — IDENTICAL (no code) |

`avoid_ub.txt` (14): all `OOT_DEBUG` in `soh/src/code/__osMalloc.c` — `:10 #define OOT_DEBUG 1` is SoH's
("#region SOH [General] We currently don't set OOT_DEBUG when building so set it here manually") selecting the
debug-arena arms of `#if OOT_DEBUG`. Not an assembly-ism; LEAVE. No `AVOID_UB`/`NON_MATCHING` text exists in
`soh/src`; `BAD_RETURN` is hard-wired to `void` (`macros.h:15-23`).

## 7. Extra greps

- **`do { … } while (0)` in function bodies: 0.** The only `while (0)` are the two macro definitions
  (`__osMalloc.c:80`, `z_play.c:47 PLAY_LOG`) — the class is empty here (SM64 had 4).
- **Nested single-statement `if`s (`&&` chains)** — scanner: each inner `if (…) {` is the only statement of its
  parent's block, no `else` on inner arms. 21 chains of depth ≥ 3 (319 of depth 2, not listed). All conditions
  are pure reads or calls whose order `&&` preserves exactly as nesting did:
  `code/code_800E4FE0.c:50` (AudioHeap_ResetStep in the middle), `code/z_bgcheck.c:753`, `:834`, `:3297`
  (`fabsf`/float tests), `:4240` (depth 4), `:4241`, `:4350` (depth 4), `:4351`, `code/z_collision_check.c:2845`,
  `ovl_Bg_Bdan_Objects:449`, `ovl_Boss_Tw:3010` (`Rand_ZeroOne()` innermost — stays last), `ovl_Door_Warp1:473`,
  `ovl_En_Heishi1:439`, `ovl_En_Insect:730`, `ovl_En_Kusa:465` (`Math_StepToF` has a side effect — it is the
  middle test in both forms), `ovl_En_Ta:787`, `ovl_En_Test:1903`, `ovl_player_actor/z_player.c:2942`, `:6833`,
  `ovl_kaleido_scope/z_kaleido_collect.c:524`, `z_kaleido_equipment.c:736`. Verdict **DO** per site
  (`if (A && B && C) { … }`); expected IDENTICAL (GCC lowers both to the same short-circuit CFG) — gate each.
  Check the outermost `if` has no `else` before merging (none of the 21 does at the cited line, but
  `z_bgcheck.c:4240/4350` are inside `for` loops whose later code must stay outside the merged body).
- **`break;` immediately after `return`/`goto`: 5**, all unreachable — `ovl_Obj_Oshihiki/z_obj_oshihiki.c:124`,
  `:128`, `:132`, `libultra/io/epirawdma.c:67`, `libultra/io/pirawdma.c:23`. **DO** delete; IDENTICAL.
  `break; break;`: 0.
- **Lone `;` statements** (grep `^\s*;`): `code_800EC960.c:3700` (§5), `ovl_Obj_Bean/z_obj_bean.c:428` (a stray
  `;` before `}` — **DO** delete), `code_800EC960.c:2229` (empty `for` body — cosmetic), `z_demo.c:2186`,
  `z_play.c:569` and 17 libultra `while (…) ;` spin-waits — LEAVE.
- **Empty `else`**: `audio_synthesis.c:750`, `z_bg_treemouth.c:243` (§3).

## Grep commands used

```
# pin / flags
git -C Shipwright rev-parse HEAD; sed -n '15597,15603p' build-cmake/build.ninja; grep -n CMAKE_BUILD_TYPE build-cmake/CMakeCache.txt
# labels incl. label:; form
grep -rnE '^\s*[A-Za-z_][A-Za-z_0-9]*:\s*;?\s*(//.*)?$' soh/src/{code,overlays,boot,libultra,buffers} --include=*.c | grep -vE '\b(default|case)\b'
# label cross-refs
grep -nE '\b<label>:|goto <label>;' <file>
# if (0) / empty else / lone ; / unreachable break / do-while-0
grep -rn 'if (0)' …; grep -rnE -A1 '\} else \{\s*(//.*)?$' … | grep -E '^\S+-[0-9]+-\s*\}\s*$'
grep -rnE '^\s*;\s*(//.*)?$' …; grep -rnE -A1 '^\s*(return[^;]*|goto [A-Za-z_0-9]+);\s*$' … | grep -E '^\S+-[0-9]+-\s*break;'
grep -rnE 'while\s*\(\s*0\s*\)\s*;' … | grep -v '\\$'
# volatile readers/writers
grep -rn --include=*.c --include=*.h --include=*.cpp '\b<name>\b' soh/src soh/include soh/soh
# ladders: scratch script ladders.py (walks each `} else if (X == k)` back to its chain head; flags
#   head `if (X != k)` with the same X,k and no other arm = redundant tail; groups ≥3-arm chains and greps
#   the chain body for writes to X). nested_ifs.py: structural scan for if{if{if{…}}} with no else.
# blame
git blame -L <n>,<n> --date=short <file>; git show -s --format='%s (%an %ad)' <sha>
```

## Recommended batch order

1. **Empty-then / `if (1)` / empty-arm deletions** — ~72 `if (x) {}` + 8 `if (1) {` unwraps +
   `audio_synthesis.c:745`, `z_bg_treemouth.c:243`, `z_en_anubice.c` `zero`, `z_en_go.c:210`,
   `ucode_disas.c:227` inversion. One patch for `code/`, one for `overlays/`. **Gate under Release flags
   only** (every one differs at -O0 and none should at -O2).
2. **Matching-comment residue** (§5 DO rows): self-assignments, dead temps, `((void)0, …)`, `(*p).`, `u64 temp`,
   `s32 one`, `& 0xFFFFFFFF`, `{ s32 pad; }`, lone `;` ×2, stale comments. ~30 sites, all IDENTICAL expected.
3. **goto → keyword** (§1 DO): `z_player_lib.c:916`, `db_camera.c:1834/1874/2007`, `audio_heap.c:442/449`
   (+ its `if (0)`), `audio_playback.c:239`, `boss_dodongo.c:1286-1292`. 8 gotos, 5 labels gone.
4. **Unreachable `break` ×5**, `z_camera.c:3614-3615`, `z_obj_bean.c:428`, `speed_meter.c:15`.
5. **`z_parameter.c` ×7 `else if` → `else`** — one file, one patch, IDENTICAL.
6. **Test-first loops** (§2 table, the "expected IDENTICAL" rows first: `audio_load.c:958/2020`, `z_jpeg.c:127`,
   `z_map_mark.c:113`, `z_lmap_mark.c:62`, `pfsfilestate.c:34`, `z_file_choose.c:241/249`, `bombstone.c:295`,
   `code_800EC960.c:5419`, `z_eff_blure.c:335`) — gate each; drop any that differs.
7. **`&&` merges** (§7, 21 chains) — gate each.
8. **Explained-diff list** (needs the maintainer's play-test): ladders → `switch` (§4b, 12 chains),
   `code_800E4FE0.c:643` case stacking, `z_skin.c:211` `CLOSE_DISPS; return;`, `audio_load.c:201` `do/while`,
   `demo_effect.c:558` struct copy, `z_scene.c:40` `play2` rename, `irqmgr.c:5` dead volatile.

Not recommended: anything in `#if 0`, the four `z_camera.c` case-jumps and the six case-label gotos
(`boss_ganon`, `boss_mo`, `en_clear_tag`, `fishing`, `en_bb`), SoH's own gotos (`graph.c`, `z_play.c:1602`,
`z_kaleido_equipment.c`), the `if (0)` rodata-string blocks, the `volatile` timing globals, and `OOT_DEBUG`.
