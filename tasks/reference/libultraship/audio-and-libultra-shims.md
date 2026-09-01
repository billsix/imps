# libultraship — audio backends and libultra OS shims

> **Pinned:** libultraship **1.3.1-486**
> (`62e973aeb4a53ad4d22bb91e2d9373ecdfcd246c`, 2026-08-15 —
> OcarinaOfTime's pin; 4 commits past 1.3.1-482).
> Updated 2026-09-01, iteration 17 of the reference crawl
> (`../../libultraship-reference-docs.md`). Re-sync check: compare
> `PIN_SHA` in `libultraship/fetch.sh` with the SHA above. This line is
> NEWER than the 1.4.x tags despite the smaller number.

## Audio

Backends `WASAPI / SDL / COREAUDIO / NUL`, selection and silent
degrade-to-NUL unchanged (`Audio.cpp:38-41`); Linux SDL-only;
`AudioSettings` (44100/1024/2480) + 5.1 via `SoundMatrixDecoder`
unchanged; push-only, no callback. Deltas:

- **`NullAudioPlayer::Buffered()` fixed (#1167)**: returns
  `GetDesiredBuffered()` instead of 0 (`NullAudioPlayer.cpp:18-21`) —
  the null backend no longer spins/hangs the game's audio thread.
- **Backend persistence moved into `Audio` itself** (#1097): it caches
  `mConfig` and reads/writes `"Window.AudioBackend"` directly via
  `GetSavedAudioBackend()` / `GetSavedAudioChannelsSetting()`
  (`Audio.cpp:57`, `:66-105`); the `"pulse"`→SDL migration lives there
  now (`:73-78`). Config knows nothing about backends.
- **WASAPI error handling reworked (#1075)**: raw `throw res`
  (HRESULT) → `HResultException` (`ship/utils/HResultException.h`),
  silent catches now `SPDLOG_ERROR`. The #1001 mutex race fix is
  retained (this pin descends from 397).
- **`~AudioPlayer` is now `virtual` (#1212, this 4-commit step)** —
  the long-standing latent hazard retires; the same fix makes
  `~WasapiAudioPlayer` call `DoClose()` (stop stream, release
  client), curing a WASAPI hang on teardown.
- Still true: `SetCurrentAudioBackend` does a full `Config::Save()` on
  every call, startup included (`Audio.cpp:107-126`); back-pressure
  per-backend (SDL drops >6000 queued, CoreAudio 6000-ring, WASAPI
  clamps to device buffer).

## libultra shims

Same 8 `os_*.cpp` files (`os_time.cpp` still 0 bytes) **plus the new
`AudioDmaRegistry.{h,cpp}`**:

| Area | Behavior at this pin |
|---|---|
| `osContInit` | **No longer exits on failure** — the gamecontrollerdb load + `SDL_Init(GAMECONTROLLER)` moved to `Context::InitControlDeck` (non-fatal `SPDLOG_WARN`, `Context.cpp:277-289`); `osContInit` shrank to `ControlDeck::Init(bits)` (`os.cpp:15-21`) |
| **`osPiStartDma`** | **No longer an unclamped memcpy (#1035)** — `AudioDma_Clamp(devAddr, nbytes)` then memcpy of the clamped size, zero-filling the tail (`os_pi.cpp:18-28`). Mechanism: an **opt-in 8-slot registry** (`AudioDma_Register/Clamp/Clear`, `AudioDmaRegistry.cpp`). **LUS itself never calls `AudioDma_Register`** — the port must register its audio blobs; an unregistered address **passes through unclamped** (`:26-35`), so the 397 corruption hazard is fixed only for registered blobs |
| `osGetTime`/`osGetCount` | still N64 46.875 MHz cycle units; `osSetTime` present (`os.cpp:35-52`). (#1023's `sysctl kern.clockrate` is SDL frame-pacing calibration, NOT an osGetTime change) |
| Rumble | unchanged: `__osMotorAccess` → `Start/StopRumble` (`os.cpp:75-84`); `osMotorStart/Stop` macros (`motor.h:9-10`) |
| Message queues | still never block (flag ignored, −1 on full/empty) |
| VI / EEPROM / cache / VM | unchanged (16 ms SDL timer; 512-byte `default.sav`; no-ops) |
| Threads | **still absent** |

**Dangling declarations unchanged** (link error if called):
`osContGetStatus` (`os.h:108`), `osAiSetFrequency` (declared twice,
`os.h:140`+`:144`), `osViFade` (`:119`), `osViRepeatLine` (`:120`).
Defined-but-undeclared set also unchanged (`osViGet*Framebuffer`,
`osVirtualToPhysical`, `osMapTLB`, `osPiReadIo/WriteIo`).

## Support layers

- `Console::Init()` still empty; commands from the GUI
  (`config-cvars-logging.md`).
- **`splitText` decl/def mismatch FIXED** — signatures agree
  (`Utils.h:58` vs `Utils.cpp:21`), now test-covered
  (`tests/splittext_tests.cpp`); `stox.cpp` no longer dead in practice
  (`tests/stox_tests.cpp`).
- Threading still flat (`BS::thread_pool` a ResourceManager member; the
  16 ms VI timer the only background timer). Much of this range's audio
  diff is Doxygen (#1065/#1077), not behavior.
