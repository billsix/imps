# libultraship — architecture overview

> **Pinned:** libultraship **1.3.1-482**
> (`2917d0f4fe62c579174561dcd34f327c9410bb72`, 2026-07-29 —
> BanjoKazooie's submodule pin; a direct descendant of iteration 15's
> 1.3.1-397, 85 commits later). Updated 2026-09-01 as iteration 16 of
> the reference crawl (`../../libultraship-reference-docs.md`).
> Re-sync check: compare `PIN_SHA` in `libultraship/fetch.sh` with the
> SHA above — if they differ, the crawl has advanced (each iteration is
> a separate imps commit; `git log` on this file is the time axis).
>
> **Version-number trap:** the 1.3.1-XXX describe-counts on this line
> run ~2 years past tag `1.4.2` (2024-08), which is a different, older
> release line. Do not order these docs' history by version string.

**What LUS is at this pin:** a static C++20 library (`libultraship.a`)
that gives an N64 decompilation "somewhere to run" — a Fast3D
display-list interpreter with per-microcode dispatch and Prism-templated
shaders (custom shaders now live via a push/pop stack), a zip-based
(`.o2r`) archive + typed resource system with an optional
manifest/signing trust chain, SDL audio/input, an ImGui overlay shell
(now renderer-agnostic with a `Fast::Fast3dGui` subclass), JSON config +
CVars, spdlog logging, thick libultra shims, **an event system**, and
**opt-in TCC-based scripting with a keystore**. A gtest suite exists
behind `LUS_BUILD_TESTS`. Still `add_subdirectory`-only (no
install/export, no version constant) — but the target now exports
symbols for dynamic loading.

## The three trees, three namespaces

Unchanged in shape (headers under `include/`, one static target):

| Tree | Namespace | Contents |
|---|---|---|
| `include/ship/` + `src/ship/` (229 files) | `Ship::` | engine: `Context`, `resource/`, `config/`, `debug/`, `window/`(+gui), `controller/`, `audio/`, `utils/`, **`events/`** (new), **`scripting/`** + **`security/`** (new, scripting-gated) |
| `include/fast/` + `src/fast/` (62) | `Fast::` | Fast3D: `interpreter.cpp`, `Fast3dWindow`, **`Fast3dGui`** (new), `backends/`, resources, `shaders/` |
| `include/libultraship/` + `src/libultraship/` (74) | `LUS::` | N64 layer: libultra shims, C `bridge/`, `LUS::ControlDeck`/`Controller`, **`InputEditorWindow` + `GfxDebuggerWindow`** (moved here from ship) |

