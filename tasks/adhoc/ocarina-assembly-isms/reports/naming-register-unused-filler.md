# Assembly-isms survey (OoT / Ship of Harkinian) — naming / `register` / `UNUSED` / filler classes

Repo: `n64/OcarinaOfTime/Shipwright`, branch `imps-standard-c` at the pristine pin
`acdbc651d` ("Fix compat issues loading pre-9.1 saves on 9.2+ (#7132)"). Anchors are `soh/src/...:line`
as the files are now; `include/` means `soh/include/`. Reader report, 2026-09-22. Everything asserted
about "never referenced" comes from a grep or the classifier script quoted in section 7; everything
asserted about a name comes from reading the function (the slot-sample dumps are reproducible with
the same script). Sister report for shape: `tasks/adhoc/mario64-assembly-isms/reports/naming-register-unused-filler.md`.

## 0. Build facts that decide every verdict below

- Compile line for a decomp file (`build-cmake/build.ninja`, `z_camera.c.o`):
  `-O2 -DNDEBUG -std=gnu2x -fno-fast-math -ffp-contract=off -Wall -Wextra ... -Wno-unused-variable ... -w`.
  The trailing **`-w` silences every warning**, so an unused local never warns here; that is why the tree
  carries `(void)x; // suppresses set but unused warning` lines from a build that did warn. `-O2` means
  GCC drops an unreferenced local entirely — a deleted `s32 pad;` cannot change the `.s`.
- **`soh/src/libultra/io/` and `soh/src/libultra/os/` are not compiled**: `soh/CMakeLists.txt:191-193`
  filter them out of the source glob, and `grep -c "libultra/io/\|libultra/os/" build-cmake/build.ninja`
  is 0. Every `register` declaration in the tree lives there (section 1), so the asm gate cannot say
  anything about them — an IDENTICAL result on an uncompiled file is meaningless.
- SoH's own lines (`CVarGetInteger`, `GameInteractor_Should`, `#region SOH`) are interleaved in decomp
  bodies. Two of the rename sites below touch such a line (called out in §2 and §5); those are CARE.
- The census regexes (`discover.sh`) over-count one class and miss another: `filler_fields` counts every
  `this->unk_XX` member *access* (12 883 of its 11 789 distinct lines are that family) and only counts a
  `pad` when it is an array (`pad*[`), so the 1 167 bare `s32 pad;` locals — the actual patch surface — are
  not in `filler_fields.txt` at all. The corrected worklist is saved as
  `data/filler_function_local_unreferenced.txt` (1 717 lines, format `path:line:decl [function]`).

## 1. `register` — 56 census hits → 48 declarations, 0 compiled

| class | census → real | verdict | sites | rewrite | why behaviour-preserving |
|---|---|---|---|---|---|
| `register` | 56 → 48 declarations (8 are comments) | **LEAVE** (unprovable), or argue-by-hand | `libultra/io/*.c` 27, `libultra/os/*.c` 21 — files listed below; `code/` 0, `overlays/` 0, `boot/` 0 | delete the keyword | GCC ignores `register` for allocation; its only semantics is forbidding `&x`, and no declared name has its address taken — but the files are not in the build, so the gate is silent |

Declarations per file (all `register` lines are top-of-function locals, no comment/string hits among them):
`io/cartrominit.c:6-12` (7), `io/driverominit.c:6-8` (3), `io/viswapcontext.c:4,5,11` (3), `io/visetxscale.c:4-5` (2),
`io/epiread.c:4`, `io/epiwrite.c:4`, `io/pirawdma.c:4`, `io/si.c:4`, `io/sp.c:4`, `io/spsetpc.c:4`, `io/viblack.c:5`,
`io/vigetcurrframebuf.c:4`, `io/visetevent.c:6`, `io/visetmode.c:4`, `io/visetspecial.c:4`, `io/visetyscale.c:4` (1 each);
`os/destroythread.c:4-6` (3), `os/dequeuethread.c:4-5` (2), `os/sendmesg.c:4-5` (2), `os/stopthread.c:4-5` (2), and one each in
`os/createthread.c:10`, `gettime.c:7`, `jammesg.c:4`, `recvmesg.c:4`, `resetglobalintmask.c:4`, `seteventmesg.c:9`,
`setglobalintmask.c:4`, `sethwintrroutine.c:5`, `setthreadpri.c:4`, `startthread.c:4`, `stoptimer.c:4`, `yieldthread.c:4`.
Names: `prevInt` ×24, `status` ×5, `a`/`ret`/`s2` ×2, the rest once.

Comment-only hits (not declarations): `code/audio_heap.c:1037`, `code/z_collision_check.c:1225,1303,1383`, `code/z_debug.c:222`,
`libultra/io/vimgr.c:89`, `overlays/misc/ovl_kaleido_scope/z_kaleido_scope_PAL.c:1972,3747`.

Address-taken check: for every declared name, `grep -nE "&\s*NAME\b"` in its file. One hit,
`libultra/os/dequeuethread.c:12 a2 = &a3->next;` — that is the address of a member *through* `a3`, not `&a3`; legal
for a `register` pointer, so even here deletion is a no-op.

