# libultraship — audio backends and libultra OS shims

> **Pinned:** libultraship **1.3.1-544**
> (`c151cc913dfcdcfbeffd0a1b50d26f4c620a5634`, 2026-07-16 — Ghostship's
> pin; **KiritoDv FORK branch** = 1.3.1-463 + 81 fork commits; mainline
> 464–486 absent). Updated 2026-09-01, iteration 18 (final) of the
> reference crawl (`crawl.md`). Re-sync
> check: compare `PIN_SHA` in `libultraship/fetch.sh`.

## Audio

Backends `WASAPI / SDL / COREAUDIO / NUL`; push-only; `AudioSettings`
(44100/1024/2480) + 5.1 unchanged; backend persistence on `Audio`
itself with the pulse→SDL migration (`Audio.cpp:69-77`);
`HResultException` error handling present (#1075, pre-463);
full-`Config::Save()` per backend set.

**REVERTED vs mainline 486 — three fixes absent, their hazards live:**

- `NullAudioPlayer::Buffered()` **returns 0**
  (`NullAudioPlayer.cpp:18-20`) — the #1167 audio-thread spin/hang on
  the null backend is a live hazard here (and NUL is the silent
  fallback when a device fails).
- **`~AudioPlayer` is non-virtual** (`AudioPlayer.h:41`) — #1212
  absent.
- `WasapiAudioPlayer` has `DoClose()` but **no destructor calls it**
  — the WASAPI teardown-hang fix is absent.

**Fork change**: iOS drops CoreAudio — `#ifdef __APPLE__` became
`#if defined(__APPLE__) && !defined(__IOS__)` (`Audio.cpp:3,24,52`);
iOS is SDL/NUL only.

## libultra shims

Same 8 `os_*.cpp` (+ `AudioDmaRegistry.{h,cpp}`, pre-463):

| Area | Behavior at this pin |
|---|---|
| `osContInit` | **REVERTED to the old shape**: gamecontrollerdb load + `SDL_Init(GAMECONTROLLER)` inside `osContInit`, **`exit(EXIT_FAILURE)` on failure** (`os.cpp:15-36`, exit `:29`) — the mainline non-fatal `InitControlDeck` move was #1103 |
| `osPiStartDma` | clamped via the opt-in 8-slot **AudioDmaRegistry** (`os_pi.cpp:17-28`); LUS never registers blobs itself — unregistered addresses pass through unclamped |
| `osGetTime`/`osSetTime` | N64 46.875 MHz cycle units (`os.cpp:48-60`) |
| Rumble / queues / VI / EEPROM / cache / VM | unchanged (rumble works via `osMotorStart/Stop`; queues never block; 16 ms VI timer; 512-byte `default.sav`; no-ops) |
| Threads | **still absent** |
| **NEW (fork, 3c511468)** | **`API_EXPORT` spread across the libultra headers** (`os.h`, `gu.h`, `message.h`, `eeprom.h`, `motor.h`) — the libultra surface is now a dynamic-loading surface for scripts, beyond the bridge |

**Dangling declarations unchanged**: `osContGetStatus` (`os.h:105`),
`osAiSetFrequency` ×2 (`os.h:137`+`:141`), `osViFade` (`:116`),
`osViRepeatLine` (`:117`) — zero definitions.

## Support layers

`Console::Init()` empty; `splitText` fixed + tested; threading flat;
`stox` tested — all as 463. See `config-cvars-logging.md` for the
reverted logging teardown.
