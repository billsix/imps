# libultraship — the bridge API (game-facing surface)

> **Pinned:** libultraship **1.3.1-486**
> (`62e973aeb4a53ad4d22bb91e2d9373ecdfcd246c`, 2026-08-15 —
> OcarinaOfTime's pin; 4 commits past 1.3.1-482).
> Updated 2026-09-01, iteration 17 of the reference crawl
> (`../../libultraship-reference-docs.md`). Re-sync check: compare
> `PIN_SHA` in `libultraship/fetch.sh` with the SHA above. This line is
> NEWER than the 1.4.x tags despite the smaller number.

`include/libultraship/bridge.h` now pulls **nine** headers: resource,
audio, controller, window, consolevariable, crashhandler, gfxdebugger,
gfx, **events** (new). A **tenth header exists but is deliberately NOT
in `bridge.h`**: `scriptingbridge.h`, wholly inside `#ifdef
ENABLE_SCRIPTING`, exposing one function —
`void* ScriptGetFunction(const char* module, const char* function)`.

**Every bridge declaration is now `API_EXPORT`** (new
`include/ship/Api.h`: `extern "C"` + Windows dllexport/dllimport keyed
on `__DLL__`; #1051). Combined with `ENABLE_EXPORTS` /
`WINDOWS_EXPORT_ALL_SYMBOLS` on the target, the bridge is a
**dynamic-loading surface** (scripts/DLLs resolve these symbols from
the game binary), not just a link-time one. Function sets are otherwise
as at 397 — the large header diffs are API_EXPORT + Doxygen churn
(verified: resourcebridge same 26 functions, windowbridge same 7).
Bridges still forward through the Context — now via
**`GetRawInstance()`** — and still **crash rather than no-op** when a
subsystem is absent (audiobridge remains the one guarded bridge;
`GfxSetNativeDimensions` still double-derefs unguarded).

## Events bridge (`eventsbridge.h`) — NEW

`EventSystemRegisterEvent(name)`, `EventSystemRegisterListener(id, cb,
priority, file, line)`, `EventSystemUnregisterListener(ev, id)`,
`EventSystemCallEvent(id, event, file, line, key)` — forwarding through
`GetRawInstance()->GetEventSystem()` **unguarded**
(`eventsbridge.cpp:7-22`). The `EventTypes.h` macros (`CALL_EVENT`,
`REGISTER_LISTENER`, …) dispatch through these functions, so C and C++
share one path. LUS fires zero events itself at this pin.

## The other bridges — deltas only

- **resource**: dropped its cross-layer `fast/resource/type/Texture.h`
  include (#1097). **`ResourceClearCache` still declared, never
  defined** (`resourcebridge.h:136`) — has now survived two tree
  reorganizations and an export-attribute pass unimplemented.
- **consolevariable**: **`CVarExists` still declared, never defined**
  (`consolevariablebridge.h:138`). `CVarClearBlock`/`CVarCopy` defined.
- **window**: same 7 (`WindowIsRunning` remains the port's main-loop
  condition), zero null guards.
- **gfx / gfxdebugger / audio / controller / crashhandler**: unchanged
  sets (controller still just Block/UnblockGameInput; LED still has no
  bridge; rumble needs none — the libultra shim covers it).
- **luslog**: unchanged; `lusprintf` still missing `va_end`.

## C++ class surface (`classes.h`)

Still the `ship/`-prefixed re-export list — but it **dropped
`InputEditorWindow.h`** (#1097): InputEditorWindow and
GfxDebuggerWindow moved to `include/libultraship/window/gui/`, and a
consumer must include them from there directly. No events or scripting
classes are re-exported; `EventSystem`/`ScriptLoader`/`Keystore` are
included explicitly from their `ship/` paths.
