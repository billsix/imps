# OoT (Ship of Harkinian) assembly-isms survey — booleans, decomp comments, whole-function reads

**Pin:** `acdbc651d4b11e29518442d6875a3ec181414cfc` (branch `imps-standard-c`, bare pin; HEAD verified =
`PIN_SHA` in `n64/OcarinaOfTime/fetch.sh`). **Date:** 2026-09-22. Read-only reader report; every claim is from
code the reader opened. Paths are relative to `n64/OcarinaOfTime/Shipwright/` (so `soh/src/...`). Sister report
(shape and rigour): `tasks/adhoc/mario64-assembly-isms/reports/booleans-comments-whole-functions.md`; rules:
`tasks/reference/mario64/assembly-isms-in-the-decomp.md` patterns 8, 9, 19, 20 and "What the first cut found".

## Build facts that decide the verdicts

- **C23, GCC `-O2`, no LTO on Linux.** `CMakeLists.txt:137` `CMAKE_C_FLAGS_RELEASE "-O2 -DNDEBUG"`;
  `INTERPROCEDURAL_OPTIMIZATION_RELEASE` is set only for Windows/Darwin targets (`soh/CMakeLists.txt:236-250`), so a
  per-file `.s` gate sees exactly what the Linux link sees. `true`/`false` are keywords (the tree uses them, not
  `TRUE`/`FALSE`).
- **Consequence for pattern 8:** `x == true` → `x` gates IDENTICAL only when the compiler already knows `x ∈ {0,1}`
  *in that function*: a `:1` bitfield, a `u8`/`bool`, a comparison, or a local written only with literal
  `true`/`false` (VRP sees it). It does **not** know it for a plain `s32`/`s16`/`s8` field, an `s32` parameter, or
  the return of an `s32` function in another TU (and not reliably for one in the same TU unless inlined) — those go to
  the explained-diff list even when every writer is `true`/`false`.
- **Consequence for pattern 9:** `x != 0` → `x` and `x == 0` → `!x` are *always* codegen-identical (both are
  truthiness tests). Class B is a readability call only; drop the comparison where the operand reads as a fact,
  keep it for counters/indices/masks/returns whose 0 is a value.
- **Consequence for byte loops:** `-O2` enables `-ftree-loop-distribute-patterns`, so an open-coded copy loop *may
  already be* a `memcpy` call in the binary — the mario64 `-O1` rule ("differs by construction") does not carry;
  let the gate decide.
- **SoH interleaving:** `git blame` over all 136 boolean sites: 133 originate in the 2022 decomp import (later touches
  are the `PlayState` rename, clang-format, scene-table rename — mechanical). Three are SoH's own code:
  `soh/src/code/z_camera.c:1428` (`SetCameraManual`, a SoH function on the SoH `bool manualCamera` field) and
  `soh/src/overlays/gamestates/ovl_select/z_select.c:1148,1168` (the "Enhanced debug warp screen" copy of the decomp
  block at `:961,:980`). **Leave those three.**

---

## Class A — `bool_vs_TRUEFALSE` (136 census hits → 136 real; 133 decomp, 3 SoH)

Verdicts by operand (declared type quoted; line lists are the census lines). One line (`audio_seqplayer.c:453`)
carries both a DO operand and a CARE operand.

### DO — compiler already knows 0/1 (≈58 lines, 25 files) → expected gate IDENTICAL

| operand | declared type (where) | sites `soh/src/…` | rewrite |
|---|---|---|---|
| `noteSubEu.bitField0.needsInit` | `u8 needsInit : 1` (`include/z64audio.h:527`) | `code/audio_playback.c:155`, `code/audio_synthesis.c:723,1028` | `if (x)` |
| `layer->stopSomething`, `->continuousNotes`, `->bit1`, `->bit3` | `u8 … : 1` (`z64audio.h:424-428`) | `code/audio_seqplayer.c:421,449,453` | `if (x)`; `bit1 == 1` → `bit1` |
| `seqPlayer->stopScript` | `u8 stopScript : 1` (`z64audio.h:265`) | `code/audio_seqplayer.c:1533` | `if (x)` |
| `sIsOcarinaInputEnabled`, `sIsMalonSinging` | `static u8` (`code_800EC960.c:889,1308`), writers all `true`/`false` (`:1633…2304`, `:3289,5184`) | `code/code_800EC960.c:2457,2460,3287` | `if (x)` |
| `….status.active` | `u8 active` (`include/z64effect.h:30`), writers `= false` only (`z_effect.c:215-251`) + zero-init | `code/z_effect.c:46,55,64,112,124,135` | `if (x)` / `if (!x)` |
| `*checkedPoly` | `u8* checkedPoly` over `u8* polyCheckTbl` (`z_bgcheck.c:925`, `z64bgcheck.h:167`) | `code/z_bgcheck.c:945` | `if (*checkedPoly \|\| …)` |
| `player->bodyIsBurning` | `u8` (`z64player.h:931`), writers `true`/`false`/`1` | `overlays/actors/ovl_Boss_Fd/z_boss_fd.c:1486` | `if (!x)` |
| `this->faceExposed` | `u8` (`z_boss_fd.h:163`), writers `0`/`true` (`z_boss_fd2.c:253,851`) | `ovl_Boss_Fd/z_boss_fd.c:1790` | `if (x && …)` |
| `isBelowWaterSurfaceCurrent`, `isJumpingUp`, `isActive` | `u8` ×3 (`z_en_fr.h:53,54,57`) | `ovl_En_Fr/z_en_fr.c:353,595,759` | `if (!x)` |
| `this->isDespawning` | `u8` (`z_en_fz.h:49`) | `ovl_En_Fz/z_en_fz.c:689` | `if (!x)` |
| `this->unk_211` | `u8 unk_211; // Conditional` (`z_en_go2.h:80`) | `ovl_En_Go2/z_en_go2.c:1681,2016` | `if (x)` |
| `this->canSpeak` | `u8` (`z_en_zo.h:29`) | `ovl_En_Zo/z_en_zo.c:521` | `if (x)` |
| `outOfWater` | `u8` parameter (`z_fishing.c:2829`) | `ovl_Fishing/z_fishing.c:2839` | `if (!x)` |
| `(anim == &gX) == false` | comparison result | `ovl_En_Ko/z_en_ko.c:692,697,745,751,765,772` | `if (this->skelAnime.animation != &gX)` |
| `((acFlags & AC_HIT) != 0) == false` | comparison result | `ovl_En_Bubble/z_en_bubble.c:287` | `if (!(… & AC_HIT))` |
| `needNewSound` | local, literal `true`/`false` only (`code_800F7260.c:442-478`) | `code/code_800F7260.c:471,482` | `if (x)` |
| `useCustomSubdivisions`, `dynaPolyCollision`, `foundSlot` | locals, literal only (`z_bgcheck.c:1564/1571`, `:1987/1993`, `:2653/2658` — `s32 foundSlot = false;`) | `code/z_bgcheck.c:1575,2007,2663` | `if (!x)` / `if (x \|\| …)` |
| `foundFree` | `s32` local, literal only (`z_effect_soft_sprite.c:100,109,112`) | `code/z_effect_soft_sprite.c:128` | `if (x)` |
| `hitWithBottle` | local, literal only (`z_boss_ganon.c:4017,4019`) | `ovl_Boss_Ganon/z_boss_ganon.c:4027,4045` | `if (!x && …)`; and `:4013-4019` → `hitWithBottle = (cond);` |
| `isFree` (daiku) | `s32 isFree = false;` + `= true` ×4 (`z_en_daiku.c:155-165`) | `ovl_En_Daiku/z_en_daiku.c:167,169` | `if (x && …)` / `if (!x && …)` |
| `animChanged` | `s32 animChanged = 0;` + `= true` (`z_en_horse.c:2026-2048`, `:2461-2482`) | `ovl_En_Horse/z_en_horse.c:2067,2503` | `if (x)` |
| `movingFast` | local, `= 0`/`= 1` only (`z_en_horse.c:3175,3178`) | `ovl_En_Horse/z_en_horse.c:3209,3210,3212,3221,3223,3254,3266,3279,3303,3308,3312,3315` | `movingFast` / `!movingFast`; `else if (movingFast == true)` → `else` |

