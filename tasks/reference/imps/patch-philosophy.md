# Reference: patch philosophy — why imps exists, what it buys, the tradeoffs

> **Provenance:** relocated 2026-09-13 from the master `CLAUDE.md`
> ("Patch philosophy — must keep working; upstream where it can") as part of the
> CLAUDE.md trim (`tasks/trim-claude-md.md`). The master keeps the ranked-goals
> summary and the `check_patches_apply.sh` gate command inline and points here for
> the full goal statements, the "what imps buys" list, the upstream-vs-pin-bump
> tradeoff, and the patch-lifecycle consequence.

## The two goals, in full (the ranking matters)

(William Emerison Six <billsix@gmail.com>, 2026-09-01; reframed 2026-09-07.)
Two goals, and the ranking matters:

0. **The patches must keep working for the maintainer over time, across
   machines, as he pulls from upstream.** This is the primary goal and the
   reason imps exists — see the paragraphs below. Upstreaming is the ideal
   outcome and has proven hard in practice, so it is the aspiration, not the
   mechanism.
1. **Shape for upstreaming anyway, where the change plausibly fits.** If a change is something
   upstream would plausibly accept — a bug fix, a portability fix, a doc
   correction — shape it as a **standalone, submission-ready patch**:
   its own commit, a commit message written for an upstream reviewer
   (problem → cause → fix, like the banjo series), no entanglement with
   personal changes. Never fold an upstreamable fix into a personal
   patch, and split a mixed change into two patches rather than ship one
   hybrid. Mark upstream candidates as such in the per-project
   CLAUDE.md patch list.
2. **Personal patches are maintained independently, indefinitely.**
   Changes upstream won't take (cheats, personal tweaks) are carried in
   the same series and **replayed onto newer upstream pins as time
   progresses** — that replay (the pin-bump operation below) is a core
   workflow, not an afterthought.

## What imps actually buys, and must keep buying

- **Repeatability across computers.** A pin + a patch series reproduces the
  same tree anywhere, with no per-project git branches to keep in sync between
  machines. That is the thing forks were failing to provide.
- **Survivable pin bumps.** The patches are replayed onto newer upstream
  commits as a routine operation; a patch's long-term rebase cost is a design
  consideration when writing it (prefer the port's event/enhancement layers over
  editing decomp internals).
- **No fork maintenance.** No branches, no merges, no divergence to reconcile —
  just a SHA and a folder of patches.
- **Coordination cost is real and deliberate to avoid.** Patching libultraship
  and its downstream consumers would mean keeping several projects in step; the
  patch-carrier design is what keeps that tractable rather than a standing
  obligation.

So when a choice arises between "shaped for upstream" and "survives the next
pin bump cleanly", both matter — but a patch that no longer applies has failed
at its primary job.

## Lifecycle consequence

Lifecycle consequence: an upstreamable patch is temporary — once merged
upstream, it retires at the next pin bump (the bump's `git am` will show
it as already applied, or the rebase drops it); a personal patch is
permanent and its long-term rebase cost is a design consideration when
writing it (prefer hooking the port's event/enhancement layers over
editing decomp internals — the mario64 cheats are the worked example).
