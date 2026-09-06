#!/usr/bin/env bash
# shell.sh — interactive/batch shell in the book build env. `exec bash "$@"`
# powers `make shell-exec`.
set -e
[ -d /work/book ] && cd /work/book
exec bash "$@"
