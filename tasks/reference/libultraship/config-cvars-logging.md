# libultraship — config, console variables, logging

> **Pinned:** libultraship **1.3.1-544**
> (`c151cc913dfcdcfbeffd0a1b50d26f4c620a5634`, 2026-07-16 — Ghostship's
> pin; **KiritoDv FORK branch** = 1.3.1-463 + 81 fork commits; mainline
> 464–486 absent). Updated 2026-09-01, iteration 18 (final) of the
> reference crawl (`crawl.md`). Re-sync
> check: compare `PIN_SHA` in `n64/libultraship/fetch.sh`.

## Config — 463 shapes throughout

`Nested()` unflattens the whole doc per get (`Config.cpp:44`);
missing-component walk keeps the subtree (`:46-52`); hardened `Reload`
(`:204-211`); `SetBlock`/`EraseBlock` self-`Save()` (`:131-186`);
`GetArray`/`SetArray` dead (`:220-229`); `mIsNewInstance` write-only;
doxygen still cites the nonexistent `RegisterConfigVersionUpdater`
(`Config.h:19` vs `:188`). Backend persistence on `Ship::Audio`
(pulse→SDL migration `Audio.cpp:75-78`) and `Ship::Window`
(`Window.cpp:125-135`). The Keystore's `"Keystore"` node is the one
non-obvious config consumer (`Keystore.cpp:59-88`).

**App dir** (`Context.cpp:520-569`): Android external storage →
**fork-new `__EMSCRIPTEN__` `"/storage"`** (`:528-530`) → iOS
`$HOME/Documents` → Apple/Linux `SHIP_HOME` (with `~` expansion) →
`NON_PORTABLE` `SDL_GetPrefPath` — which reads
`GetInstance()->mShortName` (the mainline #1170 undefined-symbol fix is
absent) → `"."`. The fork also redirects the iOS bundle path through
`FolderManager` (`:462-467`).

## CVars

- Union bugs intact: `SetString`/`CopyVariable` set `Type` then free
  possibly-reinterpreted `String` bits (`ConsoleVariable.cpp:117-121`,
  `:220-232`); `LoadLegacy` double-`strdup` leak (`:370`). Transparent
  hash lookup present (`ConsoleVariable.h:199-211`).
- `cmake/cvars.cmake` = **23 macros** (byte-identical to mainline 486;
  the earlier "24" was a miscount). `CVAR_SCRIPT_SAFE_LEVEL` still has
  zero code references.
- **NEW fork namespaces, not in cvars.cmake** — grep for the literal
  prefixes: `gShaderSettings.<pack>.<var>` (shader-pack tweakables,
  `interpreter.cpp:4777-4784`), `gEnhancements.Graphics.DitherNoise`
  (default 0), `gEnhancements.Graphics.AsyncTextureLoad`,
  `gEnhancements.Graphics.TextureUploadBudget` (default 1/frame),
  `gMipDebug`, `TextureReplacementDebug` — see `fast3d-renderer.md`.
- Bridge: **`CVarExists` still declared, never defined**
  (`consolevariablebridge.h:138`); `CVarClearBlock`/`CVarCopy` defined.

## Logging — REVERTED to the pre-#1103 shape

`spdlog::init_thread_pool(8192, 1)` (`Context.cpp:122`) and the
release async logger **uses the global pool** (`:170-171`) — the
mainline Context-owned `mLogThreadPool` does not exist here. Debug =
sync `"multi_sink"` flush-on-trace (`:166-168`); release = async
overflow-block flush-on-info; rotation 10 MB × 10 (`:163`); level
parameters default debug/warn (`Context.h:192-193`); the console-sink
level set is **commented out** (`:158`). Teardown: `~Context` ends
with `spdlog::shutdown()` (`:60`) after an unguarded
`GetWindow()->SaveWindowToConfig()` (`:40`) and `GetConfig()->Save()`
(`:58`) — early-destroy crashes live in those derefs, not in the
mainline `mLogger->flush()`. `lusprintf` still never calls `va_end`
(`luslog.cpp:15-22`).

## Console

`Init()` empty (`Console.cpp:15-16`); `Run` single-find (`:30-52`);
`GetCommand` throws `std::out_of_range` (`:71-77`); all 7 commands
(`set get help clear unbind bind bind-toggle`) registered by
`ConsoleWindow::InitElement` (`ConsoleWindow.cpp:304-317`).

## Test coverage

The (463-identical) gtest suite still covers **none** of Config,
CVars, Console, or logging.
