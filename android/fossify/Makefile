SHELL := /bin/bash
IMAGE := fossify-builder:latest
# Repo part of IMAGE (drops ":tag"), used for the export tarball filename.
IMAGE_BASE := $(firstword $(subst :, ,$(IMAGE)))

# Which upstream checkout a per-repo target acts on, and the Gradle task to
# compile inside it. Defaults document Commons (the deepest-documented repo, a
# flavorless library whose module is `commons`). The exemplar APPS carry product
# flavors, so their compile task is flavor-qualified (compileFOSSReleaseKotlin),
# NOT the bare compileReleaseKotlin a flavorless module has — override GRADLE_TASK
# for them, e.g.:
#   make build REPO=Gallery GRADLE_TASK=:app:compileFossReleaseKotlin
#   make build REPO=Phone   GRADLE_TASK=:app:compileFossReleaseKotlin
# (Gallery flavors: foss/gplay; Phone: core/foss/gplay — `foss` is the privacy
# build, and it is the flavor the image's Gradle cache is warmed for.)
REPO ?= Commons
GRADLE_MODULE ?= :commons
# compile only (no packaging/APK) — the cheapest task that still runs the Kotlin
# compiler over the module, which is all the comment-only proof needs.
GRADLE_TASK ?= $(GRADLE_MODULE):compileReleaseKotlin

# Extra flags for every container `run`. Auto-set when running nested inside a
# runClaudeInContainer/runCrushInContainer sandbox (which exports
# NESTED_PODMAN=1); empty — and byte-identical behavior — on a normal host.
# Threaded into every `run` below and NEVER into `build` (podman build rejects
# --cgroups and does not need it).
PODMAN_RUN_FLAGS ?= $(if $(filter 1,$(NESTED_PODMAN)),--cgroups=disabled)

# The whole carrier dir is mounted at /work so both checkout/<repo>/ and
# patches/<repo>/ are visible in-container. :z relabels for SELinux (Fedora).
# The share block SHELL and SHELL-EXEC hold in common (mounts + flags + image),
# so the interactive shell and its batch twin cannot drift apart.
SHELL_RUN_FLAGS = --rm $(PODMAN_RUN_FLAGS) \
        -v $(CURDIR):/work:z \
        -e HOME=/tmp \
        $(IMAGE)

.PHONY: help fetch apply image image-export image-import build check-comment-only shell shell-exec clean distclean

help: ## Show this help
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

fetch: ## Clone all upstreams in `repos` at their pins (host git)
	./fetch.sh

apply: ## Apply each repo's comment-only doc/book patch streams (host git)
	./apply.sh

image: ## Build the Fedora-44 Android/Gradle/JDK builder image
	podman build -t $(IMAGE) -f Dockerfile .

image-export: ## Save the built image to a timestamped tar here
	podman save $(IMAGE) -o $(IMAGE_BASE)-$(shell date +%m-%d-%Y_%H-%M-%S).tar

image-import: ## Load an image tar: make image-import FILE=foo.tar
	@test -n "$(FILE)" || { echo 'usage: make image-import FILE=foo.tar' >&2; exit 1; }
	podman load -i $(FILE)

# HEAVY. Compiles one module of REPO with its Gradle wrapper, OFFLINE against the
# Gradle dependency cache baked into the image at build time (see Dockerfile's
# warm step). --offline forces Gradle to resolve only from the baked cache, so
# this proves the exported image is offline-self-contained; a cache miss fails
# loudly rather than silently reaching the network. GRADLE_USER_HOME /
# ANDROID_USER_HOME come from the image ENV (both under /opt, the warmed layers).
build: image ## Compile REPO's GRADLE_MODULE in the container OFFLINE (heavy)
	podman run $(PODMAN_RUN_FLAGS) --rm \
	    -v $(CURDIR):/work:z -e HOME=/tmp $(IMAGE) \
	    bash -c 'set -euxo pipefail; cd /work/checkout/$(REPO) && ./gradlew --no-daemon --offline $(GRADLE_TASK)'

# The comment-only gate, via the SHARED, family-agnostic entry point at the repo
# root. It discovers this multi-repo project, reads patches/LANG (fossify →
# kotlin) and dispatches every repo's comment-only stream to
# tools/prove_comment_only_strip.py --lang kotlin. That stripper removes Kotlin
# comments/KDoc and byte-compares the pinned-vs-applied token stream per touched
# file — stronger than the old per-hunk "is this line a comment?" check, and it
# needs no Android SDK. Pure git + python3 — runs on the HOST, no container (the
# shared tools/ live above this carrier and are not mounted into the image).
check-comment-only: ## Prove all doc streams are comment-only (host: git + python3)
	../../tools/check_comment_only_streams.sh fossify

shell: image ## Interactive shell in the builder container
	podman run -it $(SHELL_RUN_FLAGS) bash

# Batch twin of `shell`: run a one-off command in the same env and exit.
#   make shell-exec CMD='cd checkout/Commons && ./gradlew tasks'
shell-exec: image ## Run CMD in the builder container and exit: make shell-exec CMD='...'
	@[ -n "$(CMD)" ] || { echo "usage: make shell-exec CMD='...'" >&2; exit 2; }
	podman run $(SHELL_RUN_FLAGS) bash -c 'cd /work && $(CMD)'

clean: ## Remove Gradle build outputs from every checkout
	rm -rf checkout/*/*/build checkout/*/build checkout/*/.gradle out

distclean: clean ## clean + remove the builder image
	-podman rmi -f $(IMAGE)
