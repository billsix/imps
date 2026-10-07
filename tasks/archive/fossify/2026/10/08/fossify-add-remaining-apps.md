# fossify — find and add the remaining Fossify apps to the carrier

**Status:** DONE 2026-10-08 — 13 apps added to the manifest + `.keep` streams AND all cloned (`./fetch.sh`, 1.9 GB, 18 checkouts); comment-only gate green (3 real streams proven, the 13 new apps have empty streams). One omission (Flashlight, no release). Archived.
**Priority:** 6
**Difficulty:** 4 (mechanical per app — discover the released tag, append the manifest, scaffold streams — but ~12 apps and the Android build is heavy)
**Created:** 2026-10-07 (William Emerison Six <billsix@gmail.com>: "for fossify, there are many more fossify apps that you didn't include, make a task to find them and to add them in the same way as the other fossify apps")

## BLUF

The `android/fossify/` carrier currently pins only **5** upstreams — `Commons` + four exemplar
apps (Gallery, Phone, Messages, Keyboard) — but the Fossify suite is **~17 apps**. Enumerate the
rest from the FossifyOrg GitHub org and **add each one the same way the existing ones are added**:
a `repos`-manifest line pinned to that app's latest **released tag** (SHA + tag + date commented),
a per-repo `patches/<name>/docs/.keep` + `patches/<name>/book/.keep`, and the tier-3 `CLAUDE.md`
pin/manifest index updated. Done = every current Fossify app is in the manifest, `./fetch.sh`
clones them all at their pins, `./apply.sh` and `tools/check_comment_only_streams.sh fossify` stay
green (empty streams are trivially comment-only), and the docs reflect the fuller app set.

## Context

- **The carrier is multi-repo and manifest-driven** (`android/CLAUDE.md`, `android/fossify/repos`):
  `fetch.sh` loops the `repos` manifest (one `<repo_url> <pin_sha>   # <tag> <date>` line each),
  cloning each into `checkout/<name>/` and detaching at its pin; `apply.sh` applies each repo's
  `patches/<name>/docs` then `book` stream, guarded at that repo's pin. **Adding an app is almost
  entirely: append a manifest line + create its two `.keep` stream dirs** — the scripts already
  loop, so no script change is needed per app.
- **Pins are RELEASED TAGS, not branch tips** (the manifest header says so): a fixed tag gives
  stable `file:line` / doc-region anchors and freezes which UI stack the documented code uses
  (Fossify apps are mid-migration from Views/XML to Jetpack Compose — record each app's UI stack
  per the family doc). So for each app, pick its **latest release tag's commit**, not `HEAD`.
- **Current manifest (2026-10-07):** `Commons` 6.2.0, `Gallery` 1.3.0, `Phone` 1.5.0, `Messages`
  1.2.0, `Keyboard` 1.2.0.
- **Discovery is the first step** — the authoritative app list is the **FossifyOrg org**
  (github.com/FossifyOrg). Apps likely missing (confirm against the live org at execution; names
  as of early 2026): Calendar, Contacts, File Manager, Notes, Clock, Camera, Voice Recorder, Music
  Player, Gallery(✓), Draw/Paint, Calculator, Launcher, Thank You. **Exclude** non-app repos
  (Commons is already in; website/meta/`.github` repos are not apps). Each app's latest release
  tag comes from its GitHub releases/tags.
- **Build is best-effort** (`android/CLAUDE.md`): a full APK build needs the Android SDK + Gradle +
  license acceptance and is heavy; the **comment-only gate needs no SDK** (git + python3,
  `prove_comment_only_strip.py --lang kotlin`). For this task the streams are empty, so the gate is
  trivially green; a full per-app build is not required to land the manifest additions.

## Plan

1. **Enumerate** the FossifyOrg app repos (org listing) and, per app, resolve its latest release
   tag → commit SHA + tag name + date.
