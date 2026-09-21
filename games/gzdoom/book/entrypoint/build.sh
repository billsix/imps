#!/usr/bin/env bash
# build.sh — build the book. FORMAT defaults to html; pass pdf or epub.
# Run from the book root (the Makefile sets -w /work/book); docs literalinclude
# ../Ghostship source, which must be present (fetch+apply the game checkout).
set -e
[ -d /work/book ] && cd /work/book
FORMAT="${1:-html}"
mkdir -p output
case "$FORMAT" in
  html) python3 -m sphinx -b html  docs output/html ;;
  epub) python3 -m sphinx -b epub  docs output/epub ;;
  pdf)  python3 -m sphinx -b latex docs output/latex && \
        make -C output/latex all-pdf ;;
  *) echo "usage: build.sh [html|pdf|epub]"; exit 2 ;;
esac
