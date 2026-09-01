# libultraship — audio backends and libultra OS shims

> **Pinned:** libultraship tag **1.3.0**
> (`317edd72cc317387f8ac010a9ec772d4bfdfdbb6`, 2023-10-02). Authored
> 2026-09-01, iteration 1 of the reference crawl
> (`../../libultraship-reference-docs.md`). Re-sync check: compare
> `PIN_SHA` in `libultraship/fetch.sh` with the SHA above.

## Audio

`LUS::Audio` (owner/selector) + `LUS::AudioPlayer` (abstract base,
`src/audio/AudioPlayer.h:7`) with exactly three backends: **SDL** (queue
API, always built), **WASAPI** (`_WIN32`), **PulseAudio**
(`__linux__`/`__BSD__` — but the *selector* uses `__linux` only, so BSD
compiles the class and can never pick it). No ALSA, CoreAudio, OpenAL,
or null player; macOS/consoles fall through to SDL.

**The model is push-only — there is no audio callback.** The game
pushes PCM (S16 stereo, sample rate **hard-coded 44100** at
`AudioPlayer.h:20`) via the C bridge and polls fill level; nothing in
LUS ever generates or requests audio:

- `AudioPlayerBuffered()` / `AudioPlayerGetDesiredBuffered()` /
  `AudioPlayerPlayFrame(buf, len)` (`src/public/bridge/audiobridge.cpp`).
- Desired-buffered is the magic **2480 frames** in all three backends.
- SDL: `SDL_QueueAudio`, drops the frame wholesale above 6000 queued
  frames. WASAPI: shared-mode render client, lazy `Start()` after 1500
  frames, re-inits on default-device change (`IMMNotificationClient`).
- Pulse: a synchronous `pa_mainloop` — `Play()` and `Buffered()` both
  **block** iterating the loop; buffer attrs derive from N64 constants
  `SAMPLES_HIGH 752`/`SAMPLES_LOW 720`; the stream is literally named
  `"zelda"` (`PulseAudioPlayer.cpp:103`).

**Verified bug:** `Audio::InitAudioPlayer`'s fallback path
(`Audio.cpp:29-37`) recursively creates a working SDL player via
`SetAudioBackend(SDL)`, then falls through and creates a **second** one,
leaking the first SDL audio device (no destructor closes it). Also:
`SetAudioBackend` does a full `Config::Save()` on every call, including
during startup.

## libultra shims — a very thin slice

**Everything lives in one file:** `src/public/libultra/os.cpp`. The 27
headers under `include/libultraship/libultra/` define types and macros,
but almost nothing has an implementation:

| Implemented | Behavior |
|---|---|
| `osContInit` | `SDL_Init(SDL_INIT_GAMECONTROLLER)` (**exit(1) on failure**), loads `gamecontrollerdb.txt`, then `ControlDeck::Init` — this is what finishes controller setup, not `Context` |
| `osContStartReadData` | **stub, returns 0** |
| `osContGetReadData` | zeroes 4 pads, `ControlDeck::WriteToPad` |
| `osGetTime` | `steady_clock` raw ticks — **not** N64 counter units |
| `osGetCount` | `steady_clock` **milliseconds** as uint32 |
| `osCreateMesgQueue` / `osSendMesg` / `osRecvMesg` | ring buffer; **never blocks** — `OS_MESG_BLOCK` accepted and ignored; returns −1 on full/empty. The thread-wait fields in `OSMesgQueue` are never touched |

The message-queue trio is **not declared in any header** (`os.h`
declares only the five others) — consumers declare them or use their
own prototypes.

**Not implemented at all** (types/macros only, or declared with no
definition — a consuming game must supply or avoid them):

- **Threads**: no `osCreateThread`/`osStartThread`/scheduler of any
  kind. LUS 1.0.0 assumes the game flattened its threading.
- **Rumble pak**: `motor.h` declares `__osMotorAccess`/`osMotorInit`
  (and macros `osMotorStart/Stop` onto them) with **no definition**.
- Interrupt masks (`osSetIntMask` etc.), `osPfs*`, `osVi*`, `osPi*`,
  `osSpTask*`, `osEeprom*` — headers only.

## Support layers (config/log details in `config-cvars-logging.md`)

- `src/debug/Console` — a command **registry** only: `Console::Init()`
  is an empty function; the actual commands (`bind`, `help`, `set`,
  `get`, …) are registered by the GUI's ConsoleWindow — a GUI-less
  consumer gets an empty console.
- `src/debug/CrashHandler` — signal/SEH handlers with
  backtrace+demangle (Linux) / DbgHelp StackWalk (Windows), a 32 KB
  fixed buffer, and a game-supplied callback
  (`CrashHandlerRegisterCallback`). Quirks: it tries to catch
  **SIGKILL** (always fails silently); `AppendStrTrunc` over-reads its
  source inside a signal handler.
- `src/utils/` — `Math::clamp`, `splitText` (**unusable**: declaration
  and definition have different signatures — const-ref vs by-value —
  so any caller gets a link error; zero callers today), `stox.cpp`
  (safe string→num wrappers, **entirely unused**), macOS folder
  helper, `binarytools/` (BinaryReader/Writer, MemoryStream,
  endianness).
- `src/port/` — **empty on desktop**; Switch (`SwitchImpl`, overclock
  profiles keyed by `gSwitchPerfMode`) and Wii U (`WiiUImpl`, WPAD/VPAD
  drivers). (1.0.0's Wii U compile-breaker — both controller files
  included a nonexistent `menu/ImGuiImpl.h` — was fixed in 1.0.1.) Also `Switch::PrintErrorMessageToScreen` indexes
  `RandomTexts[rand() % 25]` into a 16-entry array (with a
  missing-comma string concatenation inside it).