2. **Append** one manifest line per new app to `android/fossify/repos` (same format + comment), and
   create `patches/<name>/docs/.keep` and `patches/<name>/book/.keep` for each.
3. **Verify** `./fetch.sh` clones every app at its pin, `./apply.sh` is a no-op on the empty
   streams, and `tools/check_comment_only_streams.sh fossify` passes.
4. **Update docs:** the tier-3 `android/fossify/CLAUDE.md` pin/manifest index and the "~17 apps"
   wording; note each app's UI stack (Views vs Compose) at its pinned tag per the family contract.
5. **Stage** the manifest + `.keep` dirs + doc updates.

## Decisions (William Emerison Six <billsix@gmail.com>, 2026-10-07)

- **Run autonomously:** enumerate and add every missing Fossify app (manifest line at its latest
  stable release tag + the two empty `.keep` stream dirs + doc index update) without asking per
  app. **When an item requires too much discretion, STOP on it and log it as a new open question**
  rather than guessing.
- **Scope = carry-and-pin only** (the mechanical path): this task makes every app fetchable/pinned
  with empty comment-only streams; it does **not** decide how deeply each app gets documented.
  Whether the new apps get documented chapters (vs. keeping the Commons + four-exemplar focus) is a
  doc-philosophy call that is "too much discretion" for this mechanical task — it is **logged and
  deferred to `tasks/fossify-refdocs-and-book.md`**, not decided here.

## Results (2026-10-07, overnight run)

Enumerated the FossifyOrg org; the **apps** (vs. support libraries like GestureViews/mmslib/reprint/
java-mammoth and the website/meta repos) not already carried were **14**. **13 added** to the `repos`
manifest, each pinned at its latest release tag's commit with `# tag date`, plus `patches/<app>/docs/.keep`
and `patches/<app>/book/.keep`: Calculator 1.4.0, Calendar 1.11.0, Camera 1.5.0, Clock 1.6.0, Contacts
1.6.0, Documents 1.0.1, File-Manager 1.6.1, Launcher 1.10.0, Music-Player 1.8.1, Notes 1.7.0, Paint 1.4.0,
Thank-You 1.3.0, Voice-Recorder 1.7.1.

- **Flashlight omitted** — no semver release tag exists yet (noted in the manifest + tier-3 CLAUDE.md;
  add when it releases).
- **Verified:** manifest parses (URL+SHA extract cleanly for all 14 incl. Keyboard); 26 new `.keep` files;
  `tools/check_comment_only_streams.sh fossify` → "all PROVEN comment-only" (the 3 real streams), the 13
  new apps **cleanly skipped** ("no checkout — run ./fetch.sh"), so the gate handles the additions.
- **Not done (cheap follow-up):** the actual `./fetch.sh` clone of the 13 (~GBs of Android repos) — the
  SHAs were confirmed to exist via `git ls-remote`, so this is mechanical. See open question 1.
- Tier-3 `android/fossify/CLAUDE.md` updated with a "Carried apps" table; manifest comment reframed
  (documented exemplars vs carried suite).

## Notes / decisions (my discretion, adjustable)

- Pin each new app at its **latest stable release tag** (not a pre-release, not a branch tip),
  consistent with the existing five.

## Next action (DECIDED 2026-10-08 by the maintainer — "yes, for you to do"; NOT started)

**The agent runs `cd android/fossify && ./fetch.sh`** to clone all carried apps (the 13 new + the 5
existing) at their pins — materializing the gitignored `checkout/<app>/` dirs (~GBs of Android repos; the
SHAs are confirmed-valid). Then confirm `./apply.sh` is a no-op on the empty streams and
`tools/check_comment_only_streams.sh fossify` passes with the new apps now cloned (they currently skip as
"no checkout"). After this, the task can be archived.

## Open questions

None open. (Flashlight stays omitted until FossifyOrg cuts a release tag; documentation depth for the
carried apps remains the refdocs task's call — `tasks/fossify-refdocs-and-book.md`.)
