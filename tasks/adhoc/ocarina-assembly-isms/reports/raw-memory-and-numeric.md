# Raw memory and numeric assembly-isms — Ship of Harkinian OoT (`soh/src/`)

**Pin:** `acdbc651d` ("Fix compat issues loading pre-9.1 saves on 9.2+ (#7132)"), branch `imps-standard-c`,
working tree clean. **Date:** 2026-09-22. **Reader:** agent-assisted survey for
`tasks/ocarina-de-disassemble-ugly-c.md`; sister of `tasks/adhoc/mario64-assembly-isms/reports/raw-memory-and-numeric.md`.
Anchors are `soh/src/...:line` (or `soh/include/...`) at this pin; every type quoted was read from the header/definition
named beside it. Census logs: `tasks/adhoc/ocarina-assembly-isms/data/` (paths there carry a
`../../../n64/OcarinaOfTime/Shipwright/` prefix).

## 0. Facts verified first (they decide several verdicts below)

- **Compile flags** (`Shipwright/build-cmake/build.ninja`, rule for `soh/src/code/z_actor.c.o`): `-O2 -DNDEBUG -std=gnu2x
  -fno-fast-math -ffp-contract=off … -Wno-narrowing -Wno-incompatible-pointer-types -Wno-int-conversion -msse2 -mfpmath=sse -w`.
  Gotcha: the imps-level `n64/OcarinaOfTime/build-cmake/build.ninja` is a `-g` configure with **no `-O`** — an asmdiff gate must
  read flags from the Shipwright one, or every rewrite differs by construction.
- **Angle macros** (`soh/include/z64math.h:104-112`): there is **no integer `DEG_TO_BINANG`**. What exists is
  `DEGF_TO_BINANG(degreesf) (s16)(degreesf * 182.04167f + .5f)` (float, rounds, 182.04167 = 65535/360 not 65536/360),
  `BINANG_ROT180(angle) ((s16)(angle - 0x7FFF))` — **off by one from `+ 0x8000`** — and `BINANG_SUB(a, b) ((s16)(a - b))`.
  `ABS` is single and sane (`soh/include/macros.h:43`, `>= 0`).
- **Params macros exist**: `PARAMS_GET_U/S/NOMASK/NOSHIFT`, `PARAMS_PACK`, `PARAMS_MAKE_MASK` at `soh/include/z64actor.h:493-518`,
  used **3 times** in the tree (`ovl_En_Holl/z_en_holl.h:7-8`, `ovl_player_actor/z_player.c:5567`). `Actor.params` is `s16`
  (`z64actor.h:229`).
- **Save-flag accessors**: `GET/SET_EVENTINF_HORSES_STATE()` and `…HORSETYPE()` are pure macros (`soh/include/z64save.h:948-960`);
  `Flags_Get/Set/UnsetEventChkInf` are **functions** in `soh/src/code/z_actor.c:4931-` (a rewrite to them is a call).
- **No `rawData` union in OoT** — every `unk_XX[` in `rawdata_union.txt` (1052) is a typed array member; the SM64
  `asF32[0x37]`→`oHomeX` shape does not exist here (0 hits for `rawData|asF32|asS32|asU32`).
- **Synthetic gate**: 46 before/after pairs compiled with the flags above (GCC 16.2.1, `-S`, diff of non-directive lines) at
  `/tmp/…/scratchpad/gate/pairs*.txt`. Results are quoted per row as "gate: IDENTICAL/DIFF" — they are *shape* evidence, not a
  run of the real files; run `asmdiff.sh` on each touched file before committing.

Verdict scale: **DO** = drop-in, expected byte-identical; **CARE** = identical or explained diff but needs a per-site read;
**LEAVE** = changes bits or is not an assembly-ism.

## 1. 16-bit residue — `& 0xFFFF`, `(x << 16) >> 16` (`bit_masking_16.txt`, 87 hits, 35 files)

87 census hits + 2 `<< 0x10 … >> 0x10` the regex missed (hex spelling). Breakdown: **52 leave** (audio/RSP/format),
**11 load-bearing keep**, **22 droppable**, **2 sign-extension rewrites**.

