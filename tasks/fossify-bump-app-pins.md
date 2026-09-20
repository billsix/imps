# Fossify — bump the exemplar app pins (Gallery/Phone) so they build

**Status:** proposed — needs go-ahead. Filed 2026-09-20 (William Emerison Six <billsix@gmail.com>) as the
follow-up surfaced by [fossify-jdk-toolchain-and-gradle-offline.md](fossify-jdk-toolchain-and-gradle-offline.md).
**Priority:** 6
**Difficulty:** 4

## BLUF

The two documented **exemplar apps** — **Gallery 1.3.0** and **Phone 1.5.0** — do **not build at their
pinned tags**, so they can't be Gradle-compiled (for the offline cache warm) or verified. The cause is
**upstream JitPack/Bintray rot**, not our JDK/offline work: each depends on an *old published*
`org.fossify:commons` artifact JitPack can no longer serve. This blocks (a) offline-warming the apps and
(b) any Phase-B per-app doc chapter that needs to reference a building app. Fix by moving each app off the
dead dependency. "Done" = Gallery and Phone each compile (online, then offline via the baked cache) at a
chosen pin. **Commons is unaffected** — it builds and is offline-verified — so this is not on the critical
path; it only gates the per-app work.

## What's actually broken (diagnosed 2026-09-20, during the offline task)

Both fail **online AND offline** at their released tags:
- **Gallery 1.3.0** → depends on published `org.fossify:commons:3dd1f7f33e` → transitive
  `com.github.duolingo:rtl-viewpager:940f12724f`, whose own JitPack build fails because it needs
  `gradle-bintray-plugin` from the **shut-down `jcenter.bintray.com`** → permanent 404 (confirmed via
  JitPack's build.log).
- **Phone 1.5.0** → depends on published `org.fossify:commons:3.0.3`, which **404s** on JitPack (both
  `.pom` and `.aar`).

Warming can't cache what won't resolve anywhere, so this is upstream rot to route around, not a gap in the
image. Detail: `android/fossify/CLAUDE.md` ("Build status") and the offline task's Outcome.

## Options
- **(A) Bump each app to a newer released tag** whose published-`commons` dependency still resolves on
  JitPack (or which no longer pulls the dead `rtl-viewpager`). Simplest; keeps the "pin a released tag"
  convention. Cost: the doc patches (KDoc) may need re-anchoring if the newer tag moved the code, and the
  UI stack may have shifted further toward Compose. Re-verify the comment-only streams still apply.
- **(B) Substitute the locally-checked-out `Commons` for the published artifact** (Gradle
  `includeBuild`/composite build, or a `dependencySubstitution` in `settings.gradle`) so each app builds
  against `checkout/Commons` instead of JitPack's dead artifact. Keeps the pins as-is; matches the
  multi-repo carrier spirit (we already have Commons checked out). Cost: a build-config shim per app (and
  Gallery's `rtl-viewpager` is a *separate* dead dep, so substitution alone may not save Gallery — its
  transitive rot is outside Commons).
- **(C) Leave the apps un-built / thinly documented from source only.** Commons is the documentation centre
  of gravity; the apps are thin exemplars. The reference set + book can quote app source without compiling
  it (the comment-only gate needs no build). Cheapest; loses the "apps compile offline" property.

**Recommendation:** (B) for **Phone** (its only rot is the published Commons, which substitution fixes),
and (A) for **Gallery** (its `rtl-viewpager` rot is transitive and outside Commons, so it needs a tag with
a different viewpager dep) — or (C) for both if the per-app build isn't worth the churn. Decide per app.

## Plan (once an option is chosen)
1. Pick the approach per app; if (A), find the newest tag that builds and update the `repos` manifest pin
   (+ re-verify/rebase the `patches/<app>/docs/` stream onto the new pin, and re-run the comment-only gate).
2. If (B), add the composite-build/substitution shim and document it.
3. Add the app(s) to `entrypoint/warm-gradle-cache.sh` (they're already attempted best-effort) and confirm
   the offline export test builds them under `--network=none`.
4. Update `android/fossify/CLAUDE.md` "Build status" (drop them from the "don't build" list).

## Open questions
1. Which approach per app — (A) bump, (B) substitute local Commons, or (C) don't build? (Rec above.)
2. If (A): acceptable that a newer tag may have more Compose migration and need doc-patch re-anchoring?

## Related
- Surfaced by: [fossify-jdk-toolchain-and-gradle-offline.md](fossify-jdk-toolchain-and-gradle-offline.md)
  (DONE for Commons). Carrier: `android/fossify/` (`CLAUDE.md`, `repos`, `entrypoint/warm-gradle-cache.sh`).
- Umbrella: [fossify-refdocs-and-book.md](fossify-refdocs-and-book.md) — Phase B per-app chapters depend on
  this.
