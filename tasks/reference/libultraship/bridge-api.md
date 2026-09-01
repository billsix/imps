# libultraship 1.0.0 — the bridge API (game-facing surface)

> **Pinned:** libultraship tag **1.0.0**
> (`31189cc9b3891a6049478e955a47589ce964265d`, 2023-05-29). Authored
> 2026-09-01, iteration 1 of the reference crawl
> (`../../libultraship-reference-docs.md`). Re-sync check: compare
> `PIN_SHA` in `libultraship/fetch.sh` with the SHA above.

The README's stated API contract: *"every C linkage function, variable,
struct, class, public class method, or enum included from
`libultraship.h`"* — semantic versioning promised over exactly this
surface. `include/libultraship/bridge.h` pulls the six bridge headers
from `src/public/bridge/`; everything routes through
`Context::GetInstance()`.

## Resource bridge (`resourcebridge.h`)

C++-only overloads above the `extern "C"` block:
`ResourceLoad(const char*)` / `ResourceLoad(uint64_t crc)` (+ templated
casting forms) returning `shared_ptr<LUS::IResource>`.

C linkage — by-name and by-CRC pairs throughout:
`ResourceGetCrcByName`, `ResourceGetNameByCrc`,
`ResourceGetSizeByName/Crc`, `ResourceGetIsCustomByName/Crc`,
`ResourceGetDataByName/Crc`, `ResourceGetTexWidthByName/Crc`,
`ResourceGetTexHeightByName/Crc`, `ResourceGetTexSizeByName/Crc`,
`ResourceLoadDirectory` (blocking) / `ResourceLoadDirectoryAsync`
(**discards its futures**), `ResourceDirtyDirectory`,
`ResourceDirtyByName/Crc`, `ResourceUnloadByName/Crc`,
`ResourceUnloadDirectory`, `ResourceGetGameVersions`,
`ResourceHasGameVersion`, `ResourceDoesOtrFileExist`, and
**`ResourceClearCache` — declared but NEVER DEFINED** (link error if
called). Tex getters return `-1`-ish sentinels on miss (into unsigned
types). CRC = `CRC64` from vendored StrHash64.

## CVar bridge (`consolevariablebridge.h`)

`CVarGetInteger/Float/String/Color/Color24`,
`CVarSetInteger/Float/String/Color/Color24`,
`CVarRegisterInteger/Float/String/Color/Color24`, `CVarClear`,
`CVarLoad`, `CVarSave`. C++-only: `CVarGet` →
`shared_ptr<LUS::CVar>`. (Color = RGBA `Color_RGBA8`; Color24 = RGB.)

## Audio bridge (`audiobridge.h`)

`AudioPlayerBuffered`, `AudioPlayerGetDesiredBuffered`,
`AudioPlayerPlayFrame(const uint8_t*, size_t)`. Push-only model — see
`audio-and-libultra-shims.md`.

## Controller bridge (`controllerbridge.h`)

`ControllerBlockGameInput(uint16_t mask)`,
`ControllerUnblockGameInput(uint16_t mask)`. **That is all** — no
rumble, LED, mapping, or scan bridge; those are C++-API-only
(`ControlDeck`/`Controller`), and nothing bridges backend selection.

## Window bridge (`windowbridge.h`)

`WindowGetWidth`, `WindowGetHeight`, `WindowGetAspectRatio`,
`WindowGetPixelDepthPrepare(float,float)`,
`WindowGetPixelDepth(float,float)`. Five trivial forwards — the whole
C graphics-window surface. (The real graphics API — `gfx_run` and
friends — is NOT in the bridge; consumers include
`graphic/Fast3D/gfx_pc.h` directly. See `fast3d-renderer.md` §API.)

## Crash handler bridge (`crashhandlerbridge.h`)

`CrashHandlerRegisterCallback(CrashHandlerCallback)` — the game appends
its own state dump into the crash report. (The callback typedef is
duplicated inside and outside namespace `LUS` — benign.)

## Logging shim (`luslog.h`)

`luslog(file, line, level, msg)`, `lusprintf(file, line, level, fmt,
...)`, macros `LUSLOG_TRACE/DEBUG/INFO/WARN/ERROR/CRITICAL`.

## libultra shims (`src/public/libultra/os.h` + undeclared extras)

Declared: `osContInit`, `osContStartReadData` (stub),
`osContGetReadData`, `osGetTime`, `osGetCount`. Defined but
**undeclared in any header**: `osCreateMesgQueue`, `osSendMesg`,
`osRecvMesg` (non-blocking ring buffers), `__osMaxControllers`.
Details and the long not-implemented list:
`audio-and-libultra-shims.md`.

## C++ class surface (`classes.h`)

~30 headers from `src/` re-exported wholesale (`Context`, `Window`,
`Gui`, `ResourceManager`, `Archive`, `ControlDeck`, controllers, audio,
binarytools, …) — and since `src/` is a PUBLIC include dir, consumers
can include anything anyway. Two boundary leaks compile only via
transitive luck: `ResourceManager.h` includes the thread-pool header
from a PRIVATE include dir, and `FileHelper.h`/`PathHelper.h` include
ZAPDUtils (linked PRIVATE).
