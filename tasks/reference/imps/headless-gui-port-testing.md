# Testing a GUI game port headless (Xvfb, ImGui popups, file dialogs, crashes, cleanup)

**Reference document** — the method for proving a HarbourMasters-style port (libultraship + ImGui
+ Torch extractor) in the sandbox with no display, no GPU and no hands: what works, what silently
does not, and the process-hygiene rules learned the hard way. Distilled from the PaperBoat ROM-import
unit (2026-09-22, `tasks/reference/papermario/rom-import-investigation.md` §6/§8); applies to
Ghostship, SoH, 2S2H, Lighthouse and the next port alike. Written 2026-09-22 by William Emerison
Six <billsix@gmail.com> (agent-assisted). Update in place.

## What a headless run can and cannot prove

Can: that extraction runs and what it writes; which code path a ROM takes; that the game gets past
its first frames on a given render backend without crashing; exit codes, logs, backtraces. Cannot:
that anything is drawn correctly or heard. Say which side a claim is on.

## The recipe

1. **Display:** `Xvfb :99 -screen 0 1280x720x24`, `DISPLAY=:99`, `LIBGL_ALWAYS_SOFTWARE=1`. OpenGL
   resolves to llvmpipe, Vulkan to lavapipe — both real enough to hit renderer bugs (the PaperBoat
   null-Context crash reproduced under lavapipe exactly as on the maintainer's RADV).
2. **App directory = cwd.** Run from a fresh per-scenario directory; do not set `SHIP_HOME` — this
   libultraship doubles the config path with it (`<dir>//<dir>/<app>.cfg.json`) and never reads a
   seeded config.
3. **Crashes:** wrap in `gdb -q --batch -ex run -ex "bt 8" --args <bin> …`. The port's own crash
   handler prints registers and no symbols; a host `RIP` can be symbolized against an
   identical-toolchain sandbox build with `addr2line -f -C` (it matched for PaperBoat).
4. **ImGui popups cannot be clicked.** The GL window's contents are not capturable under Xvfb (every
   `import`/`xwd` screenshot is black), so `xdotool` has nothing to aim at, and `ImGui::Button`
   needs a real click. Add a throwaway commit: an env-gated hook (`<APP>_AUTOCLICK=1`) in the modal
   window's draw that takes the first button of every popup immediately and logs which. Never
   export it as a patch; keep it on a `-test` branch stacked on the series
   (`tasks/adhoc/papermario-rom-import/patch_autoclick.py` is the template).
5. **The port swallows stdout.** `printf` instrumentation vanishes; use `fprintf(stderr, …)` or
   spdlog. Trace the things that matter: every popup registration, every ROM load, the extractor's
   inputs (path + byte count), the state machine's entry (`patch_trace.py` is the template).
6. **Native file dialogs:** portable-file-dialogs finds `zenity` via `which` and reads the chosen
   path from its stdout. A `zenity` shim first on `PATH` that prints `$FAKE_ZENITY_PICK` for
   `--file-selection` drives the exact picker path (`zenity-shim/zenity`).
7. **Extraction proof** = Torch's `Done! Took …` in the app log plus the archive's size; compare two
   archives by `unzip -lv` name/size/CRC lists, not by file hash (zip timestamps differ).
8. **One harness, not many ad-hoc launches.** Scenario dirs, `check` helpers, a final `ALL PASS`
   line, and the full log kept in a file (piping through `tail` loses the failing head).

## Process hygiene — the rule that came from an incident

The game **ignores SIGTERM**. `timeout N`, `kill`, and gdb being killed all leave it running; a
forgotten instance in a popup loop grew to ~19 GB RSS in 8 hours, two of them swapped the
maintainer's host for ten minutes. Therefore:

- `timeout -s KILL <secs>` on **every** launch; never a plain `timeout`, never a bare `&`.
- `trap 'pkill -9 -x <binary>; pkill -9 -f <build path>' EXIT` at the top of every harness, and in
  ad-hoc launch commands.
- Never run a **renamed copy** of the binary (`pkill -x` will not match it); if a second build is
  needed, use a second build directory.
- Audit before moving on and before ending the session: `ps -eo pid,rss,etime,comm | grep -i
  <binary>`; kill what is left and **say so in the report**.

## Harness gotchas met on the way

- `check "desc" bash -c '…'` cannot see the harness's functions/variables — use `eval '…'`.
- `pkill -f "<pattern>"` matches the shell running the harness when the pattern appears in its
  own command line (it killed my shell once) — prefer `pkill -x <name>`.
- Verify the **identity of every input file at every step** (size + hash). A ROM that was replaced
  mid-session made an hour of runs look like the extractor normalized over-dumps.
- Wall-clock: a full extraction is ~27 s in the sandbox; budget 75 s per extracting scenario.
