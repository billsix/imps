# Assembly-isms in the SM64 decomp (Ghostship): the patterns, why they exist, and which rewrites are actually behaviour-preserving

**Reference document** — for anyone (or any agent) turning mechanically-lifted C back into
standard C in a HarbourMasters port. It names each pattern, says where it comes from, shows the
rewrite, and — the part that matters — states the semantic rule that decides whether that rewrite
changes behaviour. Distilled 2026-09-22 from a full census of Ghostship's decomp directories
(`src/game engine audio goddard menu`, 338 files, 137k lines, pin `49c5312a`) and four verified
reads (`tasks/adhoc/mario64-assembly-isms/`); the work record and the per-site lists are in
`tasks/archive/mario64/2026/09/23/mario64-assembly-isms-to-standard-c.md`. Written by William Emerison Six
<billsix@gmail.com> (agent-assisted). Update in place; re-census at a pin bump. The OoT twin is
`tasks/archive/ocarina/2026/09/23/ocarina-de-disassemble-ugly-c.md`; most rules here transfer.

## Why the code looks like this

The sm64 decomp was written to be **matching**: the C had to compile, with IDO 5.3 at `-O2`, to
the exact bytes of the ROM. Every oddity below is a trace of that goal — a construct chosen not
because it is good C but because it made the register allocator, instruction scheduler or stack
frame line up. A PC port keeps the code but drops the goal: there is no matching build, no IDO,
no fixed stack frame. So the question for each pattern is never "is this ugly" but "**does the
rewrite generate the same behaviour under GCC on this port** — and can I prove it?"

Two build facts frame everything in Ghostship: `VERSION_US=1` (so every `VERSION_EU`/`VERSION_SH`
region is uncompiled text — leave it) and `AVOID_UB=1`; the port compiles the decomp as C with
GCC; upstream's clang-format gate covers only `src/port/`, so the decomp directories keep their
hand style (never reformat them).

## The proof: compile before and after, diff the assembly

`tools/asmdiff.sh <file> [<ref>]` compiles one file at a git ref and
in the working tree with the build's own flags (from `compile_commands.json`) to `.s`,
normalises `__FILE__`/`__LINE__` strings, and diffs. **IDENTICAL** is the strongest possible
statement a syntactic cleanup can make; a **DIFF** is not automatically wrong (a `goto`→loop
rewrite may reschedule two blocks) but must be read and explained. Proven both ways: an
untouched file is identical; one flipped operator differs in 75 lines. Use it on every file a
patch touches, and quote the result in the commit message.

## The patterns

Each: what it is → where it comes from → the rewrite → the rule that makes it safe (or not).

### 1. `goto` where C has a keyword

`goto l1090;` with `l1090:` right after the `switch`'s closing brace; `goto out1;` after a
loop; `goto end;` before the function's final `}`; a `goto` over a body that writes only dead
locals. Origin: the decompiler emitted the branch it saw; ROM-address labels (`l1090` = 0x1090)
are the giveaway. Rewrite: `break;`, `return;`, or invert the guard (`if (run >= 0) { … }`).
**Rule:** safe when the label is the statement control would reach anyway (the first statement
after the loop/switch, or the end of a `void` function) and no statement between the `goto` and
the label runs on the goto path. Upstream's own EU arm of `audio/load.c` uses `break` where US
uses `goto out1` — the equivalence is already asserted in-tree. **Not safe:** a `goto` into the
`default:` arm of the same `switch` (`ingame_menu.c`) — there is no C construct for it short of
hoisting the arm into a function. A label needs `label:;` before `}` pre-C23; deleting it with
its goto is behaviour-free.

### 2. Loops with the exit test hoisted into the body

`while (TRUE) { x = f(i); if (x > n) break; i++; }` ⇒ `while ((x = f(i)) <= n) i++;`. Origin:
the branch was in the middle of the loop in the ROM. **Rule:** safe when the body before the
`break` is side-effect-free or its effects are reproduced in the condition (here `x` still
gets its last value), and the negated comparison is exact (integers; for floats beware NaN,
which compares false both ways). Leave genuine event loops (`for (;;)` with a dispatch `switch`)
and deliberate halts (`while (TRUE) { ; }`) — they are correct C.

### 3. `do { one_call(); } while (0);`, lone `; // needed to match`, `break; break;`, `if (1) {}`

