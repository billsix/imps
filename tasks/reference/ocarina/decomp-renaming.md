# Decomp renaming — method, findings, gotchas (reference)

> **Provenance:** authored 2026-07 against Shipwright `988b53665` (9.2.3-320, the old
> fork base) — 101 commits behind the current imps pin `acdbc651d` (9.2.3-421). Spot-check
> details against the pinned checkout before trusting them.

Durable knowledge from the address-name→meaningful-name effort on the OoT decomp under `soh/src`.
Read this before doing more renaming. The live work record + progress log is
[`tasks/archive/ocarina/2026/09/08/ocarina-decomp-rename-and-cleanup.md`](../../archive/ocarina/2026/09/08/ocarina-decomp-rename-and-cleanup.md); this doc is the *how* and *why*
that outlives any one batch.

## The single biggest lever: zeldaret/oot is the oracle
SoH's decomp is the **zeldaret/oot** decomp at the **same ROM addresses**, so SoH's `func_800A9F30` **is**
oot's function at `0x800A9F30`. oot has named most of the game. Cross-reference online:
- Raw source: `https://raw.githubusercontent.com/zeldaret/oot/main/<path>` (blob form for citing in comments).
- **Match by body + address order**, not by guessing: oot lists functions in address order within a file, so
  align SoH's `func_<addr>` sequence to oot's named sequence and confirm the body matches.
- Path mapping: actors `src/overlays/actors/ovl_X/z_x.c`; core `src/code/*.c`; **audio moved** to
  `src/audio/game/*.c` (general/sfx/sequence), `src/audio/internal/*.c` (thread/playback). When a path 404s,
  web-search the oot function name.
- **BUT oot leaves a LOT of symbols address-named too.** When it does, an LLM/descriptive name is legitimate —
  just mark it as ours (see provenance convention). Roughly ~2/3 of what we hit had no oot name.

## The second oracle: a file's own debug strings

**Before deducing anything in a file, grep it for `osSyncPrintf`.** OoT shipped
with its Japanese debug prints intact, and many of them embed the *original*
function name — so the answer is sitting in the source, not in oot's repo. This
is the strongest evidence short of an upstream name (the function says what it
is called), and it costs one command:

```sh
grep -n osSyncPrintf <file.c>
```

Worked example, `z_en_zl3.c` (2026-09-08): five of the file's 203 symbols were
named outright by their own prints — `En_Zl3_Actor_inFinal_Init`,
`En_Zl3_inFinal_Check_DemoMode`, `En_Zl3_Actor_inFinal2_Init`,
`En_Zl3_inFinal2_Check_DemoMode`, `En_Zl3_Get_path_info` — and those five are the
spine of the file, so naming them first made the surrounding 198 legible. All
five went in as HIGH with the string quoted in the reason.

The prints also disambiguate *structure* even when they do not name a function:
`En_Zl3_inFinal2_Check_DemoMode:そんな動作は無い` sits in the `default:` arm of a
cue switch, which proves the switch dispatches "demo mode" cues and that the
enclosing function is the dispatcher. Read the whole print, not just the
identifier in it.

Caveat: a print can name the function it *calls into* rather than the one it sits
in, and a print in a helper may carry the caller's name. Confirm the body matches
the name before adopting it, exactly as with an oot cross-reference.

## Provenance-comment convention (the maintainer's request)
Every renamed symbol gets a **greppable** comment directly above its definition, in one of two forms:
- `// LLM generated name (HIGH|GUESS), was <addr>: <reason from the code>` — our deduction (oot has no name).
- `// Name from zeldaret/oot <file> (was <addr>): <reason>. [oot: <url>]` — authoritative upstream name.

Audit with `git grep 'LLM generated name' -- soh/src` / `git grep 'Name from zeldaret/oot' -- soh/src`; both
are trivially strippable before upstreaming. Never let both markers land on one line. When a rename is later
confirmed against oot, upgrade the LLM comment to the oot form (swap marker, append the URL).

**The DECLARATION gets a short tag too (William Emerison Six <billsix@gmail.com>, 2026-09-07).** The long
comment above the definition leaves the *declaration* bare — and `soh/include/functions.h` is where a reader
meets a name first, with no way to tell a guess from an upstream name. So every header declaration of a
renamed symbol also carries a one-line inline tag:

```c
void AudioMgr_StopAllSfx(void);                    // was func_800C3C20 [oot]
void Audio_RestorePrevBgm(void);                   // was func_800F5B58 [LLM:HIGH]
extern u8 sAudioResetState;                        // was D_80133418 [LLM:HIGH]
```

`[oot]` = authoritative upstream name; `[LLM:HIGH]` / `[LLM:GUESS]` = ours, with the confidence carried over
from the definition comment. It stays greppable by the same handle (`git grep 'was func_'`), and deliberately
does **not** repeat the prose or the citation URL — those stay at the definition, so the shared headers don't
gain 60-odd long lines.
Gate: `n64/OcarinaOfTime/tools/check_renames.py declarations` reports any header declaration still bare;
`tools/tag_declarations.py` adds the missing ones (idempotent).

**A GUESSED name is tagged at every CALL SITE too — an adopted one is not**
(William Emerison Six <billsix@gmail.com>, 2026-09-07). The marking density tracks the uncertainty:

- **`[oot]`** — upstream's own name, body- or structure-verified. Definition + declaration only. A reader
  meeting it in the middle of a function needs no warning; it is as trustworthy as the rest of the decomp.
- **`[LLM:HIGH]` / `[LLM:GUESS]`** — ours. Tagged at the definition, every declaration, **and every call
  site**, so a reader who encounters the name anywhere knows immediately that it is inferred and can go
  read the reasoning at the definition rather than trusting it:

  ```c
      EnKz_UpdateDialogChoice(this, play);  // [LLM:HIGH] was func_80A9CB18
  ```

  Append to the existing line, never insert a new one (see the rule below), so line counts stay stable.
  This is what makes a wrong guess *findable* — `git grep '\[LLM:'` lists every place the decomp is leaning
  on an inference.

**The tag is always APPENDED to an existing line, never inserted as a new one.** That is load-bearing, not
cosmetic: no file changes its line count, so `__LINE__`/`__FILE__` and every debug print built on them are
untouched, and the preprocessed translation units stay byte-identical. Where the line already ends in a
comment, append after it with a comma (`} RumbleMgr; // size = 0x10E, was UnkRumbleStruct [LLM:HIGH]`).
**Commented-out placeholder declarations** (`// ? Audio_ResetData(?);` in `functions.h`) are skipped — they
are not declarations.

**Never append a tag to a line whose code ends in a backslash.** A `\` at end of line is a macro
continuation, so a trailing `// ...` comments the backslash out and silently truncates the macro. It broke
`z_en_insect.c`'s `EN_INSECT_SHIP_SAVESTATE_FIELDS(F)` list on 2026-09-07 (29 cascading compile errors from
one tag), and nothing in the rename gate can see it — the tagging is correct by every rule the gate checks;
only the compiler notices. Leave such lines untagged; the definition's long provenance comment already
records the rename. `apply_deduced_names.py` enforces this. A `/* ... */` comment *before* the backslash
would also work, but untagged is simpler and the tag adds nothing on a macro field list.

**A multi-line prototype is tagged on the line that CLOSES it, not the line that names it.** In
`functions.h` a long prototype wraps, so the renamed name sits on a first line ending in `,` — appending
`// ...` there comments out the rest of the parameter list. The tag goes on the line ending in `;`:

```c
void EffectSsDust_SpawnDrawFlags0(PlayState* play, Vec3f* pos, Vec3f* velocity, Vec3f* accel,
                   Color_RGBA8* primColor, s16 scale);  // was func_8002829C [LLM:HIGH]
```

The failure this prevents is silent in the opposite direction from the backslash rule: the *build* stays
clean and the gate goes red. `apply_deduced_names.py` defers the tag to the closing line, and
`check_renames.py`'s declarations check accepts it there when the name-bearing line does not end in `;` or
`{`. It bit the 11 `EffectSsDust_Spawn*` prototypes on 2026-09-07, because a wrapped prototype's first line
looks exactly like a definition's opening line — the tagger read it as a definition and skipped the tag
entirely. Header files hold only prototypes, so the tagger now treats *every* top-level match in a `.h` as
a declaration rather than guessing from the line's punctuation.

