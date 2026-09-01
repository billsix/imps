# Reference: Frame interpolation (30 Hz logic → smooth high-FPS render)

> **Provenance:** authored 2026-06/07 against Ghostship around base `67e561c6` — the imps
> pin (`49c5312a`, GitHub develop tip 2026-09-01) is 120+ commits newer and includes a
> restructure of the hook layer (`src/port/hooks/` became `src/port/events/`, with an
> expanded event list and an EVENTS.md). Claims about hooks, file paths under port/, and
> the maintainer's fork/branches are suspect — verify against the pinned checkout.

*Standing reference, high detail. How Ghostship decouples SM64's fixed 30 Hz game tick from
render framerate by drawing interpolated in-between frames at 60/120/144/…360 FPS. Read
before touching anything under `src/port/interpolation/`, `ProcessGfxCommands`, the matrix
pools, or `math_util.c`'s matrix builders. Companions:
[libultraship-integration.md](libultraship-integration.md) (the consumption hook in Fast3D),
[port-layer.md](port-layer.md), [architecture-overview.md](architecture-overview.md).*

## TL;DR

The decomp still runs at **30 Hz**. Each tick it walks the geometry graph **once**, building
**one N64 display list** plus a set of fixed-point matrices. Ghostship instruments that walk
so each matrix is **recorded** as a full float `MtxF` into a tree keyed by identity, keeping
**this tick's** tree and the **previous tick's** tree. To render faster, `ProcessGfxCommands`
replays the *same* display list several times per tick, each time handing the LUS Fast3D
interpreter a `map<Mtx*, MtxF>` of matrices **element-wise lerped** between the two trees at a
different factor `t ∈ (0,1]`. When the interpreter hits a `gSPMatrix` whose destination
address is in the map, it substitutes the interpolated matrix. **Motion is interpolated purely
at the matrix level; the game never ticks faster; audio is tied to the tick, not the render.**

Files: `src/port/interpolation/FrameInterpolation.{h,cpp}` (the engine),
`src/port/Engine.cpp` (`ProcessGfxCommands`/`RunCommands`/`GetInterpolationFPS`),
`src/port/Game.cpp` (frame pump), `src/port/Matrix.cpp` (matrix pools),
`src/engine/math_util.c` + `src/game/rendering_graph_node.c`/`hud.c`/`ingame_menu.c`/
`mario_misc.c`/`game_init.c` (recording call sites). Consumed in LUS (`src/fast/interpreter.cpp`,
`Fast3dWindow.cpp`, `gfx_sdl2.cpp` — see libultraship's `tasks/reference/fast3d-renderer.md`; the
LUS anchors below are pinned to submodule commit `e0c1b1fc`).

## 1. What ticks vs. what renders

One game step = one `thread5_iteration()` (`game_init.c:678`), driven once per main-loop pass
from `push_frame()` (`Game.cpp:22`, loop `:39-41`). Inside the tick, `display_and_vsync()` →
`exec_display_list()` → `GameEngine::ProcessGfxCommands()` (`Game.cpp:18-20`). So **one game
tick == one display-list build == one `ProcessGfxCommands` call**, and that call emits **N
rendered frames**.

Recording brackets wrap the graph walk: `FrameInterpolation_StartRecord()` (`game_init.c:691`)
… `FrameInterpolation_StopRecord()` (`:724`). Between them, every matrix converted to N64
fixed-point is captured as a full `MtxF` plus a tree "path" identifying it.