### CARE — plain-int field every writer sets true/false (16 lines) → explained diff (`cmp $1` vs `test`)

| operand | declared type | writers (all 0/1) | sites |
|---|---|---|---|
| `preload->isFree` | `s32 isFree` (`z64audio.h:697`, `AudioPreloadReq`) | `audio_load.c:1967 = false`, `:2015,:2034 = true` | `code/audio_heap.c:1112`, `code/audio_load.c:2007,2025` |
| `pool->entries[i].inUse` | `s8 inUse` (`z64audio.h:641`) | `audio_heap.c:1159,1240 = true` (cleared by pool zeroing) | `code/audio_heap.c:1129` |
| `this->lightDecay` | `s32 lightDecay; // … when set to 1` (`z64effect.h:153,174`) | **one writer, a copy: `z_eff_shield_particle.c:53 = initParams->lightDecay`** — a value test, not a boolean; a caller passing 2 would change behaviour under `if (x)`. LEAVE. | `code/z_eff_shield_particle.c:54,68,105` |
| `this->pathContinue`, `this->run` | `s32` ×2 (`z_en_daiku_kakariko.h:21,22`) | `:379,:400` / `:380,:393,:401,:422` — all `true`/`false` | `ovl_En_Daiku_Kakariko/z_en_daiku_kakariko.c:373,420,428` |
| `this->playerControlled` | `s32` (`z_en_horse.h:107`) | `:832,:2359 = false`, `:2385,:3036 = 1`, `:3042 = 0` | `ovl_En_Horse/z_en_horse.c:949,3527` |
| `this->inRace` | `s32` (`z_en_horse.h:141`) | `z_en_horse_game_check.c:149,153,338 = 1`, `z_en_horse.c:725 = false` | `ovl_En_Horse/z_en_horse.c:3508,3512` |
| `this->lockUp`, `->lockDown` | `s32` ×2 (`include/z64.h:1387-1388`) | `z_select.c:966,1063,1244,1886` / `:985,1071,1252,1887` — `true`/`false`/`0` | `ovl_select/z_select.c:961,980` (decomp); `:1148,1168` are SoH — leave |
| `noStop` | file-static (writers `z_message_PAL.c:2940 = false`, `:2964 = true`, **`:2996 = gSaveContext.hudVisibilityMode`** — multi-valued) | value test; LEAVE | `code/z_message_PAL.c:2994` |

### CARE — `s32` function result or `s32` parameter (≈58 lines) → explained diff unless inlined

Every function below returns only literal `true`/`false` or a comparison (return statements read), so
`f() == true` ⇔ `f()` *behaviourally*; the compiler does not know it across the call.

