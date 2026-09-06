.DEFAULT_GOAL := help
CONTAINER_CMD  = podman
CONTAINER_NAME = sm64book

# Auto-set when running nested inside a runClaudeInContainer/runCrushInContainer
# sandbox (which exports NESTED_PODMAN=1); empty on a normal host.
PODMAN_RUN_FLAGS ?= $(if $(filter 1,$(NESTED_PODMAN)),--cgroups=disabled)

# The book's docs `literalinclude` ../Ghostship source, so we mount the whole
# SuperMario64 dir (parent) — both book/ and Ghostship/ must be visible under
# one root for the relative paths to resolve.
PARENT := $(shell cd .. && pwd)
SHELL_RUN_FLAGS = --rm $(PODMAN_RUN_FLAGS) -v $(PARENT):/work:Z -w /work/book

image: ## Build the podman image for the book toolchain
	$(CONTAINER_CMD) build -t $(CONTAINER_NAME) .

html: image ## Build HTML into output/html
	$(CONTAINER_CMD) run $(SHELL_RUN_FLAGS) $(CONTAINER_NAME) /usr/local/bin/build.sh html

epub: image ## Build EPUB into output/epub
	$(CONTAINER_CMD) run $(SHELL_RUN_FLAGS) $(CONTAINER_NAME) /usr/local/bin/build.sh epub

pdf: image ## Build PDF (LuaLaTeX) into output/latex
	$(CONTAINER_CMD) run $(SHELL_RUN_FLAGS) $(CONTAINER_NAME) /usr/local/bin/build.sh pdf

all: html epub pdf ## Build all three formats

shell: image ## Interactive shell in the book build env
	$(CONTAINER_CMD) run -it $(SHELL_RUN_FLAGS) $(CONTAINER_NAME) /usr/local/bin/shell.sh

shell-exec: image ## Batch: make shell-exec CMD='...'  (no TTY)
	@[ -n "$(CMD)$(SCRIPT)" ] || { echo "usage: make shell-exec CMD='...' | SCRIPT=path"; exit 2; }
	$(CONTAINER_CMD) run $(SHELL_RUN_FLAGS) $(CONTAINER_NAME) /usr/local/bin/shell.sh -c '$(if $(CMD),$(CMD),exec bash $(SCRIPT))'

clean: ## Remove built output
	rm -rf output docs/_build

help:
	@grep --extended-regexp '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

.PHONY: image html epub pdf all shell shell-exec clean help