**The cross-layer cleanup (#1097) made the split real**: zero
`#include "fast/..."` anywhere under ship (grep-verified). LUS-specific
GUI windows moved to the `libultraship/` tree, and `classes.h` dropped
`InputEditorWindow.h` from its re-exports.

## `Ship::Context` — no longer a weak_ptr singleton (#1103)

**The biggest consumer-facing break in this range.** Storage is
`static std::unique_ptr<Context>` (`src/ship/Context.cpp:33`);
`CreateInstance`/`CreateUninitializedInstance` **return raw
`Context*`** (`include/ship/Context.h:52-54`); access is
**`GetRawInstance()`**, teardown is **`DestroyInstance()`**
(`Context.cpp:39-41`). `GetInstance()` does not exist — a 397-era port
holding the returned `shared_ptr` no longer compiles. (The doxygen at
`Context.h:36` still says "use GetInstance()" — stale upstream doc.)

The `CreateInstance` signature (archivePaths/validHashes/audioSettings/
window/controlDeck injection points) is otherwise as at 397 — `InitWindow`/
`InitControlDeck` still fail on null (`Context.cpp:333-348`, `:262-271`).

**Init chain** (`Context.cpp:110-118`): logging → config → cvars →
resource manager → control deck → crash handler → console → window →
audio → **event system** → file-drop mgr → *(scripting builds)*
**script loader**. `InitGfxDebugger` left Context — the GfxDebugger now
lives in `Fast::Fast3dWindow` (`Fast3dWindow.cpp:104-105`).
`InitKeystore()` is called from inside `InitResourceManager` (`:231`).
**SDL game-controller startup moved from `osContInit` into
`InitControlDeck`** (`:277-289`) — controllers work in pre-game UI, and
failure is a non-fatal `SPDLOG_WARN` (the old `exit(EXIT_FAILURE)` is
gone).

- Missing archive still fatal (messagebox → `Init` false →
  `CreateInstance` returns nullptr, `Context.cpp:248-257`);
  `allowEmptyPaths` opt-out survives.
- **The destructor null-deref survives and is MORE reachable**:
  `~Context` calls `GetWindow()->SaveWindowToConfig()` unguarded
  (`Context.cpp:45`), and a failed `CreateInstance` leaves the
  half-initialized singleton in `mContext` (the failure branch returns
  nullptr without resetting it, `:76-84`), so the process-exit
  destructor runs against it.
- Logging teardown reworked: no `spdlog::shutdown()`; explicit member
  teardown, then `mLogger->flush()` (an unconditional deref — a Context
  destroyed before `InitLogging` crashes) and the release-build
  Context-owned log thread pool released last (`:64-70`).

## New subsystems

- **Event system (#1047)** — `Ship::EventSystem`
  (`include/ship/events/EventSystem.h:57-128`): `RegisterEvent(name)` →
  int32 id, `RegisterListener(id, cb, priority, file, line)`,
  synchronous `CallEvent` in priority order. C-compatible structs +
  macro surface in `EventTypes.h` (`DEFINE_EVENT`, `REGISTER_EVENT`,
  `CALL_EVENT`, `CALL_CANCELLABLE_EVENT`, …); **the macros dispatch
  through the C bridge**, so C and C++ share one path. Cancellation is
  caller-enforced. Diagnostics `Callers` map is debug-only (#1131).
  **LUS itself defines and fires zero events at this pin** — pure
  port-facing infrastructure; `CoreEvents.h` is an empty include, and
  the shipped `EventDebuggerWindow` is referenced nowhere (the port
  must `AddGuiWindow` it).
- **Scripting (#1068/#1084, `ENABLE_SCRIPTING`, default OFF)** —
  `Ship::ScriptLoader`: compiles C sources found in mounted archives
  with TinyCC, loads them, `GetFunction(module, function)`; `SafeLevel`
  enum keyed to the `gScriptSafeLevel` CVar (macro defined, **unused at
  this pin**). `LibraryLoader`: temp-file dlopen/LoadLibrary, runtime
  option `DISABLE_DLL_LOADER`.
- **Keystore + signed archives (#1095, scripting-gated)** —
  `Ship::Keystore` (named ed25519 keys, origins User/Game/System);
  archive `manifest.json` carries checksum/signature/public_key,
  verified BLAKE2b + ed25519 via monocypher; unknown keys go through an
  `UntrustedArchiveHandler` callback. Keys persist **inside the config
  JSON** under a top-level `"Keystore"` node. See `resource-system.md`.

## The integration pattern at this pin

As at 397 (construct `Fast::Fast3dWindow` + `LUS::ControlDeck`, inject
via `CreateInstance`, register the `Fast::` resource factories yourself,
loop on `WindowIsRunning()` + `DrawAndRunGraphicsCommands`) — with the
lifecycle changes: hold the raw `Context*`, call `DestroyInstance()` to
tear down, and note the port is now expected to write
`mInterpolationIndex`/`mInterpolationT` for frame interpolation
(`fast3d-renderer.md`).

## What does NOT exist at this pin (verified absences)

- No thread shims; no Vulkan; D3D12/GLX/Switch/WiiU still deleted.
- ~~No events bus, no scripting, no keystore, no tests~~ — **all four
  arrived in this range** (above). The remaining absences: no
  install/export, no version constant, no Component/Tickable framework
  (Context members are still plain fields).
- Platform matrix grew: Windows, Darwin, iOS, Linux, Android, **OpenBSD
  (new, #971)**.

## Sibling docs

`build-system.md` · `resource-system.md` · `fast3d-renderer.md` ·
`windowing-gui-input.md` · `audio-and-libultra-shims.md` ·
`config-cvars-logging.md` · `bridge-api.md`