| sub-class | hits | verdict | sites | rewrite | why behaviour-preserving | gate |
|---|---|---|---|---|---|---|
| Store into a narrower unsigned/signed field | 9 | **DO** | `ovl_Bg_Ydan_Maruta/z_bg_ydan_maruta.c:92` (`u8 switchFlag`, `.h:14`); `ovl_Door_Ana/z_door_ana.c:142` (`s8 data`, `z64save.h:161`); `ovl_En_Elf/z_en_elf.c:470` (`s16 unk_2AA = (s16 unk_2AC * 2) & 0xFFFF`, `.h:30-31`); `ovl_player_actor/z_player.c:15008,15009` (`Vec3s force`, `:14995`, `= (s32)(…) & 0xFFFF`); `ovl_En_GeldB/z_en_geldb.c:1633` and `ovl_En_Wf/z_en_wf.c:1481` (`world.rot.y = (u16)shape.rot.y & 0xFFFF`, both `Vec3s`, `z64actor.h:31,87`); `ovl_En_Zl2/z_en_zl2.c:306` (`temp_v1 = (s16)(phi_v0 & 0xFFFF)`, both `s32`, `:235-236`); `code/z_room.c:181` (`iREG(87) = polygon2->num & 0xFFFF & 0xFFFF & 0xFFFF`, `iREG` is an `s16` register) | delete the mask (and the `(u16)` in GeldB/Wf: `world.rot.y = shape.rot.y`; delete the `// if this is real…` comment at z_room.c:181) | conversion to an 8/16-bit type is modulo 2^N on every real compiler with or without the mask; the mask is the MIPS `andi` before `sh`/`sb` | IDENTICAL (`mask_u8store`, `mask_s8store`, `mask_u16cast_s16store`, `mask_mul2_s16store`, `mask_s32float_s16store`, `mask_s16cast_of_mask`) |
| Mask on an operand already `u16` | 8 | **DO** | `code/z_kaleido_scope_call.c:74,83` (`u16 state`, `z64.h:947`); `ovl_Bg_Spot02_Objects/z_bg_spot02_objects.c:312` (`u16 action`, `z64cutscene.h:85`; delete the confession comment at `:311`); `ovl_En_Ani/z_en_ani.c:152` (`u16 textId2`, `Text_GetFaceReaction` returns `u16`, `functions.h:880`); `ovl_En_In/z_en_in.c:715,764` (`u16 eventInf[]`, `z64save.h:373`); `ovl_En_Ru2/z_en_ru2.c:748` (arg to `u16 endFrame`, `code/z_kankyo.c:512`); `code/code_800EC960.c:4146` (`s8 phi_v0`, `:4135`, provably ≥ 30 by the `else` at `:4143`) | delete the mask | `u16` promotes to `int` in 0..65535, so `& 0xFFFF` is the identity; the `s8` case is non-negative on that branch and GCC folds it | IDENTICAL (`mask_u16_plus1`, `mask_u16_cmp`, `mask_u16_or`, `mask_u16var_u16store`, `mask_u16param`, `mask_s8_branch_nonneg`) |
| Mask on the argument of `coss(u16)`/`sins(u16)` | 4 | **DO** | `code/z_scene_table.c:594,650,1446,1447` (`coss((play->gameplayFrames * 1500) & 0xFFFF)`, `u32 gameplayFrames` `z64.h:1462`, `s16 coss(u16)` `functions.h:2382`) | delete the mask | the `u16` parameter conversion is the same modulo-2^16 reduction | IDENTICAL by the same rule as `mask_u16param` |
| `<< 0x10) >> 0x10` sign-extension idiom | 2 | **DO** (cosmetic) | `code/fault.c:423,483` `(s32)((((u32)cause >> 2) & 0x1F) << 0x10) >> 0x10` | `(s32)((t->context.cause >> 2) & 0x1F)` | operand is a 5-bit unsigned value, so no negative shift and no UB — this is *not* the SM64 explained-diff case; it is just a 5-bit field read | IDENTICAL (`sext_cause`) |
| `s16 & 0xFFFF == 0x9000` | 2 | **CARE** | `ovl_En_Ex_Item/z_en_ex_item.c:272,358` (`shape.rot.y & 0xFFFF) == 0x9000`, `Vec3s`) | `(u16)this->actor.shape.rot.y == 0x9000` | the mask is **load-bearing** (an `s16` promoted is negative and never equals 0x9000); the `(u16)` cast is the standard-C spelling of the same test | IDENTICAL (`mask_s16_cmp_9000`) |
| Mask on a value the compiler cannot bound | 1 | **CARE** (diff) | `ovl_En_Cow/z_en_cow.c:144` `u16 animationTimer = ((u32)(Rand_ZeroFloat(1000.0f)) & 0xFFFF) + 40.0f` | delete the mask | numerically a no-op (value < 1000) but GCC cannot prove it | DIFF (`mask_cow_u32float`: `movzwl`+`cvtsi2ssl` vs `cvtsi2ssq`) — explained-diff list only |
| Texture-scroll wrap into a 32-bit variable | 6 | **LEAVE** (load-bearing) | `ovl_Bg_Spot16_Doughnut/z_bg_spot16_doughnut.c:122` (`u32 scroll`), `ovl_Demo_Effect/z_demo_effect.c:1790`, `ovl_Demo_Kekkai/z_demo_kekkai.c:283,340` (`s32 scroll`, `:338`, from `f32 barrierScroll` `.h:17`), `ovl_Oceff_Spot/z_oceff_spot.c:151`, `code/z_actor.c:2509,2514` (`((frames * 1500) & 0xFFFF) * M_PI / 32768.0f`) | — | the destination is 32-bit or the masked value feeds a float multiply; the mask *is* the wrap | — |
| Packed-word / compare-after-wrap / printf | 5 | **LEAVE** | `code/code_800EC960.c:2606` (`u32 sDebugPadHold`, `:1310`); `ovl_En_Ru2/z_en_ru2.c:843` (compares against a wrapped `u16` sum); `ovl_Obj_Warp2block/z_obj_warp2block.c:226` (`%04x` of `s16 params`); `code/relocation.c:90-91`; `libultra/io/contpfs.c:15` (checksum) | — | selects a half-word or a printable value | — |
| Audio command words, RSP matrix packing, ucode disassembly, S2DEX | 50 | **LEAVE** | `code/audio_seqplayer.c:1363-1372`, `audio_synthesis.c:743`, `code_800E4FE0.c:251,255`, `code_800EC960.c:3389`, `code_800F7260.c:248,252`, `code_800F9280.c` ×10, `sys_matrix.c:952-973,1005-1026` (int/frac halves of the RSP fixed-point matrix), `fault.c:840`, `ucode_disas.c:506-507,1157`, `libultra/gu/guS2DInitBg.c:22`, `us2dex.c:22` | — | these are wire formats, not sign-extension residue | — |

**Look-alikes that are NOT safe:** `z_en_ex_item.c:272,358` (a bare drop flips the test to never-true); `z_demo_kekkai.c:340`
(`s32` destination — the mask is the scroll wrap); `z_en_ru2.c:843` (the wrap changes which side of the comparison the sum lands
on); anything in `sys_matrix.c`/`code_800F9280.c` (RSP formats). There is **no `(negative) << 16 >> 16` in this tree**, so the
SM64 "UB fix, explained diff" item is empty for OoT.

