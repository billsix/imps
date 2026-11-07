# Fedora-45 builder for the Luanti engine (+ the Mineclonia game it runs).
#
# Luanti (github.com/luanti-org/luanti @ 5.18.0) is the C++ engine; Mineclonia
# (codeberg.org/mineclonia/mineclonia @ 0.124.1) is Lua + assets and needs no
# build. This image carries only the toolchain and Luanti's build deps — the
# sources are NOT baked in: the imps folder is bind-mounted by the Makefile at run
# time, so host edits propagate without an image rebuild.
FROM registry.fedoraproject.org/fedora:45

# dnf cache mounts + keepcache: speed re-builds without bloating the image layer.
# The list is installdependencies.sh's (keep them in sync) plus the container-only
# headless smoke deps: xorg-x11-server-Xvfb + mesa-dri-drivers (llvmpipe swGL).
RUN --mount=type=cache,target=/var/cache/libdnf5 \
    --mount=type=cache,target=/var/lib/dnf \
    echo 'keepcache=True' >> /etc/dnf/dnf.conf && \
    dnf upgrade -y && \
    dnf install -y \
        gcc gcc-c++ cmake make git ninja-build gettext \
        SDL2-devel freetype-devel libpng-devel libjpeg-devel zlib-devel \
        libzstd-devel libzip-devel sqlite-devel \
        luajit-devel jsoncpp-devel gmp-devel \
        openal-soft-devel libvorbis-devel libogg-devel \
        libcurl-devel leveldb-devel spatialindex-devel ncurses-devel \
        mesa-libGL-devel \
        xorg-x11-server-Xvfb mesa-dri-drivers

WORKDIR /work
