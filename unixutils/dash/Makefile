SHELL  := /bin/bash
IMAGE  := dash-builder:latest
# Repo part of IMAGE (drops ":tag"), for the export tarball name.
IMAGE_BASE := $(firstword $(subst :, ,$(IMAGE)))
# The imps-managed upstream checkout (created by fetch.sh, patched by apply.sh).
# `make build` compiles whatever state the checkout is in — normally the pin
# with the comment-only doc series applied.
SRC    := $(CURDIR)/checkout
NPROC  := $(shell nproc)

# Extra flags for every container `run` (never `build`). Auto-set when running
# nested inside a runClaudeInContainer/runCrushInContainer sandbox (which
# exports NESTED_PODMAN=1); empty — and byte-identical behavior — on a host.
PODMAN_RUN_FLAGS ?= $(if $(filter 1,$(NESTED_PODMAN)),--cgroups=disabled)

# --userns=keep-id maps the host UID in so bind-mounted files stay writable
# under rootless podman; omitted nested (no subordinate IDs there).
USERNS_FLAG ?= $(if $(filter 1,$(NESTED_PODMAN)),,--userns=keep-id)

# Shared run block for `shell`/`shell-exec` so they cannot diverge. :z relabels
# the bind mount for SELinux (harmless without it).
SHELL_RUN_FLAGS = --rm $(PODMAN_RUN_FLAGS) \
        -v $(SRC):/src:z \
        $(USERNS_FLAG) \
        -e HOME=/tmp \
        $(IMAGE)

.PHONY: help fetch apply image image-export image-import build check-comment-only \
        shell shell-exec clean distclean

help:  ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

fetch:  ## Clone dash into checkout/ and detach at the pin
	./fetch.sh

apply:  ## git am the comment-only doc streams onto the pinned checkout
	./apply.sh

image:  ## Build the Fedora-44 dash build-toolchain image
	podman build -t $(IMAGE) -f Dockerfile .

image-export:  ## Save the built image to a timestamped tar here
	podman save $(IMAGE) -o $(IMAGE_BASE)-$(shell date +%m-%d-%Y_%H-%M-%S).tar

image-import:  ## Load an image tar: make image-import FILE=foo.tar
	@test -n "$(FILE)" || { echo 'usage: make image-import FILE=foo.tar' >&2; exit 1; }
	podman load -i $(FILE)

# Compile the checkout in-tree (autotools: autogen → configure → make). Fetches
# first if the checkout is missing. Proves the source (pinned, or with the doc
# series applied) still builds.
build: image  ## Compile the dash checkout in the container (autotools)
	@[ -d $(SRC) ] || ./fetch.sh
	podman run $(SHELL_RUN_FLAGS) bash -c '\
		set -euxo pipefail; \
		cd /src; \
		./autogen.sh; \
		./configure; \
		make -j$(NPROC); \
		./src/dash -c "echo dash built: \$$0 works"; \
	'

# Prove the doc-comment / doc-region streams change nothing the compiler sees.
# Pure git + gcc (tools/prove_comment_only.sh, gcc -fpreprocessed) — runs on the
# host or in the image; needs no build, so no `image` prerequisite.
check-comment-only:  ## Prove patches/docs + patches/book are comment-only
	./check_comment_only.sh

shell: image  ## Interactive shell in the build container
	podman run -it $(SHELL_RUN_FLAGS) bash

# Batch twin of `shell`: run a command/script in the same env and exit.
#   make shell-exec CMD='cd /src && ./configure'
#   make shell-exec SCRIPT=/src/some/script.sh
shell-exec: image  ## Run CMD=... or SCRIPT=... in the build container, non-interactively
	@[ -n "$(SCRIPT)$(CMD)" ] || { echo "usage: make shell-exec CMD='...' | SCRIPT=/src/...' " >&2; exit 2; }
	podman run $(SHELL_RUN_FLAGS) \
		bash -c 'cd /src && $(if $(CMD),$(CMD),exec bash $(SCRIPT))'

clean:  ## Remove the autotools build artifacts from the checkout
	-@[ -d $(SRC) ] && $(MAKE) -C $(SRC) distclean 2>/dev/null || true
	-rm -f $(SRC)/configure $(SRC)/config.status $(SRC)/config.log

distclean: clean  ## clean + remove the podman image
	-podman rmi -f $(IMAGE)
