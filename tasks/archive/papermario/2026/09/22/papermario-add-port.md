# PaperMario: add PaperBoat as a new n64-family port

**Status:** DONE — archived 2026-09-22. Requested 2026-09-17 by William Emerison Six
<billsix@gmail.com>; pristine build executed 2026-09-21; ROM-import unit and first patch series
2026-09-22 (overnight); **host-verified 2026-09-22** by the maintainer: "building and using run.sh
works as is now". Durable knowledge lives in the reference docs (below); this is the work record.
**Priority:** 5 · **Difficulty:** 6 · **Project key:** papermario (`n64/PaperMario/`)

## BLUF

HarbourMasters' PaperBoat (Paper Mario 64 PC port) is a project in the `n64/` family: pinned at the
stable tag `1.0.1` (`424c220f0`), with `fetch.sh`/`apply.sh`/`build.sh`/`run.sh`, a three-patch
series on two lanes (command-line ROM import on Linux, a precise refusal of unsupported ROMs, the
libultraship Vulkan first-frame crash fix), and a `run.sh` that verifies/trims the ROM and seeds
OpenGL. Built, extraction-proven and crash-fixed headless in the sandbox; built and played on the
maintainer's host.

## What was done, in order

1. **2026-09-21 — pristine compile-as-is.** Read PaperBoat's own build docs and CI; it is
   libultraship-based but pins **JeodC forks** for both submodules (`external/libultraship`
   `lus-converge`, `external/torch` `pm64`). Scaffolded the folder from `SuperMario64/`
   (`fetch.sh`, `installdependencies.sh` from the CI apt line, `build.sh` = CMake presets,
   `run.sh`, `.gitignore`, README, tier-3 `CLAUDE.md`). Full 3663-step build green in the sandbox;
   in-app extraction verified headless with a correctly-sized ROM. Pin first at tip-of-`develop`
   (`611f5b68`), moved to `1.0.1` while chasing an extraction failure — the pin was irrelevant to
   it; `1.0.1` kept as the newest release. Decided: keep `1.0.1`; defer the libultraship crawl for
   the fork until a LUS-lane patch is needed.
2. **2026-09-22 (early) — the "ROM won't load" report resolved.** The maintainer's `ROMF.z64` was a
   64 MB over-dump of the 40 MB image (whole-file SHA-1 ≠ the `config.yml` key); the first 40 MB
   hash to the key and the tail is padding. Trimmed; the maintainer put the trimmed image in place.
3. **2026-09-22 (overnight) — the crash after import, and the series.** The remaining crash was the
   Vulkan backend dereferencing null Context objects on the first frame (host `RIP` symbolized
   against a sandbox build; gdb reproduction). Patches: game-tree `0001` argv ROM path on Linux,
   `0002` refuse unsupported picked ROMs with the reason; LUS-lane `0001` resolve the resource
   manager and console variables through the Context. `apply.sh` scaffolded; `run.sh [ROM]`
   (SHA-1 check, auto-trim, OpenGL seed). Six-scenario headless harness 20/20; series byte-identity
   proven from the bare pins. Incident: leaked test processes swapped the host (rule recorded).
4. **2026-09-22 (morning) — host verify.** `fetch.sh && apply.sh && build.sh && run.sh` built and
   played on the maintainer's machine.

## Follow-ons left open (not this task)

- Upstream submission of the three patches (PaperBoat ×2, JeodC/libultraship ×1) — the
  maintainer's call.
- Optional podman build (`Dockerfile` + `Makefile`, MajorasMask/SuperMario64 as reference) — its
  own task if wanted.
- The pristine binary's popup loop leaks memory (~19 GB in 8 h) — worth an upstream report.

## Reference docs (the durable knowledge)

- `tasks/reference/papermario/rom-import-investigation.md` — the full investigation, both bugs,
  the patches, the headless method, the incident.
- `tasks/reference/papermario/rom-overdump-and-trimming.md` — the ROM facts and the evidence chain.
- `tasks/reference/imps/headless-gui-port-testing.md`,
  `tasks/reference/imps/lus-render-backend-selection.md`,
  `tasks/reference/imps/n64-rom-dump-identification.md` — the cross-port lessons.
- `n64/PaperMario/CLAUDE.md` — operational facts (scripts, patches, version notes).
