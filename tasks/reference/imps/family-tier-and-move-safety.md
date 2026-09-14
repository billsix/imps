# Reference: the family tier, and why moving a project folder is safe

> **Provenance:** harvested 2026-09-07 from the completed task
> `tasks/archive/imps/2026/09/07/imps-family-folder-restructure.md`, which
> inserted the `n64/` family tier on 2026-09-02. Verified against the tree at
> harvest time.

## What the family tier is

Projects group by **the kind of thing they patch**: `imps/n64/<Game>/` for the
HarbourMasters N64 ports. The tier exists so Claude Code's ancestor-`CLAUDE.md`
loading pulls a family's concrete contract **only** for sessions inside that
family — an N64 session gets `n64/CLAUDE.md`, and a future family's session
never pays for it.

The four-tier design (master → family → project → `tasks/reference/`) is
summarized in the master `CLAUDE.md` ("Documentation structure") and described in
full in `tasks/reference/imps/documentation-structure.md`; this doc does not
duplicate it. What follows is the part that is *not* written down there.

## Moving a project folder is safe — the check, and why

Verified 2026-09-02, and the reason the restructure was a docs-and-layout change
with near-zero risk to anything that builds or runs. **Re-run this check before
any future regrouping** (a new family, a project moving between families):

| What | Why it survives a move |
|---|---|
| `fetch.sh` / `apply.sh` / `build.sh` / `run.sh` | All begin `cd "$(dirname "$0")"` and use only paths **inside their own project folder**. The single `../` is `run.sh`'s `cd runDir && ../bldInstall/…` — siblings within the project. None reach the imps root. |
| `.gitignore` | Per-project (each project dir and each checkout has its own). There is no root `.gitignore` carrying project-path patterns. |
| `patches/` | Apply **inside the checkout**, which lives inside the project folder wherever that folder sits. **No patch regeneration is needed** — do not run `git format-patch` for a move. |

What does **not** survive a move, and must be rewritten: relative links in docs.
Project docs reference the unmoved shared `tasks/` tree as `../tasks/…`, and task
and reference docs reference project folders by name — both gain or lose a path
segment. The 2026-09-02 move did that with reviewed scripts under
`tasks/adhoc/imps-family-folder-restructure/` (removed at archive; recoverable
from git history).

**The rule this yields:** a project folder is self-contained by design, so
regrouping is a *documentation* problem, never a build problem. If a future
change makes a script reach outside its project folder, that property is lost —
don't let it happen.

## The second family went to a sibling repo instead

The restructure anticipated an `openstax/` family beside `n64/`. That is **not**
what happened: the OpenStax textbook port lives in the sibling repo
**[impo](https://github.com/billsix/impo)**, split out to keep imps small (its
committed OpenStax content is large). The `n64/` tier remains worthwhile on its
own — it is what keeps the family contract out of the master doc.

The archived task carries the full 2026-09-02 OpenStax survey — the 16
`osbooks-*` repos, what the `latex`-branch delta contains (a ~27-file shared
CNXML→LaTeX toolchain, plus thousands of fetched assets in some books), the
decision that fetched content **is** wanted tracked, and four unanswered design
questions (patch-vs-subtree carrier, shared-vs-per-book toolchain, build
contract, sequencing). **Those questions now belong to impo**, not imps; they are
preserved in the archive because that is where the research was done.