**What is actually interpolated:** the header (`FrameInterpolation.cpp:17-47`) documents two
designs — interpolate transform *inputs* (pos/angle/scale) vs. interpolate *final matrices* —
and says only the second is used. In this build that's even truer: the only recorder with live
callers that produces renderer-visible output is **`MatrixMtxFToMtx`**. So concretely, **every
fixed-point matrix is element-wise lerped between last tick and this tick.** That covers object
world transforms, camera/view, shadows, HUD/text matrices, billboards, animated parts —
anything through `mtxf_to_mtx`/`guMtxF2L`. **Not interpolated:** texture coordinates; positions/
angles/scale as such (they're baked into the matrices and interpolated in matrix space). An
ortho-projection recorder and an actor-rotation-decompose mitigation exist but are **dead code**
here (§5, §7).

## 2. Data model

**Identity tree** (`FrameInterpolation.cpp:257-272`):
```cpp
struct Path {
    map<label, vector<Path>> children;   // nested OPEN/CLOSE_CHILD scopes
    map<Op, vector<Data>>    ops;        // recorded ops, bucketed by Op
    vector<pair<Op,size_t>>  items;      // ordered replay list
};
struct Recording { Path root_path; };
```
- `label = pair<const void*, uintptr_t>` (`:86`) — usually a **call-site string literal + a
  pointer/tag** identifying the object.
- Two full trees kept: `current_recording` and `previous_recording` (`:271-272`); `current_path`
  (`:268`) is the stack of open `Path*`.
- **Cross-frame identity:** the walk is instrumented with matched
  `FrameInterpolation_RecordOpenChild(name, tag)` / `RecordCloseChild()` (`:701-720`) mirroring
  the geo-node recursion. Keys are `(name, tag)` — e.g. `TAG_OBJECT(node)`
  (`rendering_graph_node.c:367`), `TAG_LETTER(strChar)` (`ingame_menu.c:1215`), plus item/smoke/
  cloud/thwomp/minimap/portrait tags (`FrameInterpolation.h:16-25`, bit-masked so classes can't
  collide). Because the tree shape and per-op ordinal are reproduced identically each tick (same
  objects, same render order), the interpolator pairs "op *i* in child (name,tag) last tick"
  with "the same op *i* in the same child this tick."
- **Per-matrix key:** the output map is `unordered_map<Mtx*, MtxF> mtx_replacements` (`:292`),
  keyed by the **destination `Mtx*` pointer**. The interpreter looks up `gSPMatrix`'s address in
  it (`interpreter.cpp:1068`). Matrices live in stable, per-frame-reused pools (`Matrix.cpp:10-24`,
  `gMatrix.Objects` deque), so the same address holds the same logical matrix across ticks — the
  reason the key works, and the thing you must not break (§7).

**Recording API** — every recorder early-returns unless `check_if_recording()` (`:676`) is true.
Live recorders:

| Recorder | Op | Live call site |
|---|---|---|
| `RecordMatrixMtxFToMtx(src,dest)` | `MatrixMtxFToMtx` | `math_util.c:588` (`mtxf_to_mtx`), `Matrix.cpp:31` (`AddMatrix`), `:79` (`AddTextMatrix`) — **the workhorse** |
| `RecordOpenChild`/`RecordCloseChild` | tree structure | `rendering_graph_node.c`, `hud.c`, `ingame_menu.c`, `mario_misc.c` |
| `Record_SetTextMatrix` | `SetTextMatrix` | `Matrix.cpp:54` |
| `RecordMatrixTranslate` | `MatrixTranslate` | `math_util.c:188` |
| `RecordMatrixPosRotZXY` | `MatrixPosRotXYZ` | `math_util.c:280` |
| `RecordMatrixRotateXYCoords` | `MatrixRotateXYCoords` | `math_util.c:603` |

`RecordMatrixMtxFToMtx` stores a **copy of the whole source `MtxF`** + the `dest` pointer
(`:906-911`); it does **not** read the running matrix stack, so interpolating this op is a pure
element-wise lerp of the two stored `MtxF`s, independent of replayed stack state.

## 3. The render loop — replay the display list N times

`GameEngine::ProcessGfxCommands` (`Engine.cpp:1000-1037`):
```cpp
std::vector<std::unordered_map<Mtx*, MtxF>> mtx_replacements;
int target_fps = GetInterpolationFPS();
static int last_fps, time;
int fps = target_fps;
int original_fps = 60 / 2;                    // == 30, the game tick rate
if (target_fps == 30 || original_fps > target_fps) fps = original_fps;
if (last_fps != fps) time = 0;

int next_original_frame = fps;
while (time + original_fps <= next_original_frame) {
    time += original_fps;
    if (time != next_original_frame)
        mtx_replacements.push_back(FrameInterpolation_Interpolate((float)time / next_original_frame));
    else
        mtx_replacements.emplace_back();      // exact keyframe: empty map => no substitution
}
time -= fps;                                  // carry the fraction to next tick
if (wnd) { wnd->SetTargetFps(GetInterpolationFPS()); wnd->SetMaximumFrameLatency(1); }
RunCommands(commands, mtx_replacements);
last_fps = fps;
```
- **N = `mtx_replacements.size()` ≈ target_fps / 30.** The `time`/`next_original_frame`
  accumulator is a Bresenham-style distributor so non-integer ratios average out. `time -= fps`
  carries the leftover between ticks; `last_fps != fps` resets it on an FPS change.
  - **60 fps:** `t=0.5`, then keyframe. N=2.
  - **90 fps:** `t=1/3, 2/3`, then keyframe. N=3.
  - **144 fps:** `t=30/144 … 120/144`, no exact keyframe; N alternates 4/5, averaging 4.8.
- **Exact keyframe pushes an empty map** (`:1024`) → interpreter substitutes nothing → the raw
  fixed-point matrices render verbatim (the true, un-interpolated frame).

**RunCommands** (`Engine.cpp:974-998`) does the replay:
```cpp
interpreter->mInterpolationIndex = 0;
for (const auto& mtxStack : mtx_replacements) {
    wnd->DrawAndRunGraphicsCommands(Commands, mtxStack);   // SAME Commands every time
    interpreter->mInterpolationIndex++;
}
```
`mInterpolationIndex` also selects per-sub-frame segment pointers via `G_MW_SEGMENT_INTERP`
(`interpreter.cpp:1893-1923`) — a display list can carry alternate segment addresses per index.

**LUS consumption** — `Interpreter::Run` stores `mCurMtxReplacements = &mtx_replacements`
(`interpreter.cpp:4350`); `Interpreter::GfxSpMatrix` (`:1065`):
```cpp
if (auto it = mCurMtxReplacements->find((Mtx*)addr); it != mCurMtxReplacements->end()) {
    // use it->second.mf[i][j], re-quantized *65536/65536 to match N64 fixed-point rounding
} else {
    // decode the fixed-point matrix baked in the display list
}
```

## 4. The interpolation factor

`FrameInterpolation_Interpolate(step)` (`:661-667`) builds an `InterpolateCtx` with `step = t`
and `w = 1 - step`, then `interpolate_branch(previous, current)` and returns the map.

- **Matrix lerp** — `interpolate_mtxf` (`:304-310`): `res->mf[i][j] = w*old + step*new`
  (straight element-wise). Applied for the workhorse op (`interpolate_branch` `:567-570`), written
  under the current-frame destination pointer via `new_replacement(dest)` (`:300-302`).
- **Scalar lerp** — `lerp` (`:319`), `lerp_s16/s32` (`:323-329`).
- **Angle interpolation (shortest-arc, NOT slerp).** Two overloads:
  - float radians (`:343-365`): wrap both to `[0,2π)`, add 2π to the smaller if `|o-n|>π`, plain
    lerp.
  - s16 binary angle (`:367-392`): work in `u16`, pick the ±0x10000 wrap minimizing the diff,
    **and snap to the new value if the delta exceeds a quarter-turn (0x4000)** — the rotation
    discontinuity guard. No quaternion path.
- **Nuance:** the recorded pos/rot/translate ops (`MatrixTranslate` `:451`, `MatrixPosRotXYZ/ZXY`
  `:482-517`, `MatrixRotateXYCoords` `:542`) only mutate a running `gInterpolationMatrix` during
  replay; the one op that reads it back (`MatrixToMtx`) has **no live callers**, so that path is
  inert. **Net effect: element-wise MtxF lerp keyed by `Mtx*`, full stop.**

## 5. Special cases / opt-outs (avoiding smear across discontinuities)

- **Per-region toggle** — `FrameInterpolation_ShouldInterpolateFrame(bool)` (`:671-674`) sets
  `camera_interpolation`/`is_recording`. Wrapping a region in `ShouldInterpolateFrame(false) …
  (true)` makes `check_if_recording()` false there → that region renders from the raw display
  list. Live uses: **Goddard/Mario head** (file-select 3D head, its own renderer —
  `mario_misc.c:91,103`) and **dialog text** (interpolate only while scrolling,
  `ingame_menu.c:1596`, reset `:1617`).
- **`StartRecord` self-heal** (`:680-694`): rotates `current→previous`, clears `current`; if
  `camera_interpolation` was left false it defaults back to true and disables recording for
  *this* frame — so a flagged discontinuity suppresses interpolation for one frame and recovers
  next frame. Recording only arms when `GetInterpolationFPS() != 30`.
- **Structural discontinuity** — `interpolate_branch` (`:406-420`): a child key present this
  frame but **not** last frame (newly spawned object, teleport that changed the tag) recurses
  new-vs-new (`:415-417`) → exact new matrix, no smear. Extra ops this frame are skipped, not
  paired with garbage (`if (item.second < it->second.size())`, `:423`).
- **Ortho jitter threshold** (`:460-471`): skip if all ortho params differ by < 2.0 (recorder
  currently dead, logic present).
- **Camera-cut epoch** — `DontInterpolateCamera()` / `GetCameraEpoch()` (`:722-728`) exist but
  have **zero callers**; camera cuts rely on `ShouldInterpolateFrame(false)` + the guards above.

## 6. FPS numbers & audio sync

- **Game FPS = 30**, hard-coded `original_fps = 60/2` (`Engine.cpp:1008`). (N64 "60" is the
  vsync field rate; the SM64 sim advances at 30.)
- **Display/target FPS** — `GetInterpolationFPS()` (`Engine.cpp:838-847`):
  1. CVar `gSettings.MatchRefreshRate` set → actual monitor Hz (`GetCurrentRefreshRate`,
     `Fast3dWindow.cpp:282`).
  2. Else if Vsync on (`CVAR_VSYNC_ENABLED`, default 1) → `min(refreshRate,
     gSettings.InterpolationFPS)`.
  3. Else → `gSettings.InterpolationFPS` (default 30).
  User controls: the **"Current FPS" slider** (`GhostshipMenuSettings.cpp:230-248`,
  `CVAR_SETTING("InterpolationFPS")`, **Min 30 / Max 360**, 30 shown as "Original (30)") and the
  **"Match Refresh Rate"** checkbox (`:249-252`). When target == 30, `check_if_recording()` is
  false and the whole path is bypassed (single 1:1 draw).
  - **Note:** `SetTargetFps(60)` at `Engine.cpp:278-280` is one-time init, **not** the
    interpolation target — the live target is recomputed every frame and re-applied at `:1031`.
- **Audio stays in sync because it's tied to the game tick, not the render count.** Audio is
  produced once per `push_frame()`: `StartAudioFrame()`/`EndAudioFrame()` bracket
  `thread5_iteration()` (`Game.cpp:22-27`), `audio_game_loop_tick()` runs once inside the tick
  (`game_init.c:703`), and the audio thread (`Engine.cpp:851-883`) makes one tick's worth of
  samples per iteration. The N interpolated renders do **not** re-run audio. Pacing keeps it
  honest: each of the N `SwapBuffers` is throttled to `target_fps` by `SyncFramerateWithTime`
  (`gfx_sdl2.cpp:644`, interval `1e6/mTargetFps` µs), so N renders take `N/target ≈ 1/30 s`
  → `push_frame` (and thus the tick + its audio) runs at 30 Hz regardless of display FPS.
  `SetMaximumFrameLatency(1)` (`Engine.cpp:1032`) keeps latency down.

## 7. Gotchas

- **Never stash an `Mtx*` across frames.** Identity is the destination pointer
  (`interpreter.cpp:1068`). The pools (`Matrix.cpp:10-24`, cleared each frame `:263-272`) reuse
  the same slot for the same logical matrix — that's what makes pairing work. Caching a matrix
  pointer and reusing it out of order, or growing/reordering the pool, breaks old↔new pairing →
  smearing or wrong-object interpolation. (The pool-clear comment `Matrix.cpp:259-262` explicitly
  worries the game doesn't clear all of these each frame.)
- **HUD/text is only partly interpolated** — HUD elements sit in their own `OpenChild` scopes
  keyed by *value* (`hud.c:414-476`) so counters snap rather than lerp through digits; dialog
  text interpolates only while scrolling.
- **First frame / cold start:** `previous_recording` is empty, so every child key misses and
  `interpolate_branch` recurses new-vs-new → exact matrices, no garbage. Same on an FPS change
  (`last_fps != fps` resets the accumulator, `Engine.cpp:1014`).
- **Angle snap:** rotations exceeding a quarter turn between ticks snap to the new value
  (`:375-376,386-387`) — deliberate anti-paper-flip, at the cost of a momentary non-smooth step
  on very fast spins.
- **Don't be misled by dead code.** The "interpolate inputs" approach and the actor
  rotation-decompose mitigation are present but inactive — `RecordActorPosRotMatrix`,
  `RecordMatrixToMtx`, `RecordMatrixReplaceRotation`, `RecordOrtho`, `RecordMatrixScale`,
  `RecordSkinMatrixMtxFToMtx`, etc. have **0 live callers** (several sites commented out with
  "`// TODO: FrameInterpolation is broken, fix it`", e.g. `math_util.c:314-315`, `Matrix.cpp:92`).
  The effective algorithm is **just element-wise MtxF lerp keyed by `Mtx*`.**
- **Cost:** per tick you build N `unordered_map<Mtx*,MtxF>` (one per sub-frame) by walking the op
  tree, and replay the whole display list N times through the software command interpreter; two
  full op trees are retained. CPU ≈ linear in target FPS.

## Open threads (not fully pinned down)
- Whether `GetActiveWindowRefreshRate` rounds to integer Hz (affects 143.9-type displays).
- Whether any Ghostship code *produces* distinct per-index `G_MW_SEGMENT_INTERP` segment
  addresses, or whether that path is a carryover consumed but never emitted here.

*The interpolation engine lives entirely in `src/port/` (Ghostship). libultraship only provides
the consumption hook (`interpreter.cpp:1065-1068`, `4344-4350`; `Fast3dWindow.cpp:185`) and
the frame pacer (`gfx_sdl2.cpp:644`).*
