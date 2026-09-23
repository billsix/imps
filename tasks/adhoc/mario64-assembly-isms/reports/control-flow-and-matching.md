# Assembly-isms in SM64 / Ghostship — survey of 11 classes

Checkout: `n64/SuperMario64/Ghostship/src` (repo-relative). All paths below are relative to that `src/`.

## Global finding that reframes half of these classes: the build is `VERSION_US=1`

`Ghostship/CMakeLists.txt:203` defines `VERSION_US=1` (and `:210` `AVOID_UB=1`). Every `#ifdef VERSION_EU` / `#ifdef VERSION_SH` block, and every `#else` of `#if defined(VERSION_JP) || defined(VERSION_US)`, is **dead text that no compiler in this port ever sees**. `audio/load_sh.c`, `audio/synthesis_sh.c`, `audio/port_sh.c` are wrapped in a file-level `#ifdef VERSION_SH` (verified at each file's line 1); `audio/port_eu.c` in `#ifdef VERSION_EU` (line 8).

Consequence: the audio subsystem — which dominates the goto/label/empty-then logs — contributes far fewer *live* hits than the raw counts suggest. Numbers per class below distinguish "is really the pattern" from "is really the pattern **and compiled**".

Also relevant: `include/types.h:16` defines `BAD_RETURN(cmd)` as plain `void`, and `include/macros.h:28` `UNUSED` as `__attribute__((unused))` — the matching-era scaffolding is already neutered at the macro level, so the *comments* about it are stale, not the code.

---

## 1. `goto.txt` — 60 hits

### What the hits really are
- 5 of the 60 lines are **comments containing the word "goto"**, not statements: `audio/copt/seq_channel_layer_process_script_copt.inc.c:373`, `audio/seqplayer.c:780`, `audio/synthesis.c:632`, `:639`, `audio/synthesis_sh.c:408`.
- 55 are real `goto` statements. **True-positive ratio 55/60 = 92%.**
- Of those 55, only **18 are compiled** under `VERSION_US`. Breakdown I verified by reading the enclosing `#if` nesting in each file:
  - dead: `audio/heap.c` ×8 (inside the `#else` of `#if defined(VERSION_JP) || defined(VERSION_US)` at `heap.c:443`, closing `#endif` at `:608`), `audio/playback.c` ×12 (`process_notes` is split at `playback.c:410 #if defined(VERSION_EU) || defined(VERSION_SH)` … `:576 #else`), `audio/seqplayer.c` ×7 (all under `#if defined(VERSION_EU) || defined(VERSION_SH)`; the US path is the copt include at `seqplayer.c:961`), `audio/load_sh.c` ×4, `audio/synthesis_sh.c` ×2, `audio/effects.c:415` ×1 (`#ifdef VERSION_SH`), plus 3 inside the `#else` of `#if COPT` in the copt file — and `copt/...inc.c:22` sets `#define COPT 1`, so `GET_INSTRUMENT`'s `goto ret##l` / `goto gi##l` macro body is never instantiated.
  - live: copt ×9, `audio/load.c` ×2, `audio/synthesis.c:818` ×1, `game/ingame_menu.c` ×4, `game/behaviors/koopa.inc.c:415` ×1, `goddard/gd_math.c:573` ×1.

### Sub-patterns
1. **`goto` that is literally `break`** — label sits immediately after the closing brace of the switch/loop being exited. Live: copt `l1090`, `l1138`, `l13cc`; `load.c` `out1`/`out2`. Upstream itself proves the equivalence: the EU branch of the very same `load.c` loop uses `break;` where JP/US use `goto out1;`.
2. **`goto` that is literally `return;`** — label is the last statement of the function. `koopa.inc.c:415 → 434`.
3. **`goto` skipping the remainder of a function body** (guard-clause inversion). `gd_math.c:573 → 590`.
4. **`goto` over a large alternative code path** — `synthesis.c:818 → 1100`, jumping ~280 lines over the ADPCM decode loop.
5. **`goto` into a shared `default:` arm of the same switch** — `ingame_menu.c:1190/1197/1204/1211 → 1213`, where `default:` and `skip:` are stacked on consecutive lines.
6. **`goto` as a synthetic else-branch inside `if (1) { label: … }`** (dead here, but the shape is instructive) — `playback.c:458-466`.

### Exemplars

**(a) `audio/load.c:327` — goto-as-break. Mechanical.**
```c
        if (sSampleDmas[gSampleDmaNumListItems].buffer == NULL) {
#if defined(VERSION_EU)
            break;
#else
            goto out1;
#endif
        }
```
with, at `load.c:336-339`:
```c
    }
#if defined(VERSION_JP) || defined(VERSION_US)
out1:
#endif
```
Rewrite: delete the `#if/#else/#endif` and the label; keep `break;`. Behaviour-preserving because the label is the first thing after the loop's closing brace and the `goto` originates from the loop's own body at loop depth 1 — the two constructs transfer control to the identical point with identical (zero) side effects. Upstream already asserts this equivalence by emitting `break` for EU. Same shape at `load.c:365` / label `:376`.

**(b) `audio/copt/seq_channel_layer_process_script_copt.inc.c:321` — goto-as-break ×3, and the labels are named after ROM addresses.**
```c
                case 0x00: // layer_note0 (play percentage, velocity, duration)
                    M64_READ_COMPRESSED_U16(state, sp3A);
                    vel = *((*state).pc++);
                    layer->noteDuration = *((*state).pc++);
                    layer->playPercentage = sp3A;
                    goto l1090;
```
and `:335-338`:
```c
            }
l1090:
            cmdSemitone = cmd - (cmd & 0xc0);
            layer->velocitySquare = vel * vel;
```
Rewrite: `break;` in all three cases, delete `l1090:`. Behaviour-preserving: `l1090:` is the statement immediately following the `switch`'s closing brace, and the switch has no `default:`, so the fall-off-the-end path already lands on the same statement — `goto l1090` and `break` are indistinguishable. Identical argument for `l1138` (`:344/348/352`, label `:354`) and `l13cc` (`:435/441`, label `:443`). These are the highest-value goto rewrites in the tree: live code, purely mechanical, and the label names (`l1090` = ROM offset) are the most blatant assembly residue in the port.

**(c) `game/behaviors/koopa.inc.c:415` — goto-as-return. Mechanical.**
```c
            cur_obj_set_model(MODEL_KOOPA_WITH_SHELL);
            obj_mark_for_deletion(shell);
            goto end;
        }
```
with `koopa.inc.c:434-435`:
```c
end:;
}
```
Rewrite: `return;` and delete `end:;`. Behaviour-preserving — the label is the final statement before the closing brace of a `void` function, so both paths run zero further statements. Note the `:;` idiom itself (empty statement after a label) exists only because C89 forbids a label before `}`.

**(d) `goddard/gd_math.c:573` — guard-clause goto over a no-op body. Mechanical, and it documents a joke function.**
```c
    if (run < 0) {
        goto end;
    }

    if ((j = i + 1) >= 4) {
```
…`gd_math.c:590-594`:
```c
end:
    vec->x = tVec.x;
    vec->y = tVec.y;
    vec->z = tVec.z;
}
```
Rewrite:
```c
    if (run >= 0) {
        if ((j = i + 1) >= 4) { j = 1; }
        if ((k = j + 1) >= 4) { k = 1; }
        jVal = quat[j];  kVal = quat[k];
        uVec.x = quat[0]; uVec.y = quat[i]; uVec.z = zHalf + zHalf;
    }
    vec->x = tVec.x;
    vec->y = tVec.y;
    vec->z = tVec.z;
```
Behaviour-preserving: everything skipped writes only to function-local `UNUSED` variables (`jVal`, `kVal`, `uVec`, `j`, `k`); `quat[]` is only read; the three `vec->` stores execute on both paths in both versions. The function is already annotated `UNUSED` and "quite literally does nothing".

**(e) `game/ingame_menu.c:1204` — goto into a shared `default:` arm. NOT mechanical.**
```c
            case DIALOG_CHAR_MULTI_THE:
                if(!ROM_JP) {
                    render_multi_text_string_lines(STRING_THE, lineNum, &linePos, linesPerBox, xMatrix, lowerBound);
                    xMatrix = 1;
                    break;
                }
                goto skip;
```
and `:1212-1213`:
```c
            default:
            skip:
```
There is no standard-C construct that jumps from case N into case `default` of the same switch (fallthrough only works to the *physically next* label). A behaviour-preserving rewrite means hoisting the `default:` arm — ~50 lines that mutate `xMatrix`, `linePos`, `mark`, `strChar` and emit display-list commands — into a `static` helper taking those by pointer, then calling it and `break`ing in each `goto skip` site. That is a real refactor, not a patch-sized edit, and it risks changing `FrameInterpolation_RecordOpenChild` nesting if done sloppily. **Classify: leave-alone / separate larger PR.**

**(f) `audio/synthesis.c:818` — long forward goto, but it is *port-authored*, not decomp residue.**
```c
                    noteSamplesDmemAddrBeforeResampling = DMEM_ADDR_UNCOMPRESSED_NOTE;
                    goto s16_done;
                }
```
jumping to `synthesis.c:1100 s16_done:;`. The enclosing block is introduced at `synthesis.c:771` by `// [Port] [Custom audio] CODEC_S16: raw 16-bit PCM — bypass ADPCM machinery` — Ghostship's own added feature. A rewrite (wrap the ADPCM section in `else { … }`) is behaviourally identical but touches ~300 lines of indentation and would collide with every future upstream sync of `synthesis.c`. **Classify: needs-care; low value.**

### Risk rating & upstream appetite
- Sub-patterns 1 and 2 (`goto`→`break`/`return`): **mechanical/safe**. Ghostship restructures freely and these have zero behavioural surface; very likely accepted, especially the copt `l1090`/`l1138`/`l13cc` trio.
- Sub-pattern 3 (`gd_math`): **mechanical/safe**.
- Sub-patterns 4, 5: **needs-care**, best as separate PRs.
- Everything under `VERSION_EU`/`VERSION_SH`: **leave-alone**. Touching it gains nothing (never compiled) and guarantees conflicts with any upstream decomp resync; if anything the right patch there is deleting the dead version arms wholesale, which is a policy decision, not a cleanup.

### Hot files
1. `audio/copt/seq_channel_layer_process_script_copt.inc.c` (13) — **9 live, all sub-pattern 1**
2. `audio/playback.c` (12) — all dead
3. `audio/seqplayer.c` (8) — all dead
4. `audio/heap.c` (8) — all dead
5. `game/ingame_menu.c` (4) — live, but hardest

---

## 2. `labels.txt` — 211 hits

### Separation (as requested)
- **194 lines contain `default:`** — ordinary switch labels. Pure noise for this purpose. The single biggest contributor, `goddard/dynlist_proc.c` with 69, is one giant dispatch switch.
- **17 non-`default:` lines remain**, of which **2 are English prose inside block comments**: `game/profiler.c:128` and `:200`, both the word `Information:` inside a `/* … */` banner.
- So the log surfaces **15 true goto-target labels**. **True-positive ratio 15/211 ≈ 7%** (or 15/17 ≈ 88% once `default:` is excluded).

### What the regex missed
I re-ran a stricter label grep over `audio engine game goddard menu` and found **21 real labels**, six of which the log never listed because its pattern rejects the `label:;` form (empty statement on the same line):
`audio/heap.c:604 out:;`, `audio/playback.c:574 skip:;`, `audio/seqplayer.c:806 skip:;`, `audio/copt/...inc.c:392 skip:;`, `audio/synthesis.c:1100 s16_done:;`, `game/behaviors/koopa.inc.c:434 end:;`.
Live labels under `VERSION_US`: exactly 10 — copt `:336 l1090`, `:354 l1138`, `:392 skip`, `:443 l13cc`; `load.c:338 out1`, `:376 out2`; `synthesis.c:1100 s16_done`; `ingame_menu.c:1213 skip`; `koopa.inc.c:434 end`; `gd_math.c:590 end`.

### Sub-patterns
1. **Address-derived names** — `l1090`, `l1138`, `l13cc` (copt). Unambiguously machine-derived.
2. **Cleanup/exit names** — `out`, `out1`, `out2`, `null_return`, `end`, `skip`, `next`, `again`, `restart`, `done`.
3. **Single-letter names** — `c:`, `d:` at `audio/playback.c:460`, `:470`. Register-allocator-era naming.
4. **`label:;` (empty statement)** — required pre-C23 because a label may not precede `}`. All six found above.

### Exemplars
`audio/playback.c:458-466` (dead, but the shape is the archetype):
```c
            goto d;
            if (1) {
                c:
                seq_channel_layer_note_release(playbackState->parentLayer);
                audio_list_remove(&note->listItem);
```
— an unreachable `if (1)` used purely to give the `c:` label a home, with `goto d` jumping over it. The standard-C shape is `if (…) { <c body> } ; <d body>`.

All other exemplars are the `goto` targets already quoted in §1 — labels and gotos must be patched as a unit.

### Risk & upstream
The 194 `default:` are not a class. The 10 live labels ride along with their gotos: **mechanical/safe** where the goto is (a)/(b)/(c)/(d), **leave-alone** otherwise. Removing a `label:;` is behaviour-free by construction (empty statement).

### Hot files
1. `goddard/dynlist_proc.c` (69 — all `default:`)
2. `goddard/renderer.c` (14 — all `default:`)
3. `game/camera.c` (12 — all `default:`)
4. `audio/seqplayer.c` (9 — mixed; the one real label, `:2181 out:`, is EU/SH-only)
5. `game/ingame_menu.c` (6 — includes the real `:1213 skip:`)

---

## 3. `infinite_loop.txt` — 27 hits

### What the hits really are
All 27 are genuinely `for (;;)` or `while (TRUE)`. **True-positive ratio as a *syntactic* match: 27/27.** As an *assembly-ism*, far lower: I read 12 and classify roughly **8/27 as rewritable-to-idiomatic-C**, the rest as legitimate.

### Sub-patterns
1. **Legitimate event/dispatch loops** — never meant to terminate, or terminate only via a tagged sentinel. `game/main.c:340` (`osRecvMesg` + switch), `game/sound_init.c:350` (audio thread), `engine/surface_load.c:608` (terrain-type dispatch with `TERRAIN_LOAD_END → break`), `engine/behavior_script.c:112`, `goddard/gd_main.c:55`, `goddard/debug_utils.c:589`. **Not assembly-isms** — `for(;;)`/`while(TRUE)` is the correct C here. At most a `while (TRUE)` → `for (;;)` spelling unification.
2. **Deliberate hangs** — `game/main.c:447` `while (TRUE) { ; }` (post-`osSetThreadPri` halt), `engine/behavior_script.c:112` inside `UNUSED void stub_behavior_script_1`, `game/spawn_object.c:223` `while (TRUE) { }` (object pool exhausted — "We've met with a terrible fate."). Legitimate; the empty body is the point.
3. **Loops whose real exit condition was hoisted into the body** — the actual assembly-ism. `game/print.c:72`, `game/macro_special_objects.c:277`/`:347`, `game/macro_special_objects.c:121`/`:196`, `game/behaviors/heave_ho.inc.c:34`.

### Exemplars

**(a) `game/print.c:72` — search loop with the test inverted into the body. Mechanical.**
```c
        while (TRUE) {
            powBase = int_pow(base, numDigits);
            if (powBase > (u32) n) {
                break;
            }
            numDigits++;
        }
```
Rewrite:
```c
        while ((powBase = int_pow(base, numDigits)) <= (u32) n) {
            numDigits++;
        }
```
Behaviour-preserving: `int_pow` is pure, the assignment to `powBase` still happens on the exiting iteration (so `powBase` holds the same value after the loop), and the negated comparison is exact for the unsigned operands involved.

**(b) `game/macro_special_objects.c:277` — unbounded table search plus a *stubbed-out* bounds check. Mechanical, and it exposes an adjacent ism.**
```c
        offset = 0;
        while (TRUE) {
            if (SpecialObjectPresets[offset].preset_id == presetID) {
                break;
            }
            if (SpecialObjectPresets[offset].preset_id == 0xFF) {
            }
            offset++;
        }
```
Rewrite:
```c
        for (offset = 0; SpecialObjectPresets[offset].preset_id != presetID; offset++) {
            /* NOTE: the original had an empty `if (preset_id == 0xFF) {}` here —
               a sentinel check whose body was optimized away. Kept absent. */
        }
```
Behaviour-preserving: the middle `if` has an empty body and `SpecialObjectPresets[offset].preset_id` is a plain array read with no side effect, so deleting it is a no-op. (It is not `volatile`; I checked the declaration site is a static table.) **Note:** this empty-bodied `if` is exactly the class `empty_then.txt` is hunting, and its regex missed it because the condition is not the literal `1`.

**(c) `game/behaviors/heave_ho.inc.c:34` — table walk with two exits. Mechanical.**
```c
    while (TRUE) {
        if (D_8032F460[sp1C][0] == -1) {
            o->oAction = 2;
            break;
        }
        if (o->oTimer < D_8032F460[sp1C][0]) {
            cur_obj_init_animation_with_accel_and_sound(2, D_8032F460[sp1C][1]);
            break;
        }
        sp1C++;
    }
```
Rewrite to `for (sp1C = 0; D_8032F460[sp1C][0] != -1; sp1C++) { if (o->oTimer < D_8032F460[sp1C][0]) { …; return; } } o->oAction = 2;` — behaviour-preserving because the two exits are mutually exclusive and the function body ends right after the loop (verified: the closing `}` at `:47` is the function's). This one is **needs-care**: it converts a `break` into a `return` and reorders which statement follows the loop, so it deserves a careful read rather than sed.

**(d) `game/main.c:447` — deliberate halt. Leave alone.**
```c
    // halt
    while (TRUE) {
        ;
    }
```
"Rewriting" this gains nothing; the lone `;` is the honest expression of a spin-halt.

### Risk & upstream
Sub-pattern 3 only: **mechanical/safe** for (a) and (b), **needs-care** for (c). Sub-patterns 1 and 2: **leave-alone** — they are correct C and a patch touching them is noise a reviewer will push back on. Ghostship would plausibly take (a)/(b) as a small readability patch; I would not bundle them with the `while (TRUE)`→`for (;;)` spelling churn.

### Hot files
1. `game/macro_special_objects.c` (4)
2. `audio/seqplayer.c` (4 — all in EU/SH-only script interpreters, dead)
3. `goddard/renderer.c` (2)
4. `goddard/debug_utils.c` (2)
5. `game/main.c` (2)

---

## 4. `do_while_0.txt` — 4 hits (all read)

### What the hits really are
**4/4 true positives**, all four in one function, `copy_spline_segment` in `game/camera.c:7173-7193`, which upstream already flags `// TODO: (Scrub C)`.

```c
    // Create the end of the spline by duplicating the last point
    do { init_spline_point(&dst[i], 0, src[j].speed, src[j].point); } while (0);
    do { init_spline_point(&dst[i + 1], 0, 0, src[j].point); } while (0);
    do { init_spline_point(&dst[i + 2], 0, 0, src[j].point); } while (0);
    do { init_spline_point(&dst[i + 3], -1, 0, src[j].point); } while (0);
```

### Sub-pattern
Exactly one: **`do { S } while (0);` wrapping a single call**, with no `break`/`continue` inside and no macro involved (`init_spline_point` is a real function at `camera.c:7166`). This is the decompiler rendering an unconditional branch-back-that-isn't; it is *not* the legitimate multi-statement-macro idiom.

### Exemplar & rewrite — `game/camera.c:7189`
```c
    init_spline_point(&dst[i],     0, src[j].speed, src[j].point);
    init_spline_point(&dst[i + 1], 0, 0,            src[j].point);
    init_spline_point(&dst[i + 2], 0, 0,            src[j].point);
    init_spline_point(&dst[i + 3], -1, 0,           src[j].point);
```
Behaviour-preserving for the strongest possible reason: `do { S } while (0);` with a constant-zero controlling expression and no jump statement in `S` executes `S` exactly once and then falls through — it is the same statement sequence with a redundant wrapper.

### Anything the regex missed in the same function
`copy_spline_segment` is the densest assembly-ism site I found. Two more, both in the same 20 lines:
```c
        } while ((src[j].index != -1) && (src[j].index != -1)); //! same comparison performed twice
    } while (j > 16);
```
The duplicated conjunct (already annotated by the decomp) reduces to `while (src[j].index != -1)` — behaviour-preserving only if you accept that the two reads of `src[j].index` cannot differ, which holds here (`src` is a non-`volatile` `struct CutsceneSplinePoint[]` and nothing between them writes it). The outer `do { … } while (j > 16)` is a rotated loop whose relationship to `j` is genuinely odd; I would **not** touch it in the same patch.

### Risk & upstream
**Mechanical/safe** for the four `while (0)` wrappers. Very likely accepted — it is four lines, the function is already TODO-marked, and there is no semantic argument against it. I would send the four wrappers alone and leave the duplicated-comparison and the outer `do/while` for a follow-up.

### Hot files
1. `game/camera.c` (4) — the only file.

---

## 5. `empty_then.txt` — 10 hits (all read)

### What the hits really are
- **4 true positives** (`if (1) {}` statement-anchors): `audio/load_sh.c:231`, `audio/playback.c:473`, `audio/seqplayer.c:2046`, `:2124`. **All four are in `VERSION_SH`/`VERSION_EU` blocks — none compiled.**
- **1 commented-out** line: `audio/seqplayer.c:2375` `//if (cmd) {}`.
- **5 regex noise** — brace-less one-line `if`s that the pattern mistook for empty bodies:
  - `game/camera.c:1286`, `:1290`, `:1299` — `if (MANUAL_CAMERA_SOUNDS) play_sound_cbutton_side();`. `MANUAL_CAMERA_SOUNDS` is a **port-added CVar**, `game/camera_settings.h:16`: `#define MANUAL_CAMERA_SOUNDS CVarGetInteger("gEnhancements.Camera.ManualCameraSounds", 1)`. Not an assembly-ism at all — it is new port code.
  - `game/mario_actions_airborne.c:617`, `game/mario_actions_submerged.c:489` — the one-line-for-matching idiom (see §8).

**True-positive ratio 4/10 = 40%, and 0/10 live.**

### Sub-patterns
1. `#ifdef`-guarded `if (1) {}` used as a **statement anchor** so a version's codegen emits a branch. Example at `audio/playback.c:471-474`:
```c
        if (playbackState->priority != NOTE_PRIORITY_DISABLED) {
#ifdef VERSION_SH
            if (1) {}
#endif
```
2. `if (1) {}` used as a **block scaffold for a label** — `audio/playback.c:459-461` `goto d; if (1) { c: … }`, covered in §2.
3. **Empty-bodied `if` with a non-constant condition** — the regex's blind spot. Verified live instance: `game/macro_special_objects.c:283` `if (SpecialObjectPresets[offset].preset_id == 0xFF) { }`. A broader `if \(.*\) \{\s*\}` over `audio engine game goddard menu` finds 14 `if (1)` and 3 `if (0)` sites total, e.g. `goddard/draw_objects.c:665 if (0) {` (a dead stubbed-printf block).

### Exemplar & rewrite
`audio/playback.c:473`:
```c
#ifdef VERSION_SH
            if (1) {}
#endif
```
Rewrite: delete. Behaviour-preserving trivially (empty statement under a true constant). But it is inside `#ifdef VERSION_SH` in a `VERSION_US` build, so the patch changes nothing the compiler sees and its only value is documentary.

The one worth patching is the live, non-constant case — see §3 exemplar (b), `game/macro_special_objects.c:283`.

### Risk & upstream
**Mechanical/safe** in isolation, **but near-zero value**: 4/4 of the class's real hits are in code this port does not compile. I would **not** send a patch for this class on its own; fold the live `macro_special_objects.c:283` deletion into the §3 loop rewrite instead. Upstream would accept it but might reasonably ask why you are editing SH-only audio at all.

### Hot files
1. `game/camera.c` (3 — all noise)
2. `audio/seqplayer.c` (3 — 2 real+dead, 1 commented)
3. `game/mario_actions_submerged.c` (1 — noise)
4. `game/mario_actions_airborne.c` (1 — noise)
5. `audio/playback.c` (1 — real, dead)

---

## 6. `if_else_ladder_num.txt` — 65 hits

### What the hits really are
All 65 match `} else if (<expr> == <integer literal>)` or similar — **syntactically 65/65**. As assembly-isms the picture is mixed; from the 8 sites I read in full I estimate:
- **~55% are genuine magic-number state ladders** that should be a `switch` over a named enum (object action/subaction/state machines). These are decompiler-shaped: the ROM had a jump table or a compare chain and the constant never got a name.
- **~25% are ladders over values that already have names elsewhere** — the constant is the ism, not the ladder.
- **~20% are legitimate C**: the condition is a compound expression, a side-effecting decrement, or a genuine non-switchable test. Examples I verified: `engine/level_script.c:125` `} else if (--sDelayFrames == 0) {`, `game/behaviors/eyerok.inc.c:112` `} else if ((o->oEyerokBossActiveHand = o->oEyerokBossUnkFC & 0x1) == 0) {`, `game/rumble_init.c:112` `} else if ((gCurrRumbleSettings.unk0A >= 2) && (gNumVblanks % gCurrRumbleSettings.unk0C == 0)) {`, `game/interaction.c:1069`. None of these can become a `switch` case.

### Sub-patterns
1. **Action-state ladder on a single variable, dense small integers** — the switch candidate. `game/behaviors/express_elevator.inc.c:5-30`, `bowser.inc.c` ×6, `sparkle_spawn_star.inc.c:96/107`, `clock_arm.inc.c:21`, `grill_door.inc.c:19`.
2. **Provably-redundant final condition** — `} else if (x == k)` where the preceding arms already exhaust the complement. `menu/intro_geo.c:58`.
3. **Grouped-value ladder** — `if (a == 4 || a == 3) … else if (a == 2 || a == 1) …`, i.e. a switch with stacked case labels. `game/behaviors/spindel.inc.c:49-55`.
4. **Ladder with a non-constant tail arm**, so a `switch` needs an `if` after it. `express_elevator.inc.c:28` `} else if (!cur_obj_is_mario_on_platform()) {`.
5. **Side-effecting or compound conditions** — not rewritable (the 20% above).

### Exemplars

**(a) `menu/intro_geo.c:58` — redundant condition. Mechanical, one word.**
```c
    if (state != 1) {
        sIntroFrameCounter = 0;
    } else if (state == 1) {
        graphNode->flags = (graphNode->flags & 0xFF) | (LAYER_OPAQUE << 8);
```
Rewrite: `} else {`. Behaviour-preserving: if `state != 1` is false then `state == 1` is true, and `state` is a plain `s32` parameter not modified in the then-arm. This exact shape recurs at `intro_geo.c:109`, `:404`, `:440` (the log's 4 other `intro_geo` hits) — one file, one patch, four identical edits.

**(b) `game/behaviors/express_elevator.inc.c:9` — action ladder → `switch`. Needs-care.**
```c
    if (o->oAction == 0) {
        if (cur_obj_is_mario_on_platform()) { o->oAction++; }
    } else if (o->oAction == 1) {
        o->oVelY = -20.0f;
        …
    } else if (o->oAction == 3) {
        …
    } else if (!cur_obj_is_mario_on_platform()) {
        o->oAction = 0;
    }
```
Rewrite:
```c
    switch (o->oAction) {
        case 0: if (cur_obj_is_mario_on_platform()) { o->oAction++; } break;
        case 1: … break;
        case 2: … break;
        case 3: … break;
        default:
            if (!cur_obj_is_mario_on_platform()) { o->oAction = 0; }
            break;
    }
```
Behaviour-preserving **only because** the arms mutate `o->oAction` but a `switch` evaluates its controlling expression once up front, exactly as the `if` ladder tests `o->oAction` afresh per arm — and here no earlier arm's mutation can make a *later* arm's test succeed in the same pass (arm 0 sets 1, arm 1 sets 2, arm 3 sets 4; each moves strictly forward past the arms below it). **That property must be re-verified per site** — it is the whole risk of this class. Where an arm decrements or resets the discriminant, the `switch` is *not* equivalent.

**(c) `game/behaviors/spindel.inc.c:49` — grouped ladder → stacked cases. Mechanical.**
```c
    if (sp18 == 4 || sp18 == 3) {
        sp18 = 4;
    } else if (sp18 == 2 || sp18 == 1) {
        sp18 = 2;
    } else if (sp18 == 0) {
        sp18 = 1;
    }
```
Rewrite:
```c
    switch (sp18) {
        case 4: case 3: sp18 = 4; break;
        case 2: case 1: sp18 = 2; break;
        case 0:         sp18 = 1; break;
    }
```
Behaviour-preserving: `sp18` is a local, all arms are disjoint constants, and each arm's write cannot re-enter the ladder. Safe here precisely because the discriminant is read once and the arms are terminal.

**(d) `engine/level_script.c:125` — NOT rewritable.**
```c
    } else if (--sDelayFrames == 0) {
```
The condition has a side effect that must occur *only when the earlier arms fail*. Hoisting it into a `switch` discriminant would decrement unconditionally. Regex noise for this class; leave it.

### Risk & upstream
- Sub-pattern 2 (`intro_geo.c` ×5): **mechanical/safe**, near-certain acceptance.
- Sub-pattern 3: **mechanical/safe** per site.
- Sub-pattern 1: **needs-care** — every site needs the discriminant-mutation check above, and the payoff (readability) is real but modest. Ghostship would take these, but as small per-file patches; a 34-file sweep would be hard to review.
- Sub-pattern 5: **leave-alone**.
- Orthogonal and higher-value: naming the constants. `o->oAction == 1` → `KOOPA_SHELLED_ACT_LYING`-style enums; the decomp already does this in some behaviors (`koopa.inc.c`) and not others (`express_elevator.inc.c`), so there is precedent to match.

### Hot files
1. `game/behaviors/bowser.inc.c` (6)
2. `menu/intro_geo.c` (5) — the easiest wins
3. `game/mario_actions_cutscene.c` (5)
4. `game/behaviors/boo.inc.c` (5)
5. `game/behaviors/eyerok.inc.c` (4) — but `:112` and `:27` are the side-effecting kind

---

## 7. `single_stmt_nested_if.txt` — 135 hits

### What the hits really are — **this regex is measuring something other than its name**
Reading 8 sites shows the pattern matches **`if (` whose closing paren is not on the same line**, i.e. it fires on *line-wrapped conditions* and on *brace-less `if` with the body on the next line*. It does **not** find `if (a) if (b) x;`.

- **~70% is plain line-wrapped multi-line conditions** — e.g. `game/camera.c:1088`, `game/interaction.c:720`, `game/mario.c:770`, `audio/external.c:692`. Legitimate C formatted to 100 columns. Pure noise.
- **~20% is `#if`-split conditions**, where the `if (` and its `{` are separated by preprocessor arms. `audio/effects.c:161`/`:163` and `audio/heap.c:711`/`:715` are the same construct counted twice by the regex. Noise for this class, though the construct itself is a version-hack ism.
- **~10% is brace-less `if` with the body on the following line** — `game/moving_texture.c:678`, `menu/file_select.c:1704`/`:1706`, `goddard/objects.c:870`, `goddard/renderer.c:2929`. Style variance, not assembly.
- A **small residue is a genuine assembly-ism**: sequential mutually-exclusive `if`s that the compiler emitted as two separate compares because the original `else` was lost.

**True-positive ratio as "single-statement nested if": ≈ 0/135. True-positive ratio as "something worth looking at": maybe 5/135.**

### Exemplars

**(a) `menu/file_select.c:1704` — the real ism in this log: two `if`s that are an `if/else`.**
```c
    if (sCursorClickingTimer == 0)
        gSPDisplayList(gDisplayListHead++, dl_menu_idle_hand);
    if (sCursorClickingTimer != 0)
        gSPDisplayList(gDisplayListHead++, dl_menu_grabbing_hand);
```
Rewrite:
```c
    if (sCursorClickingTimer == 0) {
        gSPDisplayList(gDisplayListHead++, dl_menu_idle_hand);
    } else {
        gSPDisplayList(gDisplayListHead++, dl_menu_grabbing_hand);
    }
```
Behaviour-preserving: the two conditions are exact complements over the same `s8` static, and neither body writes `sCursorClickingTimer` (it is next touched at `:1710`). `gDisplayListHead++` happens exactly once either way.

**(b) `audio/effects.c:161` — `#if`-split condition. Real ism, but version-guard shaped.**
```c
#if defined(VERSION_EU) || defined(VERSION_SH)
    if (v0 > 127)
#else
    if (v0 >= 127)
#endif
    {
        v0 = 127;
    }
```
The brace-on-its-own-line dance exists only to share one body between two conditions. Under `VERSION_US` this collapses to `if (v0 >= 127) { v0 = 127; }`. Behaviour-preserving **for this build**, but it deletes a version arm — see the `VERSION_*` policy note below.

**(c) `goddard/renderer.c:1816` — genuine nested single-statement ifs, annotated as such. NOT in this log.**
```c
        // the ifs need to be separate to match...
        if (sCurrentGdDl->vtx[i].n.ob[0] == (s16) x) {
            if (sCurrentGdDl->vtx[i].n.ob[1] == (s16) y) {
                if (sCurrentGdDl->vtx[i].n.ob[2] == (s16) z) {
```
Rewrite: `if (a == x && b == y && c == z) {`. Behaviour-preserving — all three operands are non-`volatile` struct reads with no side effects, and `&&` short-circuits in the same order the nesting did. This is what the class *meant* to find; the regex missed it because each `if (…)` closes on its own line.

### Risk & upstream
The class as logged is **not actionable** — 90%+ noise. Two actions worth extracting: (a) `file_select.c:1704` as a two-line patch (**mechanical/safe**, likely accepted), and a *re-grep* for the real construct, seeded by `renderer.c:1816`. I would re-run with a pattern anchored on `if (…) {` immediately followed by `if (…) {` with no other statement between, rather than trusting this log.

### Hot files (of a mostly-noise log)
1. `audio/seqplayer.c` (18)
2. `game/camera.c` (16)
3. `audio/external.c` (8)
4. `audio/heap.c` (6)
5. `game/mario.c` (5)

---

## 8. `matching_comments.txt` — 41 hits

### What the hits really are
- **~24 true positives** — comments that document a construct existing *only* to reproduce IDO `-O2` codegen. **Ratio ≈ 59%.**
- **~17 noise** — the word "match" used in its ordinary sense: `engine/behavior_script.c:84` ("to match its real position and rotation"), `game/area.c:58`, `game/hud.c:209`, `game/paintings.c:1223`, `game/behaviors/bird.inc.c:92`, `audio/effects.h:28`.

This is the **most valuable class in the survey**, because each true positive is a *self-identifying* assembly-ism: the comment names the construct and states why it exists. It is a map to the other classes.

### Sub-patterns
1. **"must be one line to match on -O2"** — a statement or `for` body collapsed onto the `if`/`for` line. `game/mario_actions_airborne.c:615`, `game/mario_actions_submerged.c:488`, `game/camera.c:1759`, `:4497`, `game/game_init.c:325`, `game/level_update.c:711`, `engine/math_util.c:174`, `game/behaviors/fish.inc.c:19`.
2. **"needed to match"** on a **lone `;`** — an empty statement inserted to shift codegen. `goddard/draw_objects.c:658`, `:884`, `:987`, `goddard/joints.c:72`, `goddard/particles.c:353`. (A full grep finds 15 such lone-`;` statements in scope.)
3. **"needed to match"** on an **unreachable `break`** — `goddard/renderer.c:816`.
4. **Bogus return type to match** — `game/camera.c:667` and `game/save_file.c:293`, both realized via `BAD_RETURN(x)`, which `include/types.h:16` already defines as `void`.
5. **Self-assignment to force a load** — `audio/load_sh.c:1300` (dead: SH-only).
6. **"ifs need to be separate to match"** — `goddard/renderer.c:1816`.
7. **bss-order / struct-padding hacks** — `game/camera.h:649`, `game/memory.h:40`, `audio/internal.h:285`, `:641`. **Structural; leave alone.**

### Exemplars

**(a) `goddard/draw_objects.c:658` — lone `;` for codegen. Mechanical.**
```c
        sp44.x += cam->lookAt.x;
        sp44.y += cam->lookAt.y;
        sp44.z += cam->lookAt.z;
        ; // needed to match
    } else {
```
Rewrite: delete both the `;` and the comment. Behaviour-preserving: an empty statement in a compound statement generates nothing; the only reason it existed was to steer a register allocator that this port does not use. Identical at `draw_objects.c:884`, `:987`, `joints.c:72`, `particles.c:353` — five sites, one patch, five deletions.

**(b) `goddard/renderer.c:816` — unreachable `break`. Mechanical.**
```c
                    case '%':
                        *csr = '%';
                        csr++;
                        *csr = '\0';
                        break;
                        break; // needed to match
```
Rewrite: delete the second `break;`. Behaviour-preserving by unreachability — control leaves the switch at the first `break`.

**(c) `game/mario_actions_submerged.c:488` — one-line-to-match. Mechanical.**
```c
    // This must be one line to match on -O2
    if (animFrame == 0 || animFrame == 12) play_sound(SOUND_ACTION_UNKNOWN434, m->marioObj->header.gfx.cameraToObject);
```
Rewrite:
```c
    if (animFrame == 0 || animFrame == 12) {
        play_sound(SOUND_ACTION_UNKNOWN434, m->marioObj->header.gfx.cameraToObject);
    }
```
Behaviour-preserving: identical statement, identical control flow; only the line break and braces change. The companion at `game/mario_actions_airborne.c:615` additionally carries `// clang-format off` / `// clang-format on` fences that become deletable. Same treatment for `game/camera.c:1759` (`if (gCurrLevelNum == LEVEL_BBH) { pos[1] = 2047.f; }` — already braced, just needs unwrapping onto three lines and losing the comment), `game/game_init.c:325`, `engine/math_util.c:174`, `game/level_update.c:711`.

**(d) `game/behaviors/fish.inc.c:19` — one-line-to-match, column-aligned multi-assignment. Mechanical but wide.**
```c
        // Cases need to be on one line to match with and without optimizations.
        case FISH_SPAWNER_BP_MANY_BLUE:
            model = MODEL_FISH;      schoolQuantity = 20; minDistToMario = 1500.0f; fishAnimation = blue_fish_seg3_anims_0301C2B0;
            break;
```
Rewrite: one assignment per line. Behaviour-preserving (four independent assignments to four distinct locals, no sequencing dependency). Affects all arms of the switch.

**(e) `game/save_file.c:293` — bogus return type. Already a no-op; comment is stale.**
```c
//! Needs to be s32 to match on -O2, despite no return value.
BAD_RETURN(s32) save_file_copy(s32 srcFileIndex, s32 destFileIndex) {
```
Rewrite: `void save_file_copy(...)` and drop the comment. Textually behaviour-preserving because `BAD_RETURN(s32)` *expands to* `void` (`include/types.h:16`). **But**: `BAD_RETURN` appears 310 times across `audio engine game goddard menu`. Removing it wholesale is a mass rename, not a cleanup; I'd leave the macro in place and only fix the two comments that assert a matching requirement the port does not have.

**(f) `audio/load_sh.c:1300` — NOT rewritable in spirit, and dead in fact.**
```c
        mesg = mesg;    //! needs an extra read from mesg here to match...
```
Wrapped in `#pragma GCC diagnostic ignored "-Wself-assign"`. It is inside `#ifdef VERSION_SH` → never compiled here. Leave.

### Risk & upstream
- Sub-patterns 2 and 3 (lone `;`, double `break`): **mechanical/safe**, six deletions, high confidence of acceptance.
- Sub-pattern 1 (one-line-to-match): **mechanical/safe**; the only argument against is that it erases decomp provenance — which is exactly why the comment should be *deleted along with* the construct rather than left dangling. Ghostship restructures freely, so this fits its posture.
- Sub-pattern 7 (bss/padding): **leave-alone** — these comments describe layout constraints that may still bind.
- Sub-pattern 4: **needs-care** (macro-wide).

### Hot files
1. `game/camera.c` (5)
2. `goddard/draw_objects.c` (3) — all sub-pattern 2, all easy
3. `goddard/renderer.c` (2)
4. `game/shadow.c` (2)
5. `game/level_update.c` (2)

---

## 9. `avoid_ub_macros.txt` — 17 hits (all read)

### What the hits really are
- **1 true positive**: `audio/seqplayer.c:2680` — an actual `#ifdef AVOID_UB` selecting between a correct and a buggy array bound.
- **1 comment referring to the macro**: `game/behaviors/wiggler.inc.c:232`.
- **15 regex noise**: `ALIGNED8` / `ALIGNED16` declarations in `buffers/buffers.c` (14) and `buffers/zbuffer.c` (1). These are `__attribute__((aligned(8)))` (`include/macros.h:49`) — alignment attributes, unrelated to UB avoidance. They are also in `buffers/`, outside the requested subdirs.

**True-positive ratio 1/17 ≈ 6%** (2/17 if you count the comment).

### The one real instance — `audio/seqplayer.c:2676-2686`
```c
        // @bug Size of wrong array. Zeroes out second half of gSequenceChannels[0],
        // all of gSequenceChannels[1..31], and part of gSequenceLayers[0].
        // However, this is only called at startup, so it's harmless.
#ifdef AVOID_UB
#define LAYERS_SIZE LAYERS_MAX
#else
#define LAYERS_SIZE ARRAY_COUNT(gSequenceLayers)
#endif
        for (j = 0; j < LAYERS_SIZE; j++) {
            gSequenceChannels[i].layers[j] = NULL;
        }
```
`CMakeLists.txt:210` defines `AVOID_UB=1`, so this port always takes `LAYERS_MAX`. Rewrite:
```c
        // Historically this used ARRAY_COUNT(gSequenceLayers) and overran
        // gSequenceChannels[i].layers; the port has always built with AVOID_UB.
        for (j = 0; j < LAYERS_MAX; j++) {
            gSequenceChannels[i].layers[j] = NULL;
        }
```
Behaviour-preserving **for this port only**: the `#else` arm is unreachable given `AVOID_UB=1`, so deleting it cannot change generated code. It is *not* behaviour-preserving relative to an `AVOID_UB`-undefined build — but no such build exists here, and the `#else` arm is by construction undefined behaviour.

### Risk & upstream
**Needs-care, and I recommend against sending it.** The change is provably inert, but it deletes the decomp's documentation of a real N64 bug, and upstream may want to keep the `#ifdef` as a knob for ROM-accuracy work. The `ALIGNED*` hits are not a class at all. If anything is worth doing here it is *renaming the class*: the log measures alignment attributes, not UB macros.

### Hot files
1. `buffers/buffers.c` (14 — all noise, out of scope)
2. `game/behaviors/wiggler.inc.c` (1 — comment)
3. `buffers/zbuffer.c` (1 — noise)
4. `audio/seqplayer.c` (1 — the only true positive)

---

## 10. `volatile_kw.txt` — 18 hits (all read)

### What the hits really are
- **11 are legitimate, load-bearing `volatile`** on cross-thread flags: `audio/data.c:897` `volatile s32 gAudioLoadLock`, `:912` `gAudioFrameCount`, `:917` `gCurrAudioFrameDmaCount`, `:949` `gAudioLoadLockSH`, `audio/heap.c:57` `volatile u8 gAudioResetStatus`, plus their five `extern_s` declarations in `audio/data.h:72/75/81/116` and `audio/heap.h:100/104`, and `audio/port_eu.c:25`. These are written by the audio thread and polled by the game thread. **Leave alone — removing them is a data race, not a cleanup.**
- **2 are comments**: `audio/synthesis.c:677`, `:678`.
- **1 is a comment header**: `audio/internal.h:673`.
- **4 are `volatile u8 enabled : 1;` bitfields** in `struct` definitions: `audio/internal.h:265`, `:604`, `:676`.

**True-positive ratio, reading "assembly-ism" as "volatile present only to coerce a matching build": 1/18, and that one is already inert.**

### The interesting instance — a matching-era `volatile` that is now dead
`audio/internal.h:673-678`:
```c
// volatile Note, needed in synthesis_process_notes
struct vNote {
    /* U/J, EU  */
    /*0x00*/ volatile u8 enabled : 1;
    long long int force_structure_alignment;
}; // size = 0xC0
```
and the comment it serves, `audio/synthesis.c:677-679`:
```c
        //! This function requires note->enabled to be volatile, but it breaks other functions like note_enable.
        //! Casting to a struct with just the volatile bitfield works, but there may be a better way to match.
        if (note->enabled == TRUE && IS_BANK_LOAD_COMPLETE(note->bankId) == FALSE) {
```
**`struct vNote` is referenced nowhere.** A tree-wide grep for `vNote` across `audio/` returns exactly one line — its own definition at `internal.h:674`. The cast the comment describes was removed (or never survived into this port), so the `volatile` bitfield and the `force_structure_alignment` member are dead declarations, and the `//!` comment at `synthesis.c:677` describes a workaround that is no longer present.

Rewrite: delete `struct vNote` and reword the `synthesis.c` comment to note that the volatile read is no longer performed. Behaviour-preserving: an unreferenced struct type definition emits no code and constrains no layout (`struct Note`, defined immediately below at `internal.h:679`, is the one actually used).

### Why the rest is NOT safely rewritable
`audio/data.c:897`:
```c
volatile s32 gAudioLoadLock = AUDIO_LOCK_UNINITIALIZED;
```
This is a spin-checked lock between `audio_reset_session` and the DMA/load path. In a matching N64 build the `volatile` prevented IDO from caching the load in a register; in this **port** the same requirement holds for a different reason — it is a real cross-thread variable under a real OS scheduler, and modern compilers will happily hoist the load out of a poll loop without it. **This is the case the task description anticipates, with the opposite answer: the `volatile` is needed by the port *more* than by the matching build.** Same for `gAudioResetStatus` (`heap.c:57`), which `port_eu.c:25` re-declares `extern volatile u8`.

The `volatile u8 enabled : 1` bitfields at `internal.h:265`/`:604` are inside `#if`-selected version variants of `struct Note` — a `volatile` bitfield is ABI-delicate and I would not touch it without a synthesis-path audit.

### Risk & upstream
- `struct vNote` deletion + comment refresh: **mechanical/safe**, plausibly accepted, small.
- Everything else: **leave-alone**, and I would say so explicitly in any patch series cover letter so a future reader does not re-open it.

### Hot files
1. `audio/internal.h` (4)
2. `audio/data.h` (4)
3. `audio/data.c` (4)
4. `audio/synthesis.c` (2 — both comments)
5. `audio/heap.h` (2)

---

## 11. `register_keyword.txt` — 106 hits

### What the hits really are
- **104 are the `register` storage-class specifier** on a local declaration. **True-positive ratio 104/106 ≈ 98%.**
- **2 are noise** — the word "register" in comments: `engine/geo_layout.c:100` (`// similar to SP register in MIPS`) and `:102`.

Every one of the 104 is a pure assembly-ism: `register` has been a no-op hint since forever, is *deprecated in C++17* and merely ignored in C, and here it exists because the decompiler knew which MIPS register held the value. Many sites say so in a trailing comment.

### Sub-patterns
1. **`register` + explicit MIPS register name in a comment** — the most blatant. `goddard/renderer.c:2971-2978` (`// a0`, `// a1`, `// a2`, `// a3`, `// t0`…`// t3`), `goddard/skin.c:306-314` and `:351-359` (same a1/a2/a3/t0-t3 run), `goddard/renderer.c:3624-3629` (`// s0 (84)`, `// s1 (78)`, `// s2 (74)`, `// s3 (70)` — register *and* stack offset), `goddard/draw_objects.c:135` (`// s0 (24)`).
2. **`register` on hot-loop scalars**, no comment — `engine/math_util.c` (28 hits), `engine/surface_collision.c` (13), `engine/surface_load.c` (6).
3. **`register` on list-walk pointers** in goddard — `register struct ListNode *link;` recurs ~20 times across `particles.c`, `skin.c`, `joints.c`, `shape_helper.c`, `objects.c`, `draw_objects.c`.
4. **`register` on stack-named locals** — `goddard/objects.c:437 register f32 sp28;`, `goddard/skin_movement.c:50 register f32 sp1C;`. Two isms in one line.

### Exemplars

**(a) `goddard/renderer.c:2971` — the archetype.**
```c
void Unknown801A4F58(void) {
    register s16 *cbufOff; // a0
    register s16 *cbufOn;  // a1
    register u16 *zbuf;    // a2
    register s16 colour;   // a3
```
Rewrite: drop `register` and the register-name comments:
```c
void Unknown801A4F58(void) {
    s16 *cbufOff;
    s16 *cbufOn;
    u16 *zbuf;
    s16 colour;
```
Behaviour-preserving: `register` in C only (a) hints allocation, which every compiler has ignored for decades, and (b) forbids taking the address of the object — and no `&` is applied to any of these (I checked the function body through `:2995`). Removing it therefore cannot change codegen or diagnostics.

**(b) `engine/math_util.c:159` — hot path, no `&`-taking.**
```c
void mtxf_copy(Mat4 dest, Mat4 src) {
    register s32 i;
    register u32 *d = (u32 *) dest;
    register u32 *s = (u32 *) src;
```
Rewrite: drop all three `register`s. Behaviour-preserving for the same reason. Worth stating in the commit message that this is *not* expected to change performance — a reviewer's instinct will be that `mtxf_copy` is hot; the answer is that GCC/Clang's register allocator has never consulted this keyword.

**(c) `engine/surface_collision.c:22-30` — nine `register`s in one declaration block.**
```c
    register struct Surface *surf;
    register f32 offset;
    register f32 radius = data->radius;
    register f32 x = data->x;
    register f32 y = data->y + data->offsetY;
```
Rewrite: drop `register` throughout. **One caveat to verify per function before patching**: if any `register`-qualified local ever has its address taken, the code does not currently compile as written and the `register` is load-bearing as a *constraint*, not a hint. I checked this file's `find_wall_collisions_from_list` body (`:15-60`) — all uses are by value. A mechanical sweep must include a `&<name>` check per declaration; that check is what makes this "mechanical with a script", not "mechanical with sed".

**(d) `goddard/objects.c:437` — two isms stacked.**
```c
    register f32 sp28;
```
Rewrite: `f32 sp28;` — and note the name itself (`sp28` = stack pointer offset 0x28) belongs to the `stack_named_locals` class, 494 hits, not surveyed here. Fixing `register` here without renaming leaves the more visible ism in place; consider pairing them per file.

### Risk & upstream
**Mechanical/safe**, with the `&`-check caveat. This is the single cleanest, highest-volume, lowest-argument patch in the whole survey: 104 deletions of a keyword the language ignores, plus ~25 stale register-name comments. Ghostship should accept it readily — it is also a prerequisite for a C++ compiler ever touching these files, since `register` is removed in C++17 (`port/` is already C++).

Suggested split: one patch per directory (`engine/` ≈ 47, `goddard/` ≈ 56, `game/` 1) so a reviewer can take them independently.

### Hot files
1. `engine/math_util.c` (28)
2. `goddard/skin.c` (16)
3. `engine/surface_collision.c` (13)
4. `goddard/renderer.c` (12)
5. `goddard/skin_movement.c` (7)

---

## Cross-cutting observations

### Things the regexes missed, noticed while reading

1. **`label:;` form invisible to `labels.txt`** — six real labels omitted (§2). Any goto patch driven off that log will leave dangling labels and fail to build.
2. **Empty-bodied `if` with a non-constant condition** — `empty_then.txt` only looks for `if (1)`. Live miss: `game/macro_special_objects.c:283 if (SpecialObjectPresets[offset].preset_id == 0xFF) { }`. A broader sweep finds 14 `if (1)` and 3 `if (0)` sites in scope, e.g. `goddard/draw_objects.c:665 if (0) {`.
3. **Genuinely nested single-statement ifs** — what `single_stmt_nested_if.txt` was named for but does not find. Seed: `goddard/renderer.c:1814-1819`, self-documented `// the ifs need to be separate to match...`.
4. **Duplicated conjunct** — `game/camera.c:7186 } while ((src[j].index != -1) && (src[j].index != -1)); //! same comparison performed twice`. No class covers this.
5. **`#if`-split `if` condition sharing one body** — `audio/effects.c:161-167`, `audio/heap.c:711-717`. A distinct version-hack ism; currently only visible as noise inside `single_stmt_nested_if`.
6. **`// clang-format off` / `on` fences** exist solely to protect one-line-to-match constructs (`game/mario_actions_airborne.c:614-618`). They should be deleted in the same patch as the construct, and they are a good independent grep for finding more sites.
7. **Adjacent unsurveyed classes with huge counts, seen constantly while reading**: `UNUSED u8 filler[N]` local declarations (342 in scope — stack-frame padding, pure ism), `sp`/`D_`-prefixed identifiers (2277 occurrences — stack offsets and ROM addresses as names), `BAD_RETURN` (310).

### Recommended ordering for upstream submission

Ranked by (safety × value ÷ review cost), all verified above:

1. **`register` removal** — 104 sites, zero semantic surface, unblocks C++ (§11).
2. **`matching_comments` sub-patterns 2 & 3** — 6 deletions of lone `;` and a double `break` (§8a, §8b).
3. **`do { … } while (0)` unwrapping** — 4 lines in `game/camera.c` (§4).
4. **copt `goto`→`break`** — 8 gotos + 3 labels, the most assembly-shaped live code in the port (§1b).
5. **`load.c` `goto out1/out2`→`break`** — 2 sites, with upstream's own EU arm as the correctness proof (§1a).
6. **`koopa.inc.c` `goto end`→`return`**, **`gd_math.c` guard inversion** (§1c, §1d).
7. **`intro_geo.c` `else if (state == 1)`→`else`** — 5 sites (§6a).
8. **one-line-to-match unwrapping** — 8 sites (§8c, §8d).

Deliberately **not** recommended: anything under `#ifdef VERSION_EU` / `VERSION_SH` (never compiled — see the global finding), the `volatile` audio-sync globals (§10), the `AVOID_UB` knob (§9), `ingame_menu.c`'s `goto skip` (§1e), and bss/padding-order comments (§8, sub-pattern 7).
