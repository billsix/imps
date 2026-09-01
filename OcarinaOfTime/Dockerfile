# Mirrors the Ship of Harkinian Linux CI build environment — the linux job of
# .github/workflows/generate-builds.yml at the imps pin (acdbc651d), which runs
# on ubuntu-22.04: apt deps from the repo's own linux-build-deps/apt.txt, then
# SDL2 / SDL2_net / tinyxml2 / libzip built from source, Release build with
# BUILD_REMOTE_CONTROL=1, `cpack -G External` AppImage.
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8

# Base toolchain + AppImage tooling + the shared CI library deps.  The library
# list is read straight from linux-build-deps/apt.txt — the SAME file the
# GitHub CI installs from (the build context is the Shipwright checkout) — so
# the list lives in one place.  The packages listed inline are the ones a bare
# ubuntu:22.04 lacks that the GitHub runner pre-provides (toolchain, download
# utilities, python3 for the asset extractor, imagemagick — SoH's cmake
# configure runs `convert` on sohIcon.png and fails without it — and AppImage
# packaging).
# COPY, not `RUN --mount=type=bind`: a build-time bind mount is read by the
# confined `container_t` RUN process with the file's on-disk SELinux label, so
# a `:Z`-poisoned checkout (the runClaudeInContainer sandbox's c1022,c1023 MCS
# categories) makes a host-side `podman build` fail with an MCS-mismatch AVC,
# and a build mount has no relabel step.  COPY is read by buildah as the
# unconfined host user, immune to the label.
COPY linux-build-deps/apt.txt /tmp/apt.txt
RUN apt-get update && apt-get install -y --no-install-recommends \
        $(cat /tmp/apt.txt) \
        ca-certificates wget curl gnupg git file patchelf desktop-file-utils \
        build-essential gcc g++ pkg-config python3 imagemagick \
    && rm -rf /var/lib/apt/lists/*

# The project requires CMake >= 3.26; jammy's apt ships 3.22 (the GitHub
# ubuntu-22.04 runner pre-provides a modern cmake, so CI never notices).
# Install Kitware's build — the same fix the maintainer's original 2ship
# Dockerfile used for jammy.
RUN wget -O /tmp/kitware-archive.sh https://apt.kitware.com/kitware-archive.sh \
    && bash /tmp/kitware-archive.sh \
    && apt-get install -y --no-install-recommends cmake \
    && rm -rf /var/lib/apt/lists/* /tmp/kitware-archive.sh

# SDL 2.30.3 from source (CI step "Install latest SDL").
RUN mkdir -p /deps && cd /deps \
 && wget -q https://github.com/libsdl-org/SDL/releases/download/release-2.30.3/SDL2-2.30.3.tar.gz \
 && tar -xzf SDL2-2.30.3.tar.gz \
 && cd SDL2-2.30.3 \
 && ./configure --enable-hidapi-libusb \
 && make -j"$(nproc)" \
 && make install \
 && cp -av /usr/local/lib/libSDL* /lib/x86_64-linux-gnu/ \
 && ldconfig \
 && cd / && rm -rf /deps

# SDL2_net 2.2.0 from source (CI's local install-sdl2-net action).
RUN mkdir -p /deps && cd /deps \
 && curl -fsSL https://www.libsdl.org/projects/SDL_net/release/SDL2_net-2.2.0.tar.gz | tar xz \
 && cd SDL2_net-2.2.0 \
 && ./configure \
 && make -j"$(nproc)" \
 && make install \
 && cp -av /usr/local/lib/libSDL* /lib/x86_64-linux-gnu/ \
 && ldconfig \
 && cd / && rm -rf /deps

# tinyxml2 10.0.0 from source, shadowing the apt one (CI removes it first).
RUN apt-get update && apt-get remove -y libtinyxml2-dev \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir -p /deps && cd /deps \
 && wget -q https://github.com/leethomason/tinyxml2/archive/refs/tags/10.0.0.tar.gz \
 && tar -xzf 10.0.0.tar.gz \
 && cmake -S tinyxml2-10.0.0 -B tinyxml2-10.0.0/build -DCMAKE_BUILD_TYPE=Release \
 && cmake --build tinyxml2-10.0.0/build -j"$(nproc)" \
 && cmake --install tinyxml2-10.0.0/build \
 && ldconfig \
 && cd / && rm -rf /deps

# libzip 1.10.1 without crypto backends, shadowing the apt one (CI step
# "Install libzip without crypto" removes libzip-dev first).
RUN apt-get update && apt-get remove -y libzip-dev \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir -p /deps && cd /deps \
 && wget -q https://github.com/nih-at/libzip/releases/download/v1.10.1/libzip-1.10.1.tar.gz \
 && tar -xzf libzip-1.10.1.tar.gz \
 && cmake -S libzip-1.10.1 -B libzip-1.10.1/build -DCMAKE_BUILD_TYPE=Release \
        -DENABLE_COMMONCRYPTO=OFF -DENABLE_GNUTLS=OFF \
        -DENABLE_MBEDTLS=OFF -DENABLE_OPENSSL=OFF \
 && cmake --build libzip-1.10.1/build -j"$(nproc)" \
 && cmake --install libzip-1.10.1/build \
 && cp -av /usr/local/lib/libzip* /lib/x86_64-linux-gnu/ \
 && ldconfig \
 && cd / && rm -rf /deps

WORKDIR /src
