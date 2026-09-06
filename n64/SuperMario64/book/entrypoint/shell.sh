#!/usr/bin/env bash
# shell.sh — interactive/batch shell in the book build env. `exec bash "$@"`
# powers `make shell-exec`.
set -e
[ -d /book ] && cd /book
exec bash "$@"