| callee / parameter | returns / declared | sites |
|---|---|---|
| `DynaPoly_IsBgIdBgActor` | `s32`, `return false/true` (`z_bgcheck.c:2610-2615`) | `code/code_800430A0.c:80` (other TU), `code/z_bgcheck.c:2729` |
| `CollisionPoly_CheckYIntersect`, `…Approx1` | `s32`, forward `Math3D_TriChkPointParaY…` (`sys_math3d.c:1017-1039` literal) | `code/z_bgcheck.c:562,3065` |
| `BgCheck_IsSpotScene`, `BgCheck_PosInStaticBoundingBox`, `BgActor_IsTransformUnchanged`→`ScaleRotPos_Equals`, `BgCheck_CheckDynaCeilingList`, `BgCheck_CheckLineAgainstBgActor` | `s32`, literal / `result` copies (`z_bgcheck.c:1441-1456, 1664-1673, 2501-2507, 3455-3513, 3615-3649`) | `code/z_bgcheck.c:1543,1998,2238,2817,3544,3679` |
| `BGCHECK_POS_ERROR_CHECK()` → `BgCheck_PosErrorCheck` | `s32`, `return true/false` (`z_bgcheck.c:56-66`) | `code/z_bgcheck.c:1916,2104,2178,2391` |
| `Math3D_LineVsCube`, `Math3D_XZInSphere` | `s32`, literal (`sys_math3d.c:646-839, 2114-2123`) | `code/z_bgcheck.c:2218,3116` |
| `result = BgCheck_CheckLineInSubdivision(…)` | `s32 result` (`z_bgcheck.c:2166`) | `code/z_bgcheck.c:2244` |
| `WaterBox_GetSurface1` | `s32` (`z_bgcheck.c:4209`) | `code/z_play.c:2163` |
| `FrameAdvance_IsEnabled` | `s32`, `return !!play->frameAdvCtx.enabled` (`z_play.c:2126-2128`; `s32 enabled` `z64.h:298`) | `code/z_collision_check.c:1182,1215,1260,1293,1338,1372,1412` |
| `shouldDraw = overrideLimbDraw(…)` | `SkinOverrideLimbDraw` = `s32 (*)(…)` (`z64skin.h:83`), initialised `true` (`z_skin.c:218`) | `code/z_skin.c:226,228` |
| `dialogStarted = EnGo_UpdateTalking / Npc_UpdateTalking` | `s32 dialogStarted` (`z_en_go.c:579`); callees literal (`z_actor.c:4310-4331`) | `ovl_En_Go/z_en_go.c:600` |
| `EnGo_FollowPath`, `EnGo2_IsRollingOnGround`, `EnHorse_PlayerCanMove`, `EnKo_IsWithinTalkAngle`, `EnSkj_IsLeavingGame` | `s32`, literal (same TU; GCC may inline → then IDENTICAL) | `z_en_go.c:725,755`; `z_en_go2.c:1746`; `z_en_horse.c:1105,1145,1387,1431,1529,1570`; `z_en_ko.c:710,730,770`; `z_en_skj.c:1263` |
| `Actor_IsMounted`, `Actor_NotMounted` | `s32`, literal (`z_actor.c:2188-2216`, other TU) | `ovl_En_Horse/z_en_horse.c:3033,3038` |
| `BgCheck_EntityLineTest1` → `BgCheck_CheckLineImpl` | `s32` (`z_bgcheck.c:2306, 2158-2253`) | `ovl_En_Peehat/z_en_peehat.c:998`, `ovl_En_Trap/z_en_trap.c:193`, `ovl_En_Vm/z_en_vm.c:490` |
| `animationEnded = SkelAnime_Update(…)` | `s32` via `skelAnime->update.normal` function pointer (`z_skelanime.c:1557-1558`) — range unknowable | `ovl_En_Horse_Link_Child/z_en_horse_link_child.c:389,391,408,410,417,419,424` (`x == true ? 1 : 0` → `x`) |
| `galloping` | `s32` parameter (`z_en_horse.c:2877`; caller passes `speedXZ > 8`, `:2919`) | `ovl_En_Horse/z_en_horse.c:2902` |
| `noLoad`, `didAllocate`, `sameSound`, `apply` | `s32` params / out-param (`audio_load.c:651`, `:53` `s32*`, `audio_seqplayer.c:442`, `audio_heap.c:1315`) | `code/audio_load.c:668,718`; `code/audio_seqplayer.c:453,459`; `code/audio_heap.c:1352` |

`audio_heap.c:1352` `if ((apply != false) && (apply == true))` is a fakematch: GCC folds it to `apply == 1`, so
rewriting to `if (apply == true)` alone is IDENTICAL; going further to `if (apply)` is the explained diff.

### Look-alikes that are NOT safe (class A)

- `code/z_eff_shield_particle.c:54,68,105` `lightDecay == true` — copied from an init-params struct; a value test.
- `code/z_message_PAL.c:2994` `noStop == false` — one writer stores `hudVisibilityMode`.
- Any `Flags_GetEventChkInf(...) == true` would be wrong: it returns a **mask** (`z_actor.c:4931-4933`
  `return eventChkInf[flag >> 4] & (1 << (flag & 0xF))`). None exist today; don't create one.
- `z_bg_jya_1flift.c:190` `DynaPolyActor_IsPlayerOnTop(&this->dyna) ? true : false` — the `?:` normalises an
  `s32` return; keep unless the callee is proven 0/1.

---

## Class B — `cmp_zero` sample (6491 census hits; 60 sampled by name/type)

Rule (pattern 9): drop only where the operand reads as a fact. Gate: any drop is IDENTICAL by construction.
Census shape: 510 lines are `(… & …) == 0`/`!= 0` mask tests (keep the parentheses, drop nothing), 1223 mention
`timer` (keep), 118 are `predicate(...) != 0/== 0` calls.

**DO (verifiably boolean, ≈40 in the sample):** `code/audio_heap.c:343,357,413,426` `bitField0.enabled != 0`
(`u8 enabled : 1`, `z64audio.h:526`) and `:384,398` `seqPlayers[i].enabled != 0` (`z64audio.h:259`);
`code/z_parameter.c:2906,6801` and `ovl_Bg_Dy_Yoseizo/z_bg_dy_yoseizo.c:763` `isDoubleDefenseAcquired != 0` /
`isMagicAcquired != 0 / == 0` (`u8`, `z64save.h:304,307`, writers `true`/`1`); `ovl_Bg_Spot18_Basket/…:401`
`isHeartPieceGiven != 0` (`u8`); `ovl_En_Bombf/z_en_bombf.c:324,377` `isFuseEnabled != 0` (`s32`, writers `= 1`
only); `code/z_player_lib.c:1509` `weaponInfo->active == 0` (`s32 active`, writers `= 1`); predicate calls
`ovl_Bg_Spot05_Soko/…:61` `Flags_GetSwitch(...) != 0`, `ovl_Bg_Haka_Tubo/…:199` `Flags_GetCollectible(...) != 0`,
`z_horse.c:79,172` `Flags_GetEventChkInf(...) != 0 / == 0` (mask return — `!= 0` → truthiness is exact, `== true`
would not be), `ovl_En_Brob/…:154` `DynaPolyActor_IsPlayerOnTop(...) != 0`, `ovl_Bg_Ydan_Sp/…:285`
`Player_IsBurningStickInRange(...) != 0`, `ovl_En_Dodojr/…:450` `EnDodojr_IsPlayerWithinAttackRange(...) != 0`,
`code/audio_heap.c:1214` `AudioLoad_IsFontLoadComplete(fontId) != 0`, `code/z_elf_message.c:41,54,57`
`CHECK_*_ITEM(...) != 0` (mask macros — keep `!= 0` if the result is *stored* into a bool-typed field, drop it in
an `if`).