Pure scheduling artefacts: an unconditional back-edge, an empty statement, an unreachable
statement, a constant branch. **Rule:** deleting an empty statement, an unreachable statement,
or a constant-zero loop wrapper with no `break`/`continue` inside cannot change generated code
(the gate shows IDENTICAL). Delete the explaining comment with the construct — a stranded
"needed to match" comment is worse than the construct.

### 4. "This must be one line to match on -O2" (+ `// clang-format off` fences)

A statement crammed onto the `if`/`for` line, sometimes fenced from the formatter. Rewrite: braces
and one statement per line; delete the comment and the fences. **Rule:** whitespace and braces
around a single statement never change semantics; the fences exist only to protect the
one-liner. Column-aligned multi-assignment `case` bodies (`fish.inc.c`) are the same thing:
four independent assignments to distinct locals.

### 5. `else if (x == k)` after `if (x != k)`, and value ladders that are a `switch`

The redundant tail is a one-word fix (`else`). A ladder over one variable and small constants is
a `switch` — **Rule:** only if no arm's assignment can make a *later* arm's test true (a `switch`
evaluates the discriminant once; an `if` ladder re-reads it per arm). `oAction` state machines
that only move forward are fine; an arm that resets or decrements the discriminant is not, and a
condition with a side effect (`--sDelayFrames == 0`) or a compound test can never be a `case`.
Grouped values (`a == 4 || a == 3`) become stacked `case` labels exactly.

### 6. `register`

104 uses, many with the MIPS register in a trailing comment (`register s16 *cbufOff; // a0`).
**Rule:** GCC/Clang ignore `register` for allocation; its only C semantics is forbidding `&x`, and
no `register` variable in the tree has its address taken (it builds). Deleting it, with its
register-map comment, is codegen-identical everywhere. It is also a prerequisite for C++17
(which removed the keyword). Safest, highest-volume patch in the catalogue.

### 7. Names that are registers or stack slots: `sp24`, `temp_v0`, `phi_s3`, `arg0`, `a0`, `f12`

The disassembler's names. ~95% are ordinary well-scoped variables, not scratch; ~90% can be named
from the body alone — often because **upstream already named the twin** (`detect_object_hitbox_overlap`
has `dx dz collisionRadius distance`; `…hurtbox…` still has `sp34 sp2C sp28 sp24`, same
arithmetic). **Rule:** a rename is compiler-checked and codegen-identical (gate IDENTICAL), so
the only risk is a *wrong* name; when the meaning needs a second hop (`obj_spawn_loot_coins`'s
`sp30` → `extraVelY` via `coin.inc.c`), say so in the message; when it cannot be justified,
leave it (goddard) or keep the decomp's own convention: `struct ObjJoint *j; // sp24`. Rename
header prototypes with the definition. `func_80…`/`D_80…` are a different job (the rename task).

### 8. `x == TRUE`, `x != FALSE`, boolean `++`, `switch (bool)`, `(cond) * 16`

**Rule:** `x == TRUE` ⇒ `x` only when `x` is genuinely 0/1 — a `:1` bitfield, a `bool`, the
result of a comparison, or a field every writer sets to `TRUE`/`FALSE` (grep the writers). A
multi-valued `s32` compared with `TRUE` (1) is a value test, not a boolean test: `hoot.inc.c:229`
`if (o->oInteractStatus == TRUE)` guards a flags word (bit 15 is `INT_STATUS_INTERACTED`) and the
decomp annotates it — leave it. `flag++` for `flag = TRUE` is safe only if the variable is reset
before it can reach 2 (verify every path). `switch (b) { case FALSE: … case TRUE: … }` ⇒
`if (!b) … else …` silently loses the "any other value does nothing" arm; say so.

### 9. `!= 0` / `== 0`

Not an assembly-ism per se; drop the comparison only where the operand *reads as a fact* (a
bitfield, a `bool`, a predicate result). Keep it for counters, timers, indices, lengths, enums
whose 0 is a named state, error-code returns (`seq_channel_set_layer() == 0` means success), and
parenthesised mask tests. A blanket sweep makes the code worse, not better.

### 10. Integer width residue: `& 0xFFFF` before an `s16` store, `(x << 16) >> 16`, `(s16)` casts

The MIPS `andi`/`sll`+`sra` sign-extension sequence, spelled in C. **Rules, precisely:**
- Storing an `int` into an `s16` converts modulo 2¹⁶ on every real compiler (implementation-
  defined in C99 6.3.1.3, universally wrapping); a preceding `& 0xFFFF` produces the same bits.
  Dropping it is identical *and* narrows the reliance on implementation-defined behaviour.
