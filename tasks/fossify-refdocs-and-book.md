# Fossify (Android app suite) — reference-doc set + doc-region teaching book (imps)

**Status:** in progress — go-ahead 2026-09-20 (William Emerison Six <billsix@gmail.com>). **Phase A**
(the multi-repo `android/fossify/` docs-only carrier — `repos` manifest + fetch/apply/Makefile/Dockerfile)
+ a first pass of `patches/<repo>/docs/` KDoc is DONE this session: 5 repos pinned at released tags
(Commons 6.2.0, Gallery 1.3.0, Phone 1.5.0, Messages 1.2.0, Keyboard 1.2.0), 7 KDoc patches (5 on
`Commons` — app skeleton, theming, settings store, color-picker, storage — + Gallery media pipeline +
Phone CallManager), all proven comment-only, and Commons compiled in-container (JDK 25 + Gradle) with the
patches. **UNVERIFIED / decisions** (details in `android/fossify/CLAUDE.md`): app-module builds untested
(only the Commons library compiled); Fedora 44 ships only JDK 25 (project targets JVM 17 — may need an
Adoptium 17/21 drop-in); the image isn't fully offline (Gradle cache warms at first build, not baked);
Messages & Keyboard cloned but not yet documented. **Phase B** (`tasks/reference/fossify/`) and **Phase C**
(the Sphinx book) are **DEFERRED** until the follow-ups land (maintainer's call 2026-09-20):
[fossify-jdk-toolchain-and-gradle-offline.md](fossify-jdk-toolchain-and-gradle-offline.md) and
[generalize-comment-only-gate.md](generalize-comment-only-gate.md). Scoped autonomously
2026-09-19. One of FOUR sibling documentation-only initiatives — see [ripgrep](ripgrep-refdocs-and-book.md)
for the shared recipe + family decision, plus [coreutils](coreutils-refdocs-and-book.md),
[dash](dash-refdocs-and-book.md).
**Priority:** 7
**Difficulty:** 8 (breadth — 17 apps — plus a mid-flight Compose/Views migration, so "current architecture"
is a moving target per app; the strong shared `Commons` core is what makes it tractable)

## BLUF

Bring **Fossify** (a suite of ~17 open-source, privacy-respecting **Android apps in Kotlin**, the
community continuation of Simple Mobile Tools) into imps as a **documentation-only** initiative and
produce, in the mario64 mould, a `file:line`-anchored **reference set** and a **Sphinx teaching book**
("*How Android Apps Are Built*") whose snippets come from real source via **doc-region markers**. This is
the ONE of the four that is inherently **multi-repo**: the apps share a `Commons` library, so the
initiative is **ONE umbrella** documenting **Commons + the shared app skeleton**, with **thin per-app
chapters** covering only what's app-specific — NOT a book per app (which would massively duplicate the
Commons material). No code is patched; the only stream per repo is the comment-only `book/` markers.
"Done" = a multi-repo docs-only carrier + a Commons-centred reference set + a book building HTML/PDF/EPUB.
Split into step-tasks once approved.

## Context (cold-start)

**Reuse the mario64 machinery** (doc-region markers, L0–L3 Levels of Detail, house-style `_TEMPLATE.md`,
the `n64/SuperMario64/book/` Sphinx+container template, the umbrella/step-task shape) — full pointer list
in [ripgrep-refdocs-and-book.md](ripgrep-refdocs-and-book.md) "Reuse the mario64 machinery".
Documentation-only, under a new **`android/`** family (DECIDED 2026-09-19 — categorized by kind like
`n64/`; the three CLI siblings go under `unixutils/`, Fossify under `android/`; recorded in the imps
root `CLAUDE.md`). Fossify is `android/`'s first (and, for now, only) project.
Kotlin `//` markers. **Comment-only gate:** like Rust, Kotlin has no gcc `-fpreprocessed`, so a
Gradle/Kotlin-aware analogue is needed (compile-before/after or comment-strip diff) — see open question 3.

### Fossify profile (researched 2026-09-19)

- **Org:** github.com/FossifyOrg. **License:** GPL-3.0 (Simple Mobile Tools lineage). **Language:** Kotlin
  (Android); apps are migrating classic Views/XML → Jetpack Compose, adoption varies per app and is
  ongoing (so per-app "current architecture" is a moving target). All ad-free, offline, privacy-first.
- **The shared library — the documentation centre of gravity:** **`Commons`**
  (github.com/FossifyOrg/Commons) — "helper functions and shared resources used by the Fossify apps":
  shared UI components/themes, dialogs, settings screens, permission handling, the color/customization
  system, file/media helpers. **Every app depends on it.**
