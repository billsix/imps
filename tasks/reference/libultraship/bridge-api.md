# libultraship — the bridge API (game-facing surface)

> **Pinned:** libultraship **1.3.1-544**
> (`c151cc913dfcdcfbeffd0a1b50d26f4c620a5634`, 2026-07-16 — Ghostship's
> pin; **KiritoDv FORK branch** = 1.3.1-463 + 81 fork commits; mainline
> 464–486 absent). Updated 2026-09-01, iteration 18 (final) of the
> reference crawl (`crawl.md`). Re-sync
> check: compare `PIN_SHA` in `n64/libultraship/fetch.sh`.

`include/libultraship/bridge.h` pulls the same **nine** headers
(resource, audio, controller, window, consolevariable, crashhandler,
gfxdebugger, gfx, events — `bridge.h:11`); `scriptingbridge.h` still
outside it, wholly `#ifdef ENABLE_SCRIPTING`, one function
`ScriptGetFunction` (`scriptingbridge.h:23`). `API_EXPORT`/`Api.h` on
every declaration (pre-463). **All bridges forward through
`GetInstance()`** (shared_ptr — this pin predates the mainline
`GetRawInstance` rework, e.g. `resourcebridge.cpp:9`,
`eventsbridge.cpp:7-23`), still unguarded except audiobridge.

**Fork-specific**: `API_EXPORT` now also covers the **libultra
headers** (`os.h`, `gu.h`, `message.h`, `eeprom.h`, `motor.h` —
commit 3c511468), making the whole libultra shim surface resolvable by
dynamically loaded scripts. The renderer grew C entry points beyond
the bridge headers: `gfx_register_post_pass` and friends
(`interpreter.cpp:7089`; decls `interpreter.h:828-830`),
`gfx_shader_cache_clear` (`:7108`), custom-uniform and shader-settings
registration — all reached via `include/fast/interpreter.h`, not
`bridge.h`.

## Dangling declarations (link error if called) — all survive

- `ResourceClearCache` (`resourcebridge.h:136`)
- `CVarExists` (`consolevariablebridge.h:138`)
- `osContGetStatus` (`os.h:105`), `osAiSetFrequency` declared twice
  (`os.h:137`+`:141`), `osViFade` (`os.h:116`), `osViRepeatLine`
  (`os.h:117`)

## The bridges — no set changes vs 463

resourcebridge 26 functions (`ResourceLoadDirectoryAsync` still
discards its future); windowbridge 7 (`WindowIsRunning` = the
main-loop condition); cvar bridge (`CVarClearBlock`/`CVarCopy`
defined); audiobridge guarded; controllerbridge still just
Block/UnblockGameInput (LED bridgeless; rumble via the libultra shim);
crashhandler single function; events bridge 4 functions unguarded;
luslog with the eternal missing `va_end`.

## C++ class surface (`classes.h`)

Unchanged from 463: `ship/`-prefixed re-exports, no
InputEditorWindow/GfxDebuggerWindow (both live under
`include/libultraship/window/gui/`), no events/scripting re-exports.