**KEEP (value, not fact):** `code/code_800F9280.c:191,217` `found == 0` — `u8 found` holds an *index* (`:173-204`
`found = sNumSeqRequests[…]` / `= i`); `libultra/io/*.c` `pfs->activebank != 0` (bank *number*);
`ovl_Boss_Sst/…:2586`, `ovl_En_Bili/…:559`, `ovl_En_Dh/…:489`, … `Actor_ApplyDamage(&this->actor) == 0` (returns
remaining health; 0 = dead); `ovl_En_Dnt_Demo/…:127,139` `Player_GetMask(play) == 0` (mask id, 0 = none);
`code/z_lifemeter.c:204,310,649`, `code/z_parameter.c:892,3360,6391` `interfaceCtx->unk_2xx != 0` (`s16`/`u16`/`u8`,
unnamed — meaning unknown, one is "screen fill alpha?"); every `this->unk_2xx == 0` in `z_boss_ganon.c`,
`z_en_am.c`, `z_en_attack_niw.c`, `z_en_bw.c`, `z_demo_im.c` (unnamed; the rename task owns them);
`code/sched.c:62` `sc->unk_24C != 0` (`UNK_TYPE4`); `code/z_player_lib.c:1950,1960` `func_8002DD78(this) != 0`
(`return func_8002DD6C(player) && player->unk_834` — a boolean, but unnamed; drop after the rename).

---

## Class 2 — the other boolean shapes (grep results, whole tree `soh/src`)

| shape | sites | verdict | rewrite / why | expected gate |
|---|---|---|---|---|
| `switch (bool)` with `case false:`/`case true:` and **no `default:`** (checked all 8) | `ovl_Bg_Mori_Elevator/z_bg_mori_elevator.c:97` (`static s16 sKankyoIsSpawned`), `ovl_Boss_Mo/z_boss_mo.c:2143` (`s16 work[MO_CORE_WAIT_IN_WATER]`), `ovl_En_Fr/z_en_fr.c:519` (`u8 isGrowing`), `code/audio_load.c:1916,1947,2182,2207` (`s32 async` param), `ovl_En_Heishi1/z_en_heishi1.c:287` (`s16 headBehaviorDecided`) | CARE | `if (!x) {…} else {…}` silently gains behaviour for values ≠ 0/1 (none written today); block layout changes (first cut) | DIFF, explained |
| boolean `++` | `ovl_En_Clear_Tag/z_en_clear_tag.c:927,954,980,1014,1043` (`u8 isMaterialApplied = false;`, each `++` under `if (!isMaterialApplied)`) | DO | `= true`; GCC constant-folds `0+1` after the guard | IDENTICAL expected |
| boolean `++` | `ovl_En_Ex_Item/z_en_ex_item.c:273,359` `this->stopRotate++` under `if (!this->stopRotate)` (`:270,:356`); `ovl_Boss_Va/z_boss_va.c:1631,2516` `isDead++` under `if (!isDead)`, **`:2814` unguarded** (`u8 isDead`, only ever tested for truthiness `:1629,2505,3241…3274`) | CARE | `= true` is behaviour-preserving (all reads are truthiness); `add` vs `mov` differs | DIFF, explained |
| **not** boolean `++` | `ovl_Boss_Va/z_boss_va.c:749,2888` `onCeiling++/--` — `u8 onCeiling` is multi-valued (`= 2`, `= 6`, `> 0` at `:2887`) | LEAVE | a counter with a boolean name | — |
| Yoda `literal < x` | 58 hits; decomp ones e.g. `code/z_actor.c:621`, `code/z_view.c:724,726`, `code/audio_playback.c:114,122,554`, `code/z_collision_check.c:3586,3590,3591`, `code/sys_math3d.c:1734,1738,1739`, `ovl_Arrow_*/…:103-104` `950.0f < projectedW`, `ovl_Boss_Ganon/z_boss_ganon.c:3814,3823` `0 <= index`, `ovl_Bg_Mori_Rakkatenjo/…:91,97`, `ovl_player_actor/z_player.c:15335` | DO | flip operator and operands (`x > 950.0f`); GCC canonicalises comparisons | IDENTICAL expected |
| Yoda, leave | `libultra/rmon/xldtob.c` (14 hits — libc-derived, keep its style); `code/jpegdecoder.c:117` `while (0 < zeroCount--)`, `libultra/io/contramread.c:59` `while (0 <= retryCount--)` (side effect in the operand; flipping is still exact but gains nothing) | LEAVE | | |
| Yoda `-1 == x` | `code/mempak.c:116` (SoH file) | LEAVE (SoH) | | |
| `if (c) return true; else return false;` | `code/z_actor.c:2188-2216` `Actor_IsMounted`/`Actor_NotMounted`; `code/sys_math3d.c:287,835,1046,1086,1158,1198,1272,1311,1406,1618,2120,2132,2144`; `ovl_Effect_Ss_Kakera/…:340-344`; `ovl_En_Horse/z_en_horse.c:728-737` `EnHorse_PlayerCanMove` (`if (big) return false; return true;`); `ovl_En_Ko/z_en_ko.c:672-685` (`result = true/false; return result;`); `ovl_player_actor/z_player.c:8068-8073` (`return 1; … return 0;`) | DO | `return (c);` — `c` is a comparison/`&&`-chain, so the value is already 0/1 (`s32` return type keeps `0`/`1` bits) | IDENTICAL expected (GCC emits `setcc`/`movzx` either way); gate each |
| `x = c ? true : false` on a bool-typed target | `ovl_En_Fr/z_en_fr.c:339` (`u8 isBelowWaterSurfaceCurrent`), `:797` (`u8 isButterflyDrawn`, `z_en_fr.h:72`); `ovl_En_Hy/z_en_hy.c:863` `return !LINK_IS_ADULT ? false : true;` (`LINK_IS_ADULT` is a comparison, `macros.h:56`) → `return LINK_IS_ADULT;` | DO | `x = (c);` | IDENTICAL expected |
| `(mask) ? true : false` / `? 1 : 0` normalisations | `code/z_bgcheck.c:637,4036,4043,4050,4186`, `code/relocation.c:87`, `ovl_Bg_Mori_Hineri/…:80`, `ovl_Bg_Jya_1flift/…:190`, `ovl_En_Peehat/…:771` (toggle), `ovl_En_Go2/…:1303` | LEAVE or `!= 0` | load-bearing: they *make* a 0/1 from a mask; `(m & X) != 0` is the same code | IDENTICAL if rewritten to `!= 0` |
| `x == true ? 1 : 0` | `ovl_En_Horse_Link_Child/z_en_horse_link_child.c:389-419` (`animationEnded`, unknown range — see class A) | CARE | `animationEnded` | DIFF, explained |
| `!!x` | `code/z_play.c:2127`, `code/z_bgcheck.c:4136,4150,4164` (`return !!flags;`), `ovl_Bg_Jya_Bigmirror/…:140-146`, `ovl_En_Boom/z_en_boom.c:159,197` `collided = !!(collided);` | LEAVE | mask → 0/1 normalisation returned to callers; `!= 0` spelling optional | IDENTICAL either way |
| `!!(m) == 0` | `ovl_En_Ssh/z_en_ssh.c:489`, `ovl_En_St/z_en_st.c:412` `if (!!(acFlags & AC_HIT) == 0)` | DO | `if (!(acFlags & AC_HIT))` | IDENTICAL expected |
| `== 1` on a boolean | `code/code_800EC960.c:2653` `bitField0.enabled == 1`, `code/audio_effects.c:80`, `code/audio_seqplayer.c:1789` `->enabled == 1` (all `u8 … : 1`) | DO | `if (x)` | IDENTICAL expected |
| `== 1` on a boolean | `code/audio_load.c:430` `sample->isRelocated == 1` (`u32 isRelocated : 1`, `z64audio.h:145`), `ovl_Fishing/z_fishing.c:3176,3626` `isLoach == 1` (`u8`), `ovl_En_Tk/z_en_tk.c:43` `eff->active != 1` (verify type) | DO (Tk after type check) | `if (x)` | IDENTICAL for the bitfield/`u8` ones |
| `== 1` / `!= 1` on `s32` results | `ovl_En_Horse/z_en_horse.c:731` `func_8002DD78(...) == 1` (returns `a && b` → 0/1), `:2532` `isFanfarePlaying != 1`, `ovl_Demo_Effect/z_demo_effect.c:586` `isSmallSpawner != 1` | CARE | | DIFF |
| `== 1` in SoH actor | `ovl_En_Partner/z_en_partner.c:784,801,912` (SoH's Ivan actor) | LEAVE (SoH) | | |

---

## Class 3 — `//!`/`@bug`/`FAKE`/`HACK` annotations (213 census lines → 121 distinct notes; 3 `FAKE`/`HACK`
lines, 7 false hits on `FD2_FAKEOUT_COUNT`/`GND_FAKE_BOSS`/`PLAYER_DOORTYPE_FAKE` identifiers)

