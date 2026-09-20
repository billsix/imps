SHELL := /bin/bash

# --- imps GZDoom carrier: build GZDoom (+ its ZMusic dep) in a Fedora-44 podman
# container. Native imps files (Dockerfile/Makefile are not patches). `make
# build` compiles whatever state checkout/ is in — normally the pin plus the
# applied patch series (fetch.sh then apply.sh). ---

CONTAINER_CMD  ?= podman
CONTAINER_NAME ?= gzdoom-builder
IMAGE          ?= $(CONTAINER_NAME):latest

# The imps-managed folder, bind-mounted at /work: it holds checkout/{gzdoom,zmusic}
# (fetch.sh), build/ and install/ (this Makefile), and runDir/ (game data).
WORK    := $(CURDIR)
RUN_DIR := $(CURDIR)/runDir
NPROC   := $(shell nproc)

# Release by default; `make build BUILD_TYPE=Debug` for a debug build. Each build
# type gets its own build/ and install/ subtree so the two never clobber.
BUILD_TYPE    ?= Release
INSTALL_PREFIX := /work/install/$(BUILD_TYPE)
ZMUSIC_BUILD   := /work/build/$(BUILD_TYPE)/zmusic
GZDOOM_BUILD   := /work/build/$(BUILD_TYPE)/gzdoom
GZDOOM_BIN     := $(INSTALL_PREFIX)/bin/gzdoom

# Extra flags for every container `run` (NEVER `build` — podman build rejects
# --cgroups). Auto-set when running nested inside a runClaudeInContainer /
# runCrushInContainer sandbox (which exports NESTED_PODMAN=1); empty — and
# byte-identical behavior — on a normal host. Override: make run PODMAN_RUN_FLAGS=...
PODMAN_RUN_FLAGS ?= $(if $(filter 1,$(NESTED_PODMAN)),--cgroups=disabled)

# --userns=keep-id maps the host UID into the container so bind-mounted files stay
# writable under rootless podman. Omitted nested (no subordinate IDs there, and
# inner root already matches the mount owner).
USERNS_FLAG ?= $(if $(filter 1,$(NESTED_PODMAN)),,--userns=keep-id)

# The mount/flag block shared by `shell` and `shell-exec` so the batch and
# interactive paths can't drift. :z relabels the bind mount for SELinux (Fedora);
# harmless elsewhere. SHELL_RUN_BASE is everything BEFORE the image, so smoke/run
# can splice an extra WAD mount in before `$(IMAGE)` (podman flags must precede
# the image name); SHELL_RUN_FLAGS appends the image for the plain shell targets.
SHELL_RUN_BASE  = --rm $(PODMAN_RUN_FLAGS) \
        -v $(WORK):/work:z \
        $(USERNS_FLAG) \
        -e HOME=/tmp
SHELL_RUN_FLAGS = $(SHELL_RUN_BASE) $(IMAGE)

# X11 / Wayland passthrough for `make run` on a real display (the maintainer's
# normal use). Empty when the matching env var is unset — then use XVFB=1.
X11_FLAGS     := $(if $(DISPLAY),-e DISPLAY=$(DISPLAY) -v /tmp/.X11-unix:/tmp/.X11-unix:rw,)
WAYLAND_FLAGS := $(if $(WAYLAND_DISPLAY),-e WAYLAND_DISPLAY=$(WAYLAND_DISPLAY) -e XDG_RUNTIME_DIR=/tmp -v $(XDG_RUNTIME_DIR)/$(WAYLAND_DISPLAY):/tmp/$(WAYLAND_DISPLAY):rw,)

.PHONY: help fetch apply image image-export image-import build version smoke run shell shell-exec clean distclean

help: ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

fetch: ## Clone GZDoom @ g4.14.2 + ZMusic @ 1.3.0 into checkout/ (idempotent)
	./fetch.sh

apply: ## git am the patches/ series onto the GZDoom checkout (guarded at the pin)
	./apply.sh

image: ## Build the Fedora-44 builder image
	$(CONTAINER_CMD) build -t $(IMAGE) -f Dockerfile .

image-export: ## Save the built image to a timestamped tar here
	$(CONTAINER_CMD) save $(IMAGE) -o $(CONTAINER_NAME)-$(shell date +%m-%d-%Y_%H-%M-%S).tar

image-import: ## Load an image tar: make image-import FILE=foo.tar
	@test -n "$(FILE)" || { echo 'usage: make image-import FILE=foo.tar' >&2; exit 2; }
	$(CONTAINER_CMD) load -i $(FILE)

