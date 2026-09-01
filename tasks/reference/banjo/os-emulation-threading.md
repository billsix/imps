# Reference: N64 OS emulation & threading (`src/port/OS/`)

> **Provenance:** authored 2026-07-31 against Lighthouse `6d30df9a` — the same commit
> imps pins, so no version gap. Claims about the maintainer's fork/branches predate imps.

*Standing reference — the single biggest divergence from the sibling ports, and the first
doc to read when the game hangs. Companions: [architecture-overview.md](architecture-overview.md),
[port-layer.md](port-layer.md), [frame-interpolation.md](frame-interpolation.md).*

*Banner: describes Lighthouse at branch `bill`, and its `libultraship` submodule pin
`2917d0f4` (`1.3.1-482`). The OS layer here is Lighthouse's own code, not LUS.*

## Why this layer exists (and why the siblings don't have it)

Ghostship (SM64) and Shipwright (OoT) **kill** the N64 OS: `osCreateThread`/`osStartThread`
are no-ops, `osRecvMesg` returns immediately, and the decomp's threaded loop is flattened
into a single-threaded `push_frame()` pump. Lighthouse takes the opposite path — it **runs
the decomp's own threading code** by reimplementing the parts of libultra that libultraship
doesn't serve. `src/port/OS/OS.h:4-9` states the rule: use LUS's libultra where it's correct
for a PC port; this layer exists only for the calls LUS can't serve, "so that the decomp's
own threading code can run instead of being replaced by port stand-ins."

The consequence: Lighthouse has **real concurrency** — several `std::thread`s, condition-variable
blocking, and a two-thread render/tick split — where the siblings have none. That makes it the
most deadlock-prone member of the family, which is why it ships its own deadlock diagnostic
(the ThreadWatchdog, below).

## The files

| File | Role |
|---|---|
| `OS.h` | The port-OS C API the rest of the port + decomp call |
| `OS_Threads.cpp` | `osCreateThread`/`osStartThread` → gated `std::thread`; allowlist |
| `OS_Mesg.cpp` | `osSendMesg`/`osRecvMesg`/`osJamMesg` → opt-in condvar blocking; blocked-wait registry |
| `OS_RCP.cpp` | `osSpTask*` task handoff (single slot) + RDP status/FREEZE bit |
| `OS_VI.cpp` | 60 Hz VI ticker thread → `OS_EVENT_VI` (the frame clock) |
| `OS_Cont.cpp` | controller reads (`osCont*`) + SI service |
| `OS_AI.cpp` | audio-interface DMA shims |
| `OS_Time.cpp` / `OS_Timer.cpp` | `osGetTime` / `osSetTimer`/`osStopTimer` |
| `libultra.c` | miscellaneous libultra glue |

Each file carries a "should eventually go to LUS" header comment — this layer is a staging
ground for threading/RCP APIs meant to migrate upstream.

## 1. Thread emulation — the allowlist gate (`OS_Threads.cpp`)

Decomp `osCreateThread` records a thread (entry/arg/pri/id) in a table but launches nothing
(`OS_Threads.cpp:84-93`). `osStartThread` (`:95-121`) spawns a real `std::thread` **only if the
entry point was allowlisted** via `OS_EnableThreadEntry` (`:79-82`, `:101-103`) — otherwise it
silently returns. So decomp threads are revived **deliberately, one consumer at a time**
(`OS.h:27-30`).

- **Allowlisted (thus actually launched):** `thread5_entry`, `pfsManager_entry`,
  `audioManagerThread_entry` (`Game.cpp:165-171`), `viMgr_entry` (`Game.cpp:303`), and
  `rumbleThread_entry` (self-allowlisted, `core1/bamotor.c`). Everything is allowlisted in
  `EnableThread5()` (`Game.cpp:164-174`) **before** `core1_init()` creates the threads.
- **Deliberately NOT launched:** the original boot chain — `sInitThread`/`mainThread`
  (`core1/initthread.c`), `sDefragThread` (`core1/defragmanager.c`). The port bypasses them by
  calling `core1_init()` directly (`Game.cpp:305`).
- **Priority is recorded but not applied** (`:145-155`): N64 scheduling was cooperative +
  priority-ordered; these are preemptive OS threads. Ordering/blocking comes from the queues.