**The headline: OoT's annotations are almost entirely C1.** They describe shipped behaviour (unbounded reads,
wrong-limb positions, never-taken branches, uninitialised temporaries) that the ROM has and the port reproduces;
nothing here is a work list for this stream.

### C2 — dead code deletable with its note (1)

- `soh/src/overlays/actors/ovl_En_Ossan/z_en_ossan.c:598-606`
  `//! @bug This check will always evaluate to false, it should be || not &&` guarding
  `if (params > OSSAN_TYPE_MASK && params < OSSAN_TYPE_KOKIRI)` with `OSSAN_TYPE_KOKIRI = 0`,
  `OSSAN_TYPE_MASK = 10` (`z_en_ossan.h:70,80`): the range `> 10 && < 0` is empty, GCC folds it to `false` and the
  block (`Actor_Kill`, two prints, an `assert` that is empty under `NDEBUG`, `return`) is already absent from the
  binary. Deleting lines 598-606 → IDENTICAL expected. (Making it `||` — the note's intent — would *change*
  behaviour: not this stream.)

### C3 — stale or moot notes (comment-only edits, 6)

- `soh/src/code/audio_heap.c:1036-1038` `//! @bug UB: missing return. "ret" is in v0 … explicit return uses an
  additional register.` — followed by an explicit `return ret;` (present since the 2022 import; upstream keeps it
  under `#ifdef AVOID_UB`). Reword: "the ROM fell off the end with `ret` in v0; the port returns explicitly".
- `soh/src/overlays/actors/ovl_En_Po_Sisters/z_en_po_sisters.c:1395` `//! @bug uninitialised spE7` — the port
  declares `u8 spE7 = 0;` (`:1351`). Delete or reword ("uninitialised in the ROM; zeroed here").
- `soh/src/code/z_kaleido_manager.c:101` `//! @bug Probably missing iter++ here` — inside an `#if 0` block
  (`:88-106`); the live function returns `vram` at `:86`. Dead text; delete with the `#if 0` block or leave.
- `soh/src/overlays/misc/ovl_kaleido_scope/z_kaleido_equipment.c:862-863` `//! @bug: This function shouldn't take
  any arguments` above a **commented-out** call. Delete both lines.