- `(x << 16) >> 16` on an `int` that can be negative is **undefined** (left shift of a negative,
  C99 6.5.7p4); `(s16)(x)` gives the same bits on two's-complement targets and is defined.
  Rewriting it removes UB — the best kind of upstream patch.
- **A `(s16)` cast on an angle difference is load-bearing**: `(s16)(a - b) < 0` decides which way
  round the circle is shorter; without the cast the 32-bit difference gives the wrong sign
  across the ±180° seam. ~60% of `(s16)` casts are this. A `(s16)`/`(s32)` cast on a `f32` is
  truncation toward zero — also the point (`o->oFaceAnglePitch += (s16)(vel * k)` truncates the
  addend, not the sum). `(s32) o->oVelY == 0` is a tolerance test (`|v| < 1`) spelled as a cast.
  Never treat casts as a class; prove each one.
- The `& 0xFFFF` in `(m->actionArg & 0xFFFF) == 0` selects the low half of a packed argument —
  load-bearing.

### 11. Shifts as multiply/divide

`s8 v; o->oAngleVelYaw = v << 4;` with `v` routinely negative is **undefined** (left shift of a
negative); `v * 16` is defined and bit-identical on every target, and cannot overflow `int` for
a byte. Do it. **Never rewrite `>>` on a possibly-negative value as `/`:** arithmetic right shift
rounds toward −∞, division toward zero; `-1 >> 8 == -1` but `-1 / 256 == 0`. `vib->curve[i] >> 8`
in the vibrato LFO is audible. `1 << n` flag definitions, RDP 10.2 fixed-point `x << 2`, colour
packing `(r >> 3) << 11`, and sound-ID `<< 16` fields are formats, not arithmetic — leave.

### 12. Division by a float constant

