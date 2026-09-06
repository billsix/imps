#!/usr/bin/env bash
# build.sh — build the book. FORMAT defaults to html; pass pdf or epub.
# Runs from the book dir; the docs literalinclude ../Ghostship source, which
# must be present (fetch+patch the game checkout first).
set -e
cd "$(dirname "$0")/.." 2>/dev/null || true
FORMAT="${1:-html}"
mkdir -p output
case "$FORMAT" in
  html) python3 -m sphinx -b html   docs output/html ;;
  epub) python3 -m sphinx -b epub   docs output/epub ;;
  pdf)  python3 -m sphinx -b latex  docs output/latex && \
        make -C output/latex LATEXMKOPTS="-lualatex" all-pdf ;;
  *) echo "usage: build.sh [html|pdf|epub]"; exit 2 ;;
esac
