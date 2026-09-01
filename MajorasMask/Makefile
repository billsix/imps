SHELL  := /bin/bash
# Builder variant: 'ci' (default — mirrors upstream CI: ubuntu 22.04 + gcc-12,
# Kitware cmake) or '2604' (ubuntu 26.04, distro-default gcc-15/cmake).
# Usage: make appimage VARIANT=2604
# Each variant gets its own image tag so both can coexist and you can tell
# which one built an artifact; the default keeps the plain tag.
VARIANT    ?= ci
DOCKERFILE := $(if $(filter 2604,$(VARIANT)),Dockerfile.ubuntu26.04,Dockerfile)
IMAGE      := $(if $(filter ci,$(VARIANT)),2ship-builder:latest,2ship-builder-$(VARIANT):latest)
# Repo part of IMAGE (drops the ":tag"), used for the export tarball filename.
IMAGE_BASE := $(firstword $(subst :, ,$(IMAGE)))
# The imps-managed upstream checkout (created by fetch.sh, patched by apply.sh).
# `make build` compiles whatever state the checkout is in — normally the pin
# with the patch series applied.
SRC    := $(CURDIR)/2ship2harkinian
OUT    := $(CURDIR)/out
# Working directory for `make run`. 2ship writes its files (saves, config, mods)
# into the cwd, so we run from here — the same runDir/ that run.sh uses for the
# host build, and `make clean` does NOT wipe it, to keep save data across
# rebuilds.
RUN_DIR := $(CURDIR)/runDir
NPROC  := $(shell nproc)
UID    := $(shell id -u)
GID    := $(shell id -g)

# Extra flags for every container `run`. Auto-set when running nested inside a
# runClaudeInContainer/runCrushInContainer sandbox (which exports
# NESTED_PODMAN=1); empty — and byte-identical behavior — on a normal host.
# Overridable: make build PODMAN_RUN_FLAGS='--cgroups=disabled --network=host'
PODMAN_RUN_FLAGS ?= $(if $(filter 1,$(NESTED_PODMAN)),--cgroups=disabled)

# :z relabels the bind mount for SELinux (Fedora). Harmless on systems without SELinux.
# --userns=keep-id maps your host UID into the container so bind-mounted files
# stay writable; under rootless podman, --user with subuids breaks bind mounts.
PODMAN_RUN = podman run --rm $(PODMAN_RUN_FLAGS) \
        -v $(SRC):/src:z \
        -v $(OUT):/out:z \
        --userns=keep-id \
        -e HOME=/tmp \
        $(IMAGE)

.PHONY: help image image-export image-import build appimage run shell clean distclean

help:
	@echo "Targets:"
	@echo "  make image     - build the Podman image (~10 min first time, cached after)"
	@echo "                   (VARIANT=ci [default, ubuntu 22.04 CI mirror] or VARIANT=2604 [ubuntu 26.04])"
	@echo "  make image-export - save the built image to a timestamped tar here"
	@echo "  make image-import - load an image tar: make image-import FILE=foo.tar"
	@echo "  make build     - compile 2s2h.elf inside the container"
	@echo "  make appimage  - produce out/2ship.appimage"
	@echo "  make run       - run out/2ship.appimage from runDir/ (saves land in runDir/)"
	@echo "  make shell     - interactive shell in the build container"
	@echo "  make clean     - wipe the container build dir and out/"
	@echo "  make distclean - clean + remove the Podman image"

# The build CONTEXT is the checkout, because the Dockerfile bind-mounts
# .github/workflows/apt-deps.txt out of it (context-relative path); the
# Dockerfile itself lives here in imps. Fetch first if the checkout is missing.
image:
	@[ -d $(SRC) ] || ./fetch.sh
	podman build -t $(IMAGE) -f $(DOCKERFILE) $(SRC)

# Archive the built image to a timestamped tar and reload it without a rebuild
# (move it to an offline/air-gapped machine, or snapshot a known-good build).
# No `image` prerequisite: `save` errors cleanly if nothing is built rather than
# kicking off a ~10 min rebuild. `save`/`load` start no container, so they need
# no --cgroups=disabled and run fine nested.
image-export:
	podman save $(IMAGE) -o $(IMAGE_BASE)-$(shell date +%m-%d-%Y_%H-%M-%S).tar

image-import:
	@test -n "$(FILE)" || { echo 'usage: make image-import FILE=foo.tar' >&2; exit 1; }
	podman load -i $(FILE)

$(OUT):
	mkdir -p $(OUT)

# Container build dir is build-cmake/ INSIDE the checkout (/src/build-cmake) —
# separate from the sibling build-cmake/ that the host-side build.sh uses, so
# the two builds never clobber each other.
build: image | $(OUT)
	$(PODMAN_RUN) bash -c '\
		set -euxo pipefail; \
		cmake -S /src -B /src/build-cmake -GNinja \
		      -DCMAKE_BUILD_TYPE=Release -DBUILD_REMOTE_CONTROL=1; \
		cmake --build /src/build-cmake --target Generate2ShipOtr -j$(NPROC); \
		cmake --build /src/build-cmake -j$(NPROC); \
	'

appimage: build
	$(PODMAN_RUN) bash -c '\
		set -euxo pipefail; \
		cd /src/build-cmake && cpack -G External; \
		shopt -s nullglob; \
		artifacts=(/src/build-cmake/*.appimage /src/_packages/*.appimage); \
		if [ $${#artifacts[@]} -eq 0 ]; then \
		  echo "ERROR: no .appimage produced" >&2; exit 1; \
		fi; \
		cp "$${artifacts[0]}" /out/2ship.appimage; \
		chmod +x /out/2ship.appimage; \
	'
	@echo "==> AppImage: $(OUT)/2ship.appimage"

# Run the built AppImage on the HOST -- it needs a display / GPU / audio, so it
# does NOT go through the headless build container. We cd into runDir/ first,
# because 2ship stores its files (saves, config, mods) in the current working
# directory, then launch the AppImage by a relative path ("../out/..."). No
# `appimage` prerequisite: error cleanly if it's not built rather than kicking
# off a ~10 min container build. Pass extra args with `make run ARGS="..."`.
run:
	@test -x $(OUT)/2ship.appimage || { echo "no AppImage at $(OUT)/2ship.appimage -- run 'make appimage' first" >&2; exit 1; }
	@mkdir -p $(RUN_DIR)
	cd $(RUN_DIR) && ../out/2ship.appimage $(ARGS)

shell: image | $(OUT)
	podman run --rm -it $(PODMAN_RUN_FLAGS) \
	    -v $(SRC):/src:z -v $(OUT):/out:z \
	    --userns=keep-id -e HOME=/tmp \
	    $(IMAGE) bash

clean:
	rm -rf $(SRC)/build-cmake $(SRC)/_packages $(OUT)

distclean: clean
	-podman rmi -f $(IMAGE)
