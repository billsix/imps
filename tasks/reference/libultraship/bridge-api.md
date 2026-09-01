# libultraship — the bridge API (game-facing surface)

> **Pinned:** libultraship **1.3.1-397**
> (`7f2baa104108af3fca9f094754ea974a4973bdeb`, 2026-02-28 —
> MajorasMask's pin; a close cousin of iteration 14's 1.3.1-399,
> not its descendant). Updated 2026-09-01, iteration 15 of the
> reference crawl
> (`../../libultraship-reference-docs.md`). Re-sync check: compare
> `PIN_SHA` in `libultraship/fetch.sh` with the SHA above. This line is
> NEWER than tag 1.4.2 despite the smaller number.

`include/libultraship/bridge.h` now pulls **eight** headers (was six):
resource, audio, controller, window, consolevariable, crashhandler,
**gfxdebugger** (new), **gfx** (new). Headers at
`include/libultraship/bridge/`, impls at `src/libultraship/bridge/`.
Still plain `extern "C"`, still inline forwards through
`Context::GetInstance()`. **Guarding is uneven**: audiobridge
null-checks throughout; windowbridge and most others dereference
unguarded — bridges crash rather than no-op when a subsystem is absent.

## Gfx bridge (`gfxbridge.h`) — NEW

`GfxSetNativeDimensions(w,h)`, `GfxGetPixelDepthPrepare(x,y)`,
`GfxGetPixelDepth(x,y)`. Absorbed the pixel-depth pair from the window
bridge. The two depth functions cast-and-check;
**`GfxSetNativeDimensions` derefs the window cast AND the interpreter
weak_ptr unguarded** (`gfxbridge.cpp:9-15`) — two crash sites in six
lines if the window isn't a `Fast3dWindow`.

## GfxDebugger bridge (`gfxdebuggerbridge.h`) — NEW

`GfxDebuggerRequestDebugging`, `GfxDebuggerIsDebugging`,
`GfxDebuggerIsDebuggingRequested`, `GfxDebuggerDebugDisplayList(void*)`.

## Window bridge (`windowbridge.h`)

`WindowIsRunning` (**the port's main-loop condition** — replaces the
deleted `Window::MainLoop`), `WindowGetWidth/Height/AspectRatio`,
NEW `WindowGetPosX/PosY`, NEW `WindowIsFullscreen`. Pixel-depth moved
to gfxbridge. Zero null guards on all seven.

## Resource bridge (`resourcebridge.h`)

The by-name/by-CRC pair set survives; NEW `IsResourceManagerLoaded()`;
**REMOVED `ResourceDoesOtrFileExist`**. `ResourceLoad(...)` overloads +
templated forms remain C++-only. `ResourceLoadDirectoryAsync` is a bare
void forward (futures still not surfaced).
**`ResourceClearCache` is still declared and still never defined**
(`resourcebridge.h:44`) — it has survived the entire tree
reorganization unimplemented.

## CVar bridge (`consolevariablebridge.h`)

The Get/Set/Register triples, `CVarClear`, `CVarLoad`, `CVarSave`
survive; NEW `CVarClearBlock`, `CVarCopy`, and **`CVarExists` —
declared, never defined** (second dangling symbol; link error if
called). `CVarGet` → `shared_ptr<Ship::CVar>` still C++-only. Note the
header includes the C++-tree `ship/config/ConsoleVariable.h`.

## Audio bridge (`audiobridge.h`)

`AudioPlayerBuffered`, `AudioPlayerGetDesiredBuffered`,
`AudioPlayerPlayFrame`; NEW `Get/SetAudioChannels`,
`GetNumAudioChannels` (5.1 support). The **one** bridge that guards
throughout (null player → safe defaults). Header includes the C++
`ship/audio/AudioChannelsSetting.h`.

## Controller bridge (`controllerbridge.h`)

Still just `ControllerBlockGameInput`/`UnblockGameInput`. No
rumble/LED/mapping/backend bridge — but rumble no longer needs one:
stock `osMotorStart/Stop` works via the libultra shim
(`audio-and-libultra-shims.md`). LED still C++-only, and nothing in
LUS drives it.

## Crash handler bridge

One function, `CrashHandlerRegisterCallback`; the duplicated-typedef
quirk is gone (declared once, outside any namespace).

## Logging shim (`luslog.h`)

Unchanged surface; impl moved to `src/libultraship/log/luslog.cpp`;
`lusprintf` still missing `va_end`.

## C++ class surface (`classes.h`)

`include/libultraship/classes.h:4-37` re-exports ~26 headers, all
`ship/`-prefixed, with platform guards; NEW entries: `OtrArchive.h`
(expands to nothing without MPQ support), `O2rArchive.h`,
`ArchiveManager.h`. **This list now actually matters** — `src/` no
longer contains headers, so `classes.h` + the `include/` tree really
are the surface. No events/scripting bridges at this pin (later-line
features).