- `soh/src/overlays/actors/ovl_En_Tana/z_en_tana.c:31-33` `//! @bug A third entry is missing here …` above
  `sShelfTypes[]` which has **three** entries (`:34-38`, since the 2022 import). Reword ("the ROM table had two
  entries; a third was added so type 2 prints correctly").
- `soh/src/code/z_demo.c:531` `// HACK: Align visual timing with audio during credits sequence` — SoH's own
  enhancement (under `CVAR_ENHANCEMENT("CreditsFix")`), not decomp. Leave.

### C1 — preserve (sample of the ~110; any rewrite nearby must not "fix" these)

- **Missing `return` in `s32` functions, legal because every caller ignores the value** (C11 6.9.1p12):
  `soh/src/code/z_camera.c:2308,2327,6326,7387` (`Camera_Parallel1/3`, `Camera_Demo7`, `Camera_UpdateWater`;
  dispatched at `:7626` with the result dropped), `ovl_Demo_Gj/z_demo_gj.c:236` (`DemoGj_FindGanon`, callers
  `:614,678,726` drop it), `ovl_En_St/z_en_st.c:565` (`EnSt_DecrStunTimer`, caller `:1036`),
  `code/audio_load.c:631` (`AudioLoad_SyncInitSeqPlayerInternal`), `ovl_En_Sw/z_en_sw.c:116`
  (`s32 func_80B0BE20`, `:74`). Adding `return 0;` is behaviour-free but an explained diff (sets `eax`).
- `code/z_camera.c:7248-7256` the `sp50[i++] = i / 10` UB workaround — already the fixed, defined-C form; keep.
- `code/z_actor.c:2477` `ratio = 1.0f + ((f32)temp * 0.2); // required to match` — the double literal is the
  behaviour (pattern 13); never add `f`.
- `code/sys_math3d.c:628-636` two identical conditions setting `0x20` and `0x40`: folding to `ret |= 0x60` is
  behaviour-identical (GCC likely already merged the branch); deleting either `if` is not.
- `ovl_En_Horse/z_en_horse.c:687` `//! Same flag checked twice` — `A && (B || A)` ≡ `A`, but `Flags_GetEventChkInf`
  lives in another TU, so simplifying drops a call: explained diff, behaviour-identical (pure reader of
  `gSaveContext`).
- Never-taken branches the compiler cannot prove (`ovl_Boss_Goma/z_boss_goma.c:853` `s16 framesUntilNextAction
  < 0`, `ovl_player_actor/z_player.c:8312`, `code/z_play.c:825`, `ovl_En_Tite/z_en_tite.c:833`,
  `ovl_En_Zl3/z_en_zl3.c:1900`, `ovl_En_Ge1/z_en_ge1.c:406`, `ovl_En_Fish/…:177`, `ovl_En_Ice_Hono/…:198`,
  `ovl_En_Insect/…:114` "superfluous check"): deletion is behaviour-preserving by the decomp's argument, codegen
  differs — explained diffs at best; leave in this stream.
- Documented wrong-index / wrong-object behaviour the game's feel depends on: `code/z_effect.c:92` (blures
  initialised twice), `code/z_bgcheck.c:288`, `ovl_En_Wf/z_en_wf.c:1411` (flame at 0,0,0), `ovl_En_Bb/z_en_bb.c:1164-1303`
  (the Din's Fire crash chain), `ovl_En_Dodongo/z_en_dodongo.c:467`, `ovl_En_Peehat/z_en_peehat.c:363,480`,
  `ovl_Bg_Mizu_Bwall/…:277,315,353`, `ovl_En_Boom/z_en_boom.c:142`, `code/z_map_exp.c:1016` (see "Out of
  scope"), `boot/idle.c:81` (the port's `osViSwapBuffer` — `libultra/io/viswapbuf.c:3` — just stores the pointer;
  harmless), `code/fault.c:289` (`Fault_PadCallback` is still installed at `:1076`).
- `code/z_message_PAL.c:1954` `// FAKE? Figure out what best way to match is` — see class 4 item 7.

---

## Class 4 — whole-function reads (12 files, 63 840 lines; constructs no regex finds)

1. **Comma-operator assignment inside `if`** — `soh/src/code/z_camera.c:7294`
   `if (waterCamIdx = Camera_GetWaterBoxDataIdx(camera, &waterY), waterCamIdx == -2)`, `:7341`, `:7692` (with the
   matching note `:7690-7691` "setting bgCheckId to the ret of Quake_Calc … is required"). Rewrite: hoist the
   assignment to its own statement, drop the note. Behaviour-preserving (same sequence points). IDENTICAL expected.
   `ovl_En_Horse/z_en_horse.c:770` `if ((this->bankIndex = Object_GetIndex(...)) < 0)` is ordinary C — leave.
2. **Empty-then and constant-if matching artefacts** — `ovl_En_Zl3/z_en_zl3.c:1852` `if (play) {} // Needed to
   match`, `ovl_En_Horse/z_en_horse.c:699` `if (play->sceneNum) {}`, `ovl_player_actor/z_player.c:6324`
   `if (controlStickDirection) {}`, `code/z_message_PAL.c:2536` `if (temp_s2) {}`, `code/z_actor.c:3782` `if (1) {`
   wrapper, `code/z_camera.c:3614-3615` (already commented out — delete the two comment lines),
   `ovl_En_Zl3/z_en_zl3.c:2589-2590` `Actor* thisx = &this->actor; // unused, necessary … regalloc` (unused local).
   Delete each with its comment. A non-volatile read with no use is DCE'd. IDENTICAL expected.
3. **`((void)0, x)` comma trick** — `ovl_En_Horse/z_en_horse.c:3151` `((void)0, this->actor.world).rot.y` →
   `this->actor.world.rot.y`; delete `:3150`. IDENTICAL expected.
4. **`x = x + e` "Required to match"** — `ovl_En_Horse/z_en_horse.c:3558-3562` four `cyl.dim.pos.x = cyl.dim.pos.x +
   (s16)(…)` → `+=` (lvalue evaluated once either way; the `(s16)` cast stays — it truncates the addend, pattern 10).
   IDENTICAL expected.
5. **Parameter mutated as scratch** — `code/z_actor.c:170-171` `arg6 *= …; arg6 = (arg6 < 1.0f) ? 1.0f : arg6;`;
   `ovl_player_actor/z_player.c:8063` `arg3 = arg2`, `:8078-8082` `arg1 *= updateScale; clamp`, `:4424` `arg2 += 2`.
   Rewrite: a named local (`f32 zScale = arg6 * …`) — SSA makes it the same code. IDENTICAL expected. (Names are
   the rename task's; do it there.)
6. **`if (c) return 1; return 0;`** — `ovl_player_actor/z_player.c:8058-8073` `func_8084021C` → `return (temp *
   arg1 >= 0.0f) && ((temp - arg1) * arg1 < 0.0f);`. Behaviour-identical; IDENTICAL expected. (Also class 2 row.)
7. **Open-coded 4-wide byte copy + FAKE note** — `code/z_message_PAL.c:1954-1963` (and twins `:1755-1762`,
   `:1768-1775`): `for (j = 0; j < FONT_CHAR_TEX_SIZE; j += 4) { charTexBuf[idx+j+0..3] = fontBuf[j+0..3]; }` over
   two `u8[]` (`z64.h:636,638`) → `memcpy(&font->charTexBuf[charTexIdx], fontBuf, FONT_CHAR_TEX_SIZE)`
   (`FONT_CHAR_TEX_SIZE = 128`, `z64.h:552`). Behaviour-identical; at `-O2` GCC may already have distributed the
   loop into `memcpy`, so the gate can be IDENTICAL — if not, an explained diff. `(curChar * 32) << 2` →
   `curChar * FONT_CHAR_TEX_SIZE`: identical folding, and removes a left-shift on a possibly-signed value.
8. **Search loop with hoisted exit** — `code/z_message_PAL.c:1026-1034` (and `:1365`) `j = i; while (true) {
   character = buf[j]; if (not-a-terminator) j++; else break; }` → `for (j = i; !IS_TERMINATOR(buf[j]); j++) {}`.
   Behaviour-identical (`character` is dead after the loop? verify before dropping it). Loop rotation → CARE.
9. **Post-increment split across two statements** — `code/z_collision_check.c:1236-1237` `index = colATCount;
   colAT[colATCount++] = collider;` (and `:1314-1315`, `:1395-1396`) → `index = colChkCtx->colATCount++;
   colChkCtx->colAT[index] = collider;`. Same reads/writes, same order. IDENTICAL expected. Also `:1224,1231`
   `if (!(index < count))` → `if (index >= count)` (IDENTICAL).
10. **Mirror-image duplicated blocks**
    - `ovl_Boss_Ganon/z_boss_ganon.c:3810-3827`: two nested loops identical except `x = -3..3` vs `-1..1` →
      `xRange = torn ? 1 : 3;` one loop. Behaviour-identical; loop bound becomes a variable → DIFF, explained.
    - `ovl_En_Horse/z_en_horse.c:3209-3227`: the six-line `if (!movingFast) {REVERSING} else {REVERSING;
      StartBraking}` body appears verbatim under two guards, separated by `dynaPoly = DynaPoly_GetActor(...)`
      (a pure lookup). Fold: `if (guardA || (dynaPoly = …, guardB)) { body; return; }` or a tiny static helper.
      Behaviour-identical given the lookup is pure; DIFF, explained. The `movingFast == true`/`== false` lines
      inside are the class-A DO set.
    - `ovl_En_Horse/z_en_horse.c:2026-2050` (`EnHorse_UpdateIngoHorseAnim`) four-arm ladder differing only in
      threshold + animation id (`:2461-2482` is its twin) → `anim = pick(speed); animChanged = (animationIdx !=
      anim); animationIdx = anim;`. Behaviour-identical (each arm assigns `animationIdx` unconditionally); DIFF.
    - `ovl_En_Zl3/z_en_zl3.c:1962-1974` vs `:2258-2276` vs `:1048-1056`: three near-identical lerp bodies over
      `unk_348`/`unk_354`/`world.pos` (the middle one adds `this->unk_360` on y) → one helper. DIFF, explained.
11. **Pointer-to-field alias locals named after the field** — `ovl_En_Zl3/z_en_zl3.c:140,163-164,614-615,1039,
    1049-1051,1919-1920,1964-1966,2260-2262` (`Vec3f* unk_348 = &this->unk_348;` etc., 30 in the file) and
    `code/z_camera.c:820` `Vec3f* at = &camera->at;`. Inlining the address is pure address arithmetic → IDENTICAL
    expected; but these are `unk_` names, so do it in the rename stream. `z_en_zl3.c:2270-2273` copies
    `this->unk_344/unk_346` into locals named `unk_344/unk_346` — same remark.
12. **Slot reused for two meanings** — `code/z_parameter.c:4907,4915` `i` holds a button item id, then is
    overwritten with `ITEM_BOW` to become the ammo item; `ovl_player_actor/z_player.c:11166-11167` `float0/float1
    // multi-purpose variable … (fake match?)` with `#define`d aliases. Split into named locals: IDENTICAL expected
    for `i`; `float0/1` need the defines read first (rename task).
13. **`goto` into another `case` arm's tail** — `code/z_camera.c:3337→3340` (`goto cont;` into `case 0x10`),
    `:5528→5536` (`goto setEyeNext;` into `case 2`), `ovl_Boss_Ganon/z_boss_ganon.c:1058→1066`
    (`skip_sound_and_fx` into `case 21`). Pattern 1's unsafe case: no keyword expresses it; LEAVE (or hoist the
    tail into a helper — DIFF). `code/z_play.c:1255,1429,1455,1602` gotos are SoH's own (`Play_Draw_skip` is
    `SOH [Port]`) — leave.
