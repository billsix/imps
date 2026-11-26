# Reference: replaying a patch series onto a new pin

> **Provenance:** written 2026-11-26 from the third upstream sweep (MajorasMask, BanjoKazooie, dash, ripgrep
> and OcarinaOfTime bumped; SuperMario64 stopped), logged in
> `tasks/imps-check-upstreams-and-rebase-patches.md` ("Sweep three"). Requested by William Emerison Six
> <billsix@gmail.com>, 2026-11-26, so the lessons outlive the task. The operation itself is defined in
> `CLAUDE.md` ("Pin bumps are a defined operation"); this doc is what that paragraph does not say.

## The shape of a replay

In the project's checkout: fetch the new upstream commit, make a scratch branch on it, `git am --3way` each
stream in the order `apply.sh` uses, resolve what conflicts, regenerate each stream's patch files, set
`PIN_SHA`, then run the gates. Change nothing in imps until every stream has replayed: a half-bumped project
(new pin, old patches) fails `tools/check_patches_apply.sh` for the next person.

## A conflicted hunk is resolved by reading it, never by fuzz

`git am --3way` is the only automatic step. Do not retry a conflicted hunk with `patch -F3` (or any fuzz) on
code.

What happened: SuperMario64's `cheats` patches conflicted in `src/port/mods/PortEnhancements.cpp`, a file
upstream had reorganised. Fuzz found three matching context lines and applied the hunk there, which put a
block of `REGISTER_LISTENER` calls inside another listener's lambda, before its closing `});`. `patch`
reported success. The result would not have compiled, and nothing in the replay said so.

Fuzz gave the right answer once in the same sweep, in the `standard-c` stream, where upstream had changed the
single line above a line the patch deleted. That is the only case it is safe for, and a hand resolution of
that case takes a minute. So:

- Read the conflict. Decide what upstream changed and what the patch wants.
- If upstream reorganised the file, the patch needs a port, which is a judgment call: stop and log it
  (`CLAUDE.md`, "Staying current with upstream"), as SuperMario64 was
  (`tasks/archive/mario64/2026/11/26/mario64-bump-pin-port-cheats-to-feature-registry.md`).
- After any hand resolution in code, compile the file (a configured tree is enough; see below) before
  regenerating the patch.

## The ci-appimage patch conflicts whenever upstream edits near the block it deletes

Every port's `upstreamable-ci-appimage` patch deletes the inline dependency-install steps of the Linux job in
`.github/workflows/main.yml` and replaces the build step. Any upstream edit inside or directly beside that
block conflicts. In one sweep: MajorasMask (upstream added `-qq` and `--quiet` to those steps), BanjoKazooie
(upstream added a "Fetch commit history" step directly above them) and SuperMario64.

The resolution is the same each time: keep upstream's edits outside the deleted block, and let the deletion
stand. Then check whether upstream changed what the block installs (package list, from-source library
versions), because the patch's `docker/Dockerfile` reproduces it
(`tasks/reference/imps/derived-artifact-drift.md`).

`git merge-file --theirs` on the three index stages (`:1:`, `:2:`, `:3:`) takes the patch's side for the
conflicting hunk and keeps upstream's non-conflicting edits elsewhere in the file, which is the wanted
result when the conflict is "upstream edited lines the patch deletes". When upstream *added* lines beside the
block, keep them by hand.

## Regenerating: file names, stale files, footers

- **A regenerated patch gets its file name from its subject.** When the subject is unchanged the new file
  overwrites the old one. When a subject changed, the old file stays beside the new one, and `git am` then
  applies the old file and finds the new one "already applied". SuperMario64's `book` stream carried two
  files for one patch this way from 2026-10-08 until it was found on 2026-11-26. After regenerating, compare
  the file count with the commit count (`git rev-list --count`) and `git rm` any file that no commit
  produced.
- **Count patches from commits, not files.** For the same reason, a recon that counts `*.patch` files can
  overstate a stream.
- **An upstreamable unit is generated from a branch on the bare pin** (`git format-patch --base=<pin>
  <pin>..<branch>`), so it carries a `base-commit` footer and no `prerequisite-patch-id` lines. Generating it
  from its position in the stacked series adds one prerequisite line per commit beneath it.
