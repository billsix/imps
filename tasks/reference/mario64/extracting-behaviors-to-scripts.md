# Reference: Feasibility of extracting character logic to a script (Lua? C?)

> **Provenance:** authored 2026-09-06 against Ghostship pin `49c5312a` /
> libultraship submodule `c151cc91`. Anchors verified in the port
> (`src/port/Engine.cpp`, `src/port/mods/`, `CMakeLists.txt`) and libultraship
> (`libultraship/src/ship/scripting/`). Part of the mario64 set — map at
> [`README.md`](README.md). Backs the task
> `tasks/mario64-actions-to-lua.md`. Read `hardcoded-vs-data-driven.md` and
> `object-and-behavior-system.md` first (what is bespoke C).

## TL;DR — the honest verdict

**"Extract to Lua" is the wrong framing given what the port actually has.**
There is **no Lua anywhere** in the game or libultraship. The port's scripting
runtime is **libtcc (TinyCC)**: it compiles **C** mod source *at runtime* and
links it against the game's own **exported symbols**. Mods hook in through the
**events system** (`REGISTER_LISTENER`) and static-init registration. So:

- **Extract to the port's own C-scripting (libtcc): genuinely feasible,
  incrementally, for enemies; harder for Mario.** The infrastructure already
  exists and is how every mod works today.
- **Extract to Lua specifically: a large new project** — you would add a Lua VM
  and hand-write bindings for `struct Object` / `MarioState` and hundreds of
  `cur_obj_*` helpers, then pay Lua↔C marshalling on a per-object-per-frame hot
  path. High cost, real performance risk, awkward fit for pointer/bitflag/
  struct-offset-heavy C. Only worth it if the *goal* is moddability by
  non-C programmers, not just "get the logic out of the compiled binary."

## 1. What the runtime actually is (verified)

- **libtcc, compiling C.** `libultraship/src/ship/scripting/ScriptLoader.cpp`
  includes `<libtcc.h>` (`:12`), creates a `TCCState` (`:214`), and compiles mod
  source with `tcc_compile_string` (`:317`). The CMake links `libtcc`
  (`libultraship/src/CMakeLists.txt:182`). **Zero Lua** — a grep for
  `lua_State`/`luaL_`/`.lua` across `src` and `libultraship/src` is empty.
- **Compiled with the game's own defines.** `SetupScriptLoader`
  (`Engine.cpp:301`) hands TCC the same macros the game builds with
  (`VERSION_US`, `F3D_OLD`, `GBI_FLOATS`, `_LANGUAGE_C`, …) and points it at the
  shipped `.tcc/` toolchain (includes + `libtcc1.a`). A mod is C compiled in the
  game's own dialect.
- **Reloadable.** A dev-tools menu unloads and reloads scripts live
  (`GhostshipMenuDevTools.cpp:169`, `GameEngine::LoadScripts`), so hot-reload of
  behavior C is already a solved problem here.

## 2. How a mod reaches the game (the binding surface)

This is the part that makes C-extraction feasible: **the game exports its
symbols, so a runtime-compiled mod can call the game's functions and read its
globals directly.**

- **Symbol export:** `set_target_properties(... ENABLE_EXPORTS TRUE)`
  (`CMakeLists.txt:558`) and `-Wl,-export-dynamic` (`:872`) — and the same for
  libultraship. So `cur_obj_move_using_vel`, `find_floor`, the object fields via
  a pointer, all resolve at mod link/relocate time.
- **Hooking:** mods register on the **events system** (the same one the cheats
  use — `src/port/events/`): e.g. `src/port/mods/BetterLevelSelect.cpp:499`
  `REGISTER_LISTENER(LevelScriptBeginArea, …, [](IEvent* e){...})`, and
  `EngineUniforms.cpp:77` hooks `GameLoopTick`. Registration is a static-init
  `RegisterShipInitFunc` (`BetterLevelSelect.cpp:540`). Mods declare themselves
  with a `manifest.json` (template at `workspace/template/manifest.json`).

So a mod today is **C that links against the game and reacts to events** — not a
sandboxed script in another language.

## 3. What each tier would actually take

**Enemies (the feasible target).** An enemy's native loop (`bhv_goomba_update`,
`object-and-behavior-system.md`) is a self-contained C function that touches
only `o->` fields and shared `cur_obj_*`/`obj_*` helpers — exactly the symbols a
mod can link against. Moving it into a hot-reloadable C mod is a real,
bounded experiment. **The catch:** the behavior script holds a **compile-time
function pointer** — `CALL_NATIVE(bhv_goomba_update)` bakes the address of the
compiled-in function into the `const BehaviorScript bhvGoomba[]` array. To make
the VM call a *script's* function instead, you must redirect that pointer at
runtime (patch the array — likely in read-only memory, so `mprotect` — or add a
"native by name" indirection to the VM). That indirection is the core of a PoC.

**Mario (the hard target).** Mario's action machine is bigger, hotter, and
structured as a static table of action functions outside the object/behavior
system (`hardcoded-vs-data-driven.md`). Redirecting one cold action to a mod is
conceivable; moving the whole hot machine is a major effort with the same
pointer-redirection problem at larger scale.

**Performance.** The update runs for every object every frame, and Mario's
action every frame. A C mod called across a relocated-symbol boundary is cheap
(a normal call). A **Lua** per-tick path pays VM entry + argument marshalling
per object per frame — the real reason Lua is questionable for the hot path,
and fine only for cold/rare logic.

## 4. Recommended first experiment (for the task)

1. **Add a "native-by-name" indirection** to the behavior VM (or a runtime
   pointer-patch) so a `CALL_NATIVE` target can be supplied by a loaded mod.
2. **Move `bhv_goomba_update` into a C mod**, hot-reloaded, keeping behavior
   **frame-identical** (differential trace vs. the C version).
3. **Measure** per-frame cost with many Goombas: mod-C vs. compiled-C.
4. Only if that is clean and someone still wants Lua, prototype a **single**
   scripted behavior in Lua behind a minimal binding, and measure the same — to
   quantify the marshalling cost before committing to a VM.

## How this relates to the course

Out of scope for the courses — but it is a sharp lesson in *how a moddable game
is actually built*: runtime code compilation, dynamic symbol export, an event
bus for hooks, and hot-reload. The "should behavior be data, C, or a scripting
language?" question is a real engine trade, and the answer here (the port chose
runtime **C**, not a scripting VM) is itself informative.

## Anchors (no doc-region markers added — this is analysis, not a book snippet)

`libultraship/src/ship/scripting/ScriptLoader.cpp:12,214,317`;
`libultraship/src/CMakeLists.txt:182`; `src/port/Engine.cpp:301`;
`CMakeLists.txt:558,872`; `src/port/mods/BetterLevelSelect.cpp:499,540`;
`src/port/mods/EngineUniforms.cpp:77`; `workspace/template/manifest.json`.
