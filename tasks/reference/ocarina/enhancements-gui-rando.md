# Reference: The feature layer — GameInteractor, SohGui, Randomizer

> **Provenance:** authored 2026-07 against Shipwright `988b53665` (9.2.3-320, the old
> fork base) — 101 commits behind the current imps pin `acdbc651d` (9.2.3-421). Spot-check
> details against the pinned checkout before trusting them.

*Standing reference. SoH's defining and largest area: the GameInteractor hook system, the ImGui menu
(SohGui), and the Randomizer. Read before adding an enhancement/cheat, a menu widget, or touching
rando. Companions: [port-layer.md](port-layer.md), [architecture-overview.md](architecture-overview.md).*

## GameInteractor — the hook/event system at the heart of everything

`soh/soh/Enhancements/game-interactor/`. The decoupling layer: the OoT decomp fires named events;
enhancement/rando `.cpp` files subscribe **without editing decomp**. Singleton
`GameInteractor::Instance` (`GameInteractor.h:185`), constructed in `InitOTR` (`OTRGlobals.cpp:1534`).
**SoH has a full GameInteractor** (not a stub — a real difference from some ports like Ghostship).

- **Hooks declared once** in `GameInteractor_HookTable.h` via `DEFINE_HOOK(name, (args))` (~130 hooks:
  `OnActorInit`, `OnPlayerUpdate`, `OnSceneInit`, `OnItemReceive`, `OnLoadGame`, `OnVanillaBehavior`,
  `OnSaveFile`, file-select hooks, …). It's an **X-macro `#include`d multiple times** with
  `DEFINE_HOOK` redefined per site (`GameInteractor.h:497,522`) — once to declare each hook as a
  struct type (`H::fn`, `H::filter`), once for the cleanup loop.
- **Four registration flavors** (templated on hook struct `H`, `GameInteractor.h:247-447`):
  `RegisterGameHook<H>(fn)` (all), `RegisterGameHookForID<H>(id, fn)` (per actor-id/scene/VB-flag),
  `RegisterGameHookForPtr<H>(ptr, fn)` (per instance), `RegisterGameHookForFilter<H>(filterFn, fn)`
  (predicate; helpers in `HookFilter`). Each returns a `HOOK_ID`; **unregister is deferred** (queued,
  applied at fire time / `RemoveAllQueuedHooks`, run each frame from
  `GameInteractor_ExecuteOnGameStateMainStart`).
- **Firing** — `ExecuteHooks<H>(args…)` / `…ForID` / `…ForPtr` / `…ForFilter`. Decomp C fires through
  `extern "C"` wrappers in `GameInteractor_Hooks.cpp` (e.g. `GameInteractor_ExecuteOnActorInit(actor)`
  at `z_actor.c:1263`).
- **Hook categories** (`GameInteractor_HookTable.h`): lifecycle (`OnLoadGame`, `OnGameFrameUpdate`,
  `OnSceneInit`, `OnTransitionEnd`), actors (`ShouldActorInit`, `OnActorUpdate`, `OnEnemyDefeat`,
  `OnBossDefeat`), player (`OnPlayerUpdate`, `OnPlayerBonk`, `OnPlayerHealthChange`), items/flags
  (`OnItemReceive`, `OnFlagSet`, `OnSceneFlagSet`), UI/dialog (`OnDialogMessage`,
  `OnKaleidoscopeUpdate`), file-select, audio (`OnSeqPlayerInit`), rando.

### `OnVanillaBehavior` / the VB system — the important override mechanism

This is how SoH **changes** decomp behavior (vs. just observing). Decomp calls
`GameInteractor_Should(GIVanillaBehavior flag, defaultResult, ...varargs)` (`GameInteractor_Hooks.cpp:244`)
at a decision point; subscribers can flip the returned bool. **~178 decomp call sites** are gated
this way (e.g. `z_lifemeter.c:682 VB_HEALTH_METER_BE_CRITICAL`, `z_en_item00.c:364 VB_ITEM00_DESPAWN`).
There are **421 `VB_*` flags** enumerated + documented (each with its `result`/`args` contract) in
`vanilla-behavior/GIVanillaBehavior.h` — **the real API surface between decomp and enhancements.**
Subscribe with `REGISTER_VB_SHOULD(flag, body)` / `COND_VB_SHOULD` (`GameInteractor.h:146-181`).