- **A stream that stacks on another** (OcarinaOfTime's rename stream on `standard-c`) is generated with the
  lower stream's tip as `--base`, as `tasks/reference/imps/recutting-a-stream-under-a-new-base.md` says.
- **Most regenerated files differ only in hashes.** To report what really changed, compare old and new after
  dropping the `From <sha>`, `index`, `base-commit`, `prerequisite-patch-id` and `@@` lines. OcarinaOfTime,
  2026-11-26: 527 files regenerated, 21 changed in content.

## The gates, and what each one needs

The last gate is a clean build at the new pin, made by the agent (`CLAUDE.md`, "Every sync or rebase ends
with a clean build"). The table lists the checks that come before it.

| Gate | Needs | Notes |
|---|---|---|
| `tools/check_patches_apply.sh <Project>` | the checkout, with the new pin fetched | resets the checkout and runs the real `apply.sh`; also the way to put the checkout back on the full series after any experiment |
| `tools/check_upstreamable_applies.sh <Project>` | the same | leaves the checkout on unit branches; run `check_patches_apply.sh` afterwards |
| `tools/check_comment_only_streams.sh <project>` | git and python3 (gcc for C) | for `docs`/`book` streams |
| `n64/OcarinaOfTime/tools/check_renames.py all` | the checkout on the applied series | "every rename is total" also proves no reference new at the pin still uses an old name |
| `tools/asmdiff_tree.sh <pin> <standard-c tip>` | a **configured** cmake tree | see below |

**The assembly gate needs its tree configured at the commit being checked.** `tools/asmdiff_tree.sh` skips
any file that is not in the tree's `compile_commands.json`. A tree configured with OcarinaOfTime's rename
stream applied does not list the eight address-named files that stream renames, so the gate reported "478
identical, 8 skipped" and exited 0. Configured with the checkout at the `standard-c` tip, it covered all 486.
Read the skipped count; a green exit with skips is not the whole proof.

**The tree gate also skips every included file.** A `*.inc.c` file has no compile command of its own, so
`tools/asmdiff_tree.sh` logs it as `SKIP (not compiled)`. `tools/asmdiff.sh` does handle included files (it
recompiles every translation unit that includes one), so run it on each skipped file:
`bash tools/asmdiff.sh <file> <pin>`. SuperMario64, 2026-11-26: the tree gate covered 47 of 104 files; the
other 57 were `*.inc.c` and were proven one by one.

**A sandbox-only configure is enough and is quick.** `cmake -S <checkout> -B <a directory outside the
project> -GNinja -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=ON` took about 70 seconds for
Shipwright and needs no build. Never configure into the bind-mounted `build-cmake/` (`CLAUDE.md`, the asmdiff
note). The gate itself then compiles each changed file twice (the run for OcarinaOfTime's
486 files was not timed).

**The rename stream has no codegen gate at a pin bump yet.** Comparing the `standard-c` tip with the rename
tip cannot pass, because the renamed symbols differ by design:
`tasks/ocarina-rename-stream-codegen-check-across-renames.md`.

## What moves with the pin

After the replay, before staging (the full table is `tasks/reference/imps/derived-artifact-drift.md`):

- **Submodule gitlinks.** Compare `<old>:libultraship` with `<new>:libultraship` (and Torch). When one moved,
  run the project's `fetch.sh` so the submodules follow, and read `.gitmodules`: BanjoKazooie's libultraship
  changed from Kenix3's repository to the JeodC fork in this sweep.
- **A pin recorded twice.** ripgrep's pin is in `fetch.sh` and in the Dockerfile's `RIPGREP_PIN`.
- **Toolchain floors.** ripgrep 16.0.0 raised `rust-version` from 1.85 to 1.96; a docs-only bump can still
  outdate the image.
- **The prose.** The pin comment in `fetch.sh`, the project's `CLAUDE.md`, the family index in
  `n64/CLAUDE.md`, and any README that names a tag (ripgrep's README named a tag two bumps old).

## Scripts from the sweep

`tasks/adhoc/imps-third-sweep/` holds the scripts this sweep used (independent streams, stacked streams, a
docs stream, the rename re-cut loop). They are candidates for `tools/`. The SuperMario64 bump that followed
the sweep was done by hand and with a one-shot port script, not with them. The fuzz-retry script written during the sweep was deleted on purpose.
