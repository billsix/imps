# Reference: imps documentation structure — the four tiers, and why

> **Provenance:** the rationale relocated 2026-09-13 from the master `CLAUDE.md`
> ("Documentation structure — four tiers") and the `runDir/` structural-safety
> proof, as part of the CLAUDE.md trim (`tasks/trim-claude-md.md`). The master
> keeps a lean 4-item tier list + family index and points here for the mechanics
> and the decisions behind them. The complementary "why the family tier is safe to
> move" note is `tasks/reference/imps/family-tier-and-move-safety.md`.

## The dividing principle (full statement)

The dividing principle: **a patch carries only what must live inside
upstream's own files — code. Everything that is purely the maintainer's
(CLAUDE.md content, task docs, reference docs) lives natively in imps**,
where editing it is a plain file edit (no patch regeneration), it exists
whether or not a checkout does, and it never rides along in a pin-bump
rebase.

## The four tiers and the ancestor-loading mechanics

The tiers exploit Claude Code's ancestor CLAUDE.md loading (a session
working anywhere under `imps/`, including deep inside a project's checkout,
auto-loads every CLAUDE.md on the path from cwd to the repo root). Projects
are grouped into **family folders** by the kind of thing they patch
(currently `n64/` for the HarbourMasters game ports), and the family tier
sits between the master and the project so that a
family's specialized contract loads **exactly** for that family's sessions
and never bloats another's:

1. **`CLAUDE.md` (this file, the master)** — lean and **family-agnostic**:
   what imps is, the cross-family contracts (patch philosophy, the generic
   self-contained-folder principle, the unsigned-commits rule, the
   tasks/archive convention), and a one-line-per-family index pointing at
   tier 2.
2. **`<family>/CLAUDE.md`** (e.g. `n64/CLAUDE.md`) — that family's concrete
   build/patch contract, its derived-artifact drift table and gotchas, and a
   one-line-per-project index pointing at tier 3. Auto-loads for any session
   under that family folder, and only those — a session in one family never
   loads another family's detail.
3. **`<family>/<Project>/CLAUDE.md`** — that project's operational facts:
   upstream URL, pin and why it sits there, the patch list one line each,
   build/run gotchas, and an index of its tier-4 reference docs. Sits
   OUTSIDE the checkout but is its ancestor, so it auto-loads exactly when a
   session works inside that project.
4. **`tasks/reference/<project>/*.md`** — the deep-dive reference docs,
   one subdirectory per project (e.g. `tasks/reference/ocarina/`). Pointed
   at from tier 3 — plain pointers, not `@`-imports, so one project's
   large doc set never bloats sessions about another project.

## tasks/ is project-keyed, and archives are per-project (overriding the global convention)

`tasks/` is shared across all projects at the imps root (this repo is the
one that versions them): in-flight task docs at `tasks/*.md` (named with a
project prefix, e.g. `ocarina-…`), reference docs namespaced per project
as above. **`tasks/` stays project-keyed regardless of family folder** — a
project's reference docs live at `tasks/reference/<project>/` and its archives
at `tasks/archive/<project>/…` using the **project name** as the key, never a
family segment (project names stay unique across families, so no collision).
**Archives are per-project — this overrides the global convention's flat date
layout for this repo** (decided with William Emerison Six
<billsix@gmail.com>, 2026-09-01): a completed task moves to
`tasks/archive/<project>/<YYYY>/<MM>/<DD>/<slug>.md` — project first, then
the standard date buckets. Repo-wide tasks (not about one game) use
`imps` as their project directory.

## Why `runDir/` is structurally safe today (the proof)

`runDir/` IS SACRED — never delete or rewrite it (William Emerison Six
<billsix@gmail.com>, 2026-09-07). It holds irreplaceable personal state: save
files (`runDir/Save/`), the extracted `.o2r` (regenerable only from the
maintainer's own ROM), controller/graphics config, and installed texture-pack
mods under `runDir/mods/`. **Reworking patches must never touch it.** This is
structurally safe today and must stay that way:

- `runDir/` is a **sibling** of the upstream checkout, not inside it, so every
  `git` operation on the checkout (`reset --hard`, `clean -fd`, `am`, `mv`)
  cannot reach it by construction. Keep it that way — never place it inside the
  checkout.
- `fetch.sh`, `apply.sh` and `build.sh` never mention `runDir`; only `run.sh`
  touches it, and only via `mkdir -p`.
- The Makefile's `clean` removes `build-cmake/`, `_packages/` and `out/` — **not
  `runDir/`**. A `clean` target that deletes `runDir` would be a bug.

When rewriting a patch series, work only inside the checkout, and scope any
`git clean` to the source subtree (e.g. `git clean -fd soh`) rather than the
whole tree.
