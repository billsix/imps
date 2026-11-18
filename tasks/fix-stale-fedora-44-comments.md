# Fix stale "Fedora 44" mentions in comments and docs

**Status:** open
**Priority:** 6
**Difficulty:** 1
**Started:** 2026-11-18 (William Emerison Six <billsix@gmail.com>)

## BLUF

Every Dockerfile here is already `FROM registry.fedoraproject.org/fedora:45`, but comments,
`##` help strings and docs still say "Fedora 44". Change them to 45. Done = `git grep` finds no
Fedora 44 mention outside `tasks/archive/`.

## Files

- `android/fossify/CLAUDE.md`
- `android/fossify/Dockerfile`
- `android/fossify/Makefile`
- `android/fossify/README.md`
- `games/gzdoom/CLAUDE.md`
- `games/gzdoom/Dockerfile`
- `games/gzdoom/Makefile`
- `games/gzdoom/README.md`
- `unixutils/dash/CLAUDE.md`
- `unixutils/dash/Dockerfile`
- `unixutils/dash/Makefile`
- `unixutils/ripgrep/Dockerfile`
- `unixutils/ripgrep/Makefile`