**A function-pointer declaration hides its name inside parens, and the gate has to
know that.** `check_renames.py` builds its set of renamed symbols by parsing the
declaration under each provenance comment, and the plain rule -- take the
identifier before the first `(` -- returns the RETURN TYPE for
`void (*gAudioCustomUpdateFunc)(void)` and for the array form
`s32 (*sSpot09ObjChecks[])(args)`. That single bad entry poisons the whole set:
with `void` in it, every `void` line in every header reads as an untagged
declaration. On 2026-09-08 it turned five real renames into five false failures,
and the naive fix -- matching only `(*name)` -- then let `s32` through from the
array form and turned five failures into 774. `renames_common._declared_name`
now matches both shapes, subscript included. The lesson generalises: **when the
gate reports failures in files the batch never touched, suspect the symbol set
before suspecting the tags.**

**A short tag IS a citation -- the traceability check has to accept one.** A
static declared inside a function body gets only the short tag; a long
provenance comment in the middle of a body would be noise, and
`apply_deduced_names.py` correctly declines to add one. `check_renames.py`'s
traceability check originally read only long marker comments, so on 2026-09-08
seventeen correctly-tagged function-local statics reported as untraceable. It
now reads the short tag too, exactly as `renames_common.renamed_symbols()`
already did. Both halves of the gate must agree on what counts as provenance.

**TYPE renames follow the same convention.** A struct/typedef rename is not address-named, so the
`git grep 'LLM generated name'` audit cannot see it and it is easy to ship untraceable — `UnkRumbleStruct` →
`RumbleMgr` did exactly that. Tag it like any other rename, on the line that names it (for a typedef, the
closing brace).

## One rename per commit

**A commit renames exactly one symbol — everywhere it appears — and nothing else** (William Emerison Six
<billsix@gmail.com>, 2026-09-07). Most of these names are *guesses*: at the 2026-09-07 split, 141 of 206 were
LLM-deduced because zeldaret/oot leaves the symbol address-named too. A guess that turns out wrong should cost
one `git revert`, not an untangle — which is only true if it has its own commit. The original bulk rename was
one 6,854-line commit across 145 files, unreviewable in a sitting; splitting it gave 225 commits with a median
size of 50 lines.

- Subject `soh: rename <old> -> <new>`; body names the source (`zeldaret/oot`, or the confidence for a
  deduction) and the defining file.
- **File renames are their own commits** (`soh: rename code_800A9F30.c -> z_rumble.c`), and carry any comment
  elsewhere in the tree that cross-referenced the old filename.
- Group symbol commits by defining file so a reviewer stays in one area at a time.
- Never fold two symbols into one commit, even when they are obviously related (the six `Rumble_*` functions
  are six commits).

**The gate is `n64/OcarinaOfTime/tools/check_renames.py`** — `traceable` (every rename cited, none
half-done), `declarations` (every header declaration tagged), `series` (one rename per commit, every rename
total), or `all`. Run it after every batch; a stated rule with no gate rots.

**To prove a reshape changed nothing, run `tools/prove_comment_only.sh`** (imps root):

```sh
tools/prove_comment_only.sh n64/OcarinaOfTime/Shipwright <before-ref> <after-ref>
```

It checks that no file changed line count and then has **gcc itself** strip the comments
(`gcc -fpreprocessed -dD -E -P`) and compares — so the equivalence argument rests on a compiler, not on a
regex in this repo. It is the answer to "how do I know this is safe?" without a full build, and it is also
the gate for a `book/` stream, whose `doc-region` markers are comment-only by contract (pass
`--allow-line-shift` there: a marker must occupy its own line).

The one-shot scripts that performed the 2026-09-07 split (the peel/replay engine and the table builders)
were removed when that task was archived; the **method** they implemented is written up in
[`tasks/reference/imps/splitting-a-patch-series.md`](../imps/splitting-a-patch-series.md), and the code
itself is recoverable from git history
(`git log --diff-filter=A -- tasks/adhoc/ocarina-split-rename-patch/`).

## The safe-rename mechanic
A rename must be **total** (def + every reference) and behavior-preserving. Do NOT rely on a build (the maintainer (William Emerison Six <billsix@gmail.com>)
builds/runs separately; our renames are grep-complete, not build-verified).
- Global word-boundary replace scoped to **`soh/src` + `soh/soh` + `soh/include`** (the last is easy to
  forget — see gotcha). `sed 's/\bOLD\b/NEW/g'` on the files `git grep -lwI OLD` returns.