`x / C` and `x * (1/C)` are bit-identical **iff `1/C` is exactly representable, i.e. `C` is a
power of two** (`2, 4, 8, 16, 32, 65536`). For `100.0f`, `3.0f`, `1000.0f` and every other
divisor (72% of the tree's hits) the reciprocal form rounds twice and differs for a substantial
fraction of inputs. The power-of-two cases are the ones the compiler already strength-reduces.
Net: this class is not worth a patch, and the unsafe rewrite would silently change results.

### 13. Double literals (`0.5` without `f`) in `f32` code

`v *= 0.8` promotes to double, multiplies, rounds once on store; `v *= 0.8f` rounds `0.8` to float
first, then multiplies — two different results. The decomp *chose* the double where the ROM did:
59 `//? 0.8f` annotations in goddard, a prose note in `geo_misc.c:69` (`round_float`), and the
`US_FLOAT()` macro for version-conditional literals. Adding `f` is a behaviour change and argues
against three in-tree conventions; 709 of 1494 hits are static art data anyway. Storing a literal
into an `f32`, and dividing by an exactly-representable constant, are the only no-op cases. If
anything, extend the `//?` annotation to un-annotated runtime sites.

### 14. `(f32)` casts

`(f32) i / 100.0f` — redundant (the `f` literal already forces float). `animAccel / (f32) 0x10000`
— **load-bearing** (prevents integer division). `(f32)((t / 2 & 1) - 0.5) * 2` — a
double→float narrowing at a specific point. A cast on an argument to a prototype that already
declares `f32` is a provable no-op (`guTranslate`); everything else needs the whole expression
read for an integer-division or double-narrowing trap.

### 15. `UNUSED`, stack padding, struct fillers

`UNUSED` (`__attribute__((unused))`) marks dead parameters and locals; `UNUSED u8 filler[8];` in a
function body reproduces the original stack frame (~385 of 455 filler hits are these — no layout
contract in a PC port; delete). **Rules:** keep an `UNUSED` parameter when the function's address
is taken (dispatch tables such as `sModeTransitions[]`, `GraphNodeFunc`, the level-script `Func`
typedef) — rename it if you like, never remove it; **keep an `UNUSED` local whose initializer has
side effects**, rewriting it to a bare statement instead (`UNUSED f32 sp30 = random_float();`
advances the RNG; `UNUSED s16 collisionFlags = object_step();` *is* the physics update — twenty
such lines tree-wide, the one genuine behaviour trap in this catalogue); keep a struct filler
when the layout is externally fixed — overlays ROM data, is written to a save/EEPROM image
(`save_file.h:104`), is memcpy'd/DMA'd/checksummed, is a union arm addressed by index
(`struct Object` `rawData`), or positions a byte for endianness (`audio/internal.h:846-857`).
`goddard/gd_types.h` fillers carry absolute-offset comments and goddard copies structs bytewise:
leave. An `UNUSED` on a variable that *is* used (`object_helpers.c:1205 ny`) is a lie — fix it.

### 16. Raw `rawData` indices and magic numbers

`o->rawData.asF32[0x37]` where `object_fields.h` already defines `oHomeX` for `0x37`: substitute
— textually identical after preprocessing. Where no alias exists (`asF32[0x22]` in the jumbo-star
cutscene), add one beside its siblings in the file's own style. Dynamic indices
(`asS32[angleIndex]`) and the `tuxie.inc.c` value-as-index bug are not this. Behaviour-parameter
masks (`0x0300`, `0x007F`) next to files that already use `PLATFORM_ON_TRACK_BP_*` from
`object_constants.h`: add the names in the same idiom. Struct-offset comments (`/* 0x1F4 */`),
data tables and `#define` sites are the desired end state, not the problem; they dominate the raw
hex census (5205 hits, ~8% real).

### 17. Angle constants and `DEGREES()`

`DEGREES(x) = x * 0x10000 / 360` (`camera.h:27`) is integer division: exact iff `x * 65536` is
divisible by 360, i.e. `x` a multiple of 5.625°. `0x8000`→`DEGREES(180)`, `0x4000`→`DEGREES(90)`,
`0x2000`→`DEGREES(45)` are exact; `0x22AA` is not any `DEGREES()`. In `audio/`, `0x8000` is a
gain of −100% and `0x4000` a rounding constant — never angles. `DEGREES` is scoped to camera code
by its own comment; spraying it across behaviours draws "move it to `macros.h` first".

### 18. `volatile`

Eleven `volatile` globals in `audio/` are cross-thread flags (`gAudioLoadLock`,
`gAudioResetStatus`) that the port needs *more* than the ROM did — a modern compiler hoists the
load out of a poll loop without it. The one dead one is `struct vNote` (`audio/internal.h:673`),
referenced nowhere; its comment in `synthesis.c:677` describes a workaround that no longer exists.

### 19. The decomp's own bug annotations (`//! @bug`, `//!`)

Roughly a third of the 430 `TODO`/`FIXME`/`//!` lines document **shipped behaviour that speedruns
and the game's feel depend on**: Surface Cucking (`surface_collision.c:521`), the Parallel
Universes `(s16)` cast (`:580`), the `atan2s` unbounded table read (`math_util.c:710`), `return
&dest` ×14 (bracketed by a pragma), cell-border wall misses, the Speed Crash, the key-cutscene
`//! fallthrough` that plays three sounds. These are not a work list. The zero-risk subset is
comment-only: stale notes such as `camera.c:5165` "returning uninitialized variable" (it is
initialised at `:5067`). And note `camera.c:7630` "another double typo" — "fixing" `1.0` to
`1.0f` changes codegen (§13).

### 20. Shapes no regex finds

Loop exit by sentinel assignment (`i = size; // break` — and `stop_background_music` *reads* `i`
after the loop, so a plain `break` would move an out-of-bounds write), mirror-image duplicated
blocks (camera L/R, goddard per-resource init, three cross-product edge tests), Yoda conditions
(`-0.5f < n`), `a - b < 0` for `a < b` (exact except under flush-to-zero), comma-chained
assignment in register order (`o->oPosZ = 0.0f, o->oPosX = o->oPosZ;`), return-register temps,
one slot reused for two meanings (`tempBits`), assignment inside `if`, "ordering of
instructions" comments, the deliberate `gCosineTable` overrun (`math_util.h:14-26`), three
incompatible `ABS` macros, byte-copy loops that are `memcpy`. The greps and a clone-detector
suggestion are in `tasks/adhoc/mario64-assembly-isms/reports/booleans-comments-whole-functions.md`.

## How to run a batch

(The gate, the tree gate and the per-class tools are in `tools/` since 2026-09-23 — usage and the
lessons baked into them: `tasks/reference/imps/standard-c-tooling.md`.)

1. Pick one class × one directory. Read every site (the `data/` log is the worklist; the
   reports' verdicts are the triage).
2. Edit on the `imps-standard-c` branch (bare pin + earlier batches), matching the file's hand
   style; delete the explaining comment with the construct; keep `//!` bug notes.
3. `asmdiff.sh` every touched file. IDENTICAL → commit with the rule and the result in the
   message; a diff → read it, and either explain it in the message or drop the change.
4. Export the stream, replay all streams from the bare pin (`./fetch.sh && ./apply.sh`; ORDER puts
   `standard-c` first), rebase any personal patch that conflicts, build.
5. Hand the maintainer anything with an explained diff for the in-game check; everything
   IDENTICAL needs no play-test.

## Upstream posture

Ghostship restructures the decomp freely (hooks→events, port layers), so cleanups that read as
"less MIPS, same code" are plausible; the argument is strongest for UB removals (`<< 16 >> 16`,
`s8 << 4`), keyword deletions (`register`), and finishing renames upstream started. It is weakest
for anything a reviewer can read as taste (`!= 0` sweeps, `DEGREES` in behaviours) and
nonexistent for anything that changes bits (double literals, reciprocals, `>>`→`/`). Send small
per-class patches with the gate result quoted; never bundle a personal change.

## What the first cut found (2026-09-22, 46 patches, all codegen-identical)

The batch loop above ran once over the whole catalogue (task: `tasks/archive/mario64/2026/09/23/mario64-assembly-isms-to-standard-c.md`,
progress log per batch). What the gate taught, beyond the per-pattern rules above:

- **The identical/differing line falls exactly where the compiler's knowledge ends.** `x == TRUE`
  → `x` is identical when `x` is a bitfield, a comparison, or a `u8`; on a plain `s32` field GCC
  emits `cmp $1` vs `test` — the same program under the "only ever 0/1" invariant, different
  bytes. 14 files went in, 40 stayed out. The same split hit `(a - b) << 16 >> 16` → `(s16)(a - b)`
  (GCC then uses `movzwl` because only the low half matters) and `switch (bool)` → `if/else`
  (block layout). So "assembly-identical" is a *stricter* bar than "behaviour-identical", which
  is precisely why the identical set needs no play-test and the rest does.
- **Optimisation level is part of the gate's context.** The port compiles at `-O1`, where GCC does
  not turn a byte loop into `memset`/`memcpy` (that is `-ftree-loop-distribute-patterns`, `-O2`+),
  so every open-coded copy loop → libc-call rewrite differs by construction. Check the flags in
  `compile_commands.json` before promising a class will gate clean.
- **Uncompiled regions cannot be proven, only argued.** `VERSION_EU`/`VERSION_SH` arms, the
  `#else` of a `BUGFIX_*` that is 1 for US, `src/game/main.c` (not in the compile database):
  a gate on them is trivially IDENTICAL and therefore meaningless. Either leave them, or say in
  the commit message that the same rule was applied by hand there.
- **Two rewrites the reader expected to differ came out identical:** the tilting pyramid's
  unreachable `else` (GCC had already proved `d != 0` from `dy = 500`), and `marioOnPlatform++`
  → `= TRUE` (constant-folded from the `= FALSE` initialiser). Let the gate decide; do not
  pre-sort by intuition.
- **The OoT twin (Ship of Harkinian, same day, 36 patches) confirmed the rules and added three**
  (`tasks/archive/ocarina/2026/09/23/ocarina-de-disassemble-ugly-c.md`): (1) a rename stream that must sit ON TOP of the
  rewrites can be re-cut mechanically — `git am --3way` with diff3 markers, and each conflict
  block resolved as *our side + that patch's `old -> new` substitutions + its added provenance
  lines* (`tools/resolve_rename_conflicts.py`; 87 of 488 patches,
  zero hand edits) — and then proven by compiling every file that differs between the old applied
  tree and the new one (496/496 identical); (2) files the series renames lose their compile
  command — gate them with the old path's command (`ASMDIFF_CMD_FROM`); (3) a batch tool that
  edits in place and then misreports its own count leaves ungated edits behind — the next group's
  gate showed "impossible" diffs for comment-only changes, which is how it was caught. Rule: a
  sweep parses one unambiguous summary line, and every batch starts from `git status` clean.
  At `-O2`, OoT's `if (c) return true; return false;` → `return c;` still differed (`setcc` vs a
  branch pair), and a `goto` to the very next statement still anchored a basic block (418-line
  layout diff) — both explained-diff items, neither identical.
- **Census delta** (`discover.sh`, before → after): `register` 106 → 2, `UNUSED` 1128 → 786,
  filler fields 455 → 134, `== TRUE`-family 202 → 150, `goto` 60 → 48, matching comments 41 → 25,
  `do{}while(0)` 4 → 0, argN 347 → 320, stack-slot names 494 → 470. The big remaining bodies are
  the stack-slot locals (~470, each needs a read to name — `rename_in_function.py` is the tool)
  and the explained-diff list.