- **Shutdown is counted, not blind-joined** (`:33-77`): `OS_JoinDecompThreads` waits ≤2 s on a
  live-thread counter (`:56`); threads that returned are joined, stragglers still inside game
  code are **detached** (`:71`) rather than hang the process. So a clean exit is best-effort.

## 2. Message-queue blocking — opt-in condvars (`OS_Mesg.cpp`)

**This is the heart of the hang mechanism.** LUS's queues never block: `osRecvMesg` on an empty
queue just returns −1 (`OS_Mesg.cpp:22-30`). But every decomp thread is a loop parked on a
queue, so under LUS semantics they'd spin and nobody would ever get woken. So this file
reimplements real blocking:

- Per-queue `QueueSync{ notEmpty, notFull, blockingEnabled }` (`:34-45`). The `OSMesgQueue`
  fields (`validCount`, `first`, …) stay authentic because decomp reads them directly; **only
  the waiting is ours** (`:27-29`).
- **Blocking is opt-in per queue** (`OS_SetQueueBlocking`, `:171-174`). A queue that hasn't been
  opted in returns −1 instead of blocking (`osRecvMesg` `:143-147`, `osSendMesg` `:97-101`).
- `OS_SendEventMesg`/`OS_JamEventMesg` (`:208-237`) route a hardware event (VI/SI/SP/DP) to the
  queue+message registered by `osSetEventMesg` — jam puts it at the front, the way an interrupt
  preempts.
- `OS_BeginShutdown` (`:177-185`) disables all blocking and wakes every waiter so the tick can
  unwind and be joined.

**The failure mode:** a decomp thread calls `osRecvMesg(q, …, OS_MESG_BLOCK)` on an opted-in
queue whose producer never sends → `notEmpty.wait()` blocks **forever** (`:151`). This happens if
the producer thread was never allowlisted/launched, or an earlier stall means it never runs. The
symptom is a hard freeze the instant the game loop starts.

## 3. The blocked-wait registry — why the watchdog can see the deadlock

`OS_Mesg.cpp` keeps a **lock-free** registry of which thread is parked on which queue
(`sBlockedWaits`, `:50-76`; snapshot `OS_MesgSnapshotBlockedWaits`, `:190-204`). It's atomics, not
mutex-guarded, **on purpose**: the watchdog inspecting a deadlock must not touch `sMesgMutex`,
which a deadlocked thread may be holding (`:47-49`, `:187-189`). Marking/clearing happen on the
wait path under the mutex; reading is lock-free. This is what lets a stall dump say *exactly*
which queue each stuck thread waits on.

**The blind spot:** the tick↔window renderer handshake in `Game.cpp` is a `condition_variable`
(`sSvcCv`), **not** an `OSMesgQueue`, so it is **not** in this registry. `Game.cpp:187-192`
flags it as "the one park the watchdog's blocked-wait registry cannot see." If the dump shows a
thread with no queue wait, suspect this handshake or a decomp busy-spin (§5).

## 4. RCP task handoff & the frame-in-flight trick (`OS_RCP.cpp`)

There is no RSP/RDP, so `osSpTaskStartGo` just **hands the task over** to whoever drains it
(`:52-59`). One slot suffices (`sPendingTask`, `:61`): the decomp starts a task and waits for its
SP event before starting the next, so a second can never be pending (`:58-59`).

- **Audio tasks short-circuit** (`:84-88`): `M_AUDTASK` immediately jams `OS_EVENT_SP` and returns
  — audio never goes through the renderer. Graphics tasks are stored for the window thread.
- `OS_SpTakePendingTask` (`:96-98`) is the consume; `OS_SpPeekPendingTask` (`:100-102`) is the
  watchdog's non-consuming peek.
- **RDP FREEZE bit held as real state** (`:13-50`): nothing on PC obeys FREEZE, but thread5 runs
  its pipeline off that bit (freeze after handing a frame over, clear on next retrace — that's
  what keeps exactly one frame in flight). Holding the bit as genuine state lets that decomp code
  run as written.

