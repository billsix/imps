# fossify — find and add the remaining Fossify apps to the carrier

**Status:** proposed — needs go-ahead (filed 2026-10-07 at the maintainer's request).
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

## Notes / decisions (my discretion, adjustable)

- Pin each new app at its **latest stable release tag** (not a pre-release, not a branch tip),
  consistent with the existing five.

## Open questions

None at filing — scope is decided (carry-and-pin only; documentation depth deferred to the fossify
refdocs task). New open questions get appended here during the work for any app that needs a call.
