SHELL := /bin/bash

# --- imps Mineclonia carrier: build the Luanti engine (and install the Mineclonia
# game into it) in a Fedora-45 podman container. Native imps files, not patches.
# The container runs the same ./build.sh as the native host path, so there is one
# build recipe; RUN_IN_PLACE keeps the install relocatable, so a container-built
# bldInstall/ also runs on the host. ---

CONTAINER_CMD  ?= podman
CONTAINER_NAME ?= mineclonia-builder
IMAGE          ?= $(CONTAINER_NAME):latest

WORK     := $(CURDIR)
RUN_DIR  := $(CURDIR)/runDir

BUILD_TYPE ?= Release
LUANTI_BIN := /work/bldInstall/$(BUILD_TYPE)/bin/luanti

# Extra flags for every container `run` (NEVER `build` — podman build rejects
# --cgroups). Auto-set when running nested inside a runClaudeInContainer /
# runCrushInContainer sandbox (which exports NESTED_PODMAN=1); empty on a host.
PODMAN_RUN_FLAGS ?= $(if $(filter 1,$(NESTED_PODMAN)),--cgroups=disabled)

# --userns=keep-id keeps bind-mounted files writable under rootless podman.
# Omitted nested (no subordinate IDs there; inner root already owns the mount).
USERNS_FLAG ?= $(if $(filter 1,$(NESTED_PODMAN)),,--userns=keep-id)

# The mount/flag block shared by every container target so they can't drift.
# SHELL_RUN_BASE is everything before the image (run adds display flags there).
SHELL_RUN_BASE  = --rm $(PODMAN_RUN_FLAGS) \
        -v $(WORK):/work:z \
        $(USERNS_FLAG) \
        -e HOME=/tmp -e BUILD_TYPE=$(BUILD_TYPE) -e BUILD_ROOT=build-container
SHELL_RUN_FLAGS = $(SHELL_RUN_BASE) $(IMAGE)

X11_FLAGS     := $(if $(DISPLAY),-e DISPLAY=$(DISPLAY) -v /tmp/.X11-unix:/tmp/.X11-unix:rw,)
WAYLAND_FLAGS := $(if $(WAYLAND_DISPLAY),-e WAYLAND_DISPLAY=$(WAYLAND_DISPLAY) -e XDG_RUNTIME_DIR=/tmp -v $(XDG_RUNTIME_DIR)/$(WAYLAND_DISPLAY):/tmp/$(WAYLAND_DISPLAY):rw,)

.PHONY: help fetch image image-export image-import build version smoke run shell shell-exec clean distclean

help: ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

fetch: ## Clone Luanti @ 5.18.0 + Mineclonia @ 0.124.1 into checkout/ (idempotent)
	./fetch.sh

image: ## Build the Fedora-45 builder image
	$(CONTAINER_CMD) build -t $(IMAGE) -f Dockerfile .

image-export: ## Save the built image to a timestamped tar here
	$(CONTAINER_CMD) save $(IMAGE) -o $(CONTAINER_NAME)-$(shell date +%m-%d-%Y_%H-%M-%S).tar

image-import: ## Load an image tar: make image-import FILE=foo.tar
	@test -n "$(FILE)" || { echo 'usage: make image-import FILE=foo.tar' >&2; exit 2; }
	$(CONTAINER_CMD) load -i $(FILE)

build: image ## Build Luanti + install Mineclonia into bldInstall/ (BUILD_TYPE=Debug for debug)
	@[ -d checkout/luanti ] && [ -d checkout/mineclonia ] || ./fetch.sh
	$(CONTAINER_CMD) run $(SHELL_RUN_FLAGS) bash -c 'cd /work && ./build.sh'

version: ## Print the built luanti's version (proves it links and starts)
	@$(CONTAINER_CMD) run $(SHELL_RUN_FLAGS) $(LUANTI_BIN) --version

# Headless smoke: start a dedicated server for Mineclonia in a throwaway world.
# That loads and runs every one of Mineclonia's Lua mods against this engine
# build (the real compatibility check), with no display needed. Passes when the
# server reports it is listening and the log holds no ERROR line.
TIMEOUT ?= 90
smoke: ## Headless: run a Mineclonia server in a temp world; fail on any Lua ERROR
	$(CONTAINER_CMD) run $(SHELL_RUN_FLAGS) bash -c '\
	  log=/tmp/smoke.log; \
	  timeout $(TIMEOUT) $(LUANTI_BIN) --server --gameid mineclonia \
	    --world /tmp/smoke-world --port 30123 >$$log 2>&1 & pid=$$!; \
	  for i in $$(seq 1 $(TIMEOUT)); do \
	    grep -q "listening on" $$log && break; \
	    kill -0 $$pid 2>/dev/null || break; sleep 1; done; \
	  kill $$pid 2>/dev/null; wait $$pid 2>/dev/null; \
	  grep -m1 "listening on" $$log || { tail -30 $$log; echo "SMOKE FAIL: server never listened"; exit 1; }; \
	  if grep -E "ERROR\[" $$log; then echo "SMOKE FAIL: errors above"; exit 1; fi; \
	  echo "SMOKE PASS"'

run: ## Launch luanti + Mineclonia on the host display (X11/Wayland passthrough)
	@mkdir -p $(RUN_DIR)
	$(CONTAINER_CMD) run -it $(SHELL_RUN_BASE) \
	  $(X11_FLAGS) $(WAYLAND_FLAGS) --device /dev/dri \
	  $(IMAGE) bash -c 'cd /work && exec ./run.sh $(ARGS)'

shell: image ## Interactive shell in the builder container
	$(CONTAINER_CMD) run -it $(SHELL_RUN_FLAGS) bash

shell-exec: image ## Batch twin of shell: make shell-exec CMD='...' | SCRIPT=<path under /work>
	@[ -n "$(SCRIPT)$(CMD)" ] || { echo "usage: make shell-exec CMD='...' | SCRIPT=<path under /work>" >&2; exit 2; }
	$(CONTAINER_CMD) run $(SHELL_RUN_FLAGS) \
	  bash -c 'cd /work && $(if $(CMD),$(CMD),exec bash $(SCRIPT))'

clean: ## Remove build trees and bldInstall/ (keeps checkout/ and runDir/)
	rm -rf build-cmake build-container bldInstall

distclean: clean ## clean + remove the builder image
	-$(CONTAINER_CMD) rmi -f $(IMAGE)
