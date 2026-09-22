# PaperMario: submit the three patches upstream (PaperBoat ×2, JeodC/libultraship ×1)

**Status:** proposed — needs go-ahead; **deliberately not started** (William Emerison Six
<billsix@gmail.com>, 2026-09-22: "make a task to file those upstream, but we won't do it yet").
**Priority:** 6
**Difficulty:** 3 (the code is done and proven; the work is forks, rebases onto upstream tips,
their formatting/CI, and writing the PRs well)
**Project key:** papermario

## BLUF

The series `n64/PaperMario/` carries (2026-09-22) is upstream-shaped by design: two PaperBoat
fixes (`patches/upstream-candidates/0001`, `0002`) and one libultraship fix
(`patches-libultraship/upstream-candidates/0001`, against the JeodC fork PaperBoat pins). File
them as three PRs — plus, optionally, one issue for a leak found on the way. "Done" = PRs open with
the descriptions below, links recorded here, and the imps patches annotated with their PR URLs;
later, when merged, the patches retire at the next pin bump (patch philosophy: an upstreamed
patch is a patch we stop carrying).

## Context (cold-start)

- Read first: `tasks/reference/papermario/rom-import-investigation.md` (the full account),
  `n64/PaperMario/CLAUDE.md` "Patches", and `tasks/reference/imps/patch-philosophy.md`
  (upstreaming = ultimate goal; standalone, never entangled with personal patches).
- The commits exist in the checkout on branch `imps-work` (game tree) and in
  `PaperBoat/external/libultraship` on its `imps-work` branch; the `.patch` files are the
  canonical copies. Author is the maintainer; each carries a `Co-Authored-By` trailer for the
  agent — keep it or drop it per the maintainer's preference before filing.
- Upstreams: https://github.com/HarbourMasters/PaperBoat (default branch `develop`; the pin is
  the tag `1.0.1`) and https://github.com/JeodC/libultraship, branch **`lus-converge`** (the
  branch PaperBoat's `.gitmodules` pins — NOT Kenix3 mainline; check whether mainline has the
  same code before also filing there).
- Verification that backs the claims: six headless scenarios, 20/20
  (`tasks/adhoc/papermario-rom-import/test_paperboat.sh`), the maintainer's host run
  2026-09-22 (built, played), and the gdb backtraces quoted below.

## What we learned that they need to know (the substance of the PRs)

1. **Vulkan crashes on the first frame on any Linux box with a Vulkan driver.**
   `Fast3dWindow.cpp` does `new GfxRenderingAPIVK()`; the constructor's two parameters
   (`consoleVariable`, `resourceManager`) default to `nullptr` and are stored; the first shader
   build (`BuildVulkanShader → sVKResourceManager->LoadResource`) and the first draw
   (`DrawTriangles → mConsoleVariable->GetInteger(CVAR_Z_FIGHTING_MODE)`) dereference them.
   libultraship registers Vulkan ahead of OpenGL on Linux and picks the front of the list with no
   config, so a fresh install crashes right after ROM extraction. Reproduced on RADV (host) and
   lavapipe (Xvfb); fixed by resolving both through `Ship::Context::GetRawInstance()` when
   nothing was injected — the OpenGL backend already does exactly that. Alternative they may
   prefer: pass the Context's objects at construction in `Fast3dWindow` instead.
2. **A ROM path on the command line is ignored on Linux/macOS.** `RunExtract` collects argv, but
   the transition to `ES_EXTRACT_ARGS` is only reached inside the `#ifdef _WIN32` `ES_WINDOWS`
   branch. One-line fix on the `#else` side.
3. **An unsupported ROM picked in the file dialog fails silently.** `LoadRomFromPath` accepts any
   readable file; Torch logs "No config found" and returns normally; `GenerateOTR` reports success
   with no archive; the user sees the generic "No ROM O2R file detected". Common trigger: a
   padded cart dump (64 MB for the 40 MB game) — the whole-file SHA-1 cannot match. Fix: run the
   same `GetSupportedRomNode` check `RunStandalone` already makes, and show why (size, byte
   order, "trim a padded dump").
4. **(issue, not a PR)** With no archive and no interaction, the extractor's popup loop appears to
   leak: two idle instances reached ~19 GB RSS in 8 hours (2026-09-22). Not investigated beyond
   the observation; worth a report with `ps` numbers so they can look.

## PR text drafts

**PaperBoat PR A — "extractor: honour a ROM path on the command line on Linux/macOS"** (patch
0001). Body: the one-paragraph description from item 2, plus how to reproduce
(`./Paperboat /path/rom.z64` on Linux drops into the prompts instead of extracting) and how it was
verified (headless: `RunStandalone` taken, extraction to `Done`, no prompt before extraction).

**PaperBoat PR B — "extractor: refuse a picked ROM that matches no config.yml recipe"** (patch
0002). Body: item 3, the exact user-visible message it replaces, the popup it adds, and that a
cancel is unchanged. Mention the padded-dump scenario as the motivating case and that the check
mirrors `RunStandalone`. Could be one PR with A; keep two so each is reviewable alone.

**JeodC/libultraship PR — "fast3d/vulkan: do not depend on constructor-injected Context objects"**
(LUS patch 0001), against `lus-converge`. Body: item 1 with both backtraces:

```
Fast::BuildVulkanShader -> Ship::ResourceManager::LoadResource            SIGSEGV
Fast::GfxRenderingAPIVK::DrawTriangles -> Ship::ConsoleVariable::GetInteger  SIGSEGV
```

Environment line: PaperBoat 1.0.1, LUS `7aa03b6c`, Fedora 44, gcc 16.2.1, RADV and lavapipe.
State the alternative fix (inject at construction) and that we chose the OpenGL backend's
existing pattern for symmetry.

## Plan

- [ ] Fork both upstreams under the maintainer's GitHub account; create branches from the
      current `develop` / `lus-converge` tips (not from the pins).
- [ ] `git am` each patch onto its branch; resolve drift if upstream moved; build once against
      upstream tip to make sure the fix still applies (a pin bump of imps is NOT implied).
- [ ] Run their formatter (`run-clang-format.sh` exists in the Torch tree; check PaperBoat's and
      LUS's `.clang-format`); squash any formatting fixups into the patch.
- [ ] Open the three PRs with the drafts above; optionally the leak issue.
- [ ] Record the PR URLs here and as a comment line at the top of each `.patch` file's
      description in `n64/PaperMario/CLAUDE.md`; set this task `blocked` on "upstream merges" with
      a `Recheck:` that looks for the commits in upstream `develop` / `lus-converge`.
- [ ] When merged: at the next pin bump drop the retired patch(es) — the imps patch philosophy.

## Notes / decisions

- 2026-09-22 — filed as a task but not started, at the maintainer's instruction.

## Open questions

1. Keep the `Co-Authored-By: Claude …` trailers on the upstream commits, or strip them before
   filing? (Recommendation: the maintainer's call; either is honest, upstream may have a policy.)