14. **Yoda / arithmetic-shaped float comparisons** — `code/z_collision_check.c:3586-3591` `1.0f < frac1` (DO,
    identical); `ovl_player_actor/z_player.c:8068` `((temp - arg1) * arg1) < 0.0f` is a sign test of a product, not
    `a - b < 0` — leave; `ovl_En_Horse/z_en_horse.c:574,580` `Math_SinS(a - b) > 0.0f` — the subtraction is an
    angle difference feeding a sine, not a comparison — leave. No true `a - b < 0.0f`-for-`a < b` was found in the
    12 files.
15. **Single-condition "must match" predicates** — `code/z_actor.c:1962-1968` (`Actor_OfferTalkExchange`),
    `code/z_en_item00.c:1553-1560` (fenced `// clang-format off`). Splitting into early returns is
    behaviour-identical (all short-circuit, no side effects — `Player_InCsMode` is a reader) but reschedules;
    DIFF, explained. Delete the notes only if the shape is changed.
16. **`BAD_RETURN(s32)`** — `ovl_player_actor/z_player.c:1583-1587`; under the port `BAD_RETURN(type)` is `void`
    (`include/macros.h:20,23`), so the "regalloc" comment is moot: reword or delete the comment (comment-only).
17. **`s32 pad;` / `s32 pad[2];` stack fillers** — 153 in the 12 files (`z_camera.c` 43, `z_en_zl3.c` 29,
    `z_player.c` 24, `z_boss_ganon.c` 20, …); pattern 15's "no layout contract in a PC port" → delete; a dead local
    generates nothing → IDENTICAL expected (the filler task owns the sweep).

---

## Out of scope but found — live in the port, not decomp artefacts

1. **Uninitialised read, real UB under GCC:** `soh/src/overlays/actors/ovl_En_Ge1/z_en_ge1.c:540-556` (and the
   twin at `:505`) — `s32 getItemId;` is assigned only in `case 1:`/`case 2:` of `switch (CUR_UPG_VALUE(UPG_QUIVER))`
   (no `default`), then used. The decomp's own note (`:549-552`, "Asschest") describes the ROM's junk-stack value;
   in the port it is an indeterminate read the optimiser may fold arbitrarily.
