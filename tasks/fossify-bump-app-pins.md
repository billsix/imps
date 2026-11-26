# Fossify — bumped the exemplar app pins (Gallery/Phone) so they build

**Done 2026-11-26.** Filed 2026-09-20 (William Emerison Six <billsix@gmail.com>) as the follow-up to `tasks/archive/imps/2026/09/20/fossify-jdk-toolchain-and-gradle-offline.md`. Closed by `tasks/fossify-sync-upstream-pins.md`, as the maintainer decided on 2026-11-26 ("sure": close this task if both apps build at their newest tags). The maintainer committed the work the same day.

## The problem

The two documented exemplar apps did not build at their pinned tags, online or offline, so they could not be compiled for the offline Gradle cache or verified:

- **Gallery 1.3.0** depended on published `org.fossify:commons:3dd1f7f33e`, which pulls `com.github.duolingo:rtl-viewpager:940f12724f`; that artifact's own JitPack build needs `gradle-bintray-plugin` from the shut-down `jcenter.bintray.com`, so it 404s permanently.
- **Phone 1.5.0** depended on published `org.fossify:commons:3.0.3`, which 404s on JitPack.

## The options that were on the table

(A) bump each app to a newer released tag whose Commons dependency resolves; (B) substitute the locally checked-out Commons for the published artifact; (C) leave the apps unbuilt and document them from source only.

## What was done

Option (A) for both, as part of moving every Fossify pin to its newest release tag: Gallery 1.3.0 → 1.14.3 (published Commons 7.1.3) and Phone 1.5.0 → 1.11.1 (published Commons 6.1.0). Both dependencies resolve. Both apps compile `:app:compileFossReleaseKotlin` during the image's cache warm and again under `--network=none` with the doc patches applied. The one doc patch each app carries replayed onto the new tag with no conflict, so no re-anchoring was needed. Options (B) and (C) were not needed.

The warm script still treats the two apps as best-effort, so a future tag with a dead dependency cannot block the image build. Details: `android/fossify/CLAUDE.md`, "Build status".
