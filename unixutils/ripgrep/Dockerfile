# Fedora-44 image carrying the Rust toolchain, used only to BUILD the pinned
# ripgrep checkout so the docs-only patch streams can be proven comment-only
# (see check-comment-only.sh). This carrier documents ripgrep; it does not
# change or ship it, so the image needs nothing but a compiler and git.
#
# OFFLINE-SELF-CONTAINED: ripgrep's whole Cargo dependency graph (every crate in
# its Cargo.lock at the pin) is baked into a committed CARGO_HOME layer at
# image-build (see the warm step below), so an EXPORTED image compiles ripgrep
# with the network cut — `make build` runs `cargo build --offline`. This is the
# Cargo analogue of modelviewprojection's baked /venv and the Fossify sibling's
# warmed Gradle cache: third-party crates live in the committed layer; only
# ripgrep's OWN source is (re)built from the bind-mounted checkout at runtime.
#
# github.com/BurntSushi/ripgrep — pinned at tag 14.1.1 by fetch.sh.
FROM registry.fedoraproject.org/fedora:44

# The pin to warm the Cargo cache against. MUST match fetch.sh's PIN_SHA (the
# commit tag 14.1.1 peels to) — the runtime bind-mounted checkout is that same
# pin, so its Cargo.lock matches and every dep it needs is cached here. On a pin
# bump, move PIN_SHA in fetch.sh AND this default together (or pass
# --build-arg RIPGREP_PIN=<sha>), then rebuild the image to re-warm the cache.
ARG RIPGREP_PIN=4649aa9700619f94cf9c66876e9549d83420e16c

# CARGO_HOME is a FIXED, committed path (not $HOME/.cargo) so the warmed registry
# cache survives into the image layer and the runtime `cargo build --offline`
# finds it, regardless of the container's HOME.
ENV CARGO_HOME=/opt/cargo-cache

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

# --- Warm the Cargo dependency cache (the /venv analogue) ---------------------
# Clone ripgrep at RIPGREP_PIN and `cargo fetch --locked` every crate in its
# Cargo.lock into CARGO_HOME, then discard the clone — all in ONE RUN layer, so
# only CARGO_HOME persists in the committed image. Network is ON here (image
# build); after this the runtime build needs none. Logic + rationale live in the
# script — see entrypoint/warm-cargo-cache.sh.
COPY entrypoint/warm-cargo-cache.sh /usr/local/bin/warm-cargo-cache.sh
RUN mkdir -p "${CARGO_HOME}" \
 && /usr/local/bin/warm-cargo-cache.sh "${RIPGREP_PIN}" /tmp/warm-ripgrep \
 && chmod -R a+rwX "${CARGO_HOME}"

# The checkout is bind-mounted at /ripgrep/checkout by the Makefile; the runtime
# `cargo build --offline` runs there against the baked CARGO_HOME.
WORKDIR /ripgrep
