# Fedora-44 image carrying the Rust toolchain, used only to BUILD the pinned
# ripgrep checkout so the docs-only patch streams can be proven comment-only
# (see check-comment-only.sh). This carrier documents ripgrep; it does not
# change or ship it, so the image needs nothing but a compiler and git.
#
# github.com/BurntSushi/ripgrep — pinned at tag 14.1.1 by fetch.sh.
FROM registry.fedoraproject.org/fedora:44

# dnf-cache idiom: keep the package cache in a build cache mount so rebuilds are
# fast, without baking the cache into the image.
RUN --mount=type=cache,target=/var/cache/libdnf5 \
    --mount=type=cache,target=/var/lib/dnf \
    printf 'keepcache=True\n' >> /etc/dnf/dnf.conf \
 && dnf upgrade -y \
 && dnf install -y \
        rust cargo \
        git \
        python3 \
 && dnf clean all

# The checkout is bind-mounted at /src by the Makefile; cargo build/comment-only
# run against it there.
WORKDIR /src
