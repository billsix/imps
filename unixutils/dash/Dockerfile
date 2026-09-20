# dash build toolchain — Fedora 44.
#
# dash is documentation-only in imps: this image exists ONLY to compile the
# pinned source, so `make check-comment-only` can PROVE the doc-comment /
# doc-region streams change nothing the C compiler sees (the unixutils family's
# one hard invariant). Nothing here is run as a shell for real.
#
# dash builds with GNU autotools in-tree (./autogen.sh && ./configure && make);
# the arith parser (arith_yacc.c) is hand-written and committed, so no yacc/lex
# is needed. libedit is optional (--with-libedit) and left off — a bare build
# needs only a C compiler and the autotools.
FROM registry.fedoraproject.org/fedora:44

# The dnf cache idiom (keepcache so the --mount cache is populated), then the
# toolchain: gcc + make to compile, autoconf/automake (aclocal, autoheader,
# automake --add-missing, autoconf) for ./autogen.sh, and git + gcc for the
# comment-only gate (tools/prove_comment_only.sh strips comments with
# `gcc -fpreprocessed` and compares). diffutils/findutils for the gate scripts.
RUN --mount=type=cache,target=/var/cache/libdnf5 \
    --mount=type=cache,target=/var/lib/dnf \
    echo 'keepcache=True' >> /etc/dnf/dnf.conf \
 && dnf upgrade -y \
 && dnf install -y \
        gcc make autoconf automake \
        git diffutils findutils gawk sed grep \
 && dnf clean all

WORKDIR /src
