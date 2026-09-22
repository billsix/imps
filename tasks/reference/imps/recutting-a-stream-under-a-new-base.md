# Reference: re-cutting a patch stream when a new stream lands UNDER it

> **Provenance:** written 2026-09-23 from the OoT `standard-c` landing (2026-09-22,
> `tasks/ocarina-de-disassemble-ugly-c.md` Phase C), where the 488-patch `personal` rename stream
> had to move on top of 36 new rewrite patches. The maintainer's ruling that made it possible:
> "re-cut … sure. I version control all of these patches, so I will lose nothing" (William
> Emerison Six <billsix@gmail.com>, 2026-09-22). Tooling: `tools/resolve_rename_conflicts.py`,
> `tools/asmdiff_tree.sh` (`tasks/reference/imps/standard-c-tooling.md`).

## The situation

`patches/ORDER` says which stream applies first. When a new stream must go **before** an existing
one (an upstream-bound stream under a personal one, so upstream sees the code the personal patches
are written against), every existing patch that touches the same files has to re-apply on top of
the new base. Small personal streams just re-apply (SM64: 4 patches, `--3way`, no conflicts). A
large mechanical stream — a rename series touching 509 files against 477 rewritten — does not: the
same lines carry both a rename and a rewrite.

"Re-cut" means: regenerate the stream's patches from a replay on the new base, keeping one commit
per original patch (same subjects, same bodies), and prove the final tree is the old final tree
with the new stream's changes applied. The patch files change (SHAs always; content where the
context moved or a conflict was resolved), which is why it needs the maintainer's say-so.

## The method (what the OoT run did)

1. **Reference tree first.** `imps-personal-old` = pin + the OLD series (`git am` the old patch
   files onto the bare pin). Keep it until the review is done; it is the oracle for step 5.
2. **Replay with 3-way merges and diff3 markers** onto the new base branch:
   `git -c merge.conflictStyle=diff3 am --3way patches/<stream>/*.patch`. `--3way` needs the
   pre-image blobs, which the pin provides; diff3 markers keep the BASE side of each conflict,
   which the resolver needs.
3. **Resolve conflicts mechanically** when the stream's patches are *pure* (renames + provenance
   comments): for each conflict block, the answer is OUR side (the new base) with that patch's
   `old -> new` substitutions applied, plus the lines the patch ADDED beside them (its provenance
   comments), and any inline tag the patch appended to a line carried over to our version of that
   line by prefix match. `tools/resolve_rename_conflicts.py <checkout> <patch> <conflicted files…>`
   reads the pairs from the patch body (`  * old -> new`) or subject (`rename old -> new`), prints
   one line per block, and exits non-zero on a block that is not rename+insert (hand it to a
   human). Then `git add` + `GIT_EDITOR=true git am --continue`. OoT: 401 clean, 87 resolved,
   0 by hand; one shape (rename + appended tag on a rewritten line) needed the tool extended
   mid-run, which is the expected way this goes on a new stream — read the first unresolved
   block, teach the tool, resume.
4. **The stream's own gates on the new tree.** For the rename stream: `tools/check_renames.py
   series` (every rename a commit claims is total, no unclaimed renames), `traceable`,
   `declarations`. Whatever invariant the stream has, run its gate here.
5. **The re-cut gate:** every file that differs between the old applied tree and the new one
   must compile to identical assembly — `tools/asmdiff_tree.sh imps-personal-old imps-applied`
   (renamed files via `ASMDIFF_CMD_FROM`). This is what turns "the merge looked right" into "the
   tree is the old tree plus the new stream": renames change no code, the new stream is
   gate-identical by construction, so any diff here is a resolution mistake. OoT: 496/496.
6. **Re-export** with `git format-patch --no-cover-letter --base=<new-base-tip>
   <new-base-tip>..<applied>`; the `base-commit` footer now names the new base, which the drift
   table records (the stream is keyed to that tip, not the pin — at a pin bump, bump the base
   stream first, then re-cut again). `tools/check_patches_apply.sh <project>` from the bare pin,
   then a full build.
7. **Tell the maintainer what changed:** count the patches whose *content* changed (normalise
   away `From <sha>`, `index`, `base-commit`, `prerequisite-patch-id`, `@@` lines and compare —
   OoT: 120 of 488, 87 resolved + 33 context moves) and file the review as a task
   (`tasks/ocarina-review-recut-rename-patches.md` is the worked example).

## Where it does not apply

- A stream whose patches carry **logic** (cheats, fixes) cannot be resolved mechanically; a
  conflict there is a real rebase for a human, one patch at a time.
- If the base stream is later **dropped or reordered**, the re-cut stream's `base-commit` is
  stale; re-cut again. Never edit the exported patch files by hand to "fix" a base.
