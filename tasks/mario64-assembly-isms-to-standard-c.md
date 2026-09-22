# SuperMario64: rewrite the decomp's assembly-isms into standard C — a catalogue, an upstream-first patch stream, and a proof gate

**Status:** first cut COMPLETE 2026-09-22 — awaiting the maintainer's review. Survey (34 regex
classes + 24 constructs found by reading; four reader reports under
`tasks/adhoc/mario64-assembly-isms/reports/`), then Phases B.1–B.10, C and D done the same day,
unattended, with the maintainer's authorisation to commit in the checkout and export patches
(William Emerison Six <billsix@gmail.com>: "start working on the task in my absence; on the
subprojects you can commit and make patches"). Result: **46 patches in `patches/standard-c/`, every
one codegen-identical**, full series replays, both gates green. **Left open, for the maintainer:**
(a) the B.11 explained-diff list (rewrites that change codegen — needs the in-game oracle; see
"Phase B done" in the Progress log), (b) the ~470 remaining stack-slot locals (a naming job, tool
ready), (c) the two open questions. Checkout branch `imps-standard-c` = the stream's commits at
the bare pin; see "Progress log".
**Priority:** 4 · **Difficulty:** 6 (the rewrites are small; proving each one and keeping three
other streams applying on top is the work) · **Project key:** mario64

## BLUF

Find every construct in Ghostship's decomp directories (`src/game engine audio goddard menu`)
that reads like mechanically-lifted MIPS rather than C — `goto`-as-`break`, `register`, locals
named after stack slots, `x == TRUE`, `& 0xFFFF` before an `s16` store, `do {…} while (0)` around
one call, lone `;` "needed to match", and so on — and rewrite the ones that are **clearly and
explainably** behaviour-preserving into standard C, as a patch stream shaped for upstream
submission (HarbourMasters/Ghostship, and the sm64 decomp behind it). Each rewrite is proved with
`tools/asmdiff.sh` (identical generated code, or an explained diff).
The stream applies **first**, before the personal `cheats`/`book` streams (`patches/ORDER`), and
the task ends by replaying those streams on top and fixing whatever no longer applies. "Done" =
the safe classes below are rewritten and exported, every other stream applies and builds on top,
the docs and the patterns reference are current, and the upstream submission task is filed.

## Context (cold-start)

Read first, in order:

1. **`tasks/reference/mario64/assembly-isms-in-the-decomp.md`** — the patterns reference this
   survey produced: what each pattern is, why it exists, how to recognise it, the exact rewrite,
   and the semantic rules that decide whether a rewrite is behaviour-preserving (16-bit wrap
   casts, float→int truncation, double literals, shift vs divide, division vs reciprocal,
   `volatile`, side-effecting `UNUSED`, table-dispatched signatures, layout-fixed fillers).
2. `n64/CLAUDE.md` — the family contract: two lanes, purpose streams, `patches/ORDER`
   ("WITHIN a stream order matters; ACROSS streams it usually does not; pin a dependency in
   ORDER"), `tools/check_patches_apply.sh`.
3. `n64/SuperMario64/CLAUDE.md` + `patches/ORDER` — today's streams: `cheats` (3 patches:
   `mario.c`, `mario_actions_airborne.c`, `mario.h`, port files), `book` (doc-region markers in
   `mario.c`, `skybox.c`, `rendering_graph_node.c`, `paintings.c`, `object_list_processor.c`,
   `game_init.c`, port files; plus a LUS-lane marker patch), `upstream-candidates` (docs only).
   ORDER today: `cheats` then `book`.
4. `tasks/reference/imps/patch-philosophy.md` — upstreaming is the ideal; a candidate must be a
   standalone, reviewer-facing patch, never entangled with personal changes.
5. The sibling tasks: `tasks/mario64-decomp-rename-and-cleanup.md` (owns naming the `func_80…` /
   `D_80…` symbols — **not this task**; it also has a goddard-first "readability pass" that this
   task now subsumes for the pattern classes) and `tasks/ocarina-de-disassemble-ugly-c.md` (the OoT
   twin; its Guardrails apply here too).
6. The survey kit: `tasks/adhoc/mario64-assembly-isms/discover.sh` (the census; re-run after a pin
   bump), `data/*.txt` (one `file:line` log per class, `SUMMARY.txt` with counts), `reports/*.md`
   (the four readers' verified findings), and **`asmdiff.sh`** (the gate, below).

Facts that shape everything (all verified 2026-09-22 against pin `49c5312a`, `1.0.1`-era Ghostship):

- **The build is `VERSION_US=1` + `AVOID_UB=1`** (`CMakeLists.txt:203,210`). Every
  `#ifdef VERSION_EU`/`VERSION_SH` region — including the whole of `audio/load_sh.c`,
  `port_sh.c`, `synthesis_sh.c`, `port_eu.c` and the EU/SH branches of `seqplayer.c`,
  `playback.c`, `heap.c` — is text the compiler never sees. Rewriting it gains nothing and cannot
  be verified: **leave it alone**. Several raw class counts (goto 55 → 18 live, labels 21 → 10
  live, `temp_/phi_` 61 → 9 live) shrink accordingly.
- `audio/copt/seq_channel_layer_process_script_copt.inc.c` is prefaced "Edit if you dare"
  (`seqplayer.c:960`) — but its three `goto l1090/l1138/l13cc` are goto-as-`break` with
  ROM-address labels, the single most assembly-shaped live construct in the tree; they are in
  scope precisely because the rewrite is mechanical.
- **Upstream's clang-format gate covers only `src/port/`** (`run-clang-format.sh`); the decomp
  directories are deliberately unformatted (`mario.c` differs from `.clang-format` by 266
  lines). **Never run clang-format over a decomp file**; match the surrounding hand style.
- `include/macros.h:28` `UNUSED` = `__attribute__((unused))`; `include/types.h:16`
  `BAD_RETURN(x)` = `void`. The matching-era scaffolding is already neutered at the macro level —
  the *comments* about matching are what is stale.
- The port compiles the decomp as C with GCC (`ccache cc`, `-O2`-class Release flags); `register`
  is ignored, no `register` variable has its address taken (the tree builds).

## The gate: `asmdiff.sh` — identical generated code, or an explained diff

`ASMDIFF_BUILD=<configured cmake tree> bash tools/asmdiff.sh
src/game/foo.c [<ref>]` compiles the file at `<ref>` (default `HEAD`) and in the working tree with
the build's exact flags (from `compile_commands.json`) to assembly, normalises `__FILE__`/`__LINE__`
strings, and diffs. Proven both ways 2026-09-22: an untouched `mario.c` → IDENTICAL; one flipped
operator in `math_util.c` → 75 differing lines. Rule: **a patch in the "mechanical" classes must
show IDENTICAL for every file it touches**, recorded in the commit message; a patch in a
"needs-care" class may differ, and then the commit message explains the diff (e.g. a `goto`→loop
rewrite that reorders two basic blocks). The configured tree lives in the sandbox scratchpad
(`cmake -HGhostship -B<dir> -GNinja -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=ON`);
it is not a repo artefact.

## Ground rules (each one came from a finding)

1. **Behaviour-preserving is the hard rule; the gate decides, not "it looks right".**
2. **Never script a class blind.** Every class has a look-alike that is not safe: side-effecting
   `UNUSED` locals (`end_birds_1.inc.c:5` advances the RNG), endianness pads in
   `audio/internal.h:846-857`, angle-wrap `(s16)` casts, `>>` on negatives, `== TRUE` on
   `hoot.inc.c:229`'s flags word. Read every site. (How batches 5 and 7 squared this with a
   tool: the tool only rewrites the one exact shape the reader cleared, carries a SKIP list of
   the read look-alikes, prints REVIEW for anything else, and **the gate runs per file and
   reverts any file that is not IDENTICAL** — so a site the reader missed can only survive if
   the compiler proves it harmless. That is "read every site" with the compiler as the second
   reader, not a substitute for the first.)
3. **One class × one directory per patch** (e.g. "engine: drop `register`", "goddard: delete lone
   `;` needed-to-match"), each reviewable alone, each with a commit message that states the rule
   applied and the gate result. Upstream can then take or leave patches independently.
4. **Delete the matching comment together with the construct it explains**, never leave it
   dangling; keep every `//! @bug` / `//!` note that documents shipped behaviour.
5. **Header prototypes move with parameter renames** (`mario_actions_stationary.h:31`,
   `obj_behaviors.h:67/90/103`, `level_update.h:124-126`, `audio/heap.h:112-131`,
   `audio/load.h:77-104`); a `.c`-only rename compiles and defeats the purpose.
6. **Do not remove `UNUSED` parameters from table-dispatched functions** (`sModeTransitions[]`,
   `GraphNodeFunc`, the level-script `Func` typedef); renaming is fine, removal breaks the ABI.
7. **Never touch `#ifdef VERSION_EU`/`VERSION_SH` regions, `audio/mixer.c` (hand-vectorised
   port code), `game/memory.c`'s byte arithmetic, struct-offset comments, or the `BAD_RETURN`
   macro** (a fidelity decision, not an oversight).
8. **Naming `func_80…`/`D_80…` belongs to `tasks/mario64-decomp-rename-and-cleanup.md`** — skip
   them here even when they sit inside a function being rewritten.
9. The stream is **upstream-first**: it applies before `cheats`/`book` (ORDER), and every
   personal patch that stops applying is rebased onto it — never the other way round.

## Stream design and the replay

- New stream **`n64/SuperMario64/patches/standard-c/`**, listed **first** in `patches/ORDER`
  (before `cheats`, `book`), with the ORDER comment updated to say why (the rewrite stream is
  the upstream-bound base; personal streams sit on top of the code as upstream would see it).
- Checkout branch `imps-standard-c` created at the bare pin `49c5312a`; batches are commits on
  it; export = `git format-patch --no-cover-letter --base=49c5312a 49c5312a..imps-standard-c -o
  patches/standard-c/`. Commit messages are the upstream PR text (reviewer-facing, with the gate
  result).
- After each exported batch: `./fetch.sh` (re-detach at the pin) + `./apply.sh` replays
  `standard-c` → `cheats` → `book` → `upstream-candidates` and the LUS lane; a failure is a
  personal patch to rebase: apply the failing stream with `git am --3way`, resolve, re-export
  that stream. `tools/check_patches_apply.sh SuperMario64` is the family gate for the same thing.
- Full build of the fully-applied tree in the sandbox (`cmake --build <scratch tree>`) after each
  replay; the maintainer's host run remains the behaviour oracle for anything the gate flagged as
  a codegen diff.

## The catalogue

Counts are census hits (`data/SUMMARY.txt`); "live" excludes `VERSION_EU`/`VERSION_SH` regions;
verdicts: **DO** = mechanical, gate-provable, upstream-plausible; **CARE** = do per site with a
stated argument; **LEAVE** = not this task (with the reason). Anchors are `Ghostship/src/…`.

### A. Control flow

| class | hits → real | verdict | what / where / rewrite |
|---|---|---|---|
| `goto` | 60 → 18 live | **DO** (3 shapes) / LEAVE (2) | goto-as-`break`: copt `:321,328,334→l1090`, `:344,348,352→l1138`, `:435,441→l13cc`; `audio/load.c:327→out1`, `:365→out2` (upstream's own EU arm uses `break` there). goto-as-`return`: `behaviors/koopa.inc.c:415→end:;`. Guard inversion: `goddard/gd_math.c:573→590` (skipped body writes only `UNUSED` locals). LEAVE: `game/ingame_menu.c:1190…1211 → skip:` (jumps into `default:`; a real refactor), `audio/synthesis.c:818` (port-authored CODEC_S16 path, 300-line indent churn). |
| labels | 211 → 10 live goto targets | rides with goto | 194 are `default:`; the six `label:;` forms the regex missed are listed in the control-flow report §2. |
| infinite loops | 27 → 8 | **DO** (2) / CARE (1) / LEAVE | `game/print.c:72` (test hoisted into the body → `while ((powBase = int_pow(base, numDigits)) <= (u32) n) numDigits++;`), `game/macro_special_objects.c:277` (+ the empty `if (…== 0xFF) {}` at `:283` → `for` search loop); CARE `behaviors/heave_ho.inc.c:34` (two exits → `for` + `return`). LEAVE the event loops (`main.c:340`, `sound_init.c:350`, `surface_load.c:608`, …) and the deliberate halts. |
| `do {…} while (0)` | 4 | **DO** | `game/camera.c:7189-7192` — four wrappers around single `init_spline_point` calls (function already `// TODO: (Scrub C)`). Leave the duplicated conjunct `:7186` and the outer rotated loop for a follow-up. |
| empty `then` | 10 → 1 live | fold into the loop above | the four `if (1) {}` are SH/EU; the live one is `macro_special_objects.c:283`. |
| `else if (x == k)` ladders | 65 | **DO** (redundant tail ×4, grouped ×1) / CARE (state ladders) / LEAVE (side-effecting) | `menu/intro_geo.c:59,109,404,440` `} else if (state == 1) {` after `if (state != 1)` → `} else {`; `behaviors/spindel.inc.c:49-55` grouped values → stacked `case`s. CARE: action ladders (`express_elevator.inc.c:5-30`, `bowser.inc.c` ×6, …) → `switch` only after proving no arm's write makes a later arm's test true. LEAVE `level_script.c:125` `--sDelayFrames == 0`, `eyerok.inc.c:112`, `rumble_init.c:112`. |
| "nested single-statement if" | 135 → ~0 | re-grep | the regex measured wrapped conditions; real instances: `menu/file_select.c:1704-1706` (two complementary `if`s → `if/else`, **DO**), `goddard/renderer.c:1814-1819` ("the ifs need to be separate to match" → one `&&`, **DO**). |
| matching comments | 41 → 24 | **DO** (2,3,1) / LEAVE (bss/padding) | lone `; // needed to match` ×5 (`goddard/draw_objects.c:658,884,987`, `joints.c:72`, `particles.c:353`); unreachable `break; // needed to match` (`renderer.c:816`); "must be one line to match on -O2" ×8 → braces + one statement per line, deleting the comment and any `// clang-format off/on` fence (`mario_actions_airborne.c:615`, `mario_actions_submerged.c:488`, `camera.c:1759,4497`, `game_init.c:325`, `level_update.c:711`, `math_util.c:174`, `behaviors/fish.inc.c:19` per-case one-liners). LEAVE bss-order/padding comments (`camera.h:649`, `memory.h:40`, `audio/internal.h:285,641`), `BAD_RETURN` (fix only the two stale comments `camera.c:667`, `save_file.c:293` if at all). |
| `AVOID_UB` / `ALIGNED` | 17 → 1 | LEAVE | `audio/seqplayer.c:2676-2686` is a real knob documenting an N64 bug; `ALIGNED8/16` are alignment attributes (noise). |
| `volatile` | 18 → 1 | **DO** (1) / LEAVE (rest) | delete the unreferenced `struct vNote` (`audio/internal.h:673-678`) and reword `synthesis.c:677-679`; every other `volatile` is a live cross-thread flag the port needs *more* than the ROM did. |

### B. Naming residue (compiler-checked renames)

| class | hits → real | verdict | what / where / rewrite |
|---|---|---|---|
| `register` | 106 → 104 | **DO** (per directory) | engine 47 (`math_util.c` 28, `surface_collision.c` 13, `surface_load.c` 6), goddard 56, game 1. Purely textual; drop the `// a0`/`// s1 (78)` register-map comments with it. Gate: IDENTICAL expected everywhere. Propose `engine/` first as the upstream taste-test. |
| stack-slot locals `spNN` | 494 (100% real; ~95% ordinary variables, ~90% nameable from the body) | **DO** in `game/`+`engine/` (285), CARE in goddard (173, keep the `// sp24` trailing-comment convention), LEAVE copt | oracle: upstream already renamed the twin function in-file — `object_collision.c:63-77` (`dx dz collisionRadius distance` from `:26-32`; `aBottomY/bBottomY/aTopY/bTopY`), `object_helpers.c:961-963` (`animFrame`, `nearLoopEnd`), `:199-203` (`relX/Y/Z`), `:167-182` (`roomCase`, `floor`), `behaviors/chuckya.inc.c:83-100` (`target`, `increment`, `reachedTarget`), `bubba.inc.c:16` (`distToHome`). Hot: `goddard/joints.c` 49, `objects.c` 41, `game/object_helpers.c` 31. Also the regex-missed **register-named parameters** `a0/a1/a2/f12/f14`: `object_helpers.c:198,230,943,1015`, `behaviors/bub.inc.c:47`. |
| `temp_*/phi_*` | 61 → 9 live | **DO** (one site) | `audio/heap.c:1498-1556` `phi_s3`/`temp_s2` → `allocStart`/`allocEnd` (the [start,end) of the allocation the loops evict against). The rest is SH/EU or copt. |
| `argN` params | 347 (~154 decls; audio mostly dead) | **DO** in `game/` (52) | `mario_actions_stationary.c:816`+`.h:31` `arg1`→`animation`; `mario_actions_moving.c:1594` `arg2/3/4`→`accelEndFrame`, `playHeavyLandingSound`, `actionArg`; `mario_actions_submerged.c:870`→`actionArg`; `behaviors/king_bobomb.inc.c:46`→`minDistBelow`; `eyerok.inc.c:17`→`maxRelZ`; `obj_behaviors_2.c:341-372` (`animIndex`, `animFrame`, `frame1/2`). Leave `unagi.inc.c:45`, `obj_behaviors_2.c:246`, all `func_sh_*`. |
| `UNUSED` | 1128 (439 params, ~1033 decls of which 375 fillers) | **DO** the 20 side-effecting locals → bare statements; CARE the rest; LEAVE table-dispatched params | `behaviors/end_birds_{1,2}.inc.c:5` `(void) random_float();`, `bowling_ball.inc.c:231` `object_step();`, `snowman.inc.c:81`, `red_coin.inc.c:29` (`find_floor` writes `dummyFloor`). Removable dead locals: `camera.c:927-928,1008-1009,1412,1417`, `object_collision.c:29,66`, `goddard/shape_helper.c:34-46`, `audio/external.c:446`. `object_helpers.c:1205` `UNUSED f32 ny;` is USED at `:1239` — fix the lie. |
| filler fields | 455 → ~385 function-local | **DO** the function-local `UNUSED u8 fillerN[…]` sweep (behaviors, camera, goddard, `surface_load.c:595`, `audio/synthesis.c:513…`); CARE header members; LEAVE layout-fixed | keep: `save_file.h:104` (EEPROM), `types.h:168-186` rawData union, `audio/internal.h:846-857` endianness pads, `audio/heap.h:63`, `goddard/gd_types.h` (offset-commented, raw copied). Removable headers: `surface_collision.h:20-36` (`WallCollisionData`, `FloorGeometry` — producer/consumers verified), `graph_node.h:219,345` trailing pads, `types.h:273` `MarioBodyState` tail. |

### C. Booleans and comparisons

| class | hits → real | verdict | what / where / rewrite |
|---|---|---|---|
| `== TRUE` / `!= FALSE` | 202 → ~201 | **DO** (~180) / CARE (6) / LEAVE (2) | every operand verified 0/1 (see the booleans report §A); hot `menu/file_select.c` 41, `audio/synthesis.c` 18, `seqplayer.c` 17. CARE: `door.inc.c:143/148` asymmetric pair, `obj_behaviors.c:536` double-normalisation, `goddard/debug_utils.c:84,256` double negative, boolean `++` (`tilting_inverted_pyramid.inc.c:112`, `bowser.inc.c:329,372` — reset-before-2 verified), `switch (bool)` `bowser.inc.c:419-435`. **LEAVE `hoot.inc.c:229`** (`oInteractStatus` is a flags word; the `== TRUE` is the guard) and `bowser.inc.c:423` (documented dead). |
| `!= 0` / `== 0` | 1015 | CARE, capped at ~60 | drop only on `:1` bitfields, `bool`, comparison results (`rendering_graph_node.c:166,182`, `surface_collision.c:262,461`); keep counters/timers/indices, enums, error-code returns (`seqplayer.c:2122`), parenthesised mask tests, sentinels (`renderer.c:3025`). |
| `//! @bug` / `TODO` | 430 | mostly LEAVE (shipped-bug docs); comment-only fixes | C1 preserve (`math_util.c` `return &dest` ×14, `object_helpers.c:1246`, `mario_actions_cutscene.c:1108-1114` fallthrough, Surface Cucking, Speed Crash, …). C2 do: `tilting_inverted_pyramid.inc.c:98-109` dead `else`, `goddard/draw_objects.c:458-460` `if (FALSE) {}`. C3 stale: `camera.c:5165` (initialised at `:5067`), `menu/file_select.c:1303`. **`camera.c:7630` "double typo" is C1** — `1.0`→`1.0f` changes codegen. |

### D. Raw memory and numeric

| class | hits → real | verdict | what / where / rewrite |
|---|---|---|---|
| `& 0xFFFF` / `<<16>>16` | 113 → ~10 | **DO** (7) / CARE (2) / LEAVE audio | drop the mask before an `s16` store: `engine/behavior_script.c:90-92`, `object_helpers.c:1878-1880` (implementation-defined wrap either way, identical bits); **`mario_actions_cutscene.c:1922` `<< 16 >> 16` → `(s16)(…)` removes UB** (best hit). CARE `hud.c:327`, `object_helpers.c:805`. LEAVE `mario_actions_cutscene.c:431` (mask is load-bearing), all of `audio/`, `intro_geo.c:380-382`. |
| raw `rawData` indices | 34 → 7 | **DO** | `behaviors/exclamation_box.inc.c:124-125` `asF32[0x37..0x39]` → `oHomeX/Y/Z` (textually identical after preprocessing); `mario_actions_cutscene.c:1845,1857,1881` `asF32[0x22]` → add `oMarioJumboStarCutscenePosZ OBJECT_FIELD_F32(0x22)` beside its siblings (`object_fields.h:158-166`; it is a Z). `object_helpers.c:416-417` `asU32`→`asS32` consistency. LEAVE dynamic-index sites and `tuxie.inc.c:86,100` (known bug). |
| signed shift as arithmetic | 363 → ~8 | **DO** (1 UB fix) / LEAVE | **`behaviors/rotating_platform.inc.c:41` `sp1F << 4` → `sp1F * 16`** (`s8` routinely negative; left shift of a negative is UB; identical bits on every target). `pokey.inc.c:133` `<< 2` → `* 4` (non-negative). **Never `>>` → `/` on a possibly-negative value** (`audio/effects.c:182`, `synthesis.c:1583`). |
| raw byte pointers | 181 → ~10% | thin **DO** / LEAVE | `save_file.c:69/97` make `>> 3` match `/ 8`; `:131/146` operand order `(u8 *) buffer + size - 4`; `object_helpers.c:2236` redundant `(s8 *)` (verify field type). LEAVE allocators/streams (`memory.c`, `level_script.c`, `geo_layout.c`), `(uintptr_t)` for the port API and printing. |
| angle constants | 675 → ~200 angles | CARE (multiples of 5.625° only) | `DEGREES(x)` (`camera.h:27`) truncates; exact iff `x*65536 % 360 == 0`. Safe: `bowser.inc.c:1186,1407,1451` `+ 0x8000`→`DEGREES(180)`, `mario_actions_airborne.c:265`, `moving.c:1038,1816,129,710-711`, `interaction.c:544` `±0x4000`, `wiggler.inc.c:254`, `spiny.inc.c:90`, `object_helpers.c:1712`, `file_select.c` `-0x8000` yaw args (42). Friction: `DEGREES` is scoped to camera code — propose the `macros.h` move as patch #1 of that batch. LEAVE `audio/` (gains, rounding constants), buffer sizes, `camera.c:5090` `0x22AA`. |
| hex magic | 5205 → ~8% | CARE (behaviour-param masks) / LEAVE | add `ACTIVATED_BF_PLAT_BP_*` / `SLIDING_PLATFORM_2_BP_*` masks to `object_constants.h` in the `PLATFORM_ON_TRACK_BP_*` idiom (`activated_bf_plat.inc.c:31,48,56`, `sliding_platform_2.inc.c:15-27`); `object_helpers.c:83` `0x100` → `LAYER_OPAQUE << 8` (verify `LAYER_OPAQUE == 1`). LEAVE offset comments (1191), data tables, definition sites. |
| `(s16)` casts | 197 → ~15% | LEAVE as a class | ~60% are angle-wrap (load-bearing), ~20% float→int truncation; `surface_collision.c:580` is the Parallel-Universes comment — never touch. |
| `(s32)` casts | 516 (305 = `BAD_RETURN`) | CARE (3 lines) / LEAVE | `object_helpers.c:968`, `audio/effects.c:230,232` are promotion no-ops; `goddard/renderer.c:2374` check signedness; `platform_on_track.inc.c:254` changes the result — keep. |
| `(f32)` casts | 230 → ~35% | CARE (prototype-`f32` args) | `hud.c:118`, `ingame_menu.c:1151`, `goddard/objects.c` assignment shape (57); **keep** `behavior_actions.c:225` (`/ (f32) 0x10000` prevents integer division), `koopa.inc.c:606`, `cannon.inc.c:46-47`, `shadow.c:127`. |
| double literals | 1494 → ~35% runtime | **LEAVE** (decomp convention: `//? 0.5f` annotations, `round_float` prose, `US_FLOAT()`) | adding `f` changes results for any non-power-of-two constant; 709 hits are static art data. Optional comment-only patch: extend `//?` to `shadow.c:371`, `file_select.c:463`, `moving_coin.inc.c:128`. |
| `/ const` | 338 → ~11% | **LEAVE** | `x / C` ≡ `x * (1/C)` only for power-of-two `C` (28% of hits), which the compiler already strength-reduces; the other 72% would silently change results. |

### E. Constructs the regexes missed (found by reading; greps in the reports)

Loop exit by sentinel assignment (`audio/external.c:991,2131,2326,1808-1850`; **`:2380` is not a
plain `break` — `i` is read after the loop**), boolean `++`, `switch (bool)`, Yoda/backwards
conditions (`mario_actions_cutscene.c:1127,1552`, `bowser.inc.c:1085`), `a - b < 0` for `a < b`
(`surface_collision.c:504`, flush-to-zero caveat), comma-chained register-order assignment
(`bowser.inc.c:1116` → the form `:442` already uses), mirror-image duplicated blocks
(`camera.c:5081/5110`, `goddard/renderer.c:1748/1774`, `:1375-1419`, `find_floor_from_list`'s
three edge tests — needs a clone detector), redundant guard around an idempotent `|=`
(`camera.c:5084,5113`), return-register temps (`renderer.c:2488`, `surface_collision.c:412`,
`tilting_inverted_pyramid.inc.c:44`), pointer-to-array alias locals, parameters mutated as
scratch (`renderer.c:1722`), `UNUSED` on a used variable (`object_helpers.c:1205`), version
macros as runtime `if` (port pattern — leave), exact `==` on a clamped angle (leave), one slot
reused for two meanings (`external.c:1761` `tempBits`), assignment inside `if`
(`mario_actions_cutscene.c:1488`, `renderer.c:1381`, `object_helpers.c:1239`), statement order
"for matching" (`object_helpers.c:380-381`), `-O2 needs everything on one line` (`spawn_object.c:253`,
`#if IS_64_BIT`-guarded — leave), the `gCosineTable` deliberate overrun (`math_util.h:14-26`,
leave, document), three incompatible `ABS` macros (`camera.h:20`, `gd_macros.h:13`,
`particles.c:466` — unify in a follow-up), duplicated function bodies (`behavior_script.c:85-93`
vs `object_helpers.c:1873-1881`), tolerance tests spelled as casts (`(s32) o->oVelY == 0` —
load-bearing, leave), open-coded `memcpy`/`memset` byte loops (`goddard/renderer.c:1185,2405,2704`,
`objects.c:311-314` — **DO**).

### Out of scope but found: a real bug

`engine/surface_collision.c:509-517` returns `&s` for a function-local `struct Surface s` inside
`if (interpolate)` — a dangling pointer in Ghostship's (port-authored) frame-interpolation path,
dereferenced by callers. Not a decomp artefact; **file it as its own upstream-candidate fix**
(a `static struct Surface sInterpolatedFloor;`, mirrored in `find_ceil_from_list`), not in this
stream. Also worth an upstream issue: the pristine extractor popup loop leaks memory (see the
PaperMario docs) — unrelated to this task.

## Plan

- [x] **Phase A — survey.** Census (`discover.sh`, 34 classes), four parallel verified reads,
      the catalogue above, the patterns reference, the `asmdiff.sh` gate proven both ways. 2026-09-22.
- [x] **Phase B — batches, safest and most valuable first.** Each: commit(s) on `imps-standard-c`,
      gate result in the message, export to `patches/standard-c/`, replay, sandbox build.
      **B.1–B.10 done 2026-09-22: 46 patches, every one codegen-identical.** B.11 (below) is
      NOT done — it is the explained-diff list, held for the maintainer's decision (Progress log,
      "Phase B done").
  1. `register` removal — engine, then goddard, then game (gate: IDENTICAL).
  2. Matching residue: lone `;` ×5, double `break`, `do{}while(0)` ×4, one-line-to-match ×8 (+
     clang-format fences), `struct vNote`.
  3. `goto`→`break`/`return` and the guard inversion (copt ×8 + labels, `load.c` ×2, `koopa`,
     `gd_math`); the two search loops (`print.c`, `macro_special_objects.c` + its empty `if`).
  4. Redundant `else if (state == 1)` ×4, `spindel` stacked cases, `file_select.c:1704` if/else,
     `renderer.c:1814` nested ifs → `&&`.
  5. `== TRUE`/`!= FALSE` sweep (sub-patterns 1-4), per directory.
  6. 16-bit residue: the six `& 0xFFFF` drops, `<< 16 >> 16` → `(s16)`, `sp1F << 4` → `* 16`,
     `pokey << 2` → `* 4`; `save_file.c` `>> 3`/`/ 8` and operand order.
  7. Side-effecting `UNUSED` → bare statements; the `UNUSED f32 ny` lie; dead `UNUSED` locals in
     `camera.c`/`object_collision.c`; function-local fillers sweep (behaviors first).
  8. rawData direct indices → field names (+ the `oMarioJumboStarCutscenePosZ` alias);
     `activated_bf_plat`/`sliding_platform_2` behaviour-param masks in `object_constants.h`;
     `object_helpers.c:83` layer constant.
  9. Naming: `object_collision.c` (twin oracle), `audio/heap.c` `allocStart/End`,
     `obj_behaviors_2.c` + `mario_actions_*` `argN`, register-named params in `object_helpers.c`;
     then `game/` stack-slot locals file by file (gate: IDENTICAL, since renames only).
  10. Open-coded `memcpy`/`memset` loops in goddard; comma-chained assignment; Yoda conditions;
      `bowser` `switch (bool)`; `tilting_inverted_pyramid` dead `else`; `file_select` /
      `bowser` boolean `++`.
  11. CARE items with an explained diff, one per commit: `heave_ho` loop, action ladders →
      `switch` (proof of no forward-arm mutation per site), `DEGREES()` (after the `macros.h`
      move), `!= 0` on verified booleans (~60).
- [x] **Phase C — replay.** `patches/ORDER` = `standard-c`, `cheats`, `book`; `./fetch.sh &&
      ./apply.sh`; rebase and re-export every `cheats`/`book` patch that conflicts (expected:
      `mario.c`, `mario_actions_airborne.c`, and the book's marker files); `tools/check_patches_apply.sh
      SuperMario64`; full build; `tools/check_comment_only_streams.sh SuperMario64` still green for
      `book`. **Done 2026-09-22: no personal patch needed rebasing** (all 51 game-tree + 1 LUS
      patches apply with `--3way` merges only in `math_util.c`, `surface_collision.c`,
      `game_init.c`, `mario.c`); both gates green; full sandbox build — see the Progress log.
- [x] **Phase D — docs + upstream.** `n64/SuperMario64/CLAUDE.md` patch list + stream note;
      `n64/CLAUDE.md` index line; drift table (the new stream is keyed to the pin like any other);
      re-run `discover.sh` and record the delta; file `tasks/mario64-upstream-standard-c.md`
      (PR grouping per directory/class, the maintainer's call) and the dangling-pointer fix task.
      **Done 2026-09-22** (the census delta is in the reference doc's "What the first cut found";
      the two tasks are filed `proposed`).
- [ ] **Maintainer:** host build + play with the full series (the only oracle for any explained
      codegen diff); decide the upstream grouping.

## Progress log

- 2026-09-22 — survey complete; catalogue and reference written; gate proven; `imps-standard-c`
  branch to be created at `49c5312a`; batches begin (entries below as they land).

- 2026-09-22 — **Batch 1 (`register`)**: 3 commits (engine 48, goddard 55 + their register-map
  comments, game 1); every file IDENTICAL. **Batch 2 (matching residue)**: 5 commits — goddard lone
  `;` ×5 + the double `break`; camera `do{}while(0)` ×4 + two same-line sites; game one-liners in 5
  files (fences dropped; `fish.inc.c` gated through `behavior_actions.c`); `mtxf_identity` loops;
  dead `struct vNote`. Every file IDENTICAL. Gate lessons folded into `asmdiff.sh`: pin
  `__LINE__` (Ghostship's `CALL_EVENT` bakes it into an integer argument, so a line shift read as a
  4-line codegen diff) and gate `.inc.c` files through their including TU. Exported as
  `patches/standard-c/0001-0008`; `patches/ORDER` = `standard-c`, `cheats`, `book`; **the replay from
  the bare pin applied all 13 commits + the LUS lane with no conflict** (`./fetch.sh && ./apply.sh`).

- 2026-09-22 — **Batch 3 (`goto` that is a keyword; hoisted-exit loops)**: 5 commits — copt
  `goto l1090/l1138/l13cc` ×8 → `break` + the three ROM-address labels deleted (gated through
  `seqplayer.c`); `load.c` `goto out1/out2` → `break` (the EU arm already said so); `koopa`
  `goto end` → `return`; `gd_math` guard inversion; the two `macro_special_objects.c` preset
  lookups with the test in the header (+ the empty `if (…== 0xFF) {}`). All IDENTICAL. **Dropped:**
  `print.c`'s digit-counter loop (306 differing asm lines — GCC lays the loop out differently; a
  CARE item for Phase B.11 with an explained diff, low value). Gate lesson: the koopa `goto`→`return`
  differed only in compiler-local label numbering, so `asmdiff_normalise.py` now renumbers `.L`
  labels by first appearance and drops unreferenced label definitions (control re-verified).
- 2026-09-22 — **Batch 4 (conditionals)**: 2 commits — `intro_geo.c` `else if (state == 1)` → `else`
  ×4; `renderer.c` three nested ifs → one `&&` (the "need to be separate to match" comment gone).
  IDENTICAL. **Dropped to Phase B.11:** `spindel` ladder → `switch` (GCC emits a jump table, 2560
  lines differ — equivalent, not identical) and `file_select.c` two complementary `if`s → `if/else`
  (493 lines: the compiler must re-read the static between the two `if`s because
  `gSPDisplayList(gDisplayListHead++ …)` could alias it; the rewrite removes the re-read — behaviour-
  preserving by reasoning, not by codegen). Stream now 15 patches, all gate-identical.

- 2026-09-22 — **Batch 5 (`== TRUE` / `!= FALSE` on boolean-valued expressions)**: 3 commits
  (game / goddard / audio), 14 files, 52 sites, via `tools/standard-c/drop_true_false_cmp.py`
  (rewrites only simple operands; `&&`/`||` before the operand allowed, any other binary operator →
  REVIEW). Kept = the files whose codegen came out IDENTICAL, which is exactly the set where every
  operand is a bitfield (`enabled:1`, `finished:1`…), a comparison-valued macro
  (`IS_SEQUENCE_CHANNEL_VALID`, `IS_BANK_LOAD_COMPLETE`) or a `u8`/`s8` the compiler already
  narrowed. `synthesis.c`/`seqplayer.c` also rewrite the same fields inside `#ifdef VERSION_EU`
  arms, which the port does not compile — same rule, same fields, not gate-proven (say so
  upstream). **Deferred to Phase B.11 (40 files, ~130 sites, list in `tasks/adhoc/mario64-assembly-isms/data/batch5_bool_deferred.txt`, formerly the scratch worklog
  `b5_deferred.txt`):** every site whose operand is a plain `s32` object field / global compared
  with TRUE — GCC emits `cmp $1` for `== TRUE` and `test` for the bare operand, so the rewrite is
  behaviour-preserving only via the invariant that the field is only ever assigned 0/1 (true for
  every deferred site the survey read, but codegen differs). 5 REVIEW lines left as-is (multi-line
  operands; `*inDialog`; the two listed SKIPs). Stream re-exported: **18 patches**; full replay
  from the bare pin (standard-c → cheats → book → upstream-candidates) applies cleanly, 23
  commits, standard-c tree byte-identical to the branch
  (`tasks/adhoc/mario64-assembly-isms/batches/sm64_export_and_replay.sh`).

- 2026-09-22 — **Batch 6 (16-bit residue)**: 5 commits, all IDENTICAL — `& 0xFFFF` dropped before
  the `Vec3s` stores in `behavior_script.c` and its `object_helpers.c` twin; `sp1F << 4` → `* 16`
  (rotating_platform, s8 routinely negative → UB gone); pokey `<< 2` → `* 4`; `save_file.c` `>> 3` →
  `/ 8` to match its read twin + `(u8 *) buffer + size - 4` operand order. **Dropped to Phase
  B.11:** `mario_actions_cutscene.c:388,1922` `<< 16 >> 16` → `(s16)(…)` — 5 asm lines differ
  (GCC then knows only the low 16 bits matter and uses `movzwl`/`subl %r14d` instead of two
  `movswl` + `subl`; same low-16 result, so equivalent, and the rewrite removes the UB — the best
  explained-diff candidate). **Skipped:** `object_helpers.c:2236` `(s8 *)` cast — `oToxBoxMovementPattern`
  is `OBJECT_FIELD_VPTR`, the cast is required.
- 2026-09-22 — **Batch 7 (UNUSED residue)**: 9 commits, all IDENTICAL — side-effecting `UNUSED`
  initialisers → bare calls (end_birds ×2, bowling_ball, snowman, red_coin); `UNUSED f32 ny` lie
  fixed; camera.c dead locals (cenDist, unused1/2, unusedScale, the zeroed `Vec3f unused`, three
  bare `unused`, `start`/`end` in reset_camera); object_collision.c `sp30` ×2; goddard
  `shape_helper.c` unreferenced stub anim tables + two `sUnref` arrays; then the **filler sweep**
  (`drop_filler_locals.py`: 321 `UNUSED u8 fillerN[…]` locals in 80 files, per-directory commits
  engine/game/goddard/menu). Only `src/game/main.c` (3 fillers) is left: the N64 boot file is not
  in the port's compile database, so it cannot be gated — leave. Stream: **32 patches**; full
  replay 37 commits, standard-c tree byte-identical.

- 2026-09-22 — **Batch 8 (raw memory + magic)**: 5 commits, all IDENTICAL — exclamation_box
  `rawData.asF32[0x37..0x39]` → `oHomeX/Y/Z`; `oMarioJumboStarCutscenePosZ` added to
  `object_fields.h` and used ×3; `obj_turn_toward_object` `asU32` → `asS32`; `geo_switch_anim_state`
  `0x600`/`0x100` → `LAYER_TRANSPARENT_DECAL << 8` / `LAYER_OPAQUE << 8`; `ACTIVATED_BF_PLAT_BP_*`
  and `SLIDING_PLATFORM_2_BP_*` masks in `object_constants.h` used at the six sites.
- 2026-09-22 — **Batch 9 (naming)**: 4 commits, all IDENTICAL, via
  `tools/standard-c/rename_in_function.py` (whole-word rename scoped to one
  function body or prototype line; fails loudly if a name is absent) — object_collision.c twins
  (`aBottomY/bBottomY/aTopY/bTopY`, hurtbox gets `dx/dz/collisionRadius/distance`); `landing_step`
  (`animation`, + .h), `common_ground_knockback_action` (`accelEndFrame`, `playHeavyLandingSound`,
  `actionArg`), `common_water_knockback_step` (`actionArg`); king_bobomb `minDistBelow`, eyerok
  `maxRelZ`, obj_behaviors_2.c anim wrappers (`animIndex`, `animFrame`, `frame1/2`, `frameStep`),
  bub (`increment`, `parentY`); object_helpers.c register-named params (`transform`/`obj` + relX/Y/Z,
  `dst`/`mtx`/`camMtx` + transX/Y/Z, `minVel`/`mult` + marioVel/minScaledVel, `frames`/animFrame,
  + .h). **Skipped:** `audio/heap.c` `phi_s3`/`temp_s2` — inside `#ifdef VERSION_SH` (1411–1687),
  not compiled, not gateable. **Not done (follow-up, not this stream's first cut):** the ~270
  remaining `spNN` locals in game/engine — each needs a read to name; the tool is ready.
- 2026-09-22 — **Batch 10 (regex-missed constructs)**: 5 commits, all IDENTICAL — tilting pyramid
  `marioOnPlatform++` → `= TRUE` and its unreachable `else` (GCC already folded the `d != 0` test);
  bowser `oBowserIsReacting++` ×2 → `= TRUE`; the two `15 < m->actionTimer++` Yoda tests; goddard
  `if (FALSE) {}`. **Dropped to Phase B.11:** bowser `switch (oBowserIsReacting)` → if/else (3869
  asm lines: the switch's block layout moves the whole TU). **Skipped:** bowser comma-chain
  `:1116` — under `#else` of `BUGFIX_BOWSER_FALLEN_OFF_STAGE`, which is 1 for US, not compiled.
  **Not attempted, by construction B.11:** the goddard memset/memcpy loops (`objects.c:311`,
  `renderer.c:1177,2684,3159`, `joints.c:891`, `dynlist_proc.c copy_bytes`) — the port compiles at
  `-O1`, where GCC does not turn a byte loop into a `memset`/`memcpy` call, so the rewrite always
  changes codegen (a libc call for a loop). Stream: **46 patches**; full replay 51 commits.
- **Phase B done (B.1–B.10).** B.11 = the explained-diff list, every item reverted and recorded
  above: `print.c` digit loop, `spindel` switch, `file_select.c` if/else, 40 files of `== TRUE`
  on s32 fields (`b5_deferred.txt`), cutscene `(s16)` wrap ×2, bowser switch(bool), the memset/
  memcpy loops, `heave_ho`, action ladders, `DEGREES()`, `!= 0`. Each is behaviour-preserving by
  argument, not by codegen; the maintainer's host run is the oracle. Recommend a second stream
  (`standard-c-explained/`) or a tail of this one after the identical set has been reviewed.

- 2026-09-22 — **Phase C (replay) + D (docs)**: `tools/check_patches_apply.sh SuperMario64` — 51
  game-tree patches (46 standard-c + 3 cheats + 1 book + 1 upstream-candidates) + 1 LUS applied
  cleanly from the bare pin; `--3way` fallbacks only (`math_util.c`, `surface_collision.c`,
  `game_init.c`, `mario.c` auto-merged), **no personal patch needed re-export**.
  `tools/check_comment_only_streams.sh SuperMario64` PROVEN for both book lanes. Full sandbox build
  of the fully-applied tree (`cmake --build` in the scratch `gs-build`, 718/719 → Ghostship linked,
  exit 0). Census re-run on the applied tree (delta recorded in the reference doc). Docs:
  `n64/SuperMario64/CLAUDE.md` (stream entry + ORDER rationale), `n64/CLAUDE.md` (stream list,
  index line, three ORDER cases), `tasks/reference/imps/patch-streams-design.md` (third ORDER
  case), `tasks/reference/imps/derived-artifact-drift.md` (re-run the gate at a bump),
  `tasks/reference/mario64/assembly-isms-in-the-decomp.md` ("What the first cut found"). Filed
  `tasks/mario64-upstream-standard-c.md` and `tasks/mario64-surface-collision-dangling-pointer.md`
  (both `proposed`). Checkout left on the fully-applied series (detached, 51 commits — the
  documented default); the stream's own history is branch `imps-standard-c`.

## Notes / decisions

- 2026-09-22 (maintainer) — the rewrite stream applies **before** all personal streams; after
  implementing, replay the others on top and fix any that break. Recorded as Phase C and the
  ORDER change.
- 2026-09-22 (maintainer) — the goal is upstreaming; existing task for the OoT twin and the
  mario64 rename task are kept separate (this task owns pattern classes, that one owns names).
- 2026-09-22 (agent) — `register`/`volatile`/`double literals`/`/ const`/`(s16)` classes rated
  per the semantic rules in the reference doc; three of them are LEAVE as classes because the
  "obvious" rewrite is not behaviour-preserving in general.

## Open questions

1. Upstream grouping: one PR per class (e.g. "drop `register`") or per directory? Recommendation:
   per class-×-directory as the patches are cut, so a maintainer can merge the uncontroversial
   ones first. Not blocking implementation.
2. Keep the `Co-Authored-By: Claude …` trailers on the upstream-bound commits? (Same question as
   `tasks/papermario-upstream-patches.md`; the maintainer's call.) Not blocking.
