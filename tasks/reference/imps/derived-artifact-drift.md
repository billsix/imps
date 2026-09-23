# Reference: N64 derived artifacts — where drift occurs, and the source of truth

> **Provenance:** relocated 2026-09-13 from the N64 family `n64/CLAUDE.md`
> ("Derived artifacts — where drift occurs, and what the source of truth is") as
> part of the CLAUDE.md trim (`tasks/trim-claude-md.md`). This is pin-bump-time
> reference, not per-session material. `n64/CLAUDE.md` keeps the standing rule
> ("re-verify every derived artifact against its source at each pin bump") and
> points here for the table.

## Derived artifacts — where drift occurs, and what the source of truth is

(Maintainer request, 2026-09-01.) Much of the N64 family is DERIVED from files
inside the pinned checkouts. Those copies are correct **at the pin** and
rot silently when the pin moves — so **every pin bump must re-verify each
derived artifact against its source** (this is part of the pin-bump operation
in the master `CLAUDE.md` agent contract). The pairs:

| Derived artifact (imps) | Source of truth (in the checkout) | Drift notes |
|---|---|---|
| `n64/<Project>/Dockerfile` | the upstream CI workflow's Linux job (Shipwright: `generate-builds.yml`; 2ship/Lighthouse/Ghostship: `main.yml` build-linux) | from-source lib versions (SDL 2.30.3, tinyxml2 10.0.0, libzip 1.10.1), base-OS choice, build flags — all hand-copied. Where a deps list exists as a FILE it is `COPY`d from the checkout at image build (2ship `apt-deps.txt`, Shipwright `linux-build-deps/apt.txt`, Ghostship `libultraship/requirements.txt`) and stays auto-current; the inline extras and steps do not. (`COPY`, not `RUN --mount=type=bind` — a build-time bind mount is read by the confined `container_t` RUN process with the file's on-disk SELinux label, so a `:Z`-poisoned checkout fails a host-side `podman build` with an MCS-mismatch AVC and a build mount has no relabel step; `COPY` is read by buildah as the unconfined host user. Fixed across all four Dockerfiles 2026-09-01.) Also: runner images pre-provide tools a bare base lacks (modern cmake on 22.04 and ≥3.30 on 24.04 → the Kitware blocks; python3; imagemagick for SoH's configure-time AppImage icon; noble's shaderc/spirv-tools ABI skew → the libshaderc_shared.so symlink) — CI won't notice those needs changing, we must. |
| `n64/<Project>/installdependencies.sh` | `docs/BUILDING.md` Fedora section (Lighthouse/2ship/Ghostship), `linux-build-deps/dnf.txt` (Shipwright), or the CI apt line (PaperBoat, which documents only Ubuntu/macOS) | list is inlined by design (works before first fetch) — re-diff against the doc at every pin bump. Some lines are OURS via patches (banjo SDL2_net = patch 0001; mario libshaderc = patch 0004; mm audio libs ogg/vorbis/opus/opusfile = patch 0002): derive from the PATCHED doc, and if upstream merges those patches, the doc and script converge on their own. |
| `n64/<Project>/build.sh` + `Makefile` build targets | upstream CMake target names and flags (`GenerateSohOtr` / `Generate2ShipOtr` / `GeneratePortO2R`, `BUILD_REMOTE_CONTROL`, `cpack -G External`, Ghostship's `.tcc` dir) | target names have changed across pins before (ocarina's ZAPDTR→torch restructure); check them each bump. |
| `patches/*.patch` | upstream code itself | the core case — covered by the pin-bump rebase procedure. PaperMario's LUS lane (`patches-libultraship/`) is keyed to the JeodC fork SHA in `.gitmodules`, not to the libultraship crawl's pin — replay it against the submodule's new SHA at a bump. SuperMario64's and OcarinaOfTime's `patches/standard-c/` carry a second invariant beyond "applies": every patch is codegen-identical, proven against the pinned upstream's own compile flags — at a bump, replay it AND re-run `tools/asmdiff.sh` per patch (a new upstream flag or GCC can turn an identical rewrite into a differing one). OcarinaOfTime's `personal` rename stream is keyed to the `standard-c` TIP (its `base-commit` footer), not the pin: bump `standard-c` first, then re-cut `personal` on top (`tools/resolve_rename_conflicts.py`) and re-run `tools/check_renames.py all`. |
| `n64/PaperMario/run.sh` accepted-ROM hashes | `PaperBoat/config.yml` recipe keys | **no drift by construction** — read from the built tree at run time (`sed` over `config.yml`), so a pin that adds a version needs no edit. The 41943040-byte trim size IS hand-copied (the US image size). |
| `n64/PaperMario/run.sh` + `n64/SuperMario64/run.sh` OpenGL seed (`Window.Backend.Id = 2`) | libultraship `include/fast/Fast3dWindow.h` `WindowBackend` enum (`FAST3D_SDL_OPENGL = 2`) and the `Window.Backend.*` config keys in `Window.cpp` | hand-copied; a LUS bump that renumbers the enum or renames the keys silently breaks the seed (the app then falls back to the front of its backend list = Vulkan). `tasks/reference/imps/lus-render-backend-selection.md`. |
| `tasks/reference/<project>/` docs | the pinned source | covered by per-doc provenance banners. |
| pin comments in `fetch.sh` (date, describe, "tip of develop") | the `PIN_SHA` itself | update the prose when updating the SHA. |
| per-project `CLAUDE.md` facts (submodule SHAs, patch lists, gotchas) | the checkout + `patches/` | re-verify at every pin bump and series change. |
| `n64/libultraship/fetch.sh` `PIN_SHA` | the crawl iteration log in `tasks/reference/libultraship/crawl.md` | the two advance together, one commit per iteration; check fork topology (`git merge-base`) before assuming a new pin descends from the documented one. |
| the FUTURE upstream-container-CI patches (`tasks/*-upstream-container-ci.md`) | both the Dockerfile AND the workflow | double-derived; their acceptance strategy requires re-checking fidelity against whatever CI looks like at submission time. |
