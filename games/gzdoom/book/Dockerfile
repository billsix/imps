FROM registry.fedoraproject.org/fedora:44

# Sphinx book toolchain: HTML (furo), EPUB, and PDF via LuaLaTeX (needed for
# the Unicode math the source and notes use). Graphviz renders the diagrams.
# Dependency install kept in one RUN with the dnf cache mount (build plumbing).
RUN  --mount=type=cache,target=/var/cache/libdnf5 \
     --mount=type=cache,target=/var/lib/dnf \
     echo "keepcache=True" >> /etc/dnf/dnf.conf && \
     dnf upgrade -y && \
     dnf install -y \
        sphinx python3-furo python3-myst-parser \
        python3-sphinx-latex \
        graphviz \
        texlive texlive-luahbtex texlive-luatex85 texlive-fontspec \
        texlive-gnu-freefont texlive-polyglossia latexmk \
        make findutils

COPY entrypoint/*.sh /usr/local/bin/
ENTRYPOINT ["/bin/bash"]