**Look-alikes that are NOT safe / not worth it:** nothing in the compiled tree. If the maintainer still wants the
keyword gone for C++17-cleanliness, say in the commit message that the files are uncompiled under this CMake
and that the rule was applied by hand (the mario64 doc's "uncompiled regions cannot be proven, only argued").
Recommended: skip the class for OoT.

## 2. Stack-slot / `temp_` / `phi_` / `new_var` names — 10 087 census hits → 1 988 declarations in 748 functions

Census family split (all hits, incl. uses): `sp<hex>` 7 955, `phi_*` 3 187, `temp_*` 2 069, `new_var*` 55.
Declarations (the classifier's `SLOT_DECL`, section 7): 1 988 in 748 functions; per directory
**overlays 1 446, code 532, libultra 10** (libultra's are in `gu/` which *is* compiled). `sp<hex>` never appears
as a *parameter* in OoT (regex over every definition line: 0 hits) — unlike SM64.

Hot files by declaration count: `code/z_camera.c` 173, `overlays/actors/ovl_player_actor/z_player.c` 170,
`ovl_Demo_Gt/z_demo_gt.c` 75, `code/z_eff_blure.c` 72, `ovl_Boss_Ganon2/z_boss_ganon2.c` 59, `ovl_Boss_Va/z_boss_va.c` 59,
`ovl_Boss_Mo/z_boss_mo.c` 46, `ovl_Boss_Fd/z_boss_fd.c` 42, `code/z_actor.c` 40, `ovl_Boss_Dodongo/z_boss_dodongo.c` 39,
`ovl_Boss_Ganon/z_boss_ganon.c` 38, `ovl_Fishing/z_fishing.c` 38, `ovl_En_Sw/z_en_sw.c` 35, `ovl_En_Zl3/z_en_zl3.c` 35.
`temp_`/`phi_`/`new_var` declarations: 721 total; hottest `code/z_camera.c` 53, `z_boss_ganon2.c` 39, `z_en_zl3.c` 27,
`z_demo_gt.c` 19, `code/code_800EC960.c` 16, `z_en_zf.c` 16.

### 2a. The 48 sampled functions (20 in `code/`, 28 in `overlays/`) — verdict per function

"mechanical" = every slot in the function is an ordinary well-scoped variable whose role is fixed by its uses;
the proposed names are examples, not a spec. Line = declaration line.

| function | slots | verdict | names I would use / what must stay |
|---|---|---|---|
| `code/z_eff_blure.c:611 EffectBlure_DrawElemHermiteInterpolation` | 33 | mechanical | `sp1EC/sp1E4` → `p1Cur/p2Cur` (Vec3s), `sp1CC/sp1C0` → `p1CurF/p2CurF`, `sp18C/sp180` → `p1Next/p2Next`, `sp1B4/sp1A8/sp174/sp168` → `tangent1Start…` (Hermite tangents), `sp1A4/sp1A0/sp19C/sp198` → `color1Cur/color2Cur/color1Next/color2Next`, `sp158/sp14C` → `p1Offset/p2Offset`, `spE0` → `interp`; `temp_f28..f26` already carry `// t`, `// t^2` comments → `t, t2, t3, h11, h10, h00, h01` |
| `code/z_camera.c:3221 Camera_KeepOn1` | 23 | mechanical, slow | `spD8` → `eyeNextAtDir`? no: `spC0` = at→eye, `spB8` = at→eyeNext, `spD8` = adjusted sph, `spC8` = player→target sph, `spD0` = at→target sph, `sp8C` → `eyeColChk`, `sp88` → `skipCollision`, `sp80` → `useAltAtOffset`, `spE2` (8 assigns, one meaning: yaw diff) → `yawDiff`, `spE8` (6 assigns) → `swingRate`. Every assignment keeps one meaning; needs a full read |
| `code/z_eff_spark.c:134 EffectSpark_Draw` | 20 | mechanical | 16 `u8 sp1D3..sp1C4` are `colorN.r/g/b/a` lerps → `r0,g0,b0,a0 … a3` (or four `Color_RGBA8`), `sp12C/spEC/spAC/sp6C` → `mtx/translate/scale/billboard` |
| `code/z_player_lib.c:1160 func_8008F87C` | 16 | mechanical | leg IK: `spA4/sp98` → `footPos/thighPos`? (thigh-limb vs foot), `sp84` → `floorBgId`, `sp80` → `floorY`, `sp7C/sp78/sp74` → `shinLenSq/thighLenSq/footHeight` (from `D_80126058..68[linkAge]` tables), `sp70/sp6C/sp68` → `dx/dy/dz`, `sp64` → `legLen`, `sp60/sp58/sp5C/sp54/sp50` → IK intermediates (`cosAngle`, `sinAngle`, …) |
| `code/db_camera.c:491 DbCamera_Update` | 14 | CARE | `new_var2` has **two meanings** (`:613` speed factor, `:913` eye–at distance); `sp110`/`sp111` are a 2-char text buffer (`sp110 = 'X'` then `&sp110` passed as string — a `char[2]` spelled as two locals: keep the layout, name `axisLabel[2]`); `spFC` (87 refs) → `eyeSph`, `sp104` → `atEyeSph` |
| `code/z_camera.c:2875 Camera_Battle1` | 12 | mechanical | `temp_f0_2` (`:2884`) is declared and never referenced → delete; `spFC/spF8/temp_f2_2/temp_f12_2/temp_f14` are the same swing-angle polynomial as KeepOn1 `:3404-3409` → name identically in both |
| `code/z_vr_box.c:155 func_800ADBB0` | 11 | CARE | `sp358/sp2A4/sp1F0/sp13C/sp88` → `vtxX/vtxY/vtxZ/vtxS/vtxT[45]`; `phi_a2_4/phi_t2_4/phi_a0_4/phi_t1/phi_ra` are **loop-carried across nested `for`s** (`:232,252-253`): `phi_a2_4` is initialised in the outer loop and stepped in the inner `for`-header — rename only, never restructure; also uses the real locals `pad42C/pad428` (see §4) |
| `code/code_800F9280.c:453 func_800FA3DC` | 11 | mechanical | `temp_a1` → `tempoCmd`, `temp_lo` → `tempoStep` (tempo/0x30), `phi_a2` (7 assigns, one meaning) → `tempo`, `temp_v0_4` → `tempoOp`, `temp_a0/temp_s1/temp_s0_3/temp_a3_3` → `setupOp/setupPlayerIdx/setupVal1/setupVal2` (nibbles of `setupCmd[j]`), `phi_f0` → `volScale`, `phi_t0` → `tempoTarget` |
| `code/z_camera.c:3650 Camera_KeepOn4` | 10 | mechanical | `spB0` (`:3662`) is written once by `OLib_Vec3fDiffToVecSphGeo(&spB0, …)` and never read → delete both lines (side-effect-free); `spB8` → `eyeAdjustment`, `spA8` → `atEyeNextDir`, `spA2/spA0` → `pitchTarget/yawTarget`, `sp9C` → `numTargets`, `spCC` → `targets[]` |
| `code/z_camera.c:1977 Camera_Normal3` | 10 | mechanical | `temp_f6` (`:1995`) declared, never referenced → delete; `sp98/sp94` → `yawUpdRate/pitchUpdRate`, `sp90` → `distTarget` then `=1.0f`?? — `:2096` reuses it as a scale: **two meanings**, split; `sp8C` is an out-param written by `func_80046E20` and never read — keep (callee writes through it) |
| `code/z_camera.c:644 Camera_CalcUpFromPitchYawRoll` (+ its byte-twin `db_camera.c:42`) | 10 | CARE | `sp54` = `SQ(cosPitchSinYaw)` at `:679` then `SQ(sinPitch)` at `:689`; `temp_f4_2` likewise reused (`:682`, `:690`): **two meanings each** — introduce two names; do both files in one patch (identical bodies) |
| `code/z_onepointdemo.c:100 OnePointCutscene_SetInfo` | 9 | mechanical, 1 054 lines | `spD0` → `sph`, `spC0/spB4` → `at/eye`, `spA0/sp8C` → `actorFocus/playerFocus`, `sp82/sp80/sp7E/sp7C` → `playerScreenX/actorScreenX/playerScreenY/actorScreenY` |
| `code/z_eff_blure.c:7 EffectBlure_AddVertex` | 9 | mechanical | `sp16C/sp160/sp154` → `prevMid/mid/axis`, `sp110/spD0/sp90/sp50` → `translate/rotate/tmpMtx/mtx`, `sp44/sp38` → `p2Rot/p1Rot` |
| `code/z_camera.c:4452 Camera_Subj4` | 9 | mechanical | `spAA` → `camDataIdx`?? (out of `Camera_GetCamBgDataUnderPlayer`) → `crawlspaceLen`, `sp98` → `crawlspaceEnd`, `sp88` → `dist`, `temp_f16` → `cosPitch`?? (`Math_CosS(anim->unk_2C)`) → `sway`, `sp64/sp5C/sp6C/sp8C` → `atSph/eyeAtSph/playerPosRot/atTarget` |
| `code/z_actor.c:4892 func_800359B8` | 9 | mechanical | `sp44/sp40/sp3C` → `nx/ny/nz` (floor normal), `sp38/sp34` → `sinYaw/cosYaw`, `sp30/sp2C` → `cosYawRot/sinYawRot` (yaw − 16375), `sp28/sp24` → `tanX/tanZ` |
| `code/z_camera.c:2678 Camera_Jump3` | 8 | mechanical | `temp_f18`, `temp_f2_2` (`:2706,2708`) never referenced → delete; `spB0` + its `(void)spB0` (`:2691,2774,2775`) → delete all three; `phi_f0/phi_f2` → `playerHeightAboveGround/headAboveWater` |
| `code/z_camera.c:6574 Camera_Special5` | 8 | mechanical | `sp64` (`:6584`) written by `OLib_Vec3fDiffToVecSphGeo`, never read → delete both lines; `temp_f0_2 = Rand_ZeroOne()` **is read** (`:6641`) — keep, name `rand` |
| `code/code_800EC960.c:4390 func_800F4010` | 3 | mechanical | `sp24 = func_800F3F84(arg2)` **is read** at `:4415` → `freqScale`; `phi_f0/phi_v0` → `threshold/randomOn` |
| `code/z_camera.c:1013 Camera_CalcAtForParallel` | 5 | mechanical | `temp_f2` → `tanFovDist`?? (`FTanF(fov*0.4)*dist`) → `maxYOffset`, `phi_f16` → `distXZ` then `1 - sinf(…)` at `:1060` — **two meanings**, split; `phi_f20` → `yOffsetDiff`, `sp54` → `atEyeDistXZ`, `temp_f0_4` → `playerHeight` |
| `code/code_800E4FE0.c:814 func_800E66C0` | 1 | mechanical | `phi_v1` → `count` (returned) |
| `code/z_room.c:…`, `code/z_bgcheck.c:…` | — | not sampled (0 slot decls in the named functions) | — |
| `ovl_Boss_Fd/z_boss_fd.c:273 BossFd_Fly` | 21 | mechanical | `sp1CF` → `skipSegmentUpdate`?? (u8 flag) → `isSubmerged`… name from the three `= true` sites; `temp_rand/temp_rand2` → `holeIdx/segIdx`; `sp188/sp17C/sp170/sp164/sp158` → `firePos/fireVel/dustVel/fireAccel/dustAccel`; `sp150 = 1` + `if (sp150) { // Needed for matching` at `:789` is a class-3 matching artefact, not a naming one; `phi_f20` → `armRotTarget` |
| `ovl_Boss_Va/z_boss_va.c:1952 BossVa_ZapperAttack` | 20 | mechanical | `sp7C` → `targetPos`, `sp98/sp96/sp94` → `yawToTarget/pitchSum/yawDiff`, `sp8E/sp90` → `yawTolerance/burstThreshold`, `sp6E/sp6C/sp58/sp56/sp5A/sp54/sp50` → boomerang tracking (`targetYaw/curYaw/targetPitch/curPitch/yawStep/pitchStep/stepScale`), `sp68/sp64/sp60/sp5C/sp74` → velocity components / `stepFrames` |
| `ovl_Boss_Ganon2/z_boss_ganon2.c:2266 func_809034E4` | 18 | mechanical | Bezier-ish sword trail: `sp2D0` → `pos`, `temp_f20/temp_f2/temp_f22` (Vec3f) → `seg0/seg1/seg2`, `sp2CA/sp2C8` → `yaw/pitch`, `temp_s1/temp_a1` → `yawTarget/pitchTarget`, `temp_s4/temp_s4_2` → `count1/count2`, `sp18C/sp9C` → `points1[20]/points2[20]`, `phi_s2` (6 assigns, one meaning) → `segIdx`, `phi_f30/sp294` → `segHalfLen/nextHalfLen` |
| `ovl_Fishing/z_fishing.c:2130 Fishing_UpdateLure` | 15 | mechanical | `spE4/spE0` → `waterSurfaceY/prevLureY`, `spD8/spD4/spD0` → `dx/dy/dz`, `spA8/sp9C/sp90/sp64` → `splashPos/splashVel/lineOffset/lineDelta`, `sp80/sp58` → `savedPos` (×2, same idiom), `sp7C/sp78` → `splashSpeed/splashAngle`, `phi_f0` → `surfaceMargin`, `spDC` → `rotStep` |
| `ovl_Boss_Mo/z_boss_mo.c:1877 BossMo_Core` | 13 | mechanical | `spDC/spD8/spD4` → `dx/dy/dz`, `spD0/spCC` → `pitchTarget/yawTarget` (**note** they are `f32` holding an `(s16)` cast — keep the type), `sp88` → `tentWidth`, `sp80/sp7C` → `offsetX/offsetZ`, `sp70/sp64` → `localOffset/worldOffset`, `sp60/sp5C/sp58` → `speed/angle/spread` |
| `ovl_Boss_Dodongo/z_boss_dodongo.c:996 BossDodongo_Update` | 13 | mechanical | `temp_f0` → `floorDist`?? (`func_808C4F6C` result) → `lavaHeight`, `phi_s0_3/sp90` → `dmgEffect/dmgAmount`?? — a 6-way ladder, one meaning each; `sp84/temp_f12/temp_f10` → `firePos/radius/angle`; `new_var` declared **twice** in sibling blocks (`:1209`, `:1238`) with different masks → `lavaTexIdx`, `lavaTexIdx2` |
| `ovl_kaleido_scope/z_kaleido_collect.c:10 KaleidoScope_DrawQuestStatus` | 12 | CARE | `sp21A` is a vertex index **carried from the loop at `:318` into the loops at `:372` and later without reset** — rename (`vtxIdx`) but never re-initialise; `sp218` → `i`, `phi_s3/phi_s0/sp216/phi_s0_2` are cursor-walk state (9–12 assigns each, one meaning each, but `phi_s0_2` doubles as an `osSyncPrintf` value) |
| `ovl_En_Jsjutan/z_en_jsjutan.c:85 func_80A89A6C` | 12 | mechanical | already commented in-file: `spD4/spC8/spBC` `// diffToTracked X/Y/Z`, `spB8/spB4/spB0` `// diffToPlayer X/Y/Z`, `spA8` `// wave amplitude` — the names are on the line; `spE0[3]` → `trackedActive[3]` |
| `ovl_Boss_Tw/z_boss_tw.c:4547 BossTw_UpdateEffects` | 12 | CARE | `phi_f0` = floor Y at `:4717` and a scale (`= 1.0f`) at `:4785` — **two meanings**; rest mechanical (`sp11C` → `spinOffset`, `spF4/spE8/spDC` → `pos/vel/accel`, `spC0/spB4/spA8` same, `spA6` → `bodyPart`, `sp113` → `groundBlastFound`) |
| `ovl_En_Sda/z_en_sda.c:238 func_80AF95C4` (and `:139 func_80AF8F60`, same shape) | 11 | mechanical | shadow texture painter: `temp_t0/temp_t1` → `texX/texRowOffset`, `temp_v0/temp_v1` → `x/rowOffset`, `phi_a0/phi_a3` → `dx/dy` loop vars, `sp194/sp188/sp178/sp16C/sp64` → `relPos/limbPos/shieldRot/shieldPos/bodyPos[22]` |
| `ovl_player_actor/z_player.c:7503 func_8083EC18` | 9 | CARE | `sp80/sp7C/phi_f12/phi_f14/phi_f20` are the min/max-over-vertices sweep (4–5 assigns, one meaning each: `wallX/wallZ/maxX/maxZ/minY`), `sp8C` → `climbType`?? (2 or 0) → `isClimbable`; `sp50[3]/sp44` → `wallVerts/vert` |
| `ovl_En_Zf/z_en_zf.c:1474 EnZf_HopAway` | 9 | CARE | `phi_f20_2`/`phi_f0` are stepped in a `for`-header (`:1533`) after being seeded in the body (`:1528-1531`) — loop-carried, rename only; `temp_v1_2` → `floorCheckBits`, `sp5A` → `yawToPlatform`, `sp54` → `prevHopAnim` |
| `ovl_En_Sw/z_en_sw.c:138 func_80B0C0CC` | 9 | mechanical | `sp84/sp78` → `posAbove/posBelow`, `sp9C/sp90` → `hitPos/hitPos2`, `sp70/sp6C` → `bgId/bgId2`, `sp64` → `found`, `phi_s1` → `i`; `temp_v0_2/temp_s1` are `CollisionPoly*` → `poly/poly2` |
| `ovl_En_Insect/z_en_insect.c:574 EnInsect_Dropped` | 9 | mechanical | `temp_a0`, `temp_a1` (`:575,579`) declared, never referenced → delete; `sp50` → `reachedRotX`, `sp40` → `soilDistSq`, `sp3A` → `type`, `sp38` → `yawOffset`, `sp34` → `rangeScale`, `phi_f0/phi_f2` → `speedScale/targetSpeed` |
| `ovl_En_Fhg_Fire/z_en_fhg_fire.c:414 EnFhgFire_EnergyBall` | 9 | mechanical | four `pos/vel/accel` triples for `EffectSsFhgFlash_SpawnLightBall` → `spawnPos`, `vel`, `accel` per block |
| `ovl_Boss_Mo/z_boss_mo.c:446 BossMo_Tentacle` | 9 | mechanical | `sp1B4` → `tentRotX`, `sp138/sp12C` → `camOffset/camEye`, `sp120` → `meltPos`, `spFC/spF0` → `zeroVec/playerOffset`, `spE0/spD4/spC8` → `dropletVel/dropletPos/dropletBase`; the block also holds 6 unreferenced `pad11C..pad108` (§4) |
| `ovl_Boss_Fd/z_boss_fd.c:1829 BossFd_DrawBody` | 9 | mechanical | `temp_float/spD4` → `scaleX/scaleY`, `sp84` → `boneScale`, `spFC/spE4/spDC/spF0` → `boneMtx/bonePos/boneRot/zeroVec`, `spB0/spA4` → `centerManeOffset/sideManeOffset` |
| `ovl_player_actor/z_player.c:13156 Player_Action_8084BF1C` | 8 | CARE | `sp84/sp80` are passed **into a SoH hook** `GameInteractor_Should(VB_CLIMB, true, &sp80, &sp84)` at `:13175` — renaming them edits a SoH line; propose `stickY/stickX` and say so in the message. `phi_f0/phi_f2` → `climbSpeed/climbDir` (the SoH `ClimbSpeed` CVar is on the same line `:13199`) |
| `ovl_player_actor/z_player.c:11775 Player_UpdateCommon` | 8 | CARE | `temp_f0` at `:12122` is `pos.y - prevPos.y`, then at `:12131` `+= head.y + 10` — one evolving value across a wrapped statement (`:12128-12130`); `phi_f12` → `cylinderBottom`; `sp70/sp6E` → `targetSpeed/targetYaw`, `phi_v0` → `yawStep`, `sp58/sp4C/sp5C` → `floorBgId/floorPos/floorPoly`, `sp48` → `conveyorSpeed` |
| `ovl_Fishing/z_fishing.c:1449 Fishing_UpdateLine` | 8 | mechanical | `spD8` → `segY`, `temp_f20` → `t`, `sp94/sp90/sp8C` → `dx/dy/dz`, `temp_f18` → `sinkStep`, `phi_f12` → `surfaceY`, `phi_f2` → `pull` |
| `ovl_Demo_Gt/z_demo_gt.c:1647 DemoGt_Draw8` (Draw1/4/5/6/7 identical shape) | 8 | mechanical | `sp6E` → `angle`, `sp68` → `angleRad`, `sp64` → `radius`, `sp62/sp60` → `yaw/axisYaw`, `sp50/sp44` → `axis/offset`, `sp40` → `oneMinusCos` |
| `ovl_Boss_Ganon/z_boss_ganon.c:3941 BossGanon_LightBall_Update` | 8 | mechanical | `spBA` (7 assigns, one meaning) → `hitState`, `spAC/spA0/sp94` → `vel/accel/pos`, `sp58/sp54/phi_f20/sp4E` → `rayLength/rayWidth/spread/numRays` |
| `ovl_Boss_Fd2/z_boss_fd2.c:1070 BossFd2_UpdateMane` | 8 | mechanical | `sp138/sp110/spE8[10]` → `yOffsets/yLimits/scales`, `temp_vec` → `diff`, `phi_f0` → `segY`, `temp_f2` → `maxY`, `spBC/spB0` → `segOffset/segDelta` |
| `ovl_Arms_Hook/z_arms_hook.c:144 ArmsHook_Shoot` | 7 | mechanical | `phi_f16` → `pullSpeed`, `sp94/sp90` → `grabbedDist/grabbedDistDiffLen`, `sp78/sp60` → `hitPos/lineStart`, `sp5C/sp58` → `nx/nz` |
| `ovl_Effect_Ss_Kakera/z_eff_ss_kakera.c:146 func_809A9C10` | 7 | mechanical | `temp_f18/temp_f20/temp_f14` → `linDrag/quadDrag/randRange` (from `rReg5/6/9`), `temp_f2/temp_f16/temp_f12` → `velX/velY/velZ` (after random), `temp_f0` → `drag` |
| `ovl_En_Zf/z_en_zf.c:777 EnZf_ApproachPlayer` | 7 | mechanical | `sp54/sp50/sp30` → `curFrame/prevFrame/playSpeed`, `temp_v1` → `wallYawDiff`, `sp48` → `playerPlatform`, `sp44/sp40` → `platformRange/extraRange` |
| `ovl_En_Zl3/z_en_zl3.c:541 func_80B54360` | 6 | CARE | `temp_t3` = `unk_25C[arg2]` at `:546`, then an angle difference at `:551` — **two meanings**; `phi_v0` → `vel`, `phi_t5` (7 assigns, one meaning) → `neighborVel`, `temp_v1/temp_t0/temp_t2` → `diff/diff16/diffCopy` |
| `ovl_En_Zl2/z_en_zl2.c:233 func_80B4EE38` | 3 | mechanical | `phi_v0` → `index` (walks `unk_1AC[]` chain), `temp_v1` → `target`, `phi_a3` → `angleDiff` |

Tally over the 48: **37 mechanical, 11 CARE, 0 must-stay-as-is**. Of the ~330 sampled declarations, the ones that
cannot be given one name are the eight two-meaning slots (`new_var2`, `sp90`, `sp54`, `temp_f4_2`, `phi_f16`,
`phi_f0`×2, `temp_t3`) — they need a *second* variable, not a name — plus five loop-carried `phi_` groups that
are renamable but not restructurable. Nine declarations are dead (never referenced): `temp_f0_2`, `temp_f6`,
`temp_f18`, `temp_f2_2`, `temp_a0`, `temp_a1`, and the write-only `spB0`(×2), `sp64` — same class as §4.

Per-directory estimate of the mechanical fraction: **`code/` ~85 %** (camera code carries the two-meaning slots
and the 200-line functions; effects/actor/audio files are near 100 %); **`overlays/` ~80 %** (boss/cutscene
files are pure Vec3f/angle temporaries; `z_player.c` and `z_kaleido_*` carry the SoH-hook and loop-carried
cases). Note `ovl_En_Jsjutan` and `z_eff_blure.c` already carry the names as trailing comments — those are
free.

### 2b. Look-alikes that are NOT safe (class 2)

- **Two-meaning slots** (list above): a rename that picks the first meaning is a *wrong name*, and the
  compiler cannot tell. Fix is two variables; gate result stays IDENTICAL only if both stay in registers the
  same way — read the diff.
- **Loop-carried `phi_`** (`z_vr_box.c:232-258`, `z_kaleido_collect.c:318/372`, `z_en_zf.c:1528-1533`,
  `z_boss_ganon2.c` `temp_s4`): the value is read after the loop that stepped it. Renaming is fine; a helper
  that "moves the declaration into the `for`" is a behaviour change.
- **Locals whose address goes into a SoH hook**: `z_player.c:13175 GameInteractor_Should(VB_CLIMB, true, &sp80,
  &sp84)`. Rename forces an edit of a SoH line; either accept and say so, or skip the function.
- **Shadowing**: `-w` hides `-Wshadow`, so renaming `sp24` to a name already used at file scope (`sZeroVec`,
  `sLurePos` in `z_fishing.c`) compiles silently and changes which object is read. Compile the touched file once
  with `-Wshadow -Werror` in addition to the gate.
- **`sp110`/`sp111` in `DbCamera_Update:502-503`**: two adjacent `char` locals used as one 2-byte string
  (`&sp110` passed to `func_8006376C`). Do not "clean up" into a `char[2]` — that is a layout change the gate
  will show; if you must, keep it as a rename only.
- **`f32` holding a cast `s16`** (`BossMo_Core:2179-2180`): the `(s16)` inside the assignment is the point; a name
  like `pitch` is right, changing the type is not.
- The `if (sp150) { // Needed for matching` at `z_boss_fd.c:789` belongs to the matching-comment class; renaming
  `sp150` does not license deleting the `if`.

## 3. `argN` parameters — 1 767 census hits → 172 definitions in `code/`, 240 in `overlays/`

Census per directory (all hits, incl. uses): overlays 1 005, code 744, libultra 17, boot 1. Definition lines
with an `argN` parameter: `code/` 172 (157 single-line + 15 wrapped signatures), `overlays/` 240. Headers: 145
`argN` lines in `.h`, of which 6 are **struct fields** `include/z64audio.h:706-708, 733-735` (`u8 arg0/arg1/arg2`
in the two endianness arms of the audio command union — wire format, never rename; same rule as SM64's
`audio/internal.h:829-837`), 1 is a comment (`ovl_En_Fish/z_en_fish.h:23`), and ~138 are prototypes in
`include/functions.h`. Hot files: `z_player.c` 55 definitions, `code/z_actor.c` ~45, `z_en_zl3.c` 24, `z_en_zl2.c` 17,
`code/code_800EC960.c` ~40, `code/audio_synthesis.c` 17, `code/z_camera.c` 13, `z_en_ru1.c` 10.

Verdict for the class: **DO for the ~110 `code/` functions marked with a name below, CARE for the rest**; the
rename is compiler-checked (a missed use is a compile error) and codegen-identical. Every function with a
`functions.h` prototype must have the prototype edited in the same patch — `grep -n "\bNAME\s*(" include/*.h`.

### 3a. `code/` — every definition (h = has a prototype in `include/functions.h` with the same `argN` name; "—" = none)

| site | params | proposal / reason to leave | h |
|---|---|---|---|
| `fault.c:1088 Fault_HangupFaultClient` | `arg0, arg1` (const char*) | `msg1, msg2` (printed as two lines under `#if 0`) | h |
| `fault.c:1099 Fault_AddHungupAndCrashImpl` | same | `msg1, msg2` | h |
| `irqmgr.c:166 IrqMgr_ThreadEntry` / `audioMgr.c:53 AudioMgr_ThreadEntry` / `graph.c:509 Graph_ThreadEntry` | `void* arg0` | `arg` (cast to `this`/`audioMgr` on the next line; unused in Graph). `osCreateThread` fixes the *type*, not the name | h |
| `z_effect.c:99 Effect_Add` | `u8 arg3, u8 arg4` | leave: stored into `status->unk_02/unk_01` (unnamed fields; callers pass `0, 1`) | h |
| `z_kanji.c:102 Kanji_OffsetFromShiftJIS` | `u32 arg0` | `sjisCode` | h |
| `z_skelanime.c:975 AnimationContext_SetMoveActor` | `f32 arg3` | leave: stored to `data.move.unk_08`; all callers pass `1.0f` | h |
| `audio_heap.c:13 func_800DDE20` | `f32 arg0` | leave: `256 * updatesPerFrameScaled / arg0`, called with `0.25..0.75` — unit unknown | — |
| `audio_load.c:129 AudioLoad_DmaSampleData` | `s32 arg2` | leave/CARE: non-zero selects the second DMA reuse queue (`:140,165,169`) — a list-selector flag, name would be a guess | h |
| `audio_load.c:228 AudioLoad_InitSampleDmaBuffers` | `s32 arg0` | unreferenced in the body → `unused`, or leave | h |
| `audio_load.c:413 AudioLoad_SyncLoadSeqParts` | `s32 arg1` | `loadFlags` (bit 2 = fonts, bit 1 = sequence) | h |
| `audio_load.c:481/485/489 AudioLoad_AsyncLoadSeq/SampleBank/Font` | `s32 arg1` | unreferenced (forwards `0`) → leave | h |
| `audio_load.c:552/579 AudioLoad_SyncInitSeqPlayer(Internal)` | `s32 arg2` | leave: forwarded, callers pass `0` | h (552) |
| `audio_load.c:1629/1877 AudioLoad_DmaSlowCopyUnkMedium / AsyncDmaUnkMedium` | `arg3` | empty bodies → leave | — |
| `audio_seqplayer.c:33 AudioSeq_GetScriptControlFlowArgument` | `u8 arg1` | `cmd` (indexes `D_80130520[cmd - 0xB0]`) | — |
| `audio_seqplayer.c:929 AudioSeq_SetChannelPriorities` | `u8 arg1` | `priorities` (low nibble → `notePriority`, high → `someOtherPriority`; note `arg1 = arg1 >> 4` reassigns it) | — |
| `audio_seqplayer.c:1781 AudioSeq_ProcessSequences` | `s32 arg0` | `updateIndex` (`updatesPerFrame - arg0 - 1`; caller passes `i - 1`) | h |
| `audio_synthesis.c:114 func_800DB03C` | `s32 arg0` | `updateIndex` (`numNotes * arg0`; caller `updatesPerFrame - i`) | — |
| `audio_synthesis.c:228 func_800DB4E4`, `:272 func_800DB828`, `:502 func_800DC164` | `s32 arg1, s16 arg3` | `arg3` → `bufIndex` (the siblings at `:452/:466/:494` already say `bufIndex` for the same `items[curFrame][…]` index); `arg1` is a sample count used only in `:272` (`(unk_18 << 0xF) / arg1`) → leave | — |
| `audio_synthesis.c:307 AudioSynth_MaybeMixRingBuffer1` | `s32 arg2` | `bufIndex` (forwarded to `LoadRingBuffer1AtTemp`) | — |
| `audio_synthesis.c:322 AudioSynth_ClearBuffer` | `arg1, arg2` | `dmem, size` (`aClearBuffer(cmd, dmem, count)`) | — |
| `audio_synthesis.c:335 AudioSynth_Mix` / `:379 EnvSetup1` / `:415 UnkCmd19` / `:431 UnkCmd3` | `arg1..arg4` | CARE: pure macro forwarders (`aMix(cmd, arg1, arg2, arg3, arg4)`); name only from the RSP ABI macro parameter list in `include/ultra64/abi.h` — verify order there before renaming; UnkCmd* leave | — |
| `audio_synthesis.c:386 AudioSynth_LoadBuffer` | `s32 arg1, s32 arg2, uintptr_t arg3` | `dmem, size, addr` (`aLoadBuffer(cmd, arg3, arg1, arg2)` = addr, dmem, count) | — |
| `audio_synthesis.c:390 AudioSynth_SaveBuffer` | same | `dmem, size, addr` (`aSaveBuffer(cmd, arg1, arg3, arg2)`) | — |
| `audio_synthesis.c:452/466/494 AudioSynth_LoadRingBuffer1/2, MaybeLoadRingBuffer2` | `s32 arg1` | unreferenced / forwarded → leave | — |
| `code_8006C510.c:3 func_8006C510` | `f32 arg0..arg5` | cubic Hermite: `t, tangentScale, p0, p1, m0, m1` (`(2t³−3t²+1)p0 + (3t²−2t³)p1 + (t³−2t²+t)m0·s + (t³−t²)m1·s`) | — |
| `code_800D2E30.c:4/112/118 func_800D2E30/3140/3178` | `UnkRumbleStruct* arg0` | `rumble` | h ×3 |
| `code_800E4FE0.c:523 func_800E5E84` | `s32 arg0, u32* arg1` | `seqId, outNumFonts` (forwards to `AudioLoad_GetFontsForSequence(seqId, outNumFonts)`) | h |
| `code_800E4FE0.c:527 func_800E5EA4` | `arg0, arg1, arg2` | `fontId, outSampleBankId1, outSampleBankId2` | — |
| `code_800E4FE0.c:596 func_800E60C4` | `s32 arg1` | `ioPort` (`soundScriptIO[arg1]`) | — |
| `code_800E4FE0.c:749 func_800E64B0` / `:757 func_800E651C` | `arg0..arg2` / `arg0, arg1` | leave: packed into opaque `0xFA…`/`0xFD…` audio commands | — |
| `code_800E4FE0.c:766 func_800E6590` | `s32 arg1, s32 arg2` | `channelIdx, layerIdx` (`channels[arg1]->layers[arg2]`) | — |
| `code_800E4FE0.c:814 func_800E66C0` | `s32 arg0` | leave (not read in the first 30 lines; callers pass `temp_t7`, `2`) | — |
| `code_800EC960.c:3950/3953 func_800F3138/3140` | `UNK_TYPE` | empty → leave | — |
| `code_800EC960.c:3956 func_800F314C` | `s8 arg0` | leave (packed into cmd `0x82…`) | — |
| `code_800EC960.c:4134 func_800F37B8` | `SoundBankEntry* arg1, s8 arg2` | `entry, pan` (caller `:4250` passes `entry, pan`) | — |
| `code_800EC960.c:4181 func_800F3990` | `f32 arg0` | `posY` (caller `*entry->posY`) | — |
| `code_800EC960.c:4369 func_800F3F3C` | `u8 arg0` | `ioData` (4th arg of `Audio_SeqCmd8`) | h |
| `code_800EC960.c:4376 func_800F3F84`, `:4390 func_800F4010`, `:4420 func_800F4138`, `:4459 func_800F436C`, `:4471 func_800F4414`, `:4499 func_800F45D0` | `f32 arg0/arg2` | CARE: one value threaded through all six (compared with `6.0f`, `0.75f`, clamped to `2.0f`; drives `D_8016B7A8/B0/D8` freq/vol scales). Name once for the chain (e.g. `speedScale`) or leave the chain | h (4010,4138,436C,4414) |
| `code_800EC960.c:4483 func_800F44EC` | `s8 arg0, s8 arg1` | leave: stored to unnamed `D_801305C0/BC` | h |
| `code_800EC960.c:4489 func_800F4524` | `s8 arg2` | `reverbAdd` (6th arg of `Audio_PlaySfxGeneral`) | h |
| `code_800EC960.c:4494 func_800F4578` | `f32 arg2` | `volScale` (5th arg of `Audio_PlaySfxGeneral` via `D_8016B7E0`) | — |
| `code_800EC960.c:4553 func_800F4870` | `u8 arg0` | leave: `pan = arg0 == 0 ? 0x7F : 0` — inverted flag of unknown meaning | h |
| `code_800EC960.c:4612 func_800F4A54` | `u8 arg0` | `vol` (`sRiverSoundMainBgmVol`) | h |
| `code_800EC960.c:4657 func_800F4C58` | `u8 arg2` | leave (body not read past the bank loop; caller `(s8)(actor->sfx - 1)`) | h |
| `code_800EC960.c:4678 func_800F4E30` | `f32 arg1` | `dist` (compared `<`, caller `xzDistToPlayer`) | h |
| `code_800EC960.c:4883 Audio_SetMainBgmTempoFreqAfterFanfare` | `f32 arg0, u8 arg2` | `freqScale` (`== 1.0f`, `* 100`), `duration` (3rd arg of `Audio_SeqCmdC`, caller `0x5A`) — CARE on the second | h |
| `code_800EC960.c:4898/4912/4924 Audio_Play/StopSequenceInCutscene, Audio_IsSequencePlaying` | `u16/u8 arg0` | `seqId` (also rename the derived local `arg0b` → `seqIdLow`) | h |
| `code_800EC960.c:5075 Audio_PlaySequenceWithSeqPlayerIO` | `s8 arg3, s8 arg4` | `ioPort, ioData` (`Audio_SeqCmd7(playerIdx, port, value)`) | h |
| `code_800EC960.c:5179 Audio_UpdateMalonSinging` | `u16 arg1` | `seqId` (all three callers pass `NA_BGM_LONLON`) | h |
| `code_800EC960.c:5232 func_800F64E0` | `u8 arg0` | `isOpening` (WIN_OPEN vs WIN_CLOSE) | h |
| `code_800EC960.c:5245 Audio_ToggleMalonSinging` | `u8 arg0` | `disabled` (`sMalonSingingDisabled = arg0`) | h |
| `code_800EC960.c:5288 Audio_SetSoundOutputMode` | `s8 arg0` | `outputMode` | h |
| `code_800EC960.c:5353 Audio_PlaySfxGeneralIfNotInCutscene` | `u8 arg2, f32* arg4` | `token, volScale` (positions 3 and 5 of `Audio_PlaySfxGeneral`) | — |
| `code_800EC960.c:5364 func_800F6964` / `:5392 Audio_StopBgmAndFanfare` | `u16 arg0` | `fadeTimer` (`(arg0 * 3) / 2` into `Audio_SeqCmd1`) | h |
| `code_800EC960.c:5565 func_800F71BC` | `s32 arg0` | unreferenced (caller `oldSpec`) → `unused` or leave | h |
| `code_800F9280.c:39 Audio_StartSequence` | `u8 arg2` | leave (body not read past the resolve block) | h |
| `code_800F9280.c:88 func_800F9474` | `u16 arg1` | `fadeTimer` (callers pass `fadeTimer`; `× updatesPerFrame / 4`) | h |
| `code_800F9280.c:407 func_800FA11C` | `u32 arg0, u32 arg1` | `cmdVal, cmdMask` (`arg0 == (cmd & arg1)`) | h |
| `code_800F9280.c:423 func_800FA18C` | `u8 arg1` | `setupOp` (compared with `setupCmd[i]` bits 20-23) | h |
| `code_800FC620.c:115/123/131/148 func_800FC868/8D8/948/A18` | `arg3_800FC868 arg3` (+ `s32 arg4`) | `callback`; the typedef names are address-named (rename stream's job); `arg4` leave | — |
| `code_801067F0.c:4 func_801067F0` | `f32 arg0, f32 arg1` | `x, y` (fmod: `x - (s32)(x/y)*y`) | — |
| `sched.c:482 Sched_Init` | `UNK_TYPE arg3, arg4` | unreferenced → leave | h |
| `speed_meter.c:31 SpeedMeter_InitImpl` | `u32 arg1` | `x` (sibling is `y`; stored to `unk_18`) | h |
| `z_bg_item.c:79 func_800435D8` | `s16 arg2, arg3, arg4` | CARE (callers `0x1E, 0x32, -0x14`; body is a raycast with sign) — leave | h |
| `z_bgcheck.c:584 BgCheck_RaycastFloorStatic` / `:1681 BgCheck_RaycastFloorImpl` | `u32 arg5` / `u32 arg7` | `checkFlags` (bits `1,2,4,8,0x10` tested at `:588-603`) — check `functions.h` for the Impl prototype | ? |
| `z_camera.c:347 func_80044340` | `Vec3f* arg1, Vec3f* arg2` | `from, to` (caller `at, eye`; `*arg2` is written back) | — |
| `z_camera.c:580 func_80044ADC` | `s16 arg2` | CARE: `0`/`1` flag, use not read → leave | — |
| `z_camera.c:938 func_800458D4` | `f32 arg2, f32* arg3, s16 arg4` | `yOffset, yPosOffset, calcSlope` (`:947`, `:955`, `:951`; callers pass `interfaceFlags & 1`) | — |
| `z_camera.c:978 func_80045B08` | `s16 arg3` | `calcSlope` (same shape) — CARE, verify the `if (arg3)` | — |
| `z_camera.c:1013 Camera_CalcAtForParallel` | `VecSph* arg1, f32* arg3, s16 arg4` | `eyeAtDir, yPosOffset, calcSlope` (siblings `func_800458D4`, `Camera_CalcAtForHorse` use these) | — |
| `z_camera.c:1269 Camera_CalcDefaultPitch` | `s16 arg1, arg2, arg3` | `pitch, pitchTarget, slopePitchAdj` (callers `:1733`) | — |
| `z_camera.c:1291 Camera_CalcDefaultYaw` | `f32 arg3` | leave (not read in the sampled lines) | — |
| `z_camera.c:1321 func_80046E20` | `f32 arg3, f32* arg4` | `swingUpdateRate` (`anim->swingUpdateRate = arg3`, `:1409`), `outDistRatio` (`*arg4 = temp_f0 > minDist ? 1 : temp_f0/minDist`) | — |
| `z_camera.c:8107 Camera_AddQuake` | `s32 arg1` | unreferenced → leave/`unused` | h |
| `z_camera.c:8167/8200/8205 func_8005AC48/ACFC/AD1C` | `s16 arg1` | `flags` (set / `|=` / `&= ~` on `camera->unk_14C`) — CARE, field unnamed | h ×3 |
| `z_camera.c:8210 Camera_ChangeDoorCam` / `:8286 Camera_SetCameraData` | `f32 arg3` / `UNK_TYPE arg6` | leave | h / h |
| `z_debug.c:77 func_8006375C` | `s32 arg0, s32 arg1` | `x, y` (empty body; sibling `func_8006376C(u8 x, u8 y, …)`) | h |
| `z_eff_ss_dead.c:3/29/60/86 func_80026230/400/690/860` | `s16 arg2, s16 arg3` | `frame, duration` (`Math_CosS((0x8000 / duration) * frame)`) | h ×4 |
| `z_effect_soft_sprite_old_init.c:697 EffectSsStone1_Spawn` | `s32 arg2` | leave (`initParams.unk_C`) | h |
| `z_effect_soft_sprite_old_init.c:798 EffectSsKakera_Spawn` | `Vec3f* arg3, s16 arg5..arg8, arg10, arg11` | leave: all land in `unk_XX` init-params fields; rename with the struct | h |
| `z_effect_soft_sprite_old_init.c:941/959/984/1003/1053 EffectSsFireTail_*, EffectSsEnFire_*, (…arg14)` | various | leave, same reason (`unk_14/unk_20/unk_12/unk_34`) | h |
| `z_fcurve_data_skelanime.c:40 SkelCurve_SetAnim` | `f32 arg2` | leave (`unk_0C = arg2 - animSpeed`) | h |
| `z_horse.c:277 Horse_RotateToPoint` | `Vec3f* arg1, s16 arg2` | `point, turnAmount` (caller `:536`) | h |
| `z_kankyo.c:1422 Environment_DrawLensFlare` | `u8 arg9` | leave | ? |
| `z_kankyo.c:1744 func_80074CE8` | `u32 arg1` | `lightSettingIdx`?? (`envCtx.unk_BD`; caller `SurfaceType_GetLightSettingIndex`) — CARE | h |
| `z_kankyo.c:2441 Environment_AdjustLights` | `f32 arg1..arg4` | CARE: `arg1` clamped 0..1 (`intensity`), `arg2` a z distance (`+780`), `arg3/arg4` thresholds — read the whole body | h |
| `z_lib.c:200 func_80077D10` | `f32* arg0, s16* arg1` | `outMagnitude, outAngle` | h |
| `z_lib.c:585 Sfx_PlaySfxAtPos` | `Vec3f* arg0` | `pos` | h |
| `z_onepointdemo.c:1434 OnePointCutscene_Noop` | `s32 arg1` | unreferenced → leave | h |
| `z_play.c:2004 func_800C08AC` | `s16 arg2` | unreferenced (callers `0`) → leave | h |
| `z_play.c:2037 func_800C09D8` | `s16 arg2` | `uid` (`camera->uid != arg2`) | — |
| `z_quake.c:14 Quake_AddVec` | `Vec3f* arg1, VecSph* arg2` | `pos, sph` | h |
| `z_quake.c:273 Quake_SetUnkValues` | `s16 arg1, SubQuakeRequest14 arg2` | leave (`unk_1C`, `unk_14`; no callers) | h |
| `z_room.c:46 func_80095AA0` | `Input* arg2, UNK_TYPE arg3` | empty → leave | h |
| `z_skin.c:45/140/188/254/260 Skin_ApplyLimbModifications / DrawAnimatedLimb / DrawImpl / Draw / DrawFlags` | `s32 arg3` / `s32 arg6` | one value threaded through five functions — CARE, rename the chain together or not at all | h (DrawAnimatedLimb only) |
| `z_skin_matrix.c:581 func_800A8030` | `f32* arg1` | `quat` (x/y/z/w normalised into a rotation matrix) | — |
| `z_view.c:277 func_800AAA50` / `:642 func_800AB9EC` | `s32 arg1` | `mask` (`arg1 = (view->flags & arg1) \| (arg1 >> 4)`; callers `15`, `0x7F`, `0xF`) | h ×2 |
| `z_vr_box.c:155 func_800ADBB0` / `:267 func_800AE2C0` | `s32 arg2..arg9` / `arg2..arg8` | CARE: face-builder coordinates/steps selected by `switch (arg8)` — leave | — |
| `z_vr_box.c:444 func_800AF178` | `s32 arg1` | `numFaces` (loop bound; callers `5`, `6`) | — |
| `z_actor.c:159 ActorShadow_DrawFoot` | `MtxF* arg2, s32 arg3, f32 arg4, arg5, arg6` | CARE (alpha = `arg3*0.00005*arg4`; `arg6 *= …`) — read `ActorShadow_DrawFeet` first | — |
| `z_actor.c:295 Actor_ProjectPos` | `Vec3f* arg1, Vec3f* arg2, f32* arg3` | `pos, projectedPos, invW` (callers `:3671`) | h |
| `z_actor.c:329 Attention_SetReticlePos` | `f32 arg2, arg3, arg4` | `x, y, z` | — |
| `z_actor.c:1329 Actor_SetProjectileSpeed` | `f32 arg1` | `speed` | h |
| `z_actor.c:1504 func_8002DFA4` | `f32 arg1, s16 arg2` | `arg2` → `yaw` (caller `world.rot.y`); `arg1` → `unk_150 +=` — leave | h |
| `z_actor.c:1606 func_8002E234` | `f32 arg1, s32 arg2` | `floorHeightDiff, flags` (`< -11.0f`; `& 0x10`) | — |
| `z_actor.c:1621 func_8002E2AC` | `Vec3f* arg2, s32 arg3` | `pos, flags` (caller `:1727` passes `flags`) | — |
| `z_actor.c:1878 Actor_GetWorldPosShapeRot` | `PosRot* arg0` | `dest` (and the header twins `Actor_GetFocus/GetWorld` at `functions.h:447-448`) | h |
| `z_actor.c:1888 Attention_WeightedDistToPlayerSq` | `s16 arg2` | `playerShapeYaw` | — |
| `z_actor.c:1924 Attention_ActorIsInRange` | `f32 arg1` | `distSq` | — |
| `z_actor.c:1959/1977/1981 Actor_OfferTalkExchange / EquiCylinder / OfferTalk` | `f32 arg2, f32 arg3` / `f32 arg2` | `xzRange, yRange` / `radius`; **header says `arg4` where the definition says `exchangeItemId`** (`functions.h:452-453`) — fix both | h |
| `z_actor.c:2219-2241 Actor_SetPlayerKnockback{,Large,LargeNoDamage,Small,SmallNoDamage}` | `f32 arg2, s16 arg3, f32 arg4, u32 arg5, u32 arg6` | `speed, rot, yVelocity, type, damage` (the fields they land in are named `knockbackSpeed/Rot/YVelocity/Type/Damage`) | h ×5 |
| `z_actor.c:2310 Actor_PlaySfx_FlaggedTimer` | `s32 arg1` | `timer` (callers `this->timer`, `timeLeft`) | h |
| `z_actor.c:2955 Actor_CullingVolumeTest` | `Vec3f* arg2, f32 arg3` | `projectedPos, projectedW` (caller `:2978`); header also has `actorB` for `actor` | h |
| `z_actor.c:3675/3691 FaceChange_UpdateBlinking / UpdateRandomSet` | `s16* arg0, s16 arg1, arg2, arg3` | `faceChange` (array: `[0]` face, `[1]` timer), `blinkIntervalBase, blinkIntervalRandRange` (→ `Rand_S16Offset`), `blinkDuration` — CARE on the last | h (Blinking) |
| `z_actor.c:3845 func_80033480` | `u8 arg6` | leave (`var2 = arg6`) | ? |
| `z_actor.c:4099 func_80033AEC` | `Vec3f* arg0, Vec3f* arg1, f32 arg2..arg5` | `target, pos, scale, step, farDist, nearDist` (`SmoothStepToF(&pos, target, scale, step, 0)`; `arg4 <= dist`, `arg5 < dist`) | h |
| `z_actor.c:4115 func_80033C30` | `Vec3f* arg0, Vec3f* arg1` | CARE (shadow draw; body not read) | h |
| `z_actor.c:4148/4156/4164 Actor_RequestQuake{,WithSpeed,AndRumble}` | `s16 arg1, arg2(, arg3)` | `y, countdown(, speed)` (`Quake_SetQuakeValues(var, y, …)`, `Quake_SetCountdown`, `Quake_SetSpeed`) | h ×3 |
| `z_actor.c:4254 func_8003424C` | `Vec3f* arg1` | `pos` | h |
| `z_actor.c:4655 Actor_UpdateFidgetTables` | `s16* arg1, s16* arg2, s32 arg3` | `fidgetTableY, fidgetTableZ, tableLen` | h |
| `z_actor.c:4727 func_800354B4` | `s16 arg3, arg4, arg5` | `maxActorYawDiff, maxPlayerYawDiff, actorYaw` (callers pass `shape.rot.y` last) — CARE on order | h |
| `z_actor.c:4860 func_80035844` | `Vec3f* arg0, Vec3f* arg1, Vec3s* arg2, s32 arg3` | `from, to, rot, flipY` (`dy = arg3 ? (b−a) : (a−b)`) | h |
| `z_actor.c:4872 func_800358DC` | `f32* arg3, s32 arg8` | `arg8` → `displayList`; `arg3` is a 3-float pack (`speedXZ, rotZ, rotZSpeed`) → `partParams` — CARE | h |
| `z_actor.c:4892 func_800359B8` | `s16 arg1, Vec3s* arg2` | `yaw, rot` (callers `shape.rot.y, &shape.rot`) | h |
| `z_actor.c:5110/5855/6320/6324/6329/6333/6356 func_80035BFC/36E50/37C30/37C5C/37C94/37CB8/37D98` | `s16 arg1/arg2` (+ `s32* arg3` in D98) | one discriminant threaded through the chain (a text-table selector: `switch (arg1) { case 0: … }`) — CARE, one name for all seven; `arg3` in D98 → `talkState` (`*arg3 = 1/0`) | h (C30, D98) |
| `z_actor.c:6404 Actor_TrackNone` | `Vec3s* arg0, Vec3s* arg1` | `headRot, torsoRot` | — |
| `z_actor.c:6412 Actor_TrackPoint` | `Vec3f* arg1, Vec3s* arg2, Vec3s* arg3` | `target, headRot, torsoRot` | — |
| `z_actor.c:6436 Actor_TrackPlayerSetFocusHeight` | `Vec3s* arg2, Vec3s* arg3, f32 arg4` | `headRot, torsoRot, focusHeight` | — |
| `z_actor.c:6468 Actor_TrackPlayer` | `Vec3s* arg2, Vec3s* arg3, Vec3f arg4` | `headRot, torsoRot, focusPos` | h |

### 3b. `overlays/` — the 30 hottest definitions

| site | params | proposal | header |
|---|---|---|---|
| `z_player.c:1699 func_80832594` | `s32 arg1, s32 arg2` | CARE: `av2 += arg1 + …`; callers `(0\|1, 100)` → `baseIncrement, limit`?? read the rest | — |
| `z_player.c:3138 func_80835644` | `Actor* arg2` | `heldActor` (both callers) | — |
| `z_player.c:3710 func_80836AB8` | `s32 arg1` | `useFocusRot` (`if (arg1) yaw = focus.rot.y`) | — |
| `z_player.c:4250 func_80837530` | `s32 arg2` | CARE: `unk_858 = arg2 ? 0 : 0.5`; callers `0x200`/`0` — leave | — |
| `z_player.c:4407 func_80837948` | `s32 arg2` | `meleeWeaponAnim` (compared with `PLAYER_MWA_*`; caller `this->meleeWeaponAnimation`) | — |
| `z_player.c:4673 func_80838144` / `:4683 func_8083816C` | `s32 arg0` | `floorType` (callers `sFloorType`) | — |
| `z_player.c:4896 func_80838940` / `:4913 func_808389E8` | `f32 arg2` | `yVelocity` (`velocity.y = arg2 * sWaterSpeedFactor`) | **`functions.h`** (80838940) |
| `z_en_zl3.c:218 func_80B53974` | `u8 arg1` | leave (`unk_3C8 = arg1`) | — |
| `z_en_zl3.c:541 func_80B54360` / `z_en_zl2.c:233 func_80B4EE38` / `:271 func_80B4EF64` | `s16 arg1, s32 arg2` | `angle, index` (`unk_28C[arg2] - arg1`; `unk_20C[index]`) | — |
| `z_en_zl3.c:757 func_80B54E14` / `z_en_ru1.c:362 func_80AEB264` | `u8 arg2, s32 arg4` | CARE: `arg4 == 0` → forward play, else reversed → `playBackward`; `arg2` is the `Animation_Change` mode → `animMode` (verify against the call) | — |
| `z_en_zl3.c:872 func_80B552A8` / `z_demo_im.c:373 func_80985640` / `z_en_ru1.c:607 func_80AEBCB8` | `s32/UNK_TYPE arg1` | `animFinished` (callers pass the `_UpdateSkelAnime` result / `something`) — CARE | — |
| `z_en_zl2.c:222 func_80B4EDB8` / `z_demo_sa.c:170 func_8098E654` | `s32 arg2` (+ `u16 arg2, s32 arg3`) | `cueIdx` (`_GetNpcAction(play, arg)`); demo_sa `arg2` → `action` | — |
| `z_en_ru1.c:497 func_80AEB87C` | `f32 arg0, s32 arg1, s32 arg2` | `t, from, to` (`(to - from) * t + from`) | — |
| `z_en_sw.c:119 func_80B0C020` | `Vec3f* arg1..arg3, s32* arg4` | `posA, posB, posResult, bgId` (the `BgCheck_EntityLineTest1` parameter names) | — |
| `z_en_sw.c:138 func_80B0C0CC` | `s32 arg2` | CARE (forward decl `s32 func_80B0C0CC(EnSw*, PlayState*, s32);` in the same file must change too) | in-file |
| `z_boss_ganon2.c:112 func_808FD080` / `:137 func_808FD210` | `Vec3f* arg2` / `Vec3f* arg1` | `center` / `pos` | — |
| `z_en_elf.c:99 func_80A01C38` | `s32 arg1` | `mode` (`unk_2A8 = arg1; switch (unk_2A8)`) — CARE | — |
| `z_boss_ganon.c:167 BossGanonEff_SpawnSparkle` | `s16 arg6` | leave (effect field not read) | — |
| `z_eff_ss_kakera.c:78 func_809A9818` | `f32 arg0, f32 arg1` | `center, range` (uniform in `[center−range, center+range]`) | — |
| `z_boss_dodongo.c:175 func_808C12C4` | `u8* arg1, s16 arg2` | `tex, index` (`arg2[arg1]` — note the swapped-index idiom, leave it) | — |
| `z_en_horse.c:642 func_80A5BB90` | `Vec3f* arg2, f32* arg3` | `projectedPos, projectedW` (same wrapper as `Actor_ProjectPos`) | — |

### 3c. Look-alikes that are NOT safe (class 3)

- **`include/z64audio.h:706-708, 733-735`** — `u8 arg0/arg1/arg2` are struct fields in an endianness-ordered union
  (the audio command word). Never rename; they are the wire format.
- **Header prototypes with a different name than the definition** — `functions.h:452-453` (`arg4` vs
  `exchangeItemId`), `:490` (`actorB`), `:447-448` (`arg0` for `Actor_GetFocus/GetWorld` whose definitions I did
  not read). A rename must reconcile both or the diff reads as a lie.
- **Parameters reassigned in the body** — `AudioSeq_SetChannelPriorities:188 arg1 = arg1 >> 4`,
  `z_view.c:278/651 arg1 = (view->flags & arg1) | (arg1 >> 4)`, `func_800F4414:4479 arg2 = 2.0f`,
  `ActorShadow_DrawFoot:170 arg6 *= …`, `func_80074CE8:1747 arg1 = 0`. Fine to rename, but the name must cover
  the post-assignment meaning.
- **Chains that share one value** — `Skin_*` (5), `func_800F3F84…func_800F45D0` (6), `func_80035BFC…func_80037D98`
  (7), `Camera_CalcAtFor*`/`func_800458D4`/`func_80045B08`: rename all or none, in one patch.
- **Unused `UNK_TYPE`/`argN` parameters** (`Sched_Init`, `func_80095AA0`, `Camera_AddQuake`, `OnePointCutscene_Noop`,
  `func_800C08AC`, `AudioLoad_AsyncLoad*`): renaming to `unused` is harmless; *removing* one changes a signature
  that a pointer or a prototype may fix — leave.
- **Callback typedefs** `arg3_800FC868` etc. (`code_800FC620.c`): the *typedef* is address-named — rename stream.

## 4. Fillers / padding — 11 789 census hits → 1 717 function-local dead declarations + ~1 300 layout-fixed members

The census regex counts `pad*[` arrays (281), `unk_[0-9A-F]{2,4}` **accesses** (12 883, mostly `this->unk_XXX`),
`UNK_TYPE` (27) — and misses every bare `s32 pad;`. Re-census, both halves:

```
# (a) struct members named as fillers, headers + .c struct bodies
grep -rnE '^\s*(/\*[^*]*\*/\s*)?(char|u8|s8|u16|s16|u32|s32)\s+(unk_[0-9A-Fa-f]+|pad[A-Za-z0-9_]*|padding[A-Za-z0-9_]*|filler[A-Za-z0-9_]*)\s*(\[[^]]*\])?\s*;' --include=*.h soh/include soh/src | wc -l   # 1242 (340 arrays)
grep -rnE '^\s*(/\*[^*]*\*/\s*)?(char|u8|s8|u16|s16|u32|s32)\s+(unk_[0-9A-Fa-f]+|pad[A-Za-z0-9_]*)\s*(\[[^]]*\])?\s*;' --include=*.c soh/src/code soh/src/overlays | grep -E '/\* 0x' | wc -l   # 31 (struct bodies inside .c)
# (b) function-local pad declarations, any indent, .c only
grep -rnE '^\s+(UNUSED\s+)?(s8|u8|s16|u16|s32|u32|s64|u64|f32|char|Vec3f|Vec3s)\s+\**(pad|padding|unk_pad|filler)[A-Za-z_0-9]*(\[[^]]*\])*\s*;' --include=*.c soh/src/code soh/src/overlays soh/src/boot soh/src/libultra soh/src/buffers | wc -l   # 1762
```

The 1 762 from (b) were then classified per enclosing function by `classify.py pads` (section 7), which checks
whether the declared name occurs again inside the same function body:

| bucket | count | verdict |
|---|---|---|
| function-local, name never referenced again | **1 717** (overlays 1 476, code 238, boot 3) | **DO** — delete the line |
| function-local, flagged "referenced" | 37 | 20 are a *second* `s32 pad;` in a nested block of the same function (`game.c:183/194`, `z_lights.c:415/431`, `z_demo_6k.c:571/583`, `z_demo_gt.c:47/53, 1196/1203`, `z_en_xc.c:498/506, 678/685`, `z_fishing.c:5200/5761`, `z_player.c:11776/11906`, `z_boss_mo.c:2297/2390`) → **DO** both; **14 are real variables named `pad`** → **LEAVE** (list below); 3 in `ucode_disas.c` (`:447, :1127, :1312`) → CARE (the word `pad` also names RDP-command bitfields at `:260-316`, so grep cannot separate them; by reading, the three locals are unreferenced) |
| struct members in `.c` struct bodies | 8 (`ucode_disas.c:260-316`, RDP command bitfields) + 31 (`/* 0x.. */` offset-commented `unk_XX` in overlay/actor structs) | **LEAVE** — layout |
| struct members in headers | 1 242 lines (`include/z64.h` 58 arrays, `z64audio.h` 24, `z64save.h` 16, `z64player.h` 10, overlay `.h` ~60) | **LEAVE** |

**The 14 locals named `pad` that ARE used** (deleting any breaks the build, so the gate would catch it, but a
scripted "delete `s32 pad;`" must exclude them): `audio_seqplayer.c:1003 pad1` (`:1430-1432`, a script-read S16),
`:1011 pad2` (`:1374-1376`); `z_camera.c:1270 f32 pad` (`:1285-1286`, an interpolation factor), `:2148 f32 pad2`
(`:2235-2236`), `:3487 s32 pad` (`:3603-3606`, a triangular-number divisor), `:6027 s32 pad` (`:6205-6224`, a frame
delta); `z_vr_box.c:157 u32 pad42C`, `:158 s32 pad428` (loop accumulators, 10 refs each); `z_boss_mo.c:488 f32 padEC`
(`:1112`); `z_boss_sst.c:2811 s32 pad` (`:2859-2860`); `z_boss_va.c:3339 pad8C`, `:3342 pad78`, `:3343 pad74`
(`:3365-3370`, sin/cos); `z_en_torch2.c:253 u32 pad54` (`:594-599`, a button-diff mask). These are *misnamed
variables*, i.e. class-2 work (`pad` → `interpFactor`, `frameDelta`, `sinYaw`, `buttonDiff`…), not deletions.

Shapes of the 1 717 (top): `s32 pad;` 1 167, `s32 pad[2];` 129, `s32 pad2;` 125, `s32 pad[3];` 47, `s32 pad1;` 46,
`s16 pad;` 20, `s32 pad[4];` 17, `s32 pad3;` 14, `s32 pad1[3];` 12, `s16 pad2;` 11, `f32 pad;` 9, `u16 pad;` 7,
`char pad[4];` 3, `char pad[0x1C];` 1 (`code_8006C510.c:4`), `Vec3f pad;` 2. Hot files: `z_demo_gt.c` 48,
`code/z_camera.c` 47, `z_en_ru1.c` 33, `z_en_zl3.c` 31, `code/z_draw.c` 27, `z_en_xc.c` 27, `z_boss_mo.c` 22,
`z_player.c` 22, `z_boss_ganon.c` 21, `z_en_nb.c` 20, `z_boss_ganon2.c` 18.

Twenty read by hand (every 86th line of the worklist), all a bare declaration among other locals, none
referenced: `PreRender.c:364`, `z_camera.c:652`, `z_en_item00.c:1341`, `z_bg_bowl_wall.c:77`, `z_bg_ingate.c:40`,
`z_bg_mori_rakkatenjo.c:148`, `z_bg_vb_sima.c:36`, `z_boss_mo.c:484` (one of six `pad11C..pad108`), `z_demo_gj.c:1118`,
`z_demo_sa.c:357`, `z_en_daiku.c:482` (the function's next line is a SoH `GameInteractor_Should` — the deletion does
not touch it), `z_en_fish.c:322`, `z_en_heishi2.c:621`, `z_en_ko.c:1276`, `z_en_nwc.c:257`, `z_en_ru1.c:1025`,
`z_en_test.c:1367`, `z_en_yukabyun.c:120`, `z_fishing.c:2936`, `z_oceff_wipe2.c:68`.

Why the deletion is behaviour-preserving: an unreferenced automatic object has no observable effect; at `-O2`
GCC never allocates it, so the frame, the spills and the `.s` are unchanged (SM64 proved this class IDENTICAL
across ~250 sites). There is no stack-layout contract in a PC port and no `alloca`/inline-asm in these files.

Why the header/struct fillers must stay: `SaveManager.cpp:1343 memcpy(saveContext, &gSaveContext, sizeof(gSaveContext))`
and `soh/Enhancements/savestates.cpp:445/463` copy `SaveContext` bytewise (the `z64save.h:305-334 char unk_XX[N]`
fillers are inside the on-disk/in-savestate image); `savestates.cpp:426-447` also `memcpy`s the whole system heap,
`AudioContext`, `gActiveSeqs`, `gGameInfo`, `sEffectContext` — every actor/effect/audio struct layout is
savestate-visible via `sysHeapCopy`; `ucode_disas.c:260-316` fillers are RDP command bit positions; and `z64.h`/
overlay-`.h` `/* 0x.. */ char unk_XX[N]` members carry the decomp's offset annotations that the `unk_names` rename
stream indexes by. None of these is a patch target here.

### Look-alikes that are NOT safe (class 4)

- The 14 real `pad` variables above; `ucode_disas.c` where `pad` is also a bitfield name.
- `s32 pad;` **inside a struct body in a `.c`** (31 offset-commented lines; the classifier separates them by the
  enclosing `typedef struct`/`struct {` span).
- A filler whose *initialiser* has side effects — none found (all 1 717 are bare declarations; the 5 `Vec3f pad`
  /`char pad[...]` have no initialiser).
- Deleting a pad that is the **only** declaration line in a block leaves an empty `{ }` or a stranded blank —
  cosmetic, but keep the file's hand style.

## 5. `UNUSED` and side-effecting dead locals — 1 census hit → 0 uses; 0 side-effecting dead locals found

`UNUSED` is defined (`include/attributes.h:8 #define UNUSED __attribute__((unused))`; `include/macros.h:26` has it
commented out) but **never used in `soh/src`** — the single census hit is a commented-out struct line,
`ovl_En_Go2/z_en_go2.h:30 // /* 0x00 */ UNUSED`. What OoT uses instead:

| idiom | count | where | verdict |
|---|---|---|---|
| `s32 pad;` locals | 1 717 | §4 | DO (delete) |
| `(void)x; // suppresses set but unused warning` | 4 | `code_800FC620.c:76 (void)relocCnt`, `z_camera.c:2775 (void)spB0`, `:3977`, `:5168 (void)sceneCamRot` | DO: delete the `(void)` line *with* the assignment and declaration it protects (`z_camera.c:2691/2774/2775`; `3975-3977`; `5166-5168`) — the assigned expressions (`*eye`, `BGCAM_ROT(sceneCamData)`) are pure reads |
| locals literally named `unused`, `unusedN`, `unusedZeroVecN`, `zeroVec // unused` with a constant initialiser | ~20 | `z_kankyo.c:1647,1924-1925`, `z_effect_soft_sprite_old_init.c:656-657`, `z_boss_dodongo.c:783-784`, `z_boss_va.c:3217,3989`, `z_en_ba.c:484`, `z_en_fd.c:720-721`, `z_en_go.c:629-630`, `z_en_kz.c:405,431`, `z_en_insect.c:418`, `z_en_mb.c:1494`, `z_bg_breakwall.c:138`, `z_en_dha.c:193`, `z_en_niw.c:892`, … | DO (delete): constant aggregate initialisers, no side effects; the `static` ones (`z_en_insect.c:418`, `z_en_mb.c:1494`) are `.data` objects GCC already drops |
| `sp`-named locals with a constant initialiser and no read | ~15 | `z_en_bb.c:474-475, 1229-1232`, `z_en_attack_niw.c:382`, `z_en_bx.c:74`, `z_en_fd_fire.c:244`, `z_en_horse.c:3692-3693`, `z_en_ex_ruppy.c:271-272` (`Vec3f D_80A0B388` — a local with a data-symbol name!) | DO (delete) |
| dead `temp_`/`phi_` declarations with no initialiser | ≥6 | `z_camera.c:2884, 1995, 2706, 2708`, `z_en_insect.c:575, 579` | DO (delete) |
| write-only locals filled by a pure out-param call | 2 | `z_camera.c:3662/3809 spB0`, `:6584/6610 sp64` (`OLib_Vec3fDiffToVecSphGeo(&x, …)` is a pure computation into `x`) | DO (delete call + declaration); **not** `Camera_Normal3:1989 sp8C` — `func_80046E20` has other side effects and needs a valid pointer |
| a local initialised or assigned from a side-effecting call and never read (the SM64 `UNUSED f32 sp30 = random_float();` trap) | **0 found** | scanned by `classify.py deadinit` (declaration-with-initialiser never referenced again: 95 hits, all constant initialisers or SoH/port lines) and `classify.py deadassign` (declared, then only ever assigned from a call: 0 real hits — the 8 reported are `return x;` lines the regex mistook for declarations) | nothing to rewrite to a bare statement |

Two candidates from reading that turn out to be **read**: `func_800F4010:4397 sp24 = func_800F3F84(arg2)` is read at
`:4415`; `Camera_Special5:6639 temp_f0_2 = Rand_ZeroOne()` is read at `:6641-6642`. Keep both as they are (rename per §2).

Lines the scans flagged that are **SoH/port code — do not touch**: `z_map_mark.c:123 s32 Top_MC_Margin = CVarGetInteger(…)`,
`z_kaleido_item.c:874 s16 Bottom_HUD_Margin = CVarGetInteger(…)`, `z_parameter.c:3942-3943, 4098, 4130, 6526`,
`z_en_bom_chu.c:492 CVarGetColor24`, `z_en_mag.c:528 ResourceMgr_GetGameVersion`, `graph.c:470 uint64_t freq = GetFrequency()`
(port `RunFrame`), the five `GetItemEntry getItemEntry = (GetItemEntry)GET_ITEM_NONE;` (a cast, not a call, and SoH).

Caveat on scope: both scans see one-line declarations/assignments only; a dead value produced by a multi-line
statement or through a pointer would be missed. The §2 sample (48 functions, every slot's uses listed) found none.

## 6. Recommended batch order for these classes

1. **Function-local `pad` deletions, `code/` first (238), then `overlays/` (1 476)** — driven by
   `data/filler_function_local_unreferenced.txt`, minus the 14 real variables and the 3 `ucode_disas.c` lines;
   plus the 20 nested-scope duplicates. Expect IDENTICAL on every file. One patch per directory (or per 20 files).
2. **The `unused`/`(void)`/dead-`temp_` deletions of §5** (~45 lines, ~30 files) — same argument, same gate.
3. **`argN` → names in `code/`**, in file groups that share a `functions.h` edit: `z_actor.c` (knockback ×5, quake ×3,
   track ×4, `Actor_ProjectPos`, `Actor_CullingVolumeTest`, `Actor_OfferTalk*` incl. the header mismatch),
   `code_800EC960.c` (the seqId/fadeTimer/ioPort set), `audio_synthesis.c` (`bufIndex`, `dmem/size/addr`),
   `z_camera.c` (`CalcAtFor*`, `CalcDefaultPitch`, `func_80046E20`), `z_lib.c`/`z_quake.c`/`z_horse.c`/`z_eff_ss_dead.c`.
   Then the 30 overlay ones (only `func_80838940` has a header).
4. **Rename the 14 real `pad` variables and the in-file-commented slots** (`z_en_jsjutan.c`, `z_eff_blure.c:728-734`) —
   zero-judgement renames.
5. **Stack-slot renames, `code/` effects/actor/audio files** (`z_eff_blure.c`, `z_eff_spark.c`, `z_actor.c`,
   `z_player_lib.c`, `code_800F9280.c`) — mechanical; then the camera files with the two-meaning splits called out
   above (each split is a separate hunk with its own explanation); then overlays boss-by-boss.
6. **`register`**: skip (uncompiled), or a single argued patch if C++17-cleanliness of `libultra/` is wanted.

## 7. Exact commands and scripts used

```
# checkout / flags / what is compiled
git -C n64/OcarinaOfTime/Shipwright log --oneline -1
grep -n -A6 "z_camera.c.o: " build-cmake/build.ninja | grep -E "FLAGS|DEFINES"
grep -c "libultra/io/\|libultra/os/" build-cmake/build.ninja        # 0
grep -n "libultra" soh/CMakeLists.txt                                 # :191-193 EXCLUDE io/ libc/ os/ rmon/
# register
grep -rnE '^\s*register\s' --include=*.c --include=*.h soh/src/{code,overlays,boot,libultra,buffers} | wc -l   # 48
grep -rnE '\bregister\b' ... | grep -vE '^\S+:\s*register\s'                                                  # 8 comments
for f in $(grep -rlE '^\s*register\s' --include=*.c soh/src/...); do
  for n in $(grep -oE '^\s*register\s+[A-Za-z_0-9]+\s*\**\s*[A-Za-z_0-9]+' $f | awk '{print $NF}' | sed 's/^\**//' | sort -u); do
    grep -nE "&\s*$n\b" $f; done; done                                # only dequeuethread.c:12 a2 = &a3->next
# stack slots
grep -rhoE '\b(sp[0-9A-F]{1,3}|temp_[a-z0-9_]+|phi_[a-z0-9_]+|new_var[0-9]*)\b' ... | sed -E 's/^sp.*/sp<hex>/;s/^temp_.*/temp_*/;s/^phi_.*/phi_*/' | sort | uniq -c
grep -rnE '^[A-Za-z_][A-Za-z_0-9 \*]*\s\**[A-Za-z_0-9]+\([^)]*\b(sp[0-9A-F]{1,3})\b' --include=*.c soh/src/code soh/src/overlays | wc -l   # 0 (no sp-named params)
# argN
grep -rnE '^[A-Za-z_][A-Za-z_0-9]*(\s+\**|\*+\s*|\s+)[A-Za-z_][A-Za-z_0-9]*\([^;]*\barg[0-9]\b[^;]*\)\s*\{?\s*$' --include=*.c soh/src/code       # 157 single-line definitions
grep -rnE -A2 '^[A-Za-z_][A-Za-z_0-9 \*]*[ \*][A-Za-z_][A-Za-z_0-9]*\([^;{)]*$' --include=*.c soh/src/code | grep -E '\barg[0-9]+\b'   # wrapped signatures
grep -rnE '\barg[0-9]\b' --include=*.h soh/src soh/include | wc -l                                                                     # 145
for fn in <names>; do grep -rlE "\b$fn\s*\(" --include=*.h soh/include soh/src; done                                                   # header cross-ref
# fillers
<the three greps quoted in §4>
# UNUSED / (void)
grep -rn 'define UNUSED' soh/include                                  # attributes.h:8 (live), macros.h:26 (commented)
grep -rnE '^\s+\(void\)\s*[A-Za-z_]' --include=*.c soh/src/code soh/src/overlays soh/src/boot   # 7 (3 are freopen in main.c)
```

`classify.py` (scratchpad, 230 lines; not saved in the repo — reproduce from this description): walks every
`.c/.h` under the five census dirs; finds column-0 function definitions (`ret name(...) {` … `^}$`, wrapped
signatures handled) and `typedef struct`/`struct {` spans; mode `pads` matches
`^\s+(UNUSED\s+)?(static\s+)?(const\s+)?[type]\s+\**((pad|padding|unk_pad|filler)\w*)(\[...\])*\s*;` and counts
whole-word occurrences of the name in the enclosing function body with `//` comments stripped (≤1 ⇒ unreferenced);
mode `slots` counts declarations matching `^\s+[type]\s+\**(sp[0-9A-F]{1,3}|temp_\w+|phi_\w+|new_var\d*)\b\s*(\[..\])?\s*(=|;|,)`
per function; modes `deadinit`/`deadassign` are described in §5. `funcslots.py FILE:FUNC …` prints, per slot-named
variable in a function, its reference count, assignment count and up to N use lines — the evidence behind every row
of §2a.