- **The apps (repo → purpose):** Gallery (photo/video browser), File-Manager, Phone (call manager,
  blocking, multi-SIM), Messages (SMS/MMS), Contacts, Calendar, Camera, Notes, Voice-Recorder, Clock
  (alarm/stopwatch/timer), Calculator, Paint (drawing), Music-Player, Keyboard (IME), Launcher,
  Flashlight, Thank-You (supporter app). (~17; confirm the live list at github.com/FossifyOrg at execution
  time — the suite grows.)
- **Why ONE initiative, not per-app:** the apps share `Commons` (theming, settings, dialogs, permissions,
  storage/media access), one Gradle/Android build convention, one language, one design system. The durable
  teaching value is **Commons + the shared app skeleton** (how a Fossify app is scaffolded: Activity
  structure, Compose-vs-Views state, the settings/customization framework, F-Droid/Play release setup),
  then thin app-specific chapters (Gallery's media pipeline, Phone's telephony/SIM, Messages' SMS/MMS
  stack, Keyboard's IME).

## Plan (phases → step-tasks once approved)

**Phase A — the multi-repo docs-only carrier.** `android/fossify/` with a `fetch.sh` that clones MULTIPLE
upstreams — `Commons` + a chosen set of apps — each pinned (`PIN_SHA` per repo; consider a
`repos` manifest listing repo→pin). `apply.sh` applies each repo's `book/` stream. `.gitignore` all
checkouts. Tier-3 CLAUDE.md documenting the multi-repo layout. This is the one carrier whose shape departs
from the single-repo template — design the multi-checkout fetch/apply first (open question 2).

**Phase B — the reference set** (`tasks/reference/fossify/`), from mario64's `README.md` (L0 map) +
`_TEMPLATE.md`. **Commons-centred, then thin per-app:**
1. How a Fossify app is scaffolded — the shared skeleton (Activity/entry structure, the Compose-vs-Views
   state, manifest/Gradle conventions).
2. **`Commons` tour** — likely several L2 docs: the theming/color-customization system, the shared
   settings framework, dialogs & UI components, permission handling, file/media/storage helpers.
3. Release engineering — F-Droid + Play setup shared across apps.
4. Per-app L2 docs (exemplars, only app-specific parts): Gallery (media pipeline), Phone
   (telephony/SIM/blocking), Messages (SMS/MMS), Keyboard (IME) — a handful, not all 17.
Each ends with "How this relates to the course" and a "Candidate doc-region spans" list.

**Phase C — the doc-region book** (`android/fossify/book/`, "*How Android Apps Are Built*"). `cp -r` the
mario64 `book/` template; `highlight_language="kotlin"`; `index.rst` = shared-skeleton + Commons chapters
first, then thin per-app case studies. Add a `book/` doc-region stream in EACH documented repo (Commons +
the exemplar apps). `literalinclude` reaches `../<Checkout>/...` per repo (mind the multi-repo relative
paths — the Makefile's parent-mount trick may need widening to mount several checkouts). Build
HTML/PDF/EPUB. Book umbrella + children from `tasks/mario64-sphinx-book.md`.

## Open questions

1. **Family name — DECIDED 2026-09-19:** `android/` (Fossify is its first project). Settled.
2. **Multi-repo carrier design.** How should `fetch.sh`/`apply.sh` handle N upstreams (Commons + apps)?
   Recommend a `repos` manifest (repo URL → pin) the scripts loop over, and per-repo `book/` streams.
   This is the main novel engineering vs the single-repo siblings — worth its own foundation step-task.
3. **Which apps to cover, and how deep.** Recommend: Commons in depth + 3–4 exemplar apps (Gallery,
   Phone, Messages, Keyboard) as thin chapters. Confirm the exemplar set. (Documenting all 17 in depth is
   out of proportion; the shared skeleton is the lesson.)
4. **Kotlin comment-only gate** — a Gradle/Kotlin analogue of the gcc `-fpreprocessed` check (compile
   before/after the `book/` stream, or a comment-strip diff). Shared with the Rust siblings' open question.
5. **Compose vs Views churn.** Because the migration is mid-flight, pin conservatively and note in each
   doc which UI stack the anchored code uses, so the reference set doesn't rot as apps convert.

## Related

- Sibling initiatives + shared recipe: [ripgrep](ripgrep-refdocs-and-book.md),
  [coreutils](coreutils-refdocs-and-book.md), [dash](dash-refdocs-and-book.md).
- Templates: `tasks/reference/mario64/{README.md,_TEMPLATE.md}`, `tasks/mario64-sphinx-book.md`,
  `n64/SuperMario64/book/`, `tools/check_comment_only_streams.sh`.