- **Collision check**: skip if `NEW` already exists as a token (tree-wide for externally-linked funcs).
- **Verify 0 residual** old refs after.
- **File renames**: `git mv`; the build globs `src/*` (`soh/CMakeLists.txt`), so no CMake edit — just verify
  nothing references the old filename (usually only stale cross-reference comments).
- **File-local `static` data**: scope the rename (and its collision check) to the ONE defining file. A generic
  static name (`sColChkInfoInit`, `sTentacleTextures`) legitimately exists in dozens of files with internal
  linkage — a tree-wide collision check false-trips, and a tree-wide rename would hit the wrong file.

## Gotchas that have bitten (check every time)
- **`soh/include/` headers.** `functions.h`/`variables.h` carry `func_/D_` prototypes+externs. If the rename
  scope omits `soh/include`, you leave dangling orphan protos (harmless to link, but an incomplete rename).
  Always include it. (48 symbols were left half-renamed this way until swept.)
- **Savestate `_copy` entanglement.** The C++ port layer's `savestates.cpp` snapshots specific `D_` globals
  into `<name>_copy` fields. `\b` word-boundary does NOT match `NAME_copy` (underscore is a word char), so a
  rename silently half-updates. Grep `savestates.cpp` for the symbol first; if entangled, either rename the
  `_copy` field too or skip + log (we skipped `D_801333F0`, `D_801755D0`).
- **`__OTR__` asset-layer names** (display lists, textures declared in `soh/assets/.../*.h` and looked up by
  path string at runtime) can't be renamed without matching OTRExporter/`.o2r` pipeline edits. Leave
  address-named (e.g. the `z_demo_shd` Bongo-shadow DLs).
- **PC-port symbol clashes.** oot names some things after libc (`func_801067F0` = oot `fmodf` in
  `src/libc/fmodf.c`). Adopting that in a *PC port* clashes with the system libc. Keep the SoH-safe name
  (`Math_FMod`) and note the clash. Same class of caution for anything oot names identically to a platform symbol.
