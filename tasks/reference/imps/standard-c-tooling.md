# Reference: the `standard-c` tooling — the codegen gate and the per-class rewrite tools

> **Provenance:** promoted 2026-09-23 from the two task-scoped adhoc kits
> (`tasks/adhoc/mario64-assembly-isms/`, `tasks/adhoc/ocarina-assembly-isms/`) after the SM64 and
> OoT `standard-c` streams landed (William Emerison Six <billsix@gmail.com>: "if any are worthwhile
> to keep around after this task is done, go ahead and promote them now"). This doc is the map of
> what lives in `tools/` for that work and how to run it against any project in the N64 family.
> The patterns themselves and the semantic rules: `tasks/reference/mario64/assembly-isms-in-the-decomp.md`;
> the OoT-specific findings: `tasks/reference/ocarina/assembly-isms-in-soh.md`.

## The invariant the tools serve

A `standard-c` stream rewrites a decomp's assembly-isms (matching hacks, `register`, stack-slot
names, `== TRUE`, stack padding, …) into standard C, and **every patch in it is proven by the
compiler**: each touched file compiles to byte-identical assembly before and after, with the
port's own flags. Anything that does not gate identical is not in the stream (it goes to a
per-project explained-diff task). The tools below make that provable and repeatable.

## `tools/asmdiff.sh` — the gate (one file, working tree vs a git ref)

```sh
ASMDIFF_PROJECT=SuperMario64|OcarinaOfTime  ASMDIFF_BUILD=<configured cmake tree> \
  bash tools/asmdiff.sh <path under the checkout> [<ref>=HEAD]
```

- **What it does:** looks the file's compile command up in `$ASMDIFF_BUILD/compile_commands.json`
  (configure with `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON`, same build type the project ships — Release
  `-O2` for SoH, Release for Ghostship; a Debug tree makes every rewrite differ), compiles the
  version at `<ref>` and the working-tree version to assembly, normalises
  (`tools/asmdiff_normalise.py`: drops `.file`/`.ident`, canonicalises `__FILE__` strings and
  line numbers, deletes unreferenced local labels, renumbers `.L*`/`.LFB*`/`.LFE*`/`.LC*` by first
  appearance), and diffs. Prints `IDENTICAL codegen: …` or `CODEGEN DIFFERS: … — N changed asm
  lines; first hunk:` and exits 0 / 3.
- `__LINE__` is pinned to 0 for both compiles (port macros bake it into integers), so an edit
  that only shifts lines is not a diff.
- **Included files** (`*.inc.c`, SM64): every translation unit that `#include`s the file is
  compiled with the old version swapped in at the real path, then restored (also on any exit).
- **Renamed files:** `ASMDIFF_CMD_FROM=<old path>` takes the compile command recorded for another
  file (the flags are the same for every decomp TU) — needed when a later stream renames files the
  build tree was configured with.
- **Project presets:** `SuperMario64` → checkout `Ghostship/`, sources `src/`; `OcarinaOfTime` →
  `Shipwright/`, `soh/src/`. Adding a project = one `case` arm.
- **Prove it both ways before trusting it on a new project or build tree:** an untouched file
  must say IDENTICAL, and one flipped operator (`&` → `|`) must say DIFFERS (SM64: 75 lines on
  `math_util.c`; SoH: 199 lines on `z_actor.c`). Re-run the pair after any change to the
  normaliser.

## `tools/asmdiff_tree.sh` — the gate over every file that differs between two refs

```sh
ASMDIFF_PROJECT=… ASMDIFF_BUILD=… bash tools/asmdiff_tree.sh <ref-old> <ref-new>
```

Checks out `<ref-new>`, lists the `.c` files under the sources that differ from `<ref-old>`, gates
each against `<ref-old>`, and prints `N files, I identical, D differ, S skipped` plus a
`DIFF/SKIP/GONE/NEW` log. Two uses: the **stream gate** (`<pin> <stream-branch>`: the whole stream
re-proven file by file — OoT 486/486) and the **re-cut gate** (`<old-applied> <new-applied>` after a
personal stream is re-cut under `standard-c` — OoT 478/478 plus the 18 renamed files via
`ASMDIFF_CMD_FROM`). Files the build does not compile are skipped and listed — they cannot be
gated, so the rule is "leave them alone".

## `tools/standard-c/` — the per-class rewrite tools

Each edits files in place, prints every change, is idempotent, and rewrites **only the one exact
shape the survey cleared**, printing `REVIEW` / `SKIP` for anything else; the gate then runs per
file and reverts whatever is not IDENTICAL. That pairing — the narrow tool as first reader, the
compiler as second — is how a class of hundreds of sites is swept without reading each one twice.

| tool | class | notes |
|---|---|---|
| `drop_register.py [--strip-regmap-comments]` | `register` storage class (+ the `// a0` map comments) | refuses a line where `register` is not at declaration start |
| `drop_true_false_cmp.py` | `E == TRUE/true`, `!= FALSE/false`, and the negations | simple operands only; SKIP list for the read look-alikes (flags words, value tests, SoH lines); `&&`/`\|\|` before the operand allowed, other operators → REVIEW |
| `drop_filler_locals.py` | SM64 `UNUSED u8 fillerN[…];` function-local padding | never structs |
| `drop_pad_locals.py <checkout> <worklist>` | OoT `s32 pad;` function-local padding | driven by a per-function worklist (`path:line:decl [function]`), located by function + text so line numbers may rot |
| `drop_empty_if.py` | `if (<pure read>) {}` (one- and two-line forms), no `else` | condition must have no call/assignment/`++` |
| `fold_return_bool.py` | `if (c) return true; return false;` → `return c;` | only comparison/logic conditions; at `-O2` these still differed on SoH — explained-diff material |
| `flip_yoda.py` | `LITERAL op EXPR` → `EXPR op' LITERAL` | simple right operand only |
| `merge_nested_ifs.py [--min-depth N]` | `if (A) { if (B) { if (C) {…}}}` → `if (A && B && C)` | each inner `if` the sole statement, no `else` |
| `rename_in_function.py <file> <func> old=new …` | stack-slot locals / `argN` / register-named params, scoped to one function or prototype line | whole-word, fails loudly if a name is absent |

Run a class as: tool over the candidate files → `asmdiff.sh` per file → keep IDENTICAL, `git
checkout --` the rest → one commit per class × directory with the rule and the gate result in the
message. The batch runners that did exactly this for the two projects are kept as one-shot records
under `tasks/adhoc/<slug>/batches/` (relative paths; they need `ASMDIFF_BUILD` and write their
logs to `ASMDIFF_WORK` or a temp dir). **Two lessons baked into them:** every batch starts from
`git status` clean, and a sweep parses exactly one unambiguous summary line from the tool (a
mis-parsed count once left ~70 files edited but ungated — caught by the next gate, never
committed).

## `tools/resolve_rename_conflicts.py` — re-cutting a rename stream under a new base

Used when a stream that must sit UNDER a pure-rename stream lands (OoT: `standard-c` under the
488-patch `personal`). Method and gates: `tasks/reference/imps/recutting-a-stream-under-a-new-base.md`.

## Adding a project

1. Configure a scratch tree with the project's shipped build type and
   `-DCMAKE_EXPORT_COMPILE_COMMANDS=ON`; note which sources have no compile command (OoT: 117 of
   804 — `libultra/`, `dmadata/`, `elf_message/`).
2. Add the preset arm to `tools/asmdiff.sh`; prove the gate both ways.
3. Census with a copy of `tasks/adhoc/<slug>/discover.sh`; read (fan out readers per directory);
   catalogue in the task doc; then batches, safest class first.
