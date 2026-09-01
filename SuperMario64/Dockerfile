# Mirrors the Ghostship Linux CI build environment — the build-linux job of
# .github/workflows/main.yml at the imps pin (49c5312a): one big apt list
# (including the Vulkan/shaderc toolchain), SDL2 / tinyxml2 / libzip built
# from source, python deps from libultraship/requirements.txt, Release build,
# `cpack -G External` AppImage (plus the .tcc scripting runtime dir shipped
# alongside).  CI runs on `ubuntu-latest`; GitHub's ubuntu-latest has resolved
# to the 24.04 LTS since early 2025, so this pins 24.04.
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8

# The CI job's apt list verbatim (main.yml "Install dependencies"), plus the
# packages a bare ubuntu:24.04 lacks that the GitHub runner pre-provides
# (toolchain, download utilities, python3/pip, AppImage packaging).
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc g++ git cmake ninja-build lsb-release libsdl2-dev libpng-dev \
        libsdl2-net-dev libzip-dev zipcmp zipmerge ziptool \
        nlohmann-json3-dev libtinyxml2-dev libspdlog-dev libboost-dev \
        libopengl-dev libogg-dev libvorbis-dev libmbedtls-dev \
        libvulkan-dev libshaderc-dev glslang-dev spirv-tools \
        ca-certificates wget curl gnupg file patchelf desktop-file-utils \
        build-essential pkg-config python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# libultraship prefers linking `shaderc_shared`, but Ubuntu ships the shared
# lib as plain libshaderc.so — without this compat name, cmake falls back to
# libshaderc_combined.a, which on noble is ABI-skewed against the newer
# spirv-tools static libs (undefined spvtools:: symbols at link).  The
# symlink routes LUS to the self-consistent shared library.
RUN ln -s /usr/lib/x86_64-linux-gnu/libshaderc.so \
          /usr/lib/x86_64-linux-gnu/libshaderc_shared.so

# libultraship's vendored FindVulkan.cmake references policy CMP0159, which
# needs CMake >= 3.30; noble's apt ships 3.28 (the GitHub ubuntu-latest
# runner pre-provides a modern cmake, so CI never notices).  Install
# Kitware's build — same fix as the OcarinaOfTime Dockerfile on jammy.
RUN wget -O /tmp/kitware-archive.sh https://apt.kitware.com/kitware-archive.sh \
    && bash /tmp/kitware-archive.sh \
    && apt-get install -y --no-install-recommends cmake \
    && rm -rf /var/lib/apt/lists/* /tmp/kitware-archive.sh

# Python deps for the Torch/asset tooling, read straight from the checkout's
# libultraship/requirements.txt via a build-time bind mount (the build context
# is the Ghostship checkout) — same single-source-of-truth trick as the apt
# lists elsewhere.  --break-system-packages because 24.04's python is
# PEP668-managed and this is a single-purpose container.
RUN --mount=type=bind,source=libultraship/requirements.txt,target=/tmp/requirements.txt \
    pip3 install --break-system-packages -r /tmp/requirements.txt

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

# tinyxml2 10.0.0 from source (CI step "Install latest tinyxml2"; the apt one
# stays installed and is shadowed, matching CI).
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
