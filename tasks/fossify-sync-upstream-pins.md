# Fossify — synced the eleven out-of-date pins with their newest release tags

**Done 2026-11-26** (agent; go-ahead William Emerison Six <billsix@gmail.com>, 2026-11-26: "their own job, make a task", then "go ahead and work"). The maintainer committed the work the same day.

## What was done

Eleven of the eighteen repos in `android/fossify/repos` were behind their newest release tag. Each pin was moved to that tag, the comment-only doc patches were replayed where a repo carries any, and the carrier was proven to fetch, apply and build.

| Repo | Old tag | New tag | New pin | Patches | Result |
|---|---|---|---|---|---|
| Commons | 6.2.0 | 7.1.3 | `227e7d3c` | 5 (docs) | replayed with no conflict |
| Gallery | 1.3.0 | 1.14.3 | `b286bf52` | 1 (docs) | replayed with no conflict |
| Phone | 1.5.0 | 1.11.1 | `7de52a31` | 1 (docs) | replayed with no conflict |
| Messages | 1.2.0 | 1.10.3 | `60f3557b` | 0 | pin moved |
| Keyboard | 1.2.0 | 1.9.1 | `1a2ecdff` | 0 | pin moved |
| Calendar | 1.11.0 | 1.12.2 | `0a936ec8` | 0 | pin moved |
| Documents | 1.0.1 | 1.2.2 | `1f5a0d7e` | 0 | pin moved |
| File-Manager | 1.6.1 | 1.6.5 | `8425ad35` | 0 | pin moved |
| Music-Player | 1.8.1 | 1.8.6 | `ac9c8913` | 0 | pin moved |
| Thank-You | 1.3.0 | 1.4.2 | `2bd82e51` | 0 | pin moved |
| Voice-Recorder | 1.7.1 | 1.7.5 | `f544aca2` | 0 | pin moved |

Calculator, Camera, Clock, Contacts, Launcher, Notes and Paint were already at their newest tag.

## Decisions, in the order they were made (William Emerison Six <billsix@gmail.com>, 2026-11-26)

1. **Its own job, not part of the third upstream sweep.** The recon in `tasks/imps-check-upstreams-and-rebase-patches.md` found the eleven repos behind; the agent recommended a separate task because five documented apps had moved many releases, and the maintainer agreed.
2. **The pin target stayed "newest release tag"**, never a branch tip, as `android/fossify/repos` already required; this was not reopened.
3. **If Gallery and Phone built at their newest tags, `tasks/fossify-bump-app-pins.md` would be closed** ("sure"). They did, so it was.
4. **A doc patch that no longer applied would be rewritten against the new code, not dropped** ("a"). No patch needed it.
5. The order was Commons first (every app depends on it), then Gallery and Phone, then the eight repos with empty streams. In practice one script run moved all eleven.

## Checks

- **Replay:** all seven doc patches applied with `git am --3way` and no conflict, even across Commons 6 → 7. The regenerated patch files differ from the old ones only in hashes, so no patch was rewritten or dropped (the decision recorded for a patch that no longer applies was not needed).
- **Apply and comment-only gate:** `make -C android/fossify fetch apply` from the new pins, then `make -C android/fossify check-comment-only`: 3 streams, all proven comment-only.
- **Image and online build:** `make -C android/fossify image` (nested) warmed the Gradle cache at the new pins: `BUILD SUCCESSFUL` for Commons (`:commons:compileReleaseKotlin`), Gallery and Phone (`:app:compileFossReleaseKotlin`).
- **Offline build:** each of the three then compiled with the doc patches applied under `--network=none` (`./gradlew --no-daemon --offline`), `BUILD SUCCESSFUL` for all three.
- **Not repeated at these pins:** the image export/import roundtrip of 2026-09-20.

## Consequences

- **Gallery and Phone build now.** At their old tags they depended on published Commons artifacts JitPack no longer serves; the new tags depend on published Commons 7.1.3 and 6.1.0, which resolve. That closes `tasks/fossify-bump-app-pins.md` (its option (A), applied to both apps), as decided on 2026-11-26.
- **Toolchains at the new pins:** Commons Gradle 9.7.0 / AGP 9.3.1; Gallery Gradle 9.5.1 / AGP 9.2.1; Phone Gradle 8.13 / AGP 8.11.1; all three compileSdk 36 and JDK 17. The image needed no change.
- **UI stack:** Gallery 1.14.3 still has no Compose sources, so its entry in the pins table ("mostly classic Views/XML") stands; Phone, Messages and Keyboard were not re-examined beyond a search that found no `setContent {` call.

## Where things are

- Manifest: `android/fossify/repos`. Pins tables, toolchain note and "Build status": `android/fossify/CLAUDE.md`.
- Script: `tasks/adhoc/fossify-sync-upstream-pins/sync_pins.sh` (moves every pin to its newest tag, replaying a docs stream first; idempotent, a second run reports every repo current). It is reusable for the next sync; the maintainer approved promoting it to `tools/` at archive time.
- Umbrella still open: `tasks/fossify-refdocs-and-book.md`. Its per-app chapters can now reference apps that build.
