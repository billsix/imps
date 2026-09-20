# Fedora-44 image carrying an Android/Gradle/JDK toolchain, just enough to
# COMPILE Fossify modules so the comment-only doc patches can be proven to
# change nothing the Kotlin compiler sees (see the `check-comment-only` target
# in the Makefile and the family contract in ../CLAUDE.md).
#
# BUILD STATUS: `make image` and `make build` (Commons) are verified (see
# CLAUDE.md "Build status"). A full APK build downloads the SDK, accepts
# licenses, and pulls a large Gradle/AGP dependency graph; this image installs
# the toolchain, but the Gradle dependency cache is warmed on first `make build`
# (needs network), NOT baked into the image, so the maintainer's usual
# "exported image runs offline" convention is only partially met here (noted as
# a TODO in CLAUDE.md — warming ~/.gradle at image-build is the heavy step
# skipped for this first pass). Building app modules (vs the Commons library)
# is untested.
FROM registry.fedoraproject.org/fedora:44

# --- Toolchain versions (override with --build-arg to track a pin bump) -------
# Commons 6.2.0 (the deepest-documented repo) builds with: Gradle 9.6.1
# (project wrapper — we do NOT install Gradle, the wrapper fetches it), Kotlin
# 2.3.10, AGP 9.3.1, compileSdk/targetSdk 36, kotlinJVMTarget 17. The apps track
# closely. Read these out of each repo's gradle/libs.versions.toml at a pin bump.
ARG ANDROID_COMPILE_SDK=36
ARG ANDROID_BUILD_TOOLS=36.0.0
# Google's command-line tools package (the sdkmanager). 11076708 = cmdline-tools
# 12.0; it can install any platform/build-tools revision regardless of its own
# version.
ARG CMDLINE_TOOLS_VERSION=11076708

ENV LANG=C.UTF-8 \
    ANDROID_SDK_ROOT=/opt/android-sdk \
    ANDROID_HOME=/opt/android-sdk \
    GRADLE_USER_HOME=/opt/gradle-cache

# The maintainer's Fedora dnf-cache idiom: keep the package cache across builds
# via cache mounts + keepcache, upgrade, then install. Package install is a flat
# list here (small enough not to warrant an entrypoint/0N-install-*.sh split):
# a JDK, plus the download/unzip/git tools Gradle and the SDK setup need.
#
# JDK NOTE: the project targets JVM 17 bytecode (kotlinJVMTarget), but that is
# the compile TARGET, independent of the JDK that RUNS Gradle. Fedora 44 only
# ships java-25-openjdk-devel (no 17/21 packages), so that is the runtime JDK.
# Whether AGP 9.3.1 / Gradle 9.6.1 accept JDK 25 is UNVERIFIED (see CLAUDE.md);
# if they reject it, install a JDK the toolchain supports instead (e.g. an
# Adoptium/Temurin 17 or 21 tarball) and repoint JAVA_HOME.
RUN --mount=type=cache,target=/var/cache/libdnf5 \
    --mount=type=cache,target=/var/lib/dnf \
    echo 'keepcache=True' >> /etc/dnf/dnf.conf \
 && dnf upgrade -y \
 && dnf install -y \
        java-25-openjdk-devel \
        git unzip wget ca-certificates findutils which

ENV JAVA_HOME=/usr/lib/jvm/java-25-openjdk

# --- Android SDK: command-line tools, a platform, build-tools, licenses -------
# Downloaded at image-build (network on). These land in committed image layers,
# so the SDK itself IS self-contained in an exported image; only the per-project
# Gradle dependency cache is left to first-run (the heavy part — see caveat).
RUN mkdir -p "${ANDROID_SDK_ROOT}/cmdline-tools" \
 && wget -q "https://dl.google.com/android/repository/commandlinetools-linux-${CMDLINE_TOOLS_VERSION}_latest.zip" -O /tmp/cmdline-tools.zip \
 && unzip -q /tmp/cmdline-tools.zip -d "${ANDROID_SDK_ROOT}/cmdline-tools" \
 && mv "${ANDROID_SDK_ROOT}/cmdline-tools/cmdline-tools" "${ANDROID_SDK_ROOT}/cmdline-tools/latest" \
 && rm /tmp/cmdline-tools.zip

ENV PATH="${ANDROID_SDK_ROOT}/cmdline-tools/latest/bin:${ANDROID_SDK_ROOT}/platform-tools:${PATH}"

# `yes |` accepts every SDK license non-interactively (headless build); then
# install the platform + build-tools the apps compile against.
RUN yes | sdkmanager --licenses >/dev/null \
 && sdkmanager --install \
        "platform-tools" \
        "platforms;android-${ANDROID_COMPILE_SDK}" \
        "build-tools;${ANDROID_BUILD_TOOLS}" \
 && chmod -R a+rwX "${ANDROID_SDK_ROOT}"

# The checkouts are bind-mounted at /work by the Makefile; each app is built
# with its own Gradle wrapper (./gradlew) from its checkout dir.
WORKDIR /work