- **SoH-vs-oot naming-era differences.** oot has since renamed whole subsystems SoH predates. Keep SoH's
  in-tree convention rather than half-migrating (which clashes with the file's other names):
  `ElfMessage_*` (oot `QuestHint_*`), `TransitionUnk_*` (oot `TransitionTile_*`), `Opening_*` (oot
  `TitleSetup_*`); filenames `audioMgr.c` (oot `audio_thread_manager.c`), `debug_ctrlr2.c` (oot split into
  `sys_freeze.c` + `sys_debug_controller.c`).
- **Adopting an oot name that clashes with an existing SoH name.** e.g. oot's `Message_StartOcarina` needs
  SoH's *existing* `Message_StartOcarina` (= oot `Message_StartOcarinaImpl`) renamed first — a broad change to
  a widely-called symbol. Defer such multi-step realignments to the maintainer rather than doing them unverified.
  Same shape blocked `TransitionUnk_Start`→`TransitionUnk_Update` (the Update name was already taken).
- **Mirrored-name file pairs.** Two files whose functions map onto the same names can't both be non-static in
  C. The rumble pair resolved via oot: high-level `z_rumble.c` owns bare `Rumble_Update/Init/Destroy`;
  low-level `sys_rumble.c` owns `RumbleMgr_Update/Init/Destroy`.

## SoH adds its own derivatives of an address name — and `ADDR_RE` cannot see them

`renames_common.ADDR_RE` matches `\bfunc_[0-9A-Fa-f]{6,8}\b`, so a symbol whose
name is an address plus a **suffix** does not match: the trailing `_` is a word
character, which kills the closing `\b`. SoH has such symbols, because the port
sometimes forks an upstream function and names the fork after the same address:

- `func_808C1554_Raw` (`z_boss_dodongo.c`) → `BossDodongo_UpdateLavaTextureRaw`
- `func_80AB70A0_nocutscene` (`z_en_niw.c`) → `EnNiw_SetupSwarmNoCutscene`

They are real symbols and they do get renamed, but **any check that derives
"which symbols disappeared" from `ADDR_RE` will never see them go.** So a gate
must not compare its full set of *claimed* old names against an `ADDR_RE`-derived
*observed* set — filter the claimed set through `ADDR_RE` first, and hold the
suffixed names to account some other way (`check_renames.py` uses the totality
scan, which greps for the literal old name and so is unaffected).

This bit the 2026-09-08 squash: the regrouped `series` check reported two false
failures, on exactly these two files, in the two units that happen to contain
both the address-named symbol and its suffixed derivative. The tell is a failure
whose "claimed" list is longer than its "retires" list by precisely the suffixed
names. **A false failure here looks exactly like a dropped rename**, which is why
it is worth recording rather than re-deriving.

## Cross-TU callers to remember (renames ripple here)
Actor funcs are referenced from SoH's C++ enhancement layer (`soh/soh/**.cpp`): the Anchor multiplayer
`HookHandlers.cpp`, randomizer `hook_handlers.cpp`, `BetterSaveMenu.cpp`, `AudioEditor.cpp`, TimeSavers skip
cutscene files, `z_scene_otr.cpp` (`extern "C"` + `OTRfunc_*` wrappers — leave the wrapper name intact). The
rename scope covering `soh/soh` catches these automatically; always keep it in scope.

## Guardrails — OoT has more name-based indirection than SM64

Harvested from the rename task at archive time (2026-09-08). These held for
3,781 renames and still apply to any future work in this decomp; the first
two are the ones that actually catch mistakes.
- **Behavior-preserving is the hard rule.** Renames must be total; readability rewrites must not
  change behavior. When unsure, leave it. Verify by the maintainer's build + in-game check.
- **Check for externally-fixed references before renaming.** OoT wires functions through tables and
  the DMA/overlay system: gamestate `init/destroy` pointers, actor overlay `ActorInit`/`ActorDB`
  entries, function-pointer tables, and possibly `spec`/dmadata/`.s` references. `git grep` the symbol
  across `.c/.h/.s/.inc/.spec` first; if it's referenced from a table or non-C file, update that too
  (or don't rename). Note: SoH replaced the actor overlay table with `ActorDB` (see
  `tasks/reference/ocarina/decomp-map.md`) — actor funcs are referenced from C there.
- **Temporary logging is scaffolding** — track what you add (here + a code comment) and remove it
  before the batch is done.
- **Batch small and reviewable** — one `code_*` file (or a related cluster) per batch. Shipwright's
  build is slow; make each the maintainer-verify count. Log progress below so a later session resumes cold.
- **This is stock SoH** (`bill` == upstream `develop`) — clean renames here are the kind of thing SoH
  upstream accepts, so keep changes tidy/upstreamable, and don't tangle a rename batch with unrelated
  edits.

## Renaming a `code_*.c` FILE — what "update the build system" means
Shipwright compiles the decomp via a **`GLOB_RECURSE src/*.{c,h}`** (`soh/CMakeLists.txt:188`, see
`tasks/reference/ocarina/build-system.md`), so a source file has **no explicit entry in CMake** — a
`git mv soh/src/code/code_XXXX.c soh/src/code/<newname>.c` is picked up automatically **on the next
CMake re-configure** (the glob isn't `CONFIGURE_DEPENDS`, so a bare `--build` won't notice; the maintainer
re-runs cmake). "Update the build system appropriately" therefore means: **`git mv` the file, then
verify nothing references the old name** — `git grep code_XXXX` across `.c/.h/.spec/.inc/.txt` and
CMake (a matching header, an `#include`, a dmadata/spec/linker reference, a per-file property). If a
reference exists, update it in the same change. Most `code_*.c` are standalone TUs with no such
references, so it's usually just the `git mv` + a re-configure.


## The tools that survive the effort

Promoted out of `tasks/adhoc/` on 2026-09-08, when the deduction task archived —
these are the two worth re-running, and the reason each exists:

| tool | answers | when |
| --- | --- | --- |
| `n64/OcarinaOfTime/tools/oot_oracle.py` | "what does upstream call this?" | after a **pin bump** — oot keeps naming symbols, so a newer revision yields free, authoritative names (it produced 770 here) |
| `n64/OcarinaOfTime/tools/remaining_address_names.py` | "is the naming finished?" | after a pin bump, and after any rename batch |
| `n64/OcarinaOfTime/tools/check_renames.py` | "are the conventions held?" | the **gate** — after every batch, before handing the patches over |

**`remaining_address_names.py` reads the CHECKOUT, never a census**, which is
why it replaced the census-driven work-list it grew out of: a census taken at
the start of a task goes stale the moment the tree moves, while the checkout is
the truth. Its output today is 6 rows covering 4 distinct names, all in declared
exclusions — treat that as the baseline, and anything above it as new work.

Two scripts from the same set were deliberately NOT promoted, and the reasons
generalise. `progress.py` measured renames as a fraction of a planned
denominator; after the series was regrouped it counts *commits* instead of
renames and reports 487/13.9% for work that is done — a tool that lies is worse
than no tool. `next_symbols.py` was driven by that same start-of-task census and
is strictly superseded by reading the checkout. Both stay recoverable from git
history; neither is worth maintaining.

## The kept census: `oot-oracle-census.tsv`

`tasks/reference/ocarina/oot-oracle-census.tsv` is the output of
`tools/oot_oracle.py` as it stood when the rename effort finished — 2,982 rows,
one per address-named symbol, recording what zeldaret/oot calls it and how
confident the alignment was:

| verdict | rows | meaning |
| --- | --- | --- |
| `BOTH` | 2,914 | oot leaves it address-named too — no upstream name to adopt |
| `UNSAFE` | 44 | the two function sequences disagreed; position cannot be trusted |
| `MISMATCH` | 13 | aligned, but the bodies differ enough to doubt it |
| `NOFILE` | 10 | oot has no counterpart file at either revision |
| `ADOPT` | 1 | a free upstream name still on the table |

**It is kept as a historical record, not as live input.** Nothing reads it: the
work-list tool it once fed (`next_symbols.py`) was retired in favour of reading
the checkout directly, and `tools/oot_oracle.py` writes a fresh copy beside the
checkout (gitignored) whenever it is re-run.

**When it stops being relevant — the one thing to know:** it is pinned to SoH
commit `acdbc651d4b11e29518442d6875a3ec181414cfc` and to oot revisions `main`
and `fa1ea37d5428c66bf783039117568bc3c5f4b645` (2022-05-31) **as they were on
2026-09-08**. Its `BOTH` verdicts are the perishable part: oot keeps naming
symbols, so a `BOTH` row means "oot had no name *then*", never "oot has no
name". **At the next pin bump, re-run `tools/oot_oracle.py` and treat this file
as superseded** — either replace it with the new output or delete it, but do not
consult it after the pin has moved. The `UNSAFE`/`MISMATCH` rows are the durable
half: they record where positional alignment could not be trusted between the
two decomps, which is a property of the files rather than of a moment.

## Method for a batch (repeatable)
1. Survey: per-file count of un-named `func_` defs; start with files that have the FEWEST (richest context,
   lowest risk). The "1–2 straggler" tier is done; the remaining **~175 files have 3+ un-named funcs each**.
2. Fan out read-only analysis agents (grouped by file) to propose names from body + callers + oot.
3. Apply centrally with the safe-rename mechanic (keeps consistency + the savestate/scope guards in one place).
4. Annotate with the provenance convention.
5. Log the batch + any held/deferred items + questions in the task doc.
6. Hand to the maintainer to build + run (the only real verification).

## Status at this stopping point (2026-07-31, re-measured 2026-09-07)
Done: **18 `code_<addr>.c` files renamed** (`code_800FBCE0.c`, RCP, left alone — oot leaves its 2 funcs
address-named too); **206 symbols renamed** — exactly **64** carrying oot citations and **141** marked LLM
because oot leaves them address-named, plus the `Struct_8016E320` → `SeqRequest` typedef. (The 2026-07-31
note said "65 oot / 141 LLM"; the measured split is 64/141 + 1 typedef. The one **type** rename,
`UnkRumbleStruct` → `RumbleMgr`, carried no comment at all until 2026-09-07.) This covers the `code_` files
plus every file that had only 1–2 un-named funcs. **Remaining: ~3,988 un-named `func_` defs across ~175
denser files, plus the entire de-obfuscation goal (goal 3).**

**2026-09-07:** the single bulk commit was split into **225 one-rename-per-commit patches** and every header
declaration gained a provenance tag (see "One rename per commit" and the declaration-tag rule above). The
tree is unchanged apart from those comments, proven by `verify_series.py`. **Do the remaining ~3,988 this way
from the start** — one symbol per commit, comment at the definition *and* the declaration.

Not archived — this is a live, multi-session task; resume from the survey in
[`tasks/archive/ocarina/2026/09/08/ocarina-decomp-rename-and-cleanup.md`](../../archive/ocarina/2026/09/08/ocarina-decomp-rename-and-cleanup.md).