2. **Uninitialised read:** `soh/src/overlays/actors/ovl_Shot_Sun/z_shot_sun.c:89` `s32 fairyType;` set only by the
   `switch` arms at `:90-101` (no `default`), then passed to `Actor_Spawn` at `:104-106` (`//! @bug fairyType may be
   uninitialized`). Same class as 1.
3. **Out-of-bounds read:** `soh/src/code/z_map_exp.c:1017-1019` indexes `gMapData->owEntranceFlag[sEntranceIconMapIndex]`
   (index up to 23 per the note at `:1016`) while the backing array is `static u16 sOwEntranceFlag[20]`
   (`soh/src/code/z_map_data.c:231`, wired at `:330`). The decomp note is accurate for the port too.
4. **`u8 isDead++` unguarded** at `soh/src/overlays/actors/ovl_Boss_Va/z_boss_va.c:2814` can exceed 1 on a repeat
   call; harmless today (every read is truthiness), noted so the `= true` rewrite is understood as a change of
   representation, not of behaviour.

(`z_en_toryo.c:253` "return value may be uninitialized" is *not* live: each `ret` is initialised — `:145,218,259`.)

---

## Grep commands used (run from `n64/OcarinaOfTime/Shipwright/soh`)

```
# declared types of the 136 operands (members / prototypes)
rg -n -e '^\s*/\*[^*]*\*/\s*\S+.*\b<name>\b\s*(:\s*[0-9]+)?;' -e '^\s*(u8|s8|u16|s16|u32|s32|bool)\s+\b<name>\b' include src
rg -n -e '^\w[\w ]*\*?\s+\b<fn>\b\s*\(' include src --glob '*.c' --glob '*.h'     # return type
awk '/^s32 <fn>\(/{p=1} p&&/return/{print FNR": "$0} p&&/^}/{exit}' <file>       # what it returns
rg -n -e '<field> *=[^=]' src include                                              # every writer
git blame -L N,N --porcelain -- <file>                                             # decomp vs SoH provenance
# class 2 shapes
rg -n 'case (true|false|TRUE|FALSE):' src
rg -n -e '\b(is|has|was|should|found|can|did|need|got|hit|on|stop)[A-Za-z0-9_]*(\+\+|--);' src
rg -n -e '(if|while|&&|\|\|) *\(?-?[0-9]+\.?[0-9]*f? *(<|>|<=|>=) *[a-zA-Z_(]' src --glob '*.c'
rg -n -U -e 'if \([^\n]*\) \{\n\s*return (true|false);\n\s*\}( else \{)?\n\s*return (true|false);' src
rg -n -e '\? *(true|false|1|0) *: *(true|false|1|0)\b' src ;  rg -n -e '!![a-zA-Z_(]' src
rg -n -e '\b(is|has|should|can|enabled|active)[A-Za-z0-9_]* *[!=]= *1\b' src
# class 4 shapes (12 hot files)
rg -n -e 'if \(\(?[A-Za-z_][A-Za-z0-9_.>-]*(\[[^]]*\])* = [^=]' $F ;  rg -n -i -e 'to match|fake ?match|regalloc' $F
rg -n -e '^\s*(Vec3f|Vec3s|MtxF|Gfx|Actor|SkelAnime)\*\s+\w+ = &(this|actor|player|camera|play)->' $F
rg -n -e '^\s*arg[0-9] *[-+*/]?= ' $F ;  rg -n -B2 -e '^\s{8,}(i|j|k|idx|index) = [A-Za-z_][\w>.\[\]-]*;\s*$' $F
rg -n -c -e '^\s*s32 pad[0-9]*;|^\s*s32 pad\[' $F ;  rg -n -e '\) *[<>]=? *0\.0f?\)' $F | grep -E '[A-Za-z0-9_)] - [A-Za-z0-9_(]'
# class B sample from the census log
grep -E '\b(is|has|should|can|enabled|active|found|…)[A-Za-z0-9_]* *(!=|==) *0\b' data/cmp_zero.txt | grep -v 'Timer\|Count\|Index'
grep -E '\b(Flags_Get\w+|Player_\w+|Actor_\w+|\w+_Is\w+|CHECK_\w+|func_8\w+)\([^;]*\) *(!=|==) *0\b' data/cmp_zero.txt
```

## Recommended batch order

1. **Class 2/4 trivia, all IDENTICAL-expected, one patch per file group:** `!!(m) == 0` (2), `((m)!=0) == false`
   (1), `(a == &b) == false` ×6 (`z_en_ko.c`), `? true : false` on `u8` (`z_en_fr.c:339,797`, `z_en_hy.c:863`),
   `== 1` on bitfields (3), Yoda literal-on-left in decomp files (~40, skip `libultra/rmon`), empty-then/`if (1)`
   /`((void)0, x)`/`x = x + e` matching artefacts (8 sites in class 4 items 2-4), the `z_collision_check.c`
   post-increment split (3) and `!(a < b)` (3), `if (c) return 1/0` → `return c` (15, gate each).
2. **Class A DO set** (58 lines, 25 files): bitfields, `u8` fields/statics, comparison results, literal-only
   locals. Gate every file; any DIFF demotes that site to batch 5.
3. **Class B verifiable booleans** (~40 from the sample; extend by type, never by name alone): IDENTICAL by
   construction, so the review is readability only.
4. **Class 3 comment-only edits**: the six C3 notes + `z_player.c:1583` `BAD_RETURN` note; plus the one C2 dead
   block (`z_en_ossan.c:598-606`, IDENTICAL expected).
5. **Explained-diff list (hand to the maintainer, needs the in-game check):** class A CARE (74 lines: 16 plain-int
   fields, 58 `s32` results/params), `switch (bool)` ×8, boolean `++` on `stopRotate`/`isDead`, class 4 items 8, 10,
   15. Do these last, one per patch, with the diff quoted in the message.
6. **Not this stream:** `lightDecay`, `noStop`, `onCeiling`, the `goto`-into-case sites, every C1 note, the three
   SoH-authored boolean lines, and the three out-of-scope bugs (file separately).
