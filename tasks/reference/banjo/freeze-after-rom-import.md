# Task: fix the freeze right after ROM import

> **Provenance:** authored 2026-07-31 against Lighthouse `6d30df9a` — the same commit
> imps pins, so no version gap. Claims about the maintainer's fork/branches predate imps.
> **Resolved:** this investigation concluded in the OSMesg high-byte fix now shipped as
> `BanjoKazooie/patches/0003-core1-graphics_thread-fix-post-import-freeze-from-OS.patch`.

**Status:** ✅ FIXED (2026-08-01) — confirmed working on the hardware of William Emerison Six <billsix@gmail.com>. It WAS the OSMesg thing.

## RESOLUTION (root cause + fix)

**Root cause (a 64-bit OSMesg-union bug — Bill was right):** hardware events are posted to thread5
with `OS_MESG_32(code)`, which sets the union's `.data32` but leaves the **high 4 bytes of the
8-byte `OSMesg` uninitialized (garbage)**. thread5's event-vs-task discriminator was
`if ((uintptr_t)msg.ptr < 100)` — it read all 8 bytes. When an event's garbage high bytes came up
non-zero (instrumented: SP `data32=6` arriving as `0x00007FCE_00000006`), that event was mis-read
as a task pointer and **silently dropped**. The dropped events were the gfx-completion SP and the
yield-SP, so `thread5_handleSPEvent` never ran, the gfx yield (taken so an audio task could run)
was **never resumed**, `sUnkFlag1` stuck at `TASK_YIELDED`, the frame's DP→`sMesgQueue2` signal
never fired, and game-tick hung. Layout/timing-dependent (which high-byte garbage you get) — the
non-PIE MM signature.

**Fix (one line + comment, `src/core1/graphics_thread.c` ~498):** discriminate events from task
pointers on `msg.data32` (the event code, immune to the garbage high bytes) instead of the full
`(uintptr_t)msg.ptr`. Event codes are 3–13 (`< 100`); task submissions carry a real pointer whose
low 32 bits are always large, so they still fall to the task branch. Verified: `handleSPEvent`
went 0 → 121 calls, watchdog stalls 0, and Bill confirmed the game runs on real hardware.

**Diagnosis path:** reliable headless repro → gdb read (valid pointers, ruled out truncation) →
SP-event-flow instrumentation (thread5 *receives* SP but never dispatches it) → logged the ptr HIGH
bytes (SP=garbage, DP=0). The audio "flood" (283 `startNextAudio` spins) was the symptom of the
stranded yield; audio-task preemption was the trigger — matching Bill's MM audio-root intuition,
but the actual defect was the OSMesg-union high-byte garbage.

**Also fixed this session:** bug #2 (version-incompatible re-extract dialog) via
`-u ${PROJECT_VERSION}` on the `ExtractAssets` CMake target; container GUI/build deps added to the
runClaudeInContainer Dockerfile. Follow-up worth considering: fix `OS_MESG_32` itself (LUS) to zero
the union, so no other consumer can be bitten by the garbage high bytes.