## 2. Shifts as multiply/divide (`shift_as_mul.txt`, 680 hits: 413 `<<`, 267 `>>`)

Noise: `#define`s and flag words; RDP 10.2 texture-rectangle coordinates (`z_message_PAL.c` 27, `z_kaleido_item.c` 20,
`z_parameter.c` 19, `z_rcp.c` 15, `PreRender.c` 10 — all `x << 2`, `1 << 10`); `case (ELF_MSG_TYPE_END << 5)` message-opcode
packing (`z_elf_message.c` 16); `VTX(… 32 << 5 …)` 10.5 texcoords; save-flag composites `(EVENTCHKINF_…_INDEX << 4) + n`
(`z_en_daiku.c:408`, `z_en_fr.c:961-979`, `z_en_sth.c:279`); controller-pak address CRC (`libultra/io/contram*.c`).

| sub-class | hits → real | verdict | sites (declared type; why negative) | rewrite | gate |
|---|---|---|---|---|---|
| `<<` on a signed field that **can be negative** (UB, C11 6.5.7p4) | 3 | **DO** (UB removal, upstream-worthy) | `ovl_En_Wood02/z_en_wood02.c:287` `this->drawType \|= this->unk_14C << 4;` — `s16 unk_14C` (`.h:11`), set to `-1` at `:197` and `:200` (`else if (this->unk_14C & 0x80) this->unk_14C = -1;` — a spawner whose param high byte has bit 7 set reaches `:287` with `-1`), to `-0x15` at `:389`/`:411`; `z_en_wood02.c:196` `(this->actor.home.rot.z << 8) \| this->unk_14C` — `Vec3s home.rot`, any scene-supplied `s16`; `code/audio_seqplayer.c:1679` `seqScript->value << 1` — `s8 value` (`z64audio.h:254`), guarded only against `-1` (`:1678`) | `unk_14C * 16`, `home.rot.z * 256`, `value * 2` | IDENTICAL (`shl_u8_or_store`, `shl_s16_x8_or`, `shl_s8_x2`) |
| Same field, guarded `>= 0` at the site | 2 | **DO** (consistency) | `z_en_wood02.c:363` and `:409` (`(this->unk_14C << 4) \| 0x8000`) — both inside `if ((this->unk_14C >= 0) && …)` | `* 16` | IDENTICAL (`shl_s16_x16`, `shl_s16_x16_or`) |
| `<<` on a value non-negative by construction | ~20 | **LEAVE** (defined; `*` is taste) | `ovl_En_Trap/z_en_trap.c:80` (`s16 upperParams` but `& 0xF0` first); `ovl_En_Owl/z_en_owl.c:1260` (`s16 unk_3EE` ∈ {0, 0x20}, `:147,161,234`); `z_en_ishi.c:269`, `z_en_kusa.c:142` (`s16 dropParams = (params >> 8) & 0xF`); `z_en_bili.c:371`, `z_en_bx.c:174`, `z_en_vali.c:301` (`s32 i`, 0..3); `z_en_changer.c:129,141` (`s32` item ids); `z_en_in.c:678` (`s32 type` 0/1, `z_en_horse.h:99`); `z_eff_ss_kakera.c:393` (masked); `code_800EC960.c:4586` (`u8 targetVol`); `code/z_actor.c:4263` (`& 0xF8` first); `z_en_zf.c:1508` (`!call << 1`); `fault.c:856` (`u32`) | — | — |
| `<<` on an `s16` **data** value (positive only by table contents) | 2 | **LEAVE** | `code/z_map_exp.c:950` (`s16* owMinimapWidth`, `z64.h:1726`), `ovl_file_choose/z_file_choose.c:1231` (`static s16 sFileInfoBoxPartWidths[] = {36,…}`, `:147`) | — | — |
| `>>` on a signed value | 267 (≈40 in actors on signed) | **LEAVE — never `/`** | `ovl_player_actor/z_player.c:15001-15004` (`Vec3s angVel`: `angVel.y -= angVel.y >> 3;` `angVel.x += -rot.x >> 2;`); `code/z_camera.c:1358-1359` (`BINANG_SUB(…) >> 1`), `:1945,1949` (`>> 2`); `ovl_Bg_Haka_Sgami/z_bg_haka_sgami.c:230`; `code/z_scene_table.c:594,650,1446,1447` (`s8 sp83 = coss(…) >> 8`, `:592`); `ovl_En_Okuta/z_en_okuta.c:463` (`(timer - 64) >> 1`); `ovl_En_Blkobj/z_en_blkobj.c:118` | — | DIFF (`shr_signed_div`: `/ 2` adds `shrw $15; addl` — the toward-zero fixup **is** the behaviour change) |

**Look-alikes that are NOT safe:** every `>>` above (arithmetic shift floors, division truncates: `-1 >> 3 == -1`,
`-1 / 8 == 0`; the bunny-ear spring in `z_player.c:15001` and the camera lerps depend on the floor); `Oceff_Wipe*` `timer << 9`
(`z_oceff_wipe.c:86` etc.) is fed to `Math_SinS(s16)` — the wrap into the `s16` parameter is intended; `(1 << 2)` and `<< 5`
inside `gSP*`/`VTX` are the RDP's fixed-point formats.

## 3. Raw indices where a name exists, and byte-pointer arithmetic