### Effects / RawActions (the imperative side — Crowd Control)

`GameInteractionEffect.{h,cpp}` — an effect-object hierarchy (`SetFlag`, `ModifyHealth`,
`FreezePlayer`, `ModifyGravity`, … ~40 classes) applied via `GameInteractor::ApplyEffect`.
`RawAction` (`GameInteractor.h:539`) exposes one-shot pokes (`HealOrDamagePlayer`, `TeleportPlayer`,
`SpawnActor`). `GameInteractor::State` (`:188`) holds live cheat state (LinkSize, PacifistMode,
GravityLevel) read by decomp via C accessors.

## The enhancement pattern (CVar + hook + menu widget)

Canonical three-part pattern; example `Enhancements/Cheats/MoonJump.cpp` (28 lines):
1. **CVar** — `CVAR_CHEAT("MoonJumpOnL")` (`:11`). Prefixes in `soh/soh/cvar_prefixes.h`.
2. **Hook**, conditionally registered on the CVar via `COND_HOOK(hookType, condition, body)`
   (`GameInteractor.h:155`): `MoonJump.cpp:24` registers `OnPlayerUpdate` only when the CVar is set.
   `COND_HOOK` unregisters + re-registers, so it's re-entrant.
3. **ShipInit registration** (`:27`): `static RegisterShipInitFunc initFunc(RegisterMoonJump, {
   CVAR_MOON_JUMP_NAME });`. The register function runs at boot **and** whenever the listed CVar
   changes (the menu calls `ShipInit::Init(cvar)` after a write — `CVAR_INT_SHIP_INIT` macro,
   `SohMenuEnhancements.cpp:17`).
4. **Menu widget** — declared separately in the SohGui builders (§below), keyed to the same CVar.

**The wiring, in one line:** the menu writes a CVar → `ShipInit::Init(cvar)` re-runs every
`RegisterShipInitFunc` that listed it → that function (re)registers/unregisters the GameInteractor
hook via `COND_HOOK`. **Widget and behavior are coupled only by the shared CVar string** — miss any
leg and the toggle silently does nothing. Many enhancements instead use the VB pattern
(`REGISTER_VB_SHOULD` gated on a CVar) to override decomp decisions.

## SohGui — the ImGui menu framework (`soh/soh/SohGui/`)

Built on libultraship's `Ship::GuiWindow`.
- **`Menu : public GuiWindow`** (`Menu.h:12`); **`SohMenu : public Ship::Menu`** (`SohMenu.h:30`).
- **Registered into LUS**: `SohGui.cpp:104` creates `mSohMenu = make_shared<SohMenu>(CVAR_WINDOW("Menu"),
  "Port Menu")` and `gui->SetMenu(mSohMenu)`. Auxiliary windows (editors/trackers) are also
  `make_shared` here (`:107-203`) and become LUS-managed `GuiWindow`s.
- **Content builders**: `SohMenu::AddMenuElements()` fans out to `AddMenuSettings/AddMenuEnhancements/
  AddMenuDevTools/AddMenuRandomizer/AddMenuNetwork`, each its own file (`SohMenuEnhancements.cpp`,
  `SohMenuRandomizer.cpp`, …).
- **Widget builder** (fluent): `AddSidebarEntry(section, sidebar, cols)` then `AddWidget(path, label,
  WIDGET_TYPE).CVar(...).Options(...).Callback(...).PreFunc(...)` (`SohMenuEnhancements.cpp:164-206`).
  `AddWidget` returns `WidgetInfo&` (`MenuTypes.h:101-210`).
- **Widget types** (`MenuTypes.h:32-54`): `WIDGET_CVAR_CHECKBOX/COMBOBOX/SLIDER_INT/FLOAT/
  COLOR_PICKER/BTN_SELECTOR`, `WIDGET_BUTTON`, `WIDGET_SEPARATOR_TEXT`, `WIDGET_WINDOW_BUTTON` (opens
  another GuiWindow), `WIDGET_CUSTOM`. `CVAR_*` variants auto-bind to a CVar. Options structs +
  low-level ImGui drawing in `UIWidgets.hpp/.cpp` / `UIWidgetOptions.hpp`. `WidgetPath` = {sidebar,
  section, column}. Built-in search (`WIDGET_SEARCH`).

