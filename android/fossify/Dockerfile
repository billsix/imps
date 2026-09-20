# Fedora-44 image carrying an Android/Gradle/JDK toolchain, just enough to
# COMPILE Fossify modules so the comment-only doc patches can be proven to
# change nothing the Kotlin compiler sees (see the `check-comment-only` target
# in the Makefile and the family contract in ../CLAUDE.md).
#
# BUILD STATUS: `make image`, `make build` (Commons), and the OFFLINE export
# test are verified (see CLAUDE.md "Build status"). This image is now
# offline-self-contained for Commons: the Android SDK AND Commons' Gradle
# dependency graph are baked into committed layers at image-build, so an
# exported image compiles Commons with the network cut (`./gradlew --offline` —
# proven via an export/import roundtrip + a --network=none build). The Gradle
# dep cache is the /venv analogue from modelviewprojection — warmed at build
# (the heavy step), not on first run.
#
# The two exemplar APPS (Gallery, Phone) do NOT build at their pinned tags —
# each needs an old published org.fossify:commons that JitPack can no longer
# serve (dead jcenter.bintray.com transitive / a 404'd version), which fails
# online too. The warm treats the apps as best-effort so this image still
# builds; see CLAUDE.md "Build status" and entrypoint/warm-gradle-cache.sh.
FROM registry.fedoraproject.org/fedora:44

# --- Toolchain versions (override with --build-arg to track a pin bump) -------
# Commons 6.2.0 (the deepest-documented repo) builds with: Gradle 9.6.1 (its
# wrapper — we do NOT install Gradle, each repo's wrapper fetches its own), Kotlin
# 2.3.10, AGP 9.3.1, compileSdk/targetSdk 36, kotlinJVMTarget 17. The exemplar
# APPS pin OLDER toolchains — Gallery/Phone use Gradle 8.11.1, AGP 8.10.x, Kotlin
# 2.1.21, and compileSdk 34 — so this image installs BOTH SDK platforms (34 + 36)
# and BOTH default build-tools (35.0.0 for AGP 8.10, 36.0.0 for AGP 9.3.1). Read
# these out of each repo's gradle/libs.versions.toml at a pin bump.
ARG ANDROID_SDK_PLATFORMS="platforms;android-36 platforms;android-34"
ARG ANDROID_BUILD_TOOLS="build-tools;36.0.0 build-tools;35.0.0"
# Google's command-line tools package (the sdkmanager). 11076708 = cmdline-tools
# 12.0; it can install any platform/build-tools revision regardless of its own
# version.
ARG CMDLINE_TOOLS_VERSION=11076708

ENV LANG=C.UTF-8 \
    ANDROID_SDK_ROOT=/opt/android-sdk \
    ANDROID_HOME=/opt/android-sdk \
    ANDROID_USER_HOME=/opt/android-user \
    GRADLE_USER_HOME=/opt/gradle-cache

# The maintainer's Fedora dnf-cache idiom: keep the package cache across builds
# via cache mounts + keepcache, upgrade, then install. Package install is a flat
# list here (small enough not to warrant an entrypoint/0N-install-*.sh split):
# the JDK, plus the download/unzip/git tools Gradle and the SDK setup need.
#
# JDK NOTE: run Gradle on JDK 17 (Adoptium/Temurin, GPG-verified via the Adoptium
# dnf repo below). Rationale: AGP 9.0+ requires JDK 17 as its MINIMUM, and
# Commons' libs.versions.toml sets app-build-javaVersion=VERSION_17 +
# kotlinJVMTarget=17 — so JDK 17 both satisfies AGP's floor AND matches the
# compile target, removing the "off-target JDK" uncertainty the Phase-A pass had
# with Fedora's JDK 25. Gradle 9.6.1 and 8.11.1 both run on a JDK-17 daemon (17
# is Gradle 9's minimum), so no separate toolchain-vs-daemon split is needed;
# keep it simple. Fedora 44 ships NO java-17-openjdk package, hence Temurin 17.
COPY entrypoint/adoptium.repo /etc/yum.repos.d/adoptium.repo
RUN --mount=type=cache,target=/var/cache/libdnf5 \
    --mount=type=cache,target=/var/lib/dnf \
    echo 'keepcache=True' >> /etc/dnf/dnf.conf \
 && dnf upgrade -y \
 && dnf install -y \
        temurin-17-jdk \
        git unzip wget ca-certificates findutils which

ENV JAVA_HOME=/usr/lib/jvm/temurin-17-jdk

# --- Android SDK: command-line tools, platforms, build-tools, licenses --------
# Downloaded at image-build (network on). These land in committed image layers,
# so the SDK IS self-contained in an exported image.
RUN mkdir -p "${ANDROID_SDK_ROOT}/cmdline-tools" \
 && wget -q "https://dl.google.com/android/repository/commandlinetools-linux-${CMDLINE_TOOLS_VERSION}_latest.zip" -O /tmp/cmdline-tools.zip \
 && unzip -q /tmp/cmdline-tools.zip -d "${ANDROID_SDK_ROOT}/cmdline-tools" \
 && mv "${ANDROID_SDK_ROOT}/cmdline-tools/cmdline-tools" "${ANDROID_SDK_ROOT}/cmdline-tools/latest" \
 && rm /tmp/cmdline-tools.zip

ENV PATH="${ANDROID_SDK_ROOT}/cmdline-tools/latest/bin:${ANDROID_SDK_ROOT}/platform-tools:${PATH}"

# `yes |` accepts every SDK license non-interactively (headless build); then
# install platform-tools + the platforms and build-tools the documented repos
# compile against (Commons wants 36; Gallery/Phone want 34 + build-tools 35).
RUN yes | sdkmanager --licenses >/dev/null \
 && sdkmanager --install \
        "platform-tools" \
        ${ANDROID_SDK_PLATFORMS} \
        ${ANDROID_BUILD_TOOLS} \
 && chmod -R a+rwX "${ANDROID_SDK_ROOT}"

# --- Warm the Gradle dependency cache (the /venv analogue) --------------------
# Bake every documented repo's Gradle dependency graph + wrapper distribution
# (Gradle 9.6.1 for Commons, 8.11.1 for the apps) into GRADLE_USER_HOME, so the
# runtime `./gradlew --offline` build finds everything with the network cut. The
# script clones each repo at its manifest pin, runs the SAME compile task the
# runtime build uses, and discards the clone (kept: /opt/gradle-cache). This is
# the heavy step (several minutes, network on). Logic + the repo->task map live
# in the script — see entrypoint/warm-gradle-cache.sh.
COPY repos /tmp/warm/repos
COPY entrypoint/warm-gradle-cache.sh /usr/local/bin/warm-gradle-cache.sh
RUN mkdir -p "${GRADLE_USER_HOME}" "${ANDROID_USER_HOME}" \
 && /usr/local/bin/warm-gradle-cache.sh /tmp/warm/repos /tmp/warm/clones \
 && rm -rf /tmp/warm \
 && chmod -R a+rwX "${GRADLE_USER_HOME}" "${ANDROID_USER_HOME}"

# The checkouts are bind-mounted at /work by the Makefile; each app is built
# with its own Gradle wrapper (./gradlew) from its checkout dir, OFFLINE against
# the baked cache.
WORKDIR /work
