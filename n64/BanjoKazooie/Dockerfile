# Mirrors the Lighthouse Linux CI build environment — the `build-linux` job of
# .github/workflows/main.yml at the imps pin (6d30df9a): SDL/tinyxml2/libzip
# from source, then a Release build + `cpack -G External` AppImage.
# CI runs on `ubuntu-latest`; GitHub's ubuntu-latest has resolved to the 24.04
# LTS since early 2025 (26.04 is not an LTS runner image), so this pins 24.04.
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8

# Base toolchain + AppImage tooling + the CI library deps.  Lighthouse's CI
# has no apt-deps.txt file (unlike 2s2h) — the list below is copied verbatim
# from the workflow's "Install dependencies" step at the pin, plus the
# packages a bare ubuntu image lacks that the GitHub runner pre-provides
# (toolchain, download utilities, AppImage packaging).
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc g++ git cmake ninja-build lsb-release libsdl2-dev libpng-dev \
        libsdl2-net-dev libzip-dev zipcmp zipmerge ziptool \
        nlohmann-json3-dev libtinyxml2-dev libspdlog-dev libboost-dev \
        libopengl-dev libogg-dev libvorbis-dev \
        ca-certificates wget curl file patchelf desktop-file-utils \
        build-essential pkg-config python3 \
    && rm -rf /var/lib/apt/lists/*

# SDL 2.30.3 from source (CI step "Install latest SDL").
RUN mkdir -p /deps && cd /deps \
 && wget -q https://www.libsdl.org/release/SDL2-2.30.3.tar.gz \
 && tar -xzf SDL2-2.30.3.tar.gz \
 && cd SDL2-2.30.3 \
 && ./configure --enable-hidapi-libusb \
 && make -j"$(nproc)" \
 && make install \
 && cp -av /usr/local/lib/libSDL* /lib/x86_64-linux-gnu/ \
 && ldconfig \
 && cd / && rm -rf /deps

# tinyxml2 10.0.0 from source (CI step "Install latest tinyxml2"; CI leaves
# the apt libtinyxml2-dev installed and shadows it, so we do the same).
RUN mkdir -p /deps && cd /deps \
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