OoT's actor structs are typed, so the SM64 "union index → field name" shape is absent. Three real shapes remain, and the byte
pointers. The 20 clearest sites: 5 (a) + 13 (b, horse state) + 2 (c, `memcpy`).

| shape | hits → real | verdict | sites | rewrite | why | gate |
|---|---|---|---|---|---|---|
| (a) Boss work-array indexed by a literal while the file's own enum names it | 5 | **DO** | `ovl_Boss_Ganon/z_boss_ganon.c:1567,4426,4452,4454,4468` `this->fwork[1]` — the enum `GDF_FWORK_1` is at `z_boss_ganon.h:13` and **87** other sites in the same file already use `fwork[GDF_…]` | `fwork[GDF_FWORK_1]` (and, matching the enum's style, rename it from the use at `:4426-4468`: a 0..255 alpha fade) | enum constant = the literal | IDENTICAL (`fwork_enum_index`) |
| (b) Horse-race state in `eventInf[0]` where the accessor macro exists | 13 + 2 | **DO** | `eventInf[0] & 0xF`: `code/z_horse.c:171,267`, `z_message_PAL.c:3757,4600`, `z_parameter.c:995`, `ovl_Bg_Ingate/z_bg_ingate.c:55`, `ovl_En_Horse/z_en_horse.c:689,813`, `ovl_En_In/z_en_in.c:147,549,575,929`, `ovl_Oceff_Spot/z_oceff_spot.c:84`; `(eventInf[0] & 0x10) >> 4` at `z_horse.c:217`; `z_en_in.c:678` `(eventInf[0] & ~0x10) \| (type << 4)` | `GET_EVENTINF_HORSES_STATE()`, `GET_EVENTINF_HORSES_HORSETYPE()`, `SET_EVENTINF_HORSES_HORSETYPE(type)` (`z64save.h:948-960`) | pure macros expanding to the same expression (`(e & (0xF << 0)) >> 0`) | IDENTICAL (`eventinf_state_macro`, `eventinf_settype_macro`) |
| (b') `eventChkInf[N] &= ~bit` where the flag is named but the accessor is a function | 7 | **CARE** (explained diff) | `code/z_demo.c:1233,1240,1247,1254,1261` (bits 0x800..0x8000 of word 11 = `EVENTCHKINF_COMPLETED_{FOREST,WATER,SHADOW,FIRE,LIGHT}_TRIAL` 0xBB-0xBF, `z64save.h:634-638`), `:1268` (word 10 bit 0x2000 = `EVENTCHKINF_COMPLETED_SPIRIT_TRIAL` 0xAD, `:622`), `ovl_Bg_Spot01_Fusya/z_bg_spot01_fusya.c:51` (`&= 0xFFDF` = clear 0x65 `EVENTCHKINF_PLAYED_SONG_OF_STORMS_IN_WINDMILL`, `:563`) | `Flags_UnsetEventChkInf(EVENTCHKINF_…)` (`functions.h:562`) | same bit, but through a cross-TU call | DIFF (`flags_unset_call`: `andw` → `jmp Flags_UnsetEventChkInf`) — hand to the maintainer as a semantic-identical, codegen-different patch, or add a pure-macro `CLEAR_EVENTCHKINF` first |
| Table-driven flag words | 9 | **LEAVE** | `ovl_En_Fr/z_en_fr.c:295,738,958-977` (`eventChkInf[13] & sSongIndex[…]`), `ovl_En_Niw/z_en_niw.c:174`, `ovl_En_Niw_Lady/z_en_niw_lady.c:214` (`infTable[25]`), `code/z_map_exp.c:1020,1057` (`infTable[26] & gBitFlags[…]`), `ovl_Bg_Dy_Yoseizo/z_bg_dy_yoseizo.c:772` | — | the index is a runtime table lookup; no single name applies | — |
| `unk_XX[literal]` on typed arrays | 370 | **LEAVE** | e.g. `z_kankyo.c:335,376` (`envCtx.unk_EE[1..3]`), `z_demo.c:287` (`roomCtx.unk_74[0]`), `z_en_zl2.c:239-241` (`s16 unk_1DC[0x18]`), `z_boss_ganon2.c` ×25 (`s16 unk_1A2[5]`, `.h:33`) | — | no alias exists; naming them is the rename task, not this one | — |
| (c) `(uintptr_t)ptr + N` handed to a pointer parameter | 17 | **DO** (2 unconditional, 15 after a macro check) | `code/z_message_PAL.c:1623,1631` `memcpy((uintptr_t)msgCtx->textboxSegment + MESSAGE_STATIC_TEX_SIZE, …)` — `void* textboxSegment` (`z64.h:656`); the other 15 (`:855,859,863,1090,…`) feed `gDPLoadTextureBlock`/`gSPInvalidateTexCache` | `(u8*)msgCtx->textboxSegment + MESSAGE_STATIC_TEX_SIZE` | integer→pointer conversion is a constraint violation that compiles **only** because of `-Wno-int-conversion` (GCC 16 rejects it without the flag — the gate script reproduced the error); the byte arithmetic is the same | IDENTICAL (`uintptr_plus`) — verify `gSetImage`'s cast of its `i` argument (`libultraship/include/libultraship/libultra/gbi.h:3023`) before touching the display-list sites |
| Redundant `(u8*)` on a `void*` parameter | 1 | **DO** | `ovl_Boss_Va/z_boss_va.c:731` `memset((u8*)sEffects, 0, …)` | drop the cast | `memset` takes `void*` | trivially identical |
| Allocator / overlay-relocation / ROM-segment / hardware-address byte arithmetic | ~150 | **LEAVE** | `code/__osMalloc.c` (26), `ovl_kaleido_scope/z_kaleido_scope_PAL.c` (42, `(uintptr_t)_…_staticSegmentRomStart` DMA symbols), `code/z_DLF.c`, `code_800FC620.c`, `relocation.c`, `boot/is_debug.c` (`(u32)&gISVDbgPrnAdrs->…`, 8), `boot/yaz0.c`, `stackcheck.c`, `ovl_Bg_Jya_Cobra/z_bg_jya_cobra.h:14` (`ALIGN16`), `z_player.c:10819` (align) | — | genuine byte-offset code | — |
| Debug-fill sentinel through a 32-bit truncation | 1 | **LEAVE** (flag) | `ovl_En_Horse/z_en_horse.c:2391` `(uint32_t)(uintptr_t)linkCsAction != 0xABABABAB` | — | a latent 64-bit bug, not an assembly-ism; note it in the task | — |

**Look-alikes that are NOT safe:** `z_demo_effect.c:1921` / `z_demo_kankyo.c:866` `disp = (uintptr_t)gEffFlash1DL;` carry the
decomp's own "This is probably fake" note — leave with the comment; `z_sram.c:187-188` (`i = eventChkInf[4] & ~1`) mixes a
flag clear with a temp used later — read before touching.

## 4. Casts — `(s32)`, `(f32)`, `(s16)`

| class | census → real | verdict | sites (operand type) | rewrite | why | gate |
|---|---|---|---|---|---|---|
| `(s32)` promotion no-op | 442 → 7 | **DO** | `ovl_Bg_Hidan_Kousi/z_bg_hidan_kousi.c:74`, `ovl_Bg_Spot01_Objects2/z_bg_spot01_objects2.c:112,115` (`((s32)thisx->params >> 8) & 0xFF`, `s16 params`); `ovl_En_Wallmas/z_en_wallmas.c:368` (`(s16)((s32)this->actor.yawTowardsPlayer + 0x8000)`, `s16 yawTowardsPlayer`); `ovl_Obj_Bean/z_obj_bean.c:415` (`(s32)this->unk_1C0 < 0`, `s16`, `.h:19`); `ovl_En_Fr/z_en_fr.c:850` (`(s32)ocarinaNoteIndex`, `u8`, `:811`); `code/z_skin_awb.c:123` (`limbMatrices[(s32)parentIndex]`, `u8`, `:113`) | drop the cast | integer promotion of a rank-below-`int` operand already yields `int`; no signedness flip (all operands are `s16`/`u8`) | IDENTICAL (`cast_s32_params`, `cast_s32_yaw`, `cast_s32_cmp0`, `cast_s32_u8index`) |
| `(s32)` float truncation | ~400 | **LEAVE** | `(s32)this->skelAnime.curFrame == 61` (`z_en_dh.c:468` and ~60 siblings: a frame test spelled as a cast), `(s32)(Rand_ZeroOne() * 30.0f) + 30`, `ovl_Demo_6K/z_demo_6k.c:484` `(i < (s32)this->unk_170)` — `f32 unk_170` (`.h:19`) | — | the truncation is the semantics | DIFF (`cast_s32_f32trunc_loop`, 15 lines) |
| `(f32)` on an `s16` in a float context | 370 → 32 (+~30 to read) | **DO** | all 32 `(f32)Animation_GetLastFrame(…)` (returns `s16`, `functions.h:1278`): 5 as an `f32 endFrame` argument of `Animation_Change` (`z_boss_dodongo.c:1688`, `z_en_ge3.c:62`, `z_en_mm2.c:93,97`, `z_en_tite.c:675`); 3 into `f32 frameCount` (`z_en_bom_bowl_man.c:100,133,171`, `.h:36`); **24 into `s16 endFrame`** (`z_en_dnt_jiji.c` ×9, `.h:24`; `z_en_dnt_nomal.c` ×15, `.h:31`) | drop the cast | assignment/argument conversion happens anyway; the `s16→f32→s16` round trip is exact (|v| < 2^24) and GCC folds it | IDENTICAL (`cast_f32_f32param`, `cast_f32_s16ret`, `cast_f32_roundtrip_s16store`) |
| `(f32)a / (f32)b` both integers | 12 | **CARE** | `code/z_eff_blure.c:546,575,643,648,662,682,909,1016,1098` (`s32 timer` / `s32 elemDuration`, `z64effect.h:73,85`), `z_eff_spark.c:187` | drop **one** cast only | one cast keeps the division in float; dropping both makes it integer division | IDENTICAL for one (`cast_f32_ratio_one`) |
| `(f32)a - (f32)b` on `u8` colours | 4 | **LEAVE** | `code/z_eff_spark.c:188-191` | — | same value, but GCC subtracts in int then converts — a different instruction sequence | DIFF (`cast_f32_u8diff`) |
| `(s16)` casts | 1051 → 0 removable | **LEAVE** | angle wraps: `(s16)(this->actor.yawTowardsPlayer + …)` 37, `(s16)(Camera_GetCamDirYaw(…) …)` 15, `(s16)(this->actor.shape.rot.y …)` 12; float→int: `(s16)Rand_ZeroFloat` 178, `(s16)(Rand_ZeroOne` 80, `(s16)this->fwork` 33, `(s16)(Math_SinS` 19, `(s16)(Math_FAtan` 19, `(s16)player->actor.world.pos.*` 37; **0** hits for `(s16)` on an `s16` field with no arithmetic (grep below) | — | every one either wraps an angle difference or truncates a float | `(s16)frameCount` ×22 (`f32` holding an integer, e.g. `z_en_diving_game.c:181`) is numerically a no-op but DIFF (`cast_s16_frameCount`: `cvttss2si`+`cvtsi2ss`) |

**Look-alikes that are NOT safe:** `z_demo_6k.c:484` (`unk_170` is `f32` despite the integer-looking loop);
`z_en_wallmas.c:368` keeps its **outer** `(s16)` (the wrap) — only the inner `(s32)` goes; any `(s16)` before `Math_SinS`/
`Math_CosS` of a sum is the ±180° seam.

## 5. Behaviour-parameter magic — how actors unpack `params`

**Yes, the macros exist at this pin** (`z64actor.h:493-518`) and the upstream per-actor idiom is already in-tree:
`ovl_En_Holl/z_en_holl.h:7-8` (`#define ENHOLL_GET_TYPE(thisx) PARAMS_GET_U((thisx)->params, 6, 3)`), `ovl_En_Dns/z_en_dns.h`
(`DNS_GET_TYPE`). Raw sites in `soh/src/overlays/actors` (`params (&|>>) …`): **1051 hits in 190 files**; by shape:

| raw shape | hits | macro | expansion equal? | gate |
|---|---|---|---|---|
| `(p >> s) & (2^n-1)` — e.g. `(params >> 8) & 0x3F` (91), `& 0xFF` (44), `>> 10) & 1` (12) | 230 + 57 unparenthesised (`params >> 8 & 0x3F`) | `PARAMS_GET_U(p, s, n)` | `(((p) >> (s)) & ((1 << (n)) - 1))` — textually the same after folding | IDENTICAL (`params_get_u`) |
| `p & (2^n-1)` — `& 0x3F` (109), `& 0xFF` (130), `& 0x1F` (65), `& 3` (75), `& 0x7F` (46), `& 0xF` (39), `& 1` (17) | ~590 | `PARAMS_GET_U(p, 0, n)` | `>> (0)` folds away | IDENTICAL (`params_mask_only`) |
| `p & M` with a shifted mask — `0xF0` (38), `0xFF00` (22), `0x8000` (22), `0xE000` (17), `0xFC00` (11) | ~113 | `PARAMS_GET_NOSHIFT(p, s, n)` | `(p) & (((1 << n) - 1) << s)` | identical by construction |
| `(p & M) >> s` — e.g. `(params & 0xE000) >> 0xD` (17), `(params & 0xFF00) >> 8` (14) | 69 | `PARAMS_GET_S(p, s, n)` | `(((p) & (((1 << n) - 1) << s)) >> s)` — **sign-extending**: for negative `params`, `(params & 0xFF00) >> 8` is −1..−128, while `(params >> 8) & 0xFF` is 0..255 | IDENTICAL (`params_get_s`) |
| `p >> s` with no mask | 32 | `PARAMS_GET_NOMASK(p, s)` | trivial | identical |
| `(u16)params …` | 39 | none | the cast is outside the macro's shape | leave as is |

**Verdict: CARE.** Every mapping is a pure macro and gates identical, but the payoff is the *name* (`ENXXX_GET_SWITCH_FLAG`),
which is one read per field per actor (~190 headers). Rules: map **shape to shape** (never turn an `S` site into a `U` site to
"normalise" it — the sign-extension differs), skip the 39 `(u16)` variants, and leave writes (`this->actor.params &= 0xFF`,
`z_en_wood02.c:203`) alone. `hex_magic.txt` (25378) adds nothing beyond these shapes for actors: its actor slice is these same
masks plus `Actor_SetColorFilter(…, 0x4000, …)` colour flags and `Item_DropCollectible(…, 0x4000 | …)` drop flags — named
constants for those are a different (constants) task.

## 6. Angle constants (`angle_constants.txt`, 13730; `binang_deg.txt`, 212)

Counts in `soh/src/overlays/actors/*.c`: `0x8000` 683 (226 in `± 0x8000` rotation arithmetic, 46 as `& | ^ ~` flag bits —
`Actor_SetColorFilter` `colorFlag == 0x8000` at `z_actor.c:4259`, the "don't count" drop bit `| 0x8000` at `z_en_wood02.c:409`,
params bit 15), `-0x8000` 52, `0x4000` 549 (`Actor_IsFacingPlayer(&this->actor, 0x4000)`, `ABS(yawDiff) <= 0x4000` vs the
non-angle `Actor_SetColorFilter(…, 0x4000, …)` and `| 0x4000` chest flags at `z_en_changer.c:129`), `0x2000` 210, `0x1000` 153,
`0xC000` 23, `0x7FFF` 32.

Precedent: `DEGF_TO_BINANG` appears in `z_camera.c` (145), `db_camera.c` (11), `z_olib.c` (4), `z_onepointdemo.c` (1) and **one**
actor (`ovl_En_Partner/z_en_partner.c:439`, a SoH-added actor); `RADF_TO_BINANG`/`BINANG_TO_RAD` in `z_boss_ganon.c`,
`z_en_anubice.c`, `z_en_go.c`, `z_en_du.c`, `z_en_in.c`, `z_en_ko.c`, `z_en_sa.c` — always on computed floats, never replacing a
literal. The only files mixing a raw `0x8000` with a BINANG macro are `z_boss_ganon.c`, `z_en_anubice.c`, `z_en_go.c`,
`z_en_partner.c`.

| candidate | verdict | why |
|---|---|---|
| `0x8000` → `DEGF_TO_BINANG(180.0f)` | **LEAVE** | the macro is `(s16)(32768.0006f)`: float→`s16` out of range is **UB** (C11 6.3.1.4p1). GCC 16 folds it to `-32768` (gate `c.c`: `movl $-32768`), so `y + 0x8000` stored to `s16` is IDENTICAL (`angle_0x8000_add`) — but in an `int` context (`(s32)fabsf(…) > 0x8000`, `z_en_zl2.c:310`; `ABS(d) < 0x8000`) `32768` and `-32768` are different values |
| `y + 0x8000` → `BINANG_ROT180(y)` | **LEAVE — wrong** | `BINANG_ROT180` is `(s16)(y - 0x7FFF)`: off by one (gate `angle_rot180_vs_add`: `leal -32768` vs `-32767`) |
| `0x4000`/`0x2000` → `DEGF_TO_BINANG(90.0f)`/`(45.0f)` | **LEAVE** (exact, but no gain) | folds to `16384`/`8192` exactly (gate `angle_0x4000_cmp` IDENTICAL); the rewrite trades one literal for a float expression with a rounding term, and 45% of `0x4000`s in actors are not angles — no precedent in actor code |
| `0x7FFF`, `0xC000`, `0x1000` | **LEAVE** | clamps, three-quarter turns, and non-angles; no exact macro |

Only multiples of 5.625° would ever be exact under an integer `x * 0x10000 / 360`; OoT has no such macro, so the SM64 `DEGREES()`
rows have no OoT equivalent. If the maintainer wants names, the correct first patch is a new integer macro in `z64math.h`, not a
substitution.

## 7. Double literals and `/ const` — LEAVE, confirmed

**Double literals** (`double_literals.txt`, 361 hits in 118 files — a quarter of SM64's, since zeldaret used `f` consistently).
Exact constants are no-ops but pointless (gate `dbl_exact_store`, `dbl_exact_cmp` IDENTICAL): `z_en_skj.c:1614` `= 50.0`,
`z_boss_mo.c:1108` `= 0.0`, `z_en_butte.c:279` `< 120.0`, `z_bg_gnd_nisekabe.c:34` `= 3000.0`, `z_player_lib.c:1263`
`Matrix_Scale(0.8, …)` (an `f32` parameter: `(f32)0.8 == 0.8f` by correct rounding). Five where adding `f` **changes results**:

1. `ovl_En_Am/z_en_am.c:710` `… * (this->dyna.unk_150 * 0.5f) * 0.14222` — `f32 * double` multiplies in double and rounds once (gate `dbl_inexact_mul` DIFF: `cvtss2sd; mulsd; cvtsd2ss` vs `mulss`).
2. `code/z_actor.c:2477` `ratio = 1.0f + ((f32)temp * 0.2); // required to match` — the decomp's own annotation that the double is deliberate (gate `dbl_required_to_match` DIFF).
3. `ovl_En_Gs/z_en_gs.c:433` `this->unk_1EC = M_PI / 9.0000002;` — the `…02` exists to reproduce the ROM's constant.
4. `code/z_en_item00.c:431-437` `Actor_SetScale(&this->actor, 0.045 - 1e-10);` — a double subtraction chosen to land one ulp below `0.045f`.
5. `code/z_kankyo.c:1540` `adjScale *= 0.001 * (scale + 630.0f * temp);` and `code_800EC960.c:4112,4415` (`1.0293 - …`, `(sp24 * 0.7) + 0.3`).

Annotation conventions in this tree: `// required to match` (`z_actor.c:2477`), `// (fake match?)` (`z_player.c:11166-11167`),
`//!` bug notes (196 in `soh/src`), and only **3** `//?` (none about floats — `__osMalloc.c:783`, `z_map_mark.c:81`,
`z_en_horse.h:146`); there is no `US_FLOAT`-style macro. A comment-only patch extending `// required to match` to items 1, 3-5
is the only defensible move.

**`/ const`** (`div_const.txt`, 995 hits, 209 files). Denominators: `/ 100.0f` 153, `/ 32768.0f` 71, `/ 1000.0f` 69,
`/ 3.0f` 58, `/ 10.0f` 56, `/ 2.0f` 44, `/ 4.0f` 39, `/ 180.0f` 32, `/ 255.0f` 24, `/ 6.0f` 22, … Power-of-two divisors
(`2, 4, 8, 16, 256, 1024, 32768` ≈ 180 hits) are already strength-reduced by GCC (gate `div_pow2`, `div_32768` IDENTICAL),
so the rewrite buys nothing; every other divisor (~80%) differs (gate `div_100` DIFF: `divss` → `mulss`). Five where
`x * (1/C)` changes results: `ovl_Boss_Ganon/z_boss_ganon.c:223` `scale / 1000.0f`; `ovl_En_Fire_Rock/z_en_fire_rock.c:111`
`Rand_ZeroFloat(2.0f) / 100.0f`; `ovl_Boss_Fd2/z_boss_fd2.c:499` `(spawnVel.z * -10.0f) / 100.0f`; `ovl_En_Js/z_en_js.c:195`
`sREG(81) / 10.0f`; `ovl_En_Go2/z_en_go2.c:1453` `20.0 / 3.0f` (a **double** division folded at compile time — also class 7a).

## Grep commands used

```sh
# macros and prerequisites
grep -rn "BINANG\|DEG_TO_BINANG\|PARAMS_GET\|define ABS" soh/include/macros.h soh/include/z64math.h soh/include/*.h
grep -rnoE 'PARAMS_GET_(U|S|NOMASK|NOSHIFT)|PARAMS_PACK' soh/src | cut -d: -f3 | sort | uniq -c
grep -m1 -A4 'z_actor.c.o:' Shipwright/build-cmake/build.ninja | grep -E '^\s*FLAGS'
# class 1
grep -rnE '<< *(16|0x10)\)? *>> *(16|0x10)' soh/src
# class 2
grep -v '#define' data/shift_as_mul.txt | grep '<< [1-5]' | grep -v 'gDP\|gSP\|G_TX\|G_IM'
grep -rhoE "this->[A-Za-z_0-9.]+ << (0x)?[0-9A-Fa-f]+" soh/src/overlays/actors --include=*.c | sort | uniq -c
grep '>> [1-5]' data/shift_as_mul.txt | grep overlays/actors | grep -v 'params\|gDP\|gSP\|& 0x'
# class 3
grep -rnE "\b(work|fwork|workf|unk_1A2)\[[0-9]+\]" soh/src/overlays/actors --include=*.c
grep -rhoE "eventInf\[0\] (&|\|=|&=|=) *~?(0x[0-9A-Fa-f]+|[0-9]+)" soh/src | sort | uniq -c
grep -rnE "gSaveContext\.(eventChkInf|infTable|itemGetInf)\[[0-9]+\] *(&|\|=|&=)" soh/src | grep -v 'flg_set.c\|z_sram.c'
grep -rn "(uintptr_t)msgCtx->textboxSegment" soh/src
# class 4
grep -E '\(s32\)(this|thisx)->(actor\.)?(params|unk_[0-9A-F]+|yawTowardsPlayer)\b|\(s32\)(i|limbIndex|parentIndex|ocarinaNoteIndex)\b' data/cast_s32.txt
grep -rn "(f32)Animation_GetLastFrame" soh/src/overlays/actors --include=*.c
grep -oE '\(s16\)\(?[A-Za-z_>.-]+' data/cast_s16.txt | sort | uniq -c | sort -rn
grep -E '\(s16\)(this|thisx|player)->actor\.(params|yawTowardsPlayer|shape\.rot\.[xyz]|world\.rot\.[xyz])\b *[,;)]' data/cast_s16.txt
# class 5
grep -rhoE "params (&|>>) -?(0x[0-9A-Fa-f]+|[0-9]+)\)? *(&|>>)? *(0x[0-9A-Fa-f]+|[0-9]+)?" soh/src/overlays/actors | sort | uniq -c | sort -rn
grep -rnoE "\(([A-Za-z_>.&-]*)params >> [0-9]+\) *& *(0x[0-9A-Fa-f]+|[0-9]+)" soh/src/overlays/actors --include=*.c | wc -l   # U shape
grep -rnoE "\([A-Za-z_>.-]*params & (0x[0-9A-Fa-f]+|[0-9]+)\) >> (0x[0-9A-Fa-f]+|[0-9]+)" soh/src/overlays/actors --include=*.c | wc -l  # S shape
# class 6
for c in 0x8000 -0x8000 0x4000 -0x4000 0x2000 0x1000 0xC000 0x7FFF; do grep -rnE "(^|[^0-9A-Fa-fx])$c\b" soh/src/overlays/actors --include=*.c | wc -l; done
grep -rnE "(rot\.[xyz]|[yY]aw|[aA]ngle)[^;]*[-+] 0x8000\b" soh/src/overlays/actors --include=*.c | wc -l
grep -rl "DEGF_TO_BINANG\|RADF_TO_BINANG" soh/src/overlays/actors --include=*.c
# class 7
grep -oE "/ [0-9]+\.[0-9]*f?\b" data/div_const.txt | sort | uniq -c | sort -rn
grep -rn "//?" soh/src | wc -l; grep -iE "float|double|\.0" data/matching_comments.txt
```

Synthetic gate (shape evidence, 46 pairs): the session scratchpad (`gate/pairs.txt`, not kept — the method is described below),
`pairs2.txt`, `pairs3.txt` — each line `name|before|after`, compiled with the Shipwright flags plus `-fno-asynchronous-unwind-tables`
and diffed after dropping assembler directives. Worth promoting into `tasks/adhoc/ocarina-assembly-isms/` as a `shape_gate.sh`
if the batches below go ahead (it is under a session temp path now).

## Recommended batch order

1. **Class 1 droppable masks** (22 sites: the DO rows of §1, plus the two `fault.c` sign-extension idioms) — expected IDENTICAL
   everywhere; delete the two confession comments (`z_bg_spot02_objects.c:311`, `z_room.c:181`) with their masks.
2. **Class 4 promotion casts** — the 32 `(f32)Animation_GetLastFrame` and the 7 `(s32)` no-ops; IDENTICAL; skip `z_demo_6k.c:484`.
3. **Class 3 named indices** — `fwork[GDF_FWORK_1]` ×5, the 15 horse-state macro sites, `memset` cast; then the two `memcpy`
   `textboxSegment` sites (a real portability fix: the code compiles only under `-Wno-int-conversion`), and the 15 display-list
   siblings once `gSetImage`'s cast is confirmed.
4. **Class 2 UB left shifts** — `z_en_wood02.c:196,287` (+ `:363,409` for consistency) and `audio_seqplayer.c:1679`; IDENTICAL,
   and the strongest upstream story in this report (defined behaviour, same bytes).
5. **Class 5 params** — one actor at a time, always via a per-actor `ENXXX_GET_*(thisx)` macro in its `.h` (the En_Holl idiom),
   shape-to-shape; identical by construction, but it is a naming job with ~190 headers of tail — decide the scope first.
6. **Explained-diff list for the maintainer**: `Flags_UnsetEventChkInf` ×7 (§3 b'), `z_en_cow.c:144` (§1), `(s16)frameCount` ×22
   (§4) — semantically identical, codegen different, play-test or drop.
7. **LEAVE, and say so in the task**: every `>>` on a signed value, all angle literals (no exact integer macro exists;
   `BINANG_ROT180` is off by one), the `(s16)` class, double literals, and `/ const`.