Who drains it: the window thread's `ServiceRcp()` (`Game.cpp:152-161`) takes the pending task,
renders it (`RenderTask` → `ProcessGfxCommands`), then raises `OS_EVENT_SP` + `OS_EVENT_DP`. So
thread5 (which submitted and is parked on its sync queue) only unblocks once the window thread
services the task. A window-thread stall → thread5 hangs on `sThread5SyncMesgQueue`; a
game-logic stall → no task is ever submitted. The watchdog dump tells the two apart.

## 5. The two-thread model (`Game.cpp`) — where the OS layer is driven from

`SDL_main` (`Game.cpp:278`): `GameEngine::Create` (extractor + init) → allowlist `viMgr` →
`EnableThread5()` → **`core1_init()`** (creates the decomp threads) → `ThreadWatchdog_Start()` →
launch the **game/tick thread** (`:308`) → the main thread falls into the **window/RCP loop**
(`:316-339`).

- **Game/tick thread** (`:308-315`): `while (WindowIsRunning()) { Beat(GAME_TICK); push_frame(); }`.
  `push_frame` (`:235-271`) = `StartFrame` → record interpolation (unless demo mode) → `mainLoop()`
  (the decomp tick, `core1/init.c:143`) → title refresh. `mainLoop()` blocks on the decomp's
  VI-driven queues, which is what paces the tick — there is no sleep in the normal path.
- **Window/RCP thread** (`:316-339`): every iteration pumps `HandleEvents()`, `OS_SiService()`
  (completes a controller read → `OS_EVENT_SI`), `DrainRenderService()` (runs a marshaled
  tick-side renderer call), and `ServiceRcp()` (renders a pending gfx task).
- **Renderer-call marshaling** (`port_runOnRenderThread`, `:196-213`): D3D11 hangs if renderer
  calls run off the window thread, so tick-side calls park on `sSvcCv` until the window thread
  runs them. Inlined when there's no tick thread (during init).

**Decomp busy-spins that depend on the audio thread advancing** — NOT queue waits, so invisible
to the blocked-wait registry; they surface only as a stalled `game-tick` with no queue park:
`core1/audio_instruments.c:368-371` and `:390-399`, `core2/sfx/source.c:451-463`. Each loops
until the audio callback clears player/`busy` state, with a `gPortResetPending` escape that is
**not** set during normal boot (only during a console `reset`). If the audio worker isn't
advancing at first frame, any of these spins forever.

## 6. The ThreadWatchdog — the fastest route to a freeze cause (`src/port/DevTools/`)

`ThreadWatchdog.cpp` is a purpose-built deadlock diagnostic. Every loop heartbeats
(`ThreadWatchdog_Beat` for `WATCHDOG_GAME_TICK` at `Game.cpp:311`, `WATCHDOG_MAIN_LOOP` at
`:317`; decomp threads beat inside their entries). After ~5 s stalled (10 s relaxed) it emits a
full **`STALL DETECTED`** dump via `SPDLOG_ERROR` naming the stalled thread, the parked queue
(with `validCount`/`msgCount` and its producers, via `DescribeQueue`), the pending SP task,
framebuffer/retrace state, and audio queues.

**Crucially, the window thread keeps drawing during a stall.** `Game.cpp:329-336`: when
`ServiceRcp()` finds no task and the game tick is stalled, it renders **gui-only** frames so the
ImGui menu — and the watchdog output — stay reachable instead of the whole window freezing with
the tick. So a "freeze" is observable and diagnosable, not a black box.

## Freeze-debugging playbook (the driving purpose of this doc)

1. **Reproduce, then read `logs/Lighthouse.log`** for the `STALL DETECTED` dump. That single
   dump usually names the cause.
2. **Dump shows a thread parked on a specific queue** → a producer thread wasn't launched, or a
   queue wasn't set blocking. Cross-check `EnableThread5()` (`Game.cpp:164-174`) against what the
   first frame actually waits on. Classic: thread5 parked on `sThread5SyncMesgQueue` because the
   window thread never serviced the SP task.
3. **Dump shows `game-tick` stalled with no queue wait, no beats** → a decomp busy-spin (§5,
   audio-state waits) or the `sSvcCv` render handshake (§3 blind spot). The audio worker isn't
   advancing. Absence of a queue park in the dump is itself the tell.