## The Randomizer — `soh/soh/Enhancements/randomizer/` (~88k lines, 176 files)

A full OoT-Randomizer implementation + runtime integration. **Two halves:**
- **`3drando/` (the seed generator, vendored, own `LICENSE.md`)** — the offline logic engine:
  `fill.cpp` (placement, 1503 lines), `item_pool.cpp`, `hints.cpp`, `spoiler_log.cpp`,
  `playthrough.cpp`. Produces a spoiler/seed.
- **Runtime integration** — applies a seed to the live game: `randomizer.cpp` (the `Randomizer`
  class, seed load/parse), `logic.cpp` (world logic, 132 KB), `location_access/` (region access
  rules, ~1 MB), data tables (`location_list.cpp` 404 KB, `item_list.cpp`, `settings.cpp`),
  `randomizerEnums/` (552 KB, generated-ish: `RandomizerCheck.h`, `RandomizerGet.h`, `RandomizerInf.h`,
  …), **`hook_handlers.cpp` (3046 lines)** where rando subscribes to GameInteractor hooks and rewires
  item-give/chests/entrances, `RCToRandInf.cpp` (checks↔save-flags), the per-feature `Shuffle*.cpp`
  modules (`ShufflePots`, `ShuffleGrass`, `ShuffleCows`, …), and the trackers
  (`randomizer_check/item/entrance/hint_tracker.cpp`, registered as `GuiWindow`s in `SohGui.cpp`).
  **Plandomizer** (hand-placed seeds), **Fishsanity**.

## Other major editors / features

- **Cosmetics Editor** (`Enhancements/cosmetics/CosmeticsEditor.cpp`), **Audio Editor**
  (`Enhancements/audio/AudioEditor.cpp` + `AudioCollection.cpp`), **debug tools**
  (`Enhancements/debugger/`: Save Editor, Actor Viewer, Collision Viewer, DL Viewer, **Hook Debugger**
  `hookDebugger.cpp` — inspects live GameInteractor registrations), **Gameplay Stats / Time Splits**,
  **Presets** (`Presets.cpp` — bundles of CVar values), **TTS/speech**, **Boss Rush**.
- **Network consumers** (`soh/soh/Network/`): **CrowdControl** (applies `GameInteractionEffect`s from
  an external channel), **Anchor** (co-op/multiplayer sync, own `HookHandlers.cpp`), **Sail**
  (external scripting/automation) — all pure consumers of GameInteractor.
- **Enhancement buckets** under `Enhancements/`: `Cheats/`, `Fixes/`, `QoL/`, `TimeSavers/`,
  `Restorations/`, `Difficulty/`, `ExtraModes/`, `Minigames/`, `Graphics/`, `Items/`, `camera/`,
  `controls/`.

## Newcomer trip-hazards

- **Menu ↔ behavior coupled only by a CVar string** — no direct call from checkbox to hook. The chain
  is widget → CVar → `ShipInit::Init` → `RegisterShipInitFunc` → `COND_HOOK`. Break any leg and the
  toggle silently no-ops.
- **`OnVanillaBehavior`/`VB_*` is the override mechanism, not observer hooks** — to *change* behavior
  you flip the `bool` inside a `GameInteractor_Should(VB_…)` site. The 421 flags (`GIVanillaBehavior.h`)
  are the real API; their `result`/`args` contract lives only in comments.
- **`DEFINE_HOOK` X-macro double-inclusion** — the hook table expands differently per include site.
- **Hooks are deferred-unregister and must be idempotent; order isn't guaranteed.**
- **`3drando/` is a vendored external project** — the generator half, distinct from the runtime half;
  `randomizerEnums/` + the big tables are effectively generated data, don't hand-edit blindly.
- **Two "hook" systems coexist** — GameInteractor (SoH game-behavior) vs. libultraship's window/gui
  registration (`Ship::Menu`/`GuiWindow`). They meet only at `SohGui.cpp`.
