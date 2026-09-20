#!/usr/bin/env bash
#
# warm-gradle-cache.sh — bake the Gradle dependency graph + wrapper
# distributions for the DOCUMENTED Fossify repos into GRADLE_USER_HOME at
# IMAGE-BUILD time, so an EXPORTED image builds them with the network cut
# (`./gradlew --offline`) years later. This is the Gradle analogue of how
# modelviewprojection bakes pip deps into a committed /venv layer: the deps
# land in a committed image layer (GRADLE_USER_HOME=/opt/gradle-cache) instead
# of being fetched on first `make build`.
#
# The chicken-and-egg the Phase-A pass hit: the checkouts are fetched at
# RUNTIME (gitignored), so at image-build there is no source to resolve
# against. Fix: clone each documented repo at its manifest pin into a throwaway
# dir, run the SAME compile task the runtime `make build` uses (so the runtime
# --offline build finds every artifact already cached), then discard the clone.
# Because this whole script runs inside ONE Docker `RUN` layer, the clones —
# created under a temp dir and removed here — never enter the committed layer;
# only GRADLE_USER_HOME (under /opt) persists.
#
# Pins are read from the `repos` manifest (the single source of truth, same as
# fetch.sh), so a pin bump warms the new commit automatically. Only the three
# DOCUMENTED repos are warmed — Commons + Gallery + Phone; Messages/Keyboard
# have empty doc streams, so warming them would only bloat the image.
#
# Repo -> warm task (the task the runtime build runs for that repo):
#   Commons -> :commons:compileReleaseKotlin      (the shared library module)
#   Gallery -> :app:compileFossReleaseKotlin      (app; foss flavor, release)
#   Phone   -> :app:compileFossReleaseKotlin      (app; foss flavor, release)
# The apps carry product flavors (Gallery: foss/gplay; Phone: core/foss/gplay),
# so the compile task is flavor-qualified (compileFossReleaseKotlin), NOT the
# bare compileReleaseKotlin a flavorless module would have.
#
# REQUIRED vs BEST-EFFORT (verified 2026-09-20): Commons is REQUIRED — it is the
# documentation centre of gravity and it warms/builds cleanly, so a Commons warm
# failure FAILS the image build. The two apps are BEST-EFFORT: at their pinned
# RELEASED tags they have upstream build rot that fails online too, so a failure
# is LOGGED and warming continues (an unbuildable app must not block the image's
# achievable Commons offline capability). Known state at the current pins:
#   * Gallery 1.3.0 — UNBUILDABLE online OR offline. Its published dependency
#     org.fossify:commons:3dd1f7f33e transitively needs
#     com.github.duolingo:rtl-viewpager:940f12724f, whose own JitPack build fails
#     (it needs gradle-bintray-plugin from the shut-down jcenter.bintray.com), so
#     the artifact 404s permanently. Nothing to warm — not a network/JDK issue.
#   * Phone 1.5.0 — builds on JDK 17 (its AGP 8.10.1 rejected the Phase-A JDK 25,
#     failing with the bare version string "25.0.4.1"); warms here.
# Re-check both at a pin bump: a newer app tag may drop the dead transitive / lift
# the AGP-JDK floor.
#
# Usage (from the Dockerfile, network on):
#   warm-gradle-cache.sh <manifest-path> <scratch-dir>
# Runs standalone on a bare host too (needs git, a JDK on JAVA_HOME, the Android
# SDK on ANDROID_SDK_ROOT with licenses accepted, and network).

set -uo pipefail

MANIFEST="${1:-repos}"
SCRATCH="${2:-/tmp/warm-clones}"

[ -f "$MANIFEST" ] || { echo "warm: missing manifest: $MANIFEST" >&2; exit 1; }
mkdir -p "$SCRATCH"

warmed=""      # repos whose warm succeeded
failed=""      # best-effort repos whose warm failed (logged, non-fatal)
commons_ok=0

warm_one() {
    name="$1"; task="$2"; url="$3"; sha="$4"; required="$5"
    dir="$SCRATCH/$name"
    echo "==> warming $name ($task) at $sha"
    rm -rf "$dir"
    git clone --quiet "$url" "$dir" || { echo "warm: clone of $name failed" >&2; return 1; }
    git -C "$dir" checkout -q "$sha" || { echo "warm: checkout of $name@$sha failed" >&2; return 1; }
    # --no-daemon: match the runtime build and leave no daemon behind in the
    # layer. Network is ON here (image build); the deps land in GRADLE_USER_HOME.
    if ( cd "$dir" && ./gradlew --no-daemon --stacktrace "$task" ); then
        rm -rf "$dir"
        return 0
    fi
    rm -rf "$dir"
    return 1
}

# Loop the manifest exactly like fetch.sh (strip #-comments/blanks, take the
# first two fields), mapping each DOCUMENTED repo to its warm task; skip the
# rest. Commons is required; the apps are best-effort (see the header).
while read -r url sha _; do
    case "$url" in ''|\#*) continue ;; esac
    [ -n "$sha" ] || { echo "warm: manifest line for $url has no pin SHA" >&2; exit 1; }
    name=$(basename "$url" .git)
    case "$name" in
        Commons)       task=":commons:compileReleaseKotlin"; required=1 ;;
        Gallery|Phone) task=":app:compileFossReleaseKotlin";  required=0 ;;
        *)             echo "==> skipping undocumented repo $name (not warmed)"; continue ;;
    esac

    if warm_one "$name" "$task" "$url" "$sha" "$required"; then
        warmed="$warmed $name"
        [ "$name" = Commons ] && commons_ok=1
    elif [ "$required" = 1 ]; then
        echo "warm: REQUIRED repo $name failed to warm — failing the image build" >&2
        exit 1
    else
        echo "warm: WARNING best-effort repo $name failed to warm (upstream build rot at its pin — see this script's header); continuing" >&2
        failed="$failed $name"
    fi
done < "$MANIFEST"

rm -rf "$SCRATCH"

[ "$commons_ok" = 1 ] || { echo "warm: Commons was never warmed (missing from manifest?)" >&2; exit 1; }

echo "==> gradle cache warm complete: warmed [${warmed# }]${failed:+; best-effort failures [${failed# }]}"
