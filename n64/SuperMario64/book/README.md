# How a Production Game Is Built — the Mario 64 book

A Sphinx book that teaches how a real 3D game is made, by reading the Super
Mario 64 (Ghostship) source. For a reader who has done
[Model View Projection](https://github.com/billsix/modelviewprojection).

## Build

```
[CONTAINER] make html      # HTML  -> output/html/
[CONTAINER] make epub      # EPUB  -> output/epub/
[CONTAINER] make pdf       # PDF   -> output/latex/ (LuaLaTeX)
[CONTAINER] make all       # all three
[HOST]      python3 -m sphinx -b html docs output/html   # quick HTML, no container
```

> The chapters `literalinclude` code from `../Ghostship/` by **named
> doc-region**, so the game checkout must be fetched and patched
> first (`cd .. && ./fetch.sh && ./apply.sh`). `apply.sh` applies BOTH patch
> lanes — the game tree AND the libultraship submodule — so the doc-region
> markers the chapters `literalinclude` are all present.

## Where the detail lives

Each chapter is the student-facing narrative; the exhaustive per-topic notes
are the imps reference set at `../../../tasks/reference/mario64/`.

Design + status: `../../../tasks/mario64-sphinx-book.md`.