**Repo:** github.com/HarbourMasters/Lighthouse (Bill's `bill` fork). Reference set:
[`tasks/reference/`](./) — start with
[`os-emulation-threading.md`](reference/os-emulation-threading.md).

## Symptom

Lighthouse builds and runs; the ROM-import/extraction UI works; **immediately after the ROM is
imported (the `Create()` → `core1_init()` → first-`mainLoop()` boundary) the game freezes.**
Observed on Bill's Fedora host. Not a build failure — a runtime hang.

## Hypotheses (ranked)

1. **64-bit-host `osRecvMesg` buffer bug (Bill's strong prior).** In the sibling MM port this
   class — `OSMesg` is 8 bytes on a 64-bit host, received into a 4-byte buffer → overflow → runtime
   crash — took weeks to find (2ship2harkinian `dab560f97`). A first grep of Lighthouse's decomp
   suggested it already avoids the 4-byte pattern (real receives use `OSMesg`/`NULL`/8-byte ptr),
   but that was a lead, not proof — ASAN is the decider. A subtler variant, or the same pattern in
   a path not yet swept, is very much in play.
2. **Audio busy-wait spin** — `audio_instruments.c:368/390`, `sfx/source.c:451` spin on audio
   state the callback normally clears; `gPortResetPending` escape is NOT set at boot. Surfaces as a
   stalled `game-tick` with NO queue park.
3. **Tick↔render handshake deadlock** — thread5 parked on `sThread5SyncMesgQueue` because the
   window thread never serviced the SP task, or the `sSvcCv` render handshake (watchdog-invisible).
4. **Hang before threads even start** — inside `core1_init()` before the game thread is spawned
   (→ no watchdog dump at all).

## Method (instrumentation-driven; make the tools tell us)

1. Build in-sandbox (Debug) with `-DUSE_NETWORKING=OFF` (no SDL2_net here); ROM symlinked as
   `baserom.z64`; pre-generate `bk.o2r` via the `ExtractAssets` target so the binary boots straight
   past import (no ImGui file-picker to drive headlessly).
2. Run headless under Xvfb; reproduce the freeze; **read `logs/Lighthouse.log` for the
   ThreadWatchdog `STALL DETECTED` dump** (names the stalled thread + parked queue).
3. Attach `gdb -p <pid>`, `thread apply all bt` — a `condition_variable::wait` frame points at the
   stuck `osRecvMesg`/`osSendMesg` and its queue.
4. **Rebuild with `-DENABLE_ASAN=ON`** to directly test hypothesis #1 — a stack/global buffer
   overflow in `osRecvMesg` receive is exactly what ASAN catches, with the call site.
5. Two gates per change: regression (does it still boot?) + progress (did the hang move/clear?).

## Environment facts

- ROM: `/foo/opt/n64/n64roms/BanjoKazooie/ROMF.z64` (US rev0, SHA-1 `1fe1632…5d7a`).
- Build here needs `-DUSE_NETWORKING=OFF`; `ExtractAssets` needs `baserom.z64` in the repo root.
- PIE note: the MM layout-dependent bugs only bit non-PIE builds. Lighthouse sets no explicit PIE
  flag (Fedora default = PIE). If Bill's affected build is non-PIE, match that here.

## Findings log

### 2026-08-01: REPRODUCED headless; watchdog localized the freeze (NOT the OSMesg bug)

Built Debug (`-DUSE_NETWORKING=OFF`, GCC 16, **non-PIE** `LSB executable`), fresh `bk.o2r`
extracted from the ROM (24.9 MB), ran under Xvfb. It boots past import into `gameMode=3 map=0x1f`,
then **freezes on the first frame**. ThreadWatchdog `STALL DETECTED` dump (`logs/Lighthouse.log`):

```
game-tick STALLED  recv sMesgQueue2 (vimgr.c) 0/1   ← "this one first"
In loop: push_frame -> mainLoop (Game.cpp)
Parked at: osRecvMesg (empty) on sMesgQueue2 (vimgr.c)
Producers: viMgr_func_8024BFAC <- thread5_handleDPEvent (needs sUnkFlag2 bit30)
thread5   STALLED  29 beats (NO queue wait)
Pipeline: sUnkFlag1=TASK_YIELDED  sUnkFlag2=0x40000001  taskQ=20/20(FULL)  pendingSpTask=no  gfxRing=1->1
```

**Root chain (graphics/VI-sync deadlock, not audio):**
- game-tick is in `mainLoop → game_draw → viMgr_func_8024BFD8(1)` blocked at `vimgr.c:186`
  `osRecvMesg(&sMesgQueue2, BLOCK)`, waiting for the "frame done" message.
- That message is sent by `viMgr_func_8024BFAC` (`vimgr.c:172`, `osSendMesg32(&sMesgQueue2,…)`),
  driven by `thread5_handleDPEvent` (DP-done), gated on `sUnkFlag2 bit30` (which IS set: 0x40000001).
- **thread5 is itself stalled** (no queue wait → not a queue park), `taskQ=20/20` full,
  `sUnkFlag1=TASK_YIELDED`, `pendingSpTask=no`.
- Leading hypothesis: `OS_RCP.cpp osSpTaskStartGo` **drops the resumed SP task** — on
  `sResumePending` it returns early WITHOUT re-storing `sPendingTask` (`OS_RCP.cpp:90-93`). So the
  window thread's `ServiceRcp` sees no task → never renders → never raises DP → `handleDPEvent`
  never runs → `sMesgQueue2` never sent → game-tick hangs. thread5 wedges behind it (task queue
  fills, 20/20).
- audio-mgr / pfsmanager stalls appear only in the 15 s dump (not the 5 s one) → **downstream**,
  not root. **This is NOT the MM OSMesg 4-byte-receive bug** — that grep-checked clean earlier.

gdb `thread apply all bt` was low-value (all threads at `__syscall_cancel_arch`, deep frames not
unwound); the ThreadWatchdog dump is the real oracle here.

### 2026-08-01: SECOND, EARLIER failure reported by William Emerison Six <billsix@gmail.com> — version-incompatible → crash

Bill on his host: "incompatible… would ask to reimport the rom… then crapped out." This is the
**version handshake** (`portArchiveVersionMatch`, `Engine.cpp:155`, `// TODO: port archive
versioning`) firing on a stale o2r vs a freshly-rebuilt binary → offers re-extract → **crashes on
that path**. Distinct from the freeze above (you only reach the freeze with matching archives).
Workaround to get past it: delete the stale `bk.o2r`/`lighthouse.o2r` (or match versions) and
re-extract. Root-cause the crash separately.

### 2026-08-01: OSMesg receive sweep (thorough) + ASAN to settle it empirically

Bill pushed back: before the OS_RCP fix, does the 64-bit `OSMesg` bug still need fixing?
Re-checked EXHAUSTIVELY — every non-NULL `osRecvMesg` receive buffer in core1/core2/boot:
- `graphics_thread.c:487` (thread5 loop — the deadlock path): `OSMesg msg` (8B) ✓, and reads
  `.data32`/`.ptr` correctly with a `[port]` comment (the authors already applied the MM fix).
- `vimgr.c:239` `OSMesg sp48` ✓; `audio_manager.c:553/564` `OSMesg temp_mesg` ✓;
  `audio_manager.c:367` `struct* D_80275844` (8B ptr) ✓; all others receive into `NULL`.
So on source evidence the 8-into-4 `OSMesg` overflow is NOT present here. **But** proving it needs
ASAN (catches an overflow hiding in a struct/indirect path that a grep can't see).

**ASAN build was itself broken on GCC/Fedora — a real project bug.** `CMakeLists.txt:91` linked
`-static-libsan` (a Clang spelling); GCC wants `-static-libasan`, and Fedora ships NO static asan
runtime (only `libasan.so.8`). So `ENABLE_ASAN` fails to build on Bill's own platform ("unrecognized
option -static-libsan", dies building bundled zlib). **Temporary [port/debug] edit** (per Bill's
standing sanitizer-build-aid arrangement): link the shared libasan on GCC, keep `-static-libsan`
only for non-GNU. Marked `# [port/debug]` at CMakeLists.txt:91. **Worth keeping as a real fix — flag
to Bill.** (If not kept, revert by task end.)

### 2026-08-01: root cause CONFIRMED by reading the full thread5 state machine; fix under test

Full trigger chain (all in `src/core1/graphics_thread.c` + `src/port/OS/OS_RCP.cpp`):
1. `thread5_startF3DEXTask` (`:169-172`): `osSpTaskStartGo(&sGfxTask)` stores `sPendingTask`;
   `sUnkFlag2 = task_data->unk4 | 1 = 0x40000001` (bit30 = "on this task's DP, signal the VI mgr").
2. Audio timer fires while gfx in flight → `thread5_startNextAudioTask` (`:377-388`): gfx is
   running + audio pending → `osSpTaskYield()` (`:385`), `sUnkFlag1 = TASK_YIELDED`.
3. `thread5_handleSPEvent` (`:327-333`): `osSpTaskYielded(&sGfxTask)` → sets `sResumePending`;
   starts the audio task (M_AUDTASK, jams SP); `sUnkFlag1 = AUDIO_TASK`.
4. Audio SP → `handleSPEvent` (`:343-348`): resumes gfx via `osSpTaskStartGo(&sGfxTask)` (`:345`).
   **OS_RCP swallowed this** (`sResumePending` → early return, `sPendingTask` NOT stored). No RSP
   here, so the window thread never renders the gfx frame → no DP → `thread5_handleDPEvent`
   (`:246-251`, which on bit30 calls `viMgr_func_8024BFAC` → `sMesgQueue2`) never runs → game-tick
   blocked at `vimgr.c:186` forever. Watchdog signature matches exactly: `sUnkFlag1=TASK_YIELDED`,
   `sUnkFlag2=0x40000001`, `pendingSpTask=no`, `taskQ=20/20`, game-tick recv `sMesgQueue2`.

**Root:** the port renders gfx atomically from `sPendingTask` (no stateful RSP), so a "resume"
must re-hand the task to the window thread; swallowing it drops the frame. **Fix under test**
(`OS_RCP.cpp:90`): on resume, clear `sResumePending` but STILL `sPendingTask.store(task)`.
Rebuilding non-ASAN Debug to measure whether the `sMesgQueue2` stall clears. (NOT the OSMesg bug —
that's confirmed absent; source-clean + ASAN memory-clean through boot.)

### 2026-08-01: RELIABLE repro achieved; fix #1 progresses but does NOT solve; bug #2 root-caused

**Environment fully solved** (headless repro now reliable):
- bk.o2r must sit NEXT TO THE EXE (`build-cmake/`), not runDir — the game searches app/exe dirs,
  not cwd (`O2R file not found at path: ./bk.o2r` even with it in runDir).
- Container needed GUI deps: `gtk3 PackageKit-gtk3-module xdotool zenity xdg-desktop-portal-gtk`
  (installed; to be added to runClaudeInContainer Dockerfile). Force software GL:
  `LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe` (ZINK/dri2 fail headless otherwise).

**Bug #2 ROOT CAUSE (real build bug):** `VerifyArchiveVersion` (`Engine.cpp:139`) requires the
o2r `portVersion` == build major.minor. `ReadPortVersionFromOTR` returns `{0,0,0}` when a `.o2r`
lacks a `portVersion` record. The `ExtractAssets` CMake target (`CMakeLists.txt:759`,
`torch o2r baserom.z64`) **omits the `-u <version>` stamp** that Torch's `o2r` cmd supports
(`Torch/src/main.cpp:145`). So a CMake-extracted bk.o2r is version `{0,0,0}` ≠ `1.0.0` → always
"incompatible" → re-extract dialog. **Fix: add `-u <PROJECT_VERSION>` to the ExtractAssets command**
(mirror GeneratePortO2R). Workaround used: `torch o2r baserom.z64 -u 1.0.0` regenerates a stamped
bk.o2r → dialog gone, reaches gameMode=3.

**Fix #1 (OS_RCP resume re-store) — PROGRESSES but does NOT solve the freeze.** On the clean
matched build it still stalls `game-tick recv sMesgQueue2`, BUT the pipeline state changed:
- BEFORE: `sUnkFlag2=0x40000001`(bit30 stuck), thread5 STALLED, `taskQ=20/20`.
- AFTER : `sUnkFlag2=0x2`(bit30 CLEARED), thread5 `ok`/848 beats, `taskQ=0/20`, rings advancing.
So thread5 is un-wedged and DP handling runs now — but bit30 (sUnkFlag2) is **cleared before the DP
signals sMesgQueue2** for the frame game-tick awaits. Likely a double-render from re-storing the
task, or the deeper SP/DP-multiplexing race (all of gfx-SP / audio-SP-jam / yield-SP share
OS_EVENT_SP; single-slot sPendingTask). Real fix needs: gfx task rendered EXACTLY once, its DP
reaching game-tick with bit30 still set. Candidate directions: (a) don't yield gfx for audio at all
(port audio doesn't use the RSP — `thread5_startNextAudioTask:385`); (b) distinguish gfx-SP from
audio-SP so completions aren't conflated. **Needs runtime instrumentation of the SP/DP/task
sequence, or Bill's MM RCP fix shape.** Repro is now cheap, so iteration is viable.

### 2026-08-01: exhaustive OSMesg audit (William Emerison Six <billsix@gmail.com>: "#1 priority, it literally was the osmesg thing")

Bill is confident the MM fix was the 64-bit OSMesg issue and directed a full replication for this
project. Did the exhaustive MM-style sweep of EVERY message send/recv/construction on the paths
that matter (gfx / audio / vimgr / RCP):
- **Every `osRecvMesg` with a non-NULL buffer (5 total):** `graphics_thread.c:487` (`OSMesg msg`),
  `vimgr.c:239` (`OSMesg sp48`), `audio_manager.c:553/564` (`OSMesg temp_mesg`),
  `audio_manager.c:367` (`struct* D_80275844`, 8-byte ptr). All correct width. No `(OSMesg*)&u32`.
- **Send side / pointer-as-32bit (the MM `sched.c` `.ptr` class):** task pointers travel as
  `arg0.ptr`; event codes as `.data32`; audio reply is `OS_MESG_PTR(&info->reply_mesg_data)`
  (`audio_manager.c:444`, with a `// [port] OSMesg is a union on PC` comment). `audio_mesg` is an
  `OSMesg` field (`core1.h:168`). Event registration uses `OS_MESG_32` for small event codes
  (correct). `thread5_sendTaskToQueue` has an explicit `// Lighthouse [port] ... OSMesg union` note.
- **Port queue emulation** (`OS_Mesg.cpp`) copies full 8-byte `OSMesg`.

**Finding: the Banjo/Lighthouse port authors ALREADY applied the MM OSMesg fix** — the 8-byte union
is handled correctly everywhere, with `[port]` comments proving it. The specific MM
receive-overflow / pointer-truncation bug is NOT present here to re-fix. Reconciliation with Bill's
certainty: the *scenario* is identical to MM (an audio task preempting the in-flight gfx task), but
because OSMesg is already correct here, that scenario manifests as the **RCP SP/DP task-handoff
race** (see above) rather than memory corruption. ASAN also ran memory-clean through boot.
**Open: need Bill to point at the specific MM commit/symbol if a concrete analog is still expected.**

### 2026-08-01: bug #2 real fix APPLIED

`CMakeLists.txt` ExtractAssets: added `-u ${PROJECT_VERSION}` to the `torch o2r` command so bk.o2r
carries a matching portVersion (staged).

### 2026-08-01: LIVE gdb read at the deadlock — pointers valid, it's a race (NOT 64-bit corruption)

Reverted OS_RCP to baseline, Debug build (symbols), reproduced freeze, gdb-read the RCP statics
at the stall:
- `sGfxTask.t.data_ptr = 0x334869d0` (VALID decomp-pool addr), `data_size=0xb90`, `type=1` — no
  truncation. `sPendingTask = NULL`. `sUnkFlag1 = TASK_YIELDED`. **`sYieldPending = TRUE` (stuck)**,
  `sResumePending = 0`, `sGfxTaskYielded = 0`.
- Same reverted binary froze in TWO end-states across runs (`sUnkFlag2=0x40000001,taskQ=20/20` and
  `0x2,taskQ=0/20`) → **timing race**, non-deterministic.

**Empirical verdict:** every task pointer is a valid 64-bit pointer → NO truncation / memory
corruption (consistent with ASAN-clean). The freeze is the RCP **SP-event conflation race**:
gfx-completion-SP, audio-SP-jam (M_AUDTASK), and yield-SP all share `OS_EVENT_SP` on a single-slot
handoff; `osSpTaskYield` sets `sYieldPending`+jams SP, but the SP that `thread5_handleSPEvent`
consumes can be the wrong one, stranding the yield (`sYieldPending` stuck TRUE). This closes the
64-bit/OSMesg hypothesis empirically. Fix direction: make the yield/SP handshake robust to the
multiplexing, or (simpler) don't yield gfx for audio at all — port audio (M_AUDTASK) never uses the
RSP, so the yield in `thread5_startNextAudioTask:385` is unnecessary on this port.

### 2026-08-01: the yield is LOAD-BEARING (tick↔window sync); removing it → gfx-interpreter abort

Tried the "don't yield gfx for audio" experiment (`thread5_startNextAudioTask:384`). Result: the
freeze became a timing-dependent **freeze-OR-abort**. Caught the abort via Lighthouse's crash
handler (SIGABRT, not segfault): unhandled C++ exception, backtrace →
`Fast::gfx_step()` (`libultraship .../fast/interpreter.cpp:4914`) ← `RenderTask` (`Game.cpp:147`)
← `ServiceRcp` (`Game.cpp:158`). `gfx_step` does `ucode_handlers[...]->at(opcode)`, which throws
`std::out_of_range` on a bad opcode. **Mechanism:** without the yield, the window thread renders
the display list WHILE the tick thread is still building it → data race → garbage opcode → throw
→ `std::terminate` → abort. So **the yield synchronizes the tick and window threads on the display
list — it cannot be removed.** Change reverted.

**Consolidated understanding of the freeze:** the port multiplexes gfx-completion-SP,
audio-SP-jam (M_AUDTASK), and yield-SP all onto `OS_EVENT_SP` with a single-slot `sPendingTask`.
That handshake both (a) synchronizes tick↔window on the DL and (b) sequences the frame's DP →
`sMesgQueue2` → game-tick. The freeze is that handshake deadlocking (SP events conflated/dropped;
`sYieldPending` stranded; in the taskQ-full variant the yield-SP jam is dropped because event jams
are NOBLOCK). Pointers are all valid (not 64-bit). **The fix must repair the SP/DP sequencing, not
bypass the yield.** Per Bill's MM experience the real root may be audio-side (excess audio-task /
SP generation flooding the handshake — "augmented sound generation"); worth checking the audio
task rate + the M_AUDTASK SP-jam path next. Repro is cheap; instrument the SP/DP/yield sequence.

## Two distinct bugs, ranked

1. **Graphics/VI-sync freeze after successful import** — localized above; likely `OS_RCP.cpp`
   yield/resume dropping the SP task. (The original reported symptom.)
2. **Version-incompatible → re-extract path crashes** — Bill's host symptom; the `// TODO: port
   archive versioning` path.
