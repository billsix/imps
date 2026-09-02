SHELL  := /bin/bash
IMAGE  := soh-builder:latest
# Repo part of IMAGE (drops the ":tag"), used for the export tarball filename.
IMAGE_BASE := $(firstword $(subst :, ,$(IMAGE)))
# The imps-managed upstream checkout (created by fetch.sh, patched by apply.sh).
# `make build` compiles whatever state the checkout is in — normally the pin
# with the patch series applied.
SRC    := $(CURDIR)/Shipwright
OUT    := $(CURDIR)/out
# Working directory for `make run` — the same runDir/ the host run.sh uses, so
# saves/config/oot.o2r are shared; `make clean` does NOT wipe it.
RUN_DIR := $(CURDIR)/runDir
NPROC  := $(shell nproc)

# Extra flags for every container `run`. Auto-set when running nested inside a
# runClaudeInContainer/runCrushInContainer sandbox (which exports
# NESTED_PODMAN=1); empty — and byte-identical behavior — on a normal host.
PODMAN_RUN_FLAGS ?= $(if $(filter 1,$(NESTED_PODMAN)),--cgroups=disabled)

# --userns=keep-id maps your host UID into the container so bind-mounted files
# stay writable under rootless podman. Inside the nested sandbox
# (NESTED_PODMAN=1) there are no subordinate IDs for keep-id to build its user
# namespace from — and the inner root already matches the mount owner — so the
# flag is omitted there. On a normal host: keep-id, byte-identical to before.
USERNS_FLAG ?= $(if $(filter 1,$(NESTED_PODMAN)),,--userns=keep-id)

# :z relabels the bind mount for SELinux (Fedora). Harmless without SELinux.
PODMAN_RUN = podman run --rm $(PODMAN_RUN_FLAGS) \
        -v $(SRC):/src:z \
        -v $(OUT):/out:z \
        $(USERNS_FLAG) \
        -e HOME=/tmp \
        $(IMAGE)

.PHONY: help image image-export image-import build appimage run shell clean distclean

help:
	@echo "Targets:"
	@echo "  make image     - build the Podman image (ubuntu 22.04 CI mirror)"
	@echo "  make image-export - save the built image to a timestamped tar here"
	@echo "  make image-import - load an image tar: make image-import FILE=foo.tar"
	@echo "  make build     - compile soh inside the container (incl. soh.o2r)"
	@echo "  make appimage  - produce out/soh.appimage"
	@echo "  make run       - run out/soh.appimage from runDir/"
	@echo "  make shell     - interactive shell in the build container"
	@echo "  make clean     - wipe the container build dir and out/"
	@echo "  make distclean - clean + remove the Podman image"

# The build CONTEXT is the checkout, because the Dockerfile bind-mounts
# linux-build-deps/apt.txt out of it (context-relative path).  Fetch first if
# the checkout is missing.
image:
	@[ -d $(SRC) ] || ./fetch.sh
	podman build -t $(IMAGE) -f Dockerfile $(SRC)

# Archive the built image to a timestamped tar / reload it without a rebuild.
# `save`/`load` start no container, so they run fine nested with no flags.
image-export:
	podman save $(IMAGE) -o $(IMAGE_BASE)-$(shell date +%m-%d-%Y_%H-%M-%S).tar

image-import:
	@test -n "$(FILE)" || { echo 'usage: make image-import FILE=foo.tar' >&2; exit 1; }
	podman load -i $(FILE)

$(OUT):
	mkdir -p $(OUT)

# Container build dir is build-cmake/ INSIDE the checkout (/src/build-cmake) —
# separate from the sibling build-cmake/ the host-side build.sh uses.
# GenerateSohOtr builds soh.o2r in-tree (CI does it in a separate job and
# downloads the artifact; same result).  Build flags mirror CI: Release +
# BUILD_REMOTE_CONTROL=1.
build: image | $(OUT)
	$(PODMAN_RUN) bash -c '\
		set -euxo pipefail; \
		cmake --no-warn-unused-cli -S /src -B /src/build-cmake -GNinja \
		      -DCMAKE_BUILD_TYPE:STRING=Release -DBUILD_REMOTE_CONTROL=1; \
		cmake --build /src/build-cmake --target GenerateSohOtr -j$(NPROC); \
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
		cp "$${artifacts[0]}" /out/soh.appimage; \
		chmod +x /out/soh.appimage; \
	'
	@echo "==> AppImage: $(OUT)/soh.appimage"

# Run the built AppImage on the HOST — it needs a display / GPU / audio.
# cd into runDir/ first (soh stores saves/config/oot.o2r in the cwd).
run:
	@test -x $(OUT)/soh.appimage || { echo "no AppImage at $(OUT)/soh.appimage -- run 'make appimage' first" >&2; exit 1; }
	@mkdir -p $(RUN_DIR)
	cd $(RUN_DIR) && ../out/soh.appimage $(ARGS)

shell: image | $(OUT)
	podman run --rm -it $(PODMAN_RUN_FLAGS) \
	    -v $(SRC):/src:z -v $(OUT):/out:z \
	    $(USERNS_FLAG) -e HOME=/tmp \
	    $(IMAGE) bash

clean:
	rm -rf $(SRC)/build-cmake $(SRC)/_packages $(OUT)

distclean: clean
	-podman rmi -f $(IMAGE)
