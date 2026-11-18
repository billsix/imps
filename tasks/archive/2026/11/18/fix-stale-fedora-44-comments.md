# Fix stale "Fedora 44" mentions in comments and docs (done)

**Done:** 2026-11-18 (William Emerison Six <billsix@gmail.com>)

Every Dockerfile was already `FROM registry.fedoraproject.org/fedora:45`, but comments, `##`
help strings and docs still said "Fedora 44". They were changed to 45 in the
`android/fossify`, `games/gzdoom`, `unixutils/dash` and `unixutils/ripgrep` Dockerfiles,
Makefiles, CLAUDE.md and README files, the `android/`, `games/` and `unixutils/` CLAUDE.md
summaries, and `tasks/reference/gzdoom/build-and-cli-wad-repro.md`'s description of the
container path. The "Fedora 44/45 ships no `java-17-openjdk`" statements in `android/fossify`
were checked against Fedora 45 (`dnf repoquery --releasever=45` lists only java-25 and
java-latest), so they are still true.

Left as written on purpose, because each records what was true on its date: the n64 CLAUDE.md
"verified in a fedora:44 container" lines, the `fedora44Fixes` fork-branch name, the
MajorasMask patch header, the PaperMario host-build notes, dated environment lines in
`tasks/reference/`, and the status lines of the open `tasks/fossify-refdocs-and-book.md` and
`tasks/gzdoom-port-and-cli-wad-patch.md`.
