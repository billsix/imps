# libultraship — audio backends and libultra OS shims

> **Pinned:** libultraship **1.3.1-399**
> (`e0c1b1fc35e3b4143f9417b21c7ea6e75ccfb94b`, 2026-02-20). Updated
> 2026-09-01, iteration 14 of the reference crawl
> (`../../libultraship-reference-docs.md`). Re-sync check: compare
> `PIN_SHA` in `libultraship/fetch.sh` with the SHA above. This line is
> NEWER than tag 1.4.2 despite the smaller number.

## Audio

`AudioBackend { WASAPI, SDL, COREAUDIO, NUL }`
(`include/ship/audio/Audio.h:9`). **PulseAudio is deleted** (configs
carrying `"pulse"` migrate to SDL at read); **CoreAudio and a Null
player are new**. Selection (`Audio.cpp:16-41`): WASAPI on `_WIN32`,
CoreAudio on `__APPLE__`, SDL always, default → Null. The 1.4.2
double-player leak is **fixed** — the fallback is now a clean
`if (!Init()) SetCurrentAudioBackend(NUL)` — but that means a bad
device **degrades to silence with nothing surfaced**. Linux is
SDL-only. `SetCurrentAudioBackend` still does a full `Config::Save()`
on every call, startup included (`:67-68`).

**Sample rate is no longer hard-coded**: `AudioSettings { SampleRate =
44100, SampleLength = 1024, DesiredBuffered = 2480, ChannelSetting =
audioStereo }` (`include/ship/audio/AudioPlayer.h:11-16`), threaded
`CreateInstance` → `InitAudio` → each player; runtime setters exist.
The 2480 magic number is now just the default.

**NEW: 5.1 surround.** `AudioChannelsSetting` stereo / matrix-5.1
(through a `SoundMatrixDecoder`) / raw-5.1; runtime channel switching
reinitializes the device without restart (`AudioPlayer.cpp:79-107`,
`Audio.cpp:77-85`).

Push-only is unchanged — no callback, LUS never requests audio;
interleaved S16. Back-pressure is per-backend now: SDL drops the frame
above 6000 queued; CoreAudio uses 6000 as its ring size; **WASAPI has
no 6000 constant** — it clamps to device-buffer free space. Latent
hazard: `AudioPlayer::~AudioPlayer()` is **non-virtual** — safe today
only because players are made via `make_shared<Concrete>`.

## libultra shims — no longer "a very thin slice"

Now **8 files** at `src/libultraship/libultra/`: `os.cpp os_cache.cpp
os_eeprom.cpp os_mesg.cpp os_pi.cpp os_time.cpp(empty!) os_vi.cpp
os_vm.cpp`.

| Area | Behavior at this pin |
|---|---|
| `osContInit` | new signature `(OSMesgQueue*, uint8_t* bits, OSContStatus*)`; loads `gamecontrollerdb.txt`, `SDL_Init(GAMECONTROLLER)` — **still `exit(EXIT_FAILURE)` on failure** (`os.cpp:29`) — then `ControlDeck::Init` |
| `osContStartReadData` / `osContGetReadData` | still stub-0 / zero-fill + `WriteToPad` |
| `osGetTime` / `osGetCount` | **CHANGED — now real N64 46.875 MHz cycle units** via a `std::ratio<3000,64>` duration (`os.cpp:5-8`, `:54-64`). A port compensating for 1.4.2's raw-ticks/milliseconds is now wrong by a large constant factor. `osSetTime` is new |
| **Rumble** | **implemented**: `__osMotorAccess` → `GetRumble()->Start/StopRumble` (`os.cpp:88-102`) — stock `osMotorStart/Stop` just works |
| Message queues | now declared in `message.h`; `osJamMesg`/`osSetEventMesg` added — but **the block flag is still ignored, never blocks**, −1 on full/empty (`os_mesg.cpp:15,39`). The complete-looking API invites the wrong assumption |
| **VI** (new) | `osCreateViManager` installs a 16 ms `SDL_AddTimer` posting `OS_EVENT_VI`; other setters no-op; framebuffer getters return nullptr (`os_vi.cpp`) |
| **PI/DMA** (new) | `osPiStartDma` is a **plain unclamped `memcpy`** (`os_pi.cpp:18`) — a decomp trusting SDK bounds behavior gets memory corruption, not an error |
| **EEPROM** (new) | full 512-byte `default.sav` read/write via the app dir (`os_eeprom.cpp`) |
| Cache / VM (new) | all no-ops; `osVirtualToPhysical` = identity |
| **Threads** | **still absent** — zero `osCreateThread` etc.; `thread.h` has only the ABI struct |

**Declared-but-undefined** (link error if called): `osContGetStatus`,
`osAiSetFrequency` (declared **twice**, `os.h:140`+`:144`), `osViFade`,
`osViRepeatLine`. **Defined-but-undeclared** (a C port writes its own
prototype): `osViGetNext/CurrentFramebuffer`, `osVirtualToPhysical`,
`osMapTLB`, `osPiReadIo/WriteIo`. The AI shims `osAiGetLength`/
`osAiSetNextBuffer` are `// TODO` stubs returning 0.

## Support layers

- Threading is flat: `BS::thread_pool` is a direct `ResourceManager`
  member; the only background timer is the 16 ms VI SDL timer. No
  `ThreadPool` component (that's a later-line thing).
- `Console::Init()` still empty — commands come from the GUI
  (`config-cvars-logging.md`).
- `src/ship/utils/`: `splitText` decl/def signature mismatch **still**
  a link error for any caller (`Utils.h:18` vs `Utils.cpp:26`, which
  also puts default args on the definition); `stox.cpp` still entirely
  unused; `glob.c` vendored from the Linux kernel.
- Switch/Wii U port layers deleted (with their bugs);
  `src/ship/port/mobile/MobileImpl.cpp` is the only port dir
  (android/iOS).
