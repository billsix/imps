# Mirrors the 2 Ship 2 Harkinian Linux CI build environment
# (.github/workflows/main.yml: ubuntu-22.04 + gcc-12, SDL/tinyxml2/libzip from source).
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    CC=gcc-12 \
    CXX=g++-12 \
    LANG=C.UTF-8

# Base toolchain + AppImage tooling + the shared CI library deps.
# The library list is read straight from .github/workflows/apt-deps.txt — the
# SAME file the GitHub Linux CI installs from — so the list lives in one place
# (no duplication). The packages listed inline are the ones a bare ubuntu:22.04
# lacks that the GitHub runner pre-provides (toolchain, checkout/download
# utilities, AppImage packaging) plus the zip CLI tools the CI installs
# alongside apt-deps.
# COPY, not `RUN --mount=type=bind`: a build-time bind mount is read by the
# confined `container_t` RUN process with the file's on-disk SELinux label, so
# a `:Z`-poisoned checkout (the runClaudeInContainer sandbox's c1022,c1023 MCS
# categories) makes a host-side `podman build` fail with an MCS-mismatch AVC,
# and a build mount has no relabel step.  COPY is read by buildah as the
# unconfined host user, immune to the label.
COPY .github/workflows/apt-deps.txt /tmp/apt-deps.txt
RUN apt-get update && apt-get install -y --no-install-recommends \
        $(cat /tmp/apt-deps.txt) \
        ca-certificates wget curl gnupg git file patchelf desktop-file-utils \
        lsb-release build-essential gcc-12 g++-12 pkg-config python3 \
        zipcmp zipmerge ziptool \
    && rm -rf /var/lib/apt/lists/*

# Project requires CMake >= 3.26; jammy ships 3.22. Install Kitware's build.
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

# tinyxml2 10.0.0 from source (CI removes the apt one first).
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

# libzip 1.10.1 without crypto backends (CI step "Install libzip without crypto").
RUN mkdir -p /deps && cd /deps \
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
