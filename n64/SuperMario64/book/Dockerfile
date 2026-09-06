FROM registry.fedoraproject.org/fedora:44

# Sphinx book toolchain: HTML (furo), EPUB, and PDF via LuaLaTeX (needed for
# the Unicode math the source and notes use). Graphviz renders the diagrams.
# Dependency install kept in one RUN with the dnf cache mount (build plumbing).
RUN  --mount=type=cache,target=/var/cache/libdnf5 \
     --mount=type=cache,target=/var/lib/dnf \
     echo "keepcache=True" >> /etc/dnf/dnf.conf && \
     dnf upgrade -y && \
     dnf install -y \
        python3-sphinx python3-furo python3-myst-parser \
        graphviz \
        texlive-luahbtex texlive-latexmk texlive-fontspec gnu-free-fonts \
        texlive-fncychap texlive-wrapfig texlive-capt-of texlive-needspace \
        texlive-tabulary texlive-framed texlive-titlesec texlive-varwidth \
        texlive-fancyhdr texlive-multirow texlive-threeparttable texlive-eqparbox \
        make findutils

COPY entrypoint/*.sh /usr/local/bin/
ENTRYPOINT ["/bin/bash"]