# Build ZMusic (installed into the prefix so GZDoom's FindZMusic.cmake locates it
# via CMAKE_PREFIX_PATH), then GZDoom, both into the shared install prefix. Fetch
# first if the checkout is missing.
#   -DSYSTEMINSTALL=ON bakes PROGDIR=<prefix>/share/games/doom into gzdoom so the
#   binary finds its own gzdoom.pk3 (and the other resource .pk3s) from a
#   non-standard install prefix; without it GZDoom only looks next to the binary
#   and in /usr/share, so an out-of-prefix install cannot find gzdoom.pk3 and
#   falls into the GTK IWAD picker (the container path is fixed at /work).
build: image ## Build ZMusic then GZDoom (Release; BUILD_TYPE=Debug for debug)
	@[ -d checkout/gzdoom ] || ./fetch.sh
	$(CONTAINER_CMD) run $(SHELL_RUN_FLAGS) bash -c '\
	  set -euxo pipefail; \
	  cmake -S /work/checkout/zmusic -B $(ZMUSIC_BUILD) -G Ninja \
	        -DCMAKE_INSTALL_PREFIX=$(INSTALL_PREFIX) -DCMAKE_BUILD_TYPE=$(BUILD_TYPE); \
	  cmake --build $(ZMUSIC_BUILD) -j$(NPROC); \
	  cmake --install $(ZMUSIC_BUILD); \
	  cmake -S /work/checkout/gzdoom -B $(GZDOOM_BUILD) -G Ninja \
	        -DCMAKE_INSTALL_PREFIX=$(INSTALL_PREFIX) -DCMAKE_BUILD_TYPE=$(BUILD_TYPE) \
	        -DCMAKE_PREFIX_PATH=$(INSTALL_PREFIX) -DSYSTEMINSTALL=ON; \
	  cmake --build $(GZDOOM_BUILD) -j$(NPROC); \
	  cmake --install $(GZDOOM_BUILD); \
	'
	@echo "==> built gzdoom: install/$(BUILD_TYPE)/bin/gzdoom"

# GZDoom has no --version early-exit; it prints its version banner ("GZDoom
# <ver> ... SDL version") unconditionally at startup, then wants an IWAD. Capture
# just the banner (grep exits 0 on the match; gzdoom's own non-zero exit for "no
# IWAD" is upstream of the pipe and ignored) — this proves the binary links
# (incl. libzmusic) and starts.
version: ## Print the built gzdoom's version banner (headless — proves it links/launches)
	@$(CONTAINER_CMD) run $(SHELL_RUN_FLAGS) bash -c '\
	  LD_LIBRARY_PATH=$(INSTALL_PREFIX)/lib64:$(INSTALL_PREFIX)/lib \
	  $(GZDOOM_BIN) --version 2>&1 | grep -m1 "^GZDoom "'

# Headless smoke/repro: run the built gzdoom under Xvfb with a CLI WAD and capture
# what it does (loads / GTK IWAD picker / not found). Mounts the WAD read-only.
# Usage: make smoke WAD=/host/path/to.wad [ARGS='-file foo.wad'] [TIMEOUT=25]
TIMEOUT ?= 25
# The WAD is mounted at a fixed /wads/iwad.wad (not $(notdir $(WAD))) and the -v
# spec is single-quoted so a host path containing spaces (e.g. ".../Doom 2/...")
# survives make word-splitting as one podman argument.
smoke: ## Headless (Xvfb) CLI-WAD launch of the built gzdoom: make smoke WAD=/path.wad
	@test -n "$(WAD)" || { echo 'usage: make smoke WAD=/path/to.wad [ARGS=...]' >&2; exit 2; }
	$(CONTAINER_CMD) run $(SHELL_RUN_BASE) \
	  -v '$(WAD):/wads/iwad.wad:ro' \
	  $(IMAGE) bash -c '\
	    set -x; \
	    export LD_LIBRARY_PATH=$(INSTALL_PREFIX)/lib64:$(INSTALL_PREFIX)/lib SDL_AUDIODRIVER=dummy; \
	    timeout $(TIMEOUT) xvfb-run -a -s "-screen 0 1280x720x24" \
	      $(GZDOOM_BIN) -iwad /wads/iwad.wad $(ARGS) \
	      +echo GZDOOM_SMOKE_CONSOLE_REACHED +wait 70 +quit; \
	    echo "gzdoom exit: $$? (0 = loaded+reached game; 124 = blocked, e.g. GTK IWAD picker)"'

# Launch on a real display (X11 or Wayland passthrough + audio) — the maintainer's
# normal use. Add XVFB=1 to force headless. Usage: make run WAD=/path.wad [ARGS=...]
run: ## Launch the built gzdoom with a CLI WAD: make run WAD=/path.wad [ARGS=...]
	@test -n "$(WAD)" || { echo 'usage: make run WAD=/path/to.wad [ARGS=...]' >&2; exit 2; }
	@mkdir -p $(RUN_DIR)
	$(CONTAINER_CMD) run -it $(SHELL_RUN_BASE) \
	  $(X11_FLAGS) $(WAYLAND_FLAGS) --device /dev/dri \
	  -v '$(WAD):/wads/iwad.wad:ro' \
	  $(IMAGE) bash -c '\
	    export LD_LIBRARY_PATH=$(INSTALL_PREFIX)/lib64:$(INSTALL_PREFIX)/lib; \
	    if [ "$(XVFB)" = 1 ]; then \
	      exec xvfb-run -a $(GZDOOM_BIN) -iwad /wads/iwad.wad $(ARGS); \
	    else \
	      exec $(GZDOOM_BIN) -iwad /wads/iwad.wad $(ARGS); \
	    fi'

shell: image ## Interactive shell in the builder container
	$(CONTAINER_CMD) run -it $(SHELL_RUN_FLAGS) bash

shell-exec: image ## Batch twin of shell: make shell-exec CMD='...' | SCRIPT=<path under /work>
	@[ -n "$(SCRIPT)$(CMD)" ] || { echo "usage: make shell-exec CMD='...' | SCRIPT=<path under /work>" >&2; exit 2; }
	$(CONTAINER_CMD) run $(SHELL_RUN_FLAGS) \
	  bash -c 'cd /work && $(if $(CMD),$(CMD),exec bash $(SCRIPT))'

clean: ## Remove build/ and install/ (keeps checkout/ and runDir/)
	rm -rf build install

distclean: clean ## clean + remove the builder image
	-$(CONTAINER_CMD) rmi -f $(IMAGE)
