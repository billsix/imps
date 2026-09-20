# Fedora-44 builder for GZDoom + ZMusic.
#
# GZDoom (github.com/ZDoom/gzdoom @ g4.14.2) links against ZMusic
# (github.com/ZDoom/ZMusic @ 1.3.0), which is built first. This image carries
# only the CMake/C++ toolchain and GZDoom's Linux build dependencies — the
# sources are NOT baked in: the imps checkout/ is bind-mounted by the Makefile at
# run time, so host edits and applied patches propagate without an image rebuild.
FROM registry.fedoraproject.org/fedora:44

# dnf cache mounts + keepcache: speed re-builds without bloating the image layer.
# The install list is GZDoom's Linux build deps:
#   toolchain           gcc-c++ cmake make git ninja-build pkgconf-pkg-config
#   core libs           SDL2 zlib libjpeg-turbo bzip2
#   audio               openal-soft fluidsynth (ZMusic backends)
#   video (cutscenes)   libvpx  (GZDoom 4.14 cmake/FindVPX.cmake)
#   GL / Vulkan render  mesa-libGL vulkan-loader vulkan-headers
#   IWAD-picker GUI     gtk3  (the GTK startup dialog GZDoom pops on Linux)
#   headless smoke-run  xorg-x11-server-Xvfb + mesa-dri-drivers (llvmpipe swGL)
RUN --mount=type=cache,target=/var/cache/libdnf5 \
    --mount=type=cache,target=/var/lib/dnf \
    echo 'keepcache=True' >> /etc/dnf/dnf.conf && \
    dnf upgrade -y && \
    dnf install -y \
        gcc-c++ cmake make git ninja-build pkgconf-pkg-config \
        SDL2-devel zlib-devel libjpeg-turbo-devel bzip2-devel \
        openal-soft-devel fluidsynth-devel \
        libvpx-devel \
        mesa-libGL-devel vulkan-loader-devel vulkan-headers \
        gtk3-devel \
        xorg-x11-server-Xvfb mesa-dri-drivers \
    && dnf clean all

WORKDIR /work
