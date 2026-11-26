# Fossify — sync the eleven out-of-date pins with their newest release tags

**Status:** ready — decisions recorded 2026-11-26; starts on the maintainer's word (recon done, no pin moved)
**Priority:** 6
**Difficulty:** 5 (seven comment-only patches to replay, but the three documented repos that carry them moved many releases, so their KDoc anchors will have shifted)
**Created:** 2026-11-26 (William Emerison Six <billsix@gmail.com>, on whether the fossify bumps belong in the third upstream sweep: "their own job, make a task").

## BLUF

Eleven of the eighteen Fossify repos in `android/fossify/repos` are pinned behind their newest release tag. This task moves each of those pins to the newest tag, replays the comment-only doc patches where a repo carries any, and proves the carrier still fetches, applies and (for Commons) builds. Done means the manifest and `android/fossify/CLAUDE.md` carry the new tags, `make -C android/fossify check-comment-only` is green, and the build status of Commons, Gallery and Phone at the new pins is recorded.

## Context

**Read first:** `android/fossify/CLAUDE.md` (manifest, pins table, doc streams, "Build status"), `android/CLAUDE.md` (the docs-only, multi-repo carrier contract) and `CLAUDE.md`, "Staying current with upstream" (what "sync" and "rebase" mean; the agent stages, the maintainer commits; imps is never configured unsigned). The recon that produced the table below is the "Recon 2026-11-26" section of `tasks/imps-check-upstreams-and-rebase-patches.md`; the third sweep recorded there leaves fossify out.

**How the carrier pins.** Each line of `android/fossify/repos` is `<url> <pin sha>  # <tag> <date>`. A pin is a released tag's commit, never a branch tip, because the doc patches and later the book's doc-region spans anchor on it. `fetch.sh` clones each repo into `checkout/<name>/`; `apply.sh` applies `patches/<name>/docs` then `patches/<name>/book` with `git am --3way`.

**The eleven behind** (recon 2026-11-26: `git ls-remote --tags`, version-sorted, pre-releases excluded):

| Repo | Pinned tag | Newest tag | Patches carried | Work |
|---|---|---|---|---|
| Commons | 6.2.0 | 7.1.3 | 5 (docs) | rebase; a major version, and every app depends on it |
| Gallery | 1.3.0 | 1.14.3 | 1 (docs) | rebase; does not build at the current pin |
| Phone | 1.5.0 | 1.11.1 | 1 (docs) | rebase; does not build at the current pin |
| Messages | 1.2.0 | 1.10.3 | 0 | sync |
| Keyboard | 1.2.0 | 1.9.1 | 0 | sync |
| Calendar | 1.11.0 | 1.12.2 | 0 | sync |
| Documents | 1.0.1 | 1.2.2 | 0 | sync |
| File-Manager | 1.6.1 | 1.6.5 | 0 | sync |
| Music-Player | 1.8.1 | 1.8.6 | 0 | sync |
| Thank-You | 1.3.0 | 1.4.2 | 0 | sync |
| Voice-Recorder | 1.7.1 | 1.7.5 | 0 | sync |

**Current (pin is the newest tag):** Calculator, Camera, Clock, Contacts, Launcher, Notes, Paint. The newest tags above were read on 2026-11-26; re-read them when the work starts.

**Where the risk is.**

- **Commons 6 → 7.** The five KDoc patches document Commons classes (`BaseConfig` among them, per `android/fossify/CLAUDE.md`). A major release may have moved, renamed or rewritten them toward Compose. A patch whose target was rewritten is re-anchored by hand or dropped, and the choice is logged here.
- **Gallery and Phone do not build at their current pins** (dead JitPack artifacts; `tasks/fossify-bump-app-pins.md` has the diagnosis and three options). Moving them to the newest tag is that task's option (A) for both. Whether the newest tags build is unknown until tried.
- **The UI stack column** in the pins table (`android/fossify/CLAUDE.md`) records Views or Compose per documented repo. Gallery moving eleven minor releases probably changes its entry.
- **The offline Gradle cache.** The image bakes a cache warmed for Commons 6.2.0 (`android/fossify/entrypoint/warm-gradle-cache.sh`). Commons 7.1.3 needs its dependencies warmed, which means an image rebuild (about 4 GB) before `make build` works offline again.

**Open tasks this touches:** `tasks/fossify-bump-app-pins.md` (Gallery and Phone builds) and `tasks/fossify-refdocs-and-book.md` (the umbrella; its per-app chapters want building apps and stable anchors, so this sync is better done before more documentation is written against the old pins).

## Plan

Order: Commons first (the apps depend on it), then Gallery and Phone, then the eight repos with empty streams.

- [ ] Re-read the newest tag of each of the eighteen repos; update the table if any moved.
- [ ] Per repo with patches (Commons, Gallery, Phone): on a branch at the new tag in a scratch clone, `git am --3way` the `docs` stream; re-anchor or drop what fails, logging each case; regenerate the series into `android/fossify/patches/<repo>/docs/`.
- [ ] Update each moved repo's line in `android/fossify/repos` (SHA, tag, date).
- [ ] `make -C android/fossify fetch apply` from clean checkouts, then `make -C android/fossify check-comment-only`.
- [ ] Rebuild the image so the Gradle cache is warmed at the new Commons, then `make -C android/fossify build` for Commons, offline.
- [ ] Try Gallery and Phone at their new tags, online then offline; record the result here and in `tasks/fossify-bump-app-pins.md`.
- [ ] Refresh `android/fossify/CLAUDE.md`: both pins tables, the UI stack notes, the descriptions of the doc patches if any changed, and "Build status".
- [ ] Stage each repo's bump as its own unit; the maintainer commits.

## Decisions (William Emerison Six <billsix@gmail.com>, 2026-11-26)

- **If Gallery and Phone build at their newest tags, `tasks/fossify-bump-app-pins.md` is closed** (its option
  (A), applied to both apps): rewrite it as a done-record and archive it with this task's work. If either
  does not build, that task stays open with the new diagnosis.
- **A doc patch that no longer applies is rewritten against the new code**, not dropped. Each rewrite is
  logged here. If the documented class no longer exists at all, there is nothing to rewrite against: log it
  here and in `tasks/fossify-refdocs-and-book.md`.

## Open questions

None.
