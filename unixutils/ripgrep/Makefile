SHELL          := /bin/bash
CONTAINER_CMD  := podman
CONTAINER_NAME := ripgrep-doc-builder
IMAGE          := $(CONTAINER_NAME):latest
# The carrier dir (this repo folder) is mounted here; the checkout, patches and
# scripts all live under it, so fetch/apply/build/check all resolve.
REPO_MOUNT     := /ripgrep

.DEFAULT_GOAL := help

# Extra flags for every container `run` (never `build`). Auto-set when running
# nested inside a runClaudeInContainer/runCrushInContainer sandbox (which
# exports NESTED_PODMAN=1); empty — and byte-identical behavior — on a host.
PODMAN_RUN_FLAGS ?= $(if $(filter 1,$(NESTED_PODMAN)),--cgroups=disabled)

# The whole mount/flag block shared by `shell` and `shell-exec` so the two
# cannot drift. :z relabels the bind mount for SELinux (harmless without it).
SHELL_RUN_FLAGS = --rm $(PODMAN_RUN_FLAGS) \
        -v $(CURDIR):$(REPO_MOUNT):z \
        -e HOME=/tmp \
        $(IMAGE)

.PHONY: help fetch apply image build check-comment-only shell shell-exec \
        image-export image-import clean

help:  ## Show this help.
	@grep --extended-regexp '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

fetch:  ## Clone ripgrep into checkout/ and detach at the pinned tag (host).
	./fetch.sh

apply:  ## git am the comment-only patch streams onto the checkout (host).
	./apply.sh

image:  ## Build the Fedora-44 + Rust builder image.
	$(CONTAINER_CMD) build -t $(IMAGE) -f Dockerfile .

build: image  ## cargo build the checkout inside the container.
	@[ -d checkout ] || ./fetch.sh
	$(CONTAINER_CMD) run $(SHELL_RUN_FLAGS) \
	    bash -c 'cd $(REPO_MOUNT)/checkout && cargo build'

# The docs-only family gate: prove patches/docs/ is comment-only, then that it
# still compiles. Runs the same script the host uses (check-comment-only.sh).
check-comment-only: image  ## Prove the docs stream is comment-only + compiles.
	@[ -d checkout ] || { ./fetch.sh && ./apply.sh; }
	$(CONTAINER_CMD) run $(SHELL_RUN_FLAGS) \
	    bash -c 'cd $(REPO_MOUNT) && ./check-comment-only.sh'

shell: image  ## Interactive shell in the builder container (repo at /ripgrep).
	$(CONTAINER_CMD) run -it $(SHELL_RUN_FLAGS) bash

# Batch twin of `shell`: run a repo-relative SCRIPT or an inline CMD in the same
# container environment, no TTY. Depends on `image` (never `check-comment-only`
# or any mutating target) so a runner never reformats/rebuilds as a side effect.
shell-exec: image  ## Run SCRIPT=<path> or CMD='...' in the container, no TTY.
	@[ -n "$(SCRIPT)$(CMD)" ] || { echo "usage: make shell-exec SCRIPT=<repo-relative path> | CMD='...'" >&2; exit 2; }
	$(CONTAINER_CMD) run $(SHELL_RUN_FLAGS) \
	    bash -c 'cd $(REPO_MOUNT) && $(if $(CMD),$(CMD),exec bash $(SCRIPT))'

image-export:  ## Save the builder image to a timestamped tar here.
	$(CONTAINER_CMD) save $(CONTAINER_NAME) -o $(CONTAINER_NAME)-$(shell date +%m-%d-%Y_%H-%M-%S).tar

image-import:  ## Load an image tar: make image-import FILE=foo.tar
	@test -n "$(FILE)" || { echo 'usage: make image-import FILE=foo.tar' >&2; exit 1; }
	$(CONTAINER_CMD) load -i $(FILE)

clean:  ## Remove the checkout's build output (keeps the checkout + patches).
	rm -rf checkout/target
