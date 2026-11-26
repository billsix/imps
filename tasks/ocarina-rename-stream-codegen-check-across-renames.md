# OcarinaOfTime — built a codegen check that works across the rename stream

**Done 2026-11-26** (agent; William Emerison Six <billsix@gmail.com>, 2026-11-26: "your recommendation is fine", then "do the ocarina rename check task").

## The problem

The master `CLAUDE.md` asked for two codegen checks at an OcarinaOfTime pin bump. The second was "prove the rename re-cut changed no code — `asmdiff_tree.sh <new-standard-c-tip> <re-cut-tip>`". Run for the first time during the third upstream sweep, at pin `64df9cb8`, it reported 457 files, 17 identical, 411 "differ", 29 skipped, and none of the 411 was a finding:

- `tools/asmdiff.sh` compiles the working-tree file and the old ref's copy of it inside one tree. For 259 files the old source did not compile, because it calls the old names and the tree's headers declare only the new ones.
- For the 152 that compiled on both sides, every renamed symbol was a difference (`func_80002384` against `Assert_Fail`, and so on).

The re-cut method in `tasks/reference/imps/recutting-a-stream-under-a-new-base.md` had never hit this, because it compares the old applied tree with the new applied tree, and both carry the renames. That comparison is only valid on the same base; at a pin bump the base moves.

## Decision (William Emerison Six <billsix@gmail.com>, 2026-11-26)

Of three options — (a) a rename-aware comparison across two worktrees, (b) a per-patch check, (c) dropping the codegen check for conflict-free replays — the maintainer took the agent's recommendation, (a). Until it existed, a conflict-free replay plus `check_renames.py all` stood in.

## What was built

`tools/asmdiff_across_renames.py`. For every `.c` and `.cpp` file of the game's own tree that differs between two refs, it compiles each side in its own temporary worktree (old source with old headers, new source with new headers) with the file's recorded compile command, normalises both with `tools/asmdiff_normalise.py`, rewrites the identifiers in the old side's assembly with the stream's rename pairs, and compares. The pairs are read from the patch bodies through `tools/resolve_rename_conflicts.py`'s `renames_of`, with chains followed to the final name. The checkout is not touched, and the worktrees are removed afterwards.

Things that came up while building it, in order:

1. **The recorded command names its own source as `-c`'s value.** The first run failed every file with "cannot specify -o with -c, -S or -E with multiple files"; `-c` is now dropped together with its value.
2. **Three short renamed files were not paired by git.** `code_800A9F30.c`, `code_800C3C20.c` and `code_800D31A0.c` fell under git's rename-similarity threshold and showed as a deletion and an addition each. They are now paired through the file renames the stream declares (`  * old.c -> new.c` in patch 0001).
3. **The first green run covered only `.c` files under `soh/src`**, as `asmdiff_tree.sh` does. The stream also touches 32 C++ files (call sites in `soh/soh/`), 23 headers and two `.inc` data files. The scope was widened to every `.c` and `.cpp` under `soh/`.
4. **The C++ files then differed in one line each**, a `__FILE__` string holding the temporary worktree's path, which the normaliser does not canonicalise for C++ paths. The tool replaces the worktree root with a constant in both outputs.

## Result at pin `64df9cb8`

`standard-c` tip against the rename tip: **487 files, 479 identical (455 C, 32 C++), 0 differing, 0 errors, 8 skipped.** The 8 are libultra files the port does not build; nothing includes them and they are not in `compile_commands.json`. The two `.inc` files the stream touches are covered through `z_camera.c` and `z_onepointdemo.c`, which both changed and were compared.

So the rename stream is proven to change no code at this pin, which closes the second codegen check that had been open since the stream was first re-cut onto a moved base (2026-10-20).

## Proof that the check can fail

Run with the C files only, before the scope was widened (the comparison logic did not change afterwards):

- **One flipped operator.** A throwaway commit on top of the rename tip changed `(actor->bgCheckFlags & 1)` to `|` in `soh/src/code/z_actor.c`. The tool reported a DIFF in exactly that file and 445 identical.
- **Rename pairs withheld.** Pointed at an empty patch directory, it reported 421 files differing and 22 identical, which shows the identical verdicts depend on the rename map and are not vacuous.

## Limits

- Only translation units are compiled. An included file is covered only through a unit that itself changed; SuperMario64's `*.inc.c` files would need `tools/asmdiff.sh`'s includer handling added before the tool is used there.
- A rename inside a string whose length the assembly records would show as a DIFF. None occurred.
- The checkout's submodules must be at the commits the refs expect, since include paths for submodules keep pointing at the checkout.

## Where things are

- The tool: `tools/asmdiff_across_renames.py` (ruff-clean). Usage, what it needs, and these limits: `tasks/reference/imps/standard-c-tooling.md`.
- `CLAUDE.md` (the asmdiff note) and `tasks/reference/imps/replaying-a-series-onto-a-new-pin.md` now name this tool for check (2). The result is recorded in `n64/OcarinaOfTime/CLAUDE.md` and `n64/CLAUDE.md`.