4. **No dump at all** → the watcher/threads never started; the hang is earlier, in `core1_init()`
   (`Game.cpp:305`) before the game thread is spawned.
5. **Corroborate with gdb** (`gdb -p <pid>`, `thread apply all bt`) — the OS layer's threads carry
   real backtraces, so a `std::condition_variable::wait` frame points straight at the stuck
   `osRecvMesg`/`osSendMesg` call site and its queue.

## 64-bit-host portability hazards (`OSMesg` width, pointer-range guards)

The sibling MM port (2ship2harkinian, the `fedora44Fixes` branch of the maintainer (William Emerison Six <billsix@gmail.com>), commit `dab560f97` "Fix silent
SFX and several 64-bit-host audio crashes") documents a bug class that **builds clean and only
crashes at runtime on a 64-bit host** — directly relevant because Lighthouse reimplements the
message queues. The classes and Lighthouse's status (verified 2026-07-31):

- **`OSMesg` is 8 bytes on a 64-bit host** (a union with `.data8/.data16/.data32/.ptr`;
  `.ptr` holds a `void*`). `osRecvMesg` copies a full 8-byte `OSMesg`, so receiving into a
  **4-byte** local via `(OSMesg*)&someU32` overflows the buffer. MM had several such sites
  (`AudioLoad_ProcessScriptLoads`, `AudioThread_GetExternalLoadQueueMsg`); the fix is to receive
  into an `OSMesg` and read `.data32`. **Lighthouse status: appears clean** — real-buffer receives
  use `OSMesg`-typed locals (`audio_manager.c:546`, `vimgr.c:237`) or `NULL`; the one `(OSMesg*)&`
  cast (`audio_manager.c:367`) targets an 8-byte pointer (`struct … *D_80275844`), which is safe.
  Re-check any NEW `osRecvMesg` site added later for the 4-byte pattern.
- **`.data32` vs `.ptr` on a pointer-carrying message.** Reading a message that holds a pointer
  through `.data32` truncates it on a 64-bit host (MM's `sched.c` fix). **Lighthouse status: already
  handled** — `graphics_thread.c:483` reads event words through `.data32` and tasks through `.ptr`
  by design.
- **N64-address-range pointer guards.** A guard like `if ((uintptr_t)p < 0x80000000) …`, meant to
  reject "below N64 RAM," misfires on a 64-bit host in a **layout-dependent** way — harmless under
  PIE/ASLR (heap lands high), but skips real work under a non-PIE build (heap lands low). MM's
  silent-SFX bug was exactly this. **Lighthouse: no such audio guard found**, but hardcoded N64
  addresses exist — Stop 'n' Swop scans `0x80000000–0x80400080` (`sns.c:65`, boot-path via
  `sns_find_and_parse_payload()`), carrying a `[port]` note (`stopnswop.c:108`); confirm it's
  actually neutralized.
- **PIE vs non-PIE changes which bugs manifest.** Layout-dependent bugs are masked under PIE and
  surface under non-PIE. Lighthouse sets no explicit PIE flag (follows the toolchain default — PIE
  on Fedora). **When reproducing a freeze/crash, match the affected build's PIE setting**, or a
  layout-dependent bug won't reproduce.
- **`graphics_thread.c:501`** spins `do{}while(1)` on `THREAD5_MESSAGE_EVENT_FAULT` — a fault into
  thread5 hangs forever by design (an N64 fault-handler artifact).

## Trip-hazards

- **`OS_MESG_BLOCK` is a hint, not a guarantee** — a queue only blocks if opted in via
  `OS_SetQueueBlocking`; forgetting to opt one in turns a blocking recv into a silent −1 spin.
- **The `sSvcCv` render handshake is invisible to the watchdog registry** (`Game.cpp:187-192`).
- **Thread priority does nothing** (`OS_Threads.cpp:145-155`) — don't reason about scheduling from it.
- **Shutdown detaches stragglers** (`OS_Threads.cpp:71`) — a thread stuck in game code at exit is
  abandoned, not joined; a crash-on-exit can trace to that.
- **Audio tasks never reach the renderer** (`OS_RCP.cpp:84-88`) — don't look for audio in `ServiceRcp`.
