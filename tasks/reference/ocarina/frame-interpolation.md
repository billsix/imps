# Reference: Frame interpolation (fixed logic tick → smooth high-FPS render)

> **Provenance:** authored 2026-07 against Shipwright `988b53665` (9.2.3-320, the old
> fork base) — 101 commits behind the current imps pin `acdbc651d` (9.2.3-421). Spot-check
> details against the pinned checkout before trusting them.

*Standing reference, high detail. How OoT's fixed logic tick is decoupled from render framerate so
SoH draws interpolated in-between frames at up to 360 FPS. This is the **original** implementation;
Mario 64 (Ghostship) derived a pared-down version from it — the comparison is in §8. Read before
touching `soh/soh/frame_interpolation.cpp`, the render loop, or `sys_matrix.c`. Companions:
[libultraship-integration.md](libultraship-integration.md), [port-layer.md](port-layer.md).*

**Version:** SoH's libultraship submodule is `1.3.1-463`; LUS-side anchors below are for that commit.

## TL;DR

One game tick builds the display list once. The render loop replays that **same** display list N
times, each replay handed a `map<Mtx*, MtxF>` of matrices interpolated between last tick and this
tick at factor `t ∈ (0,1]`. The LUS Fast3D interpreter substitutes an interpolated matrix whenever a
`gSPMatrix` destination address is in the map. **The game never ticks faster; audio is tied to the
tick.** Unlike Ghostship, SoH records the *whole matrix stack* and re-executes it with interpolated
inputs, so it interpolates transform inputs (translate/rotate/scale/angles), not only final matrices.

Files: `soh/soh/frame_interpolation.{cpp,h}` (the engine), `soh/soh/OTRGlobals.cpp` (render loop:
`Graph_ProcessGfxCommands` `:1804`, `RunCommands` `:1776`, `GetInterpolationFPS` `:1004`),
`soh/src/code/sys_matrix.c` (the matrix-op **record call sites**), `soh/include/macros.h:206-239`
(`OPEN_DISPS`/`CLOSE_DISPS` auto-record), `soh/src/code/z_view.c:355-478` (camera-cut heuristic),
`libultraship/src/fast/interpreter.cpp` (consumption: `GfxSpMatrix` `:1386`, `Run` `:4978`),
`Fast3dWindow.cpp` (`DrawAndRunGraphicsCommands` `:194`, `SetTargetFps` `:118`).

## 1. The game FPS is variable (not a fixed 20)

`original_fps = 60 / R_UPDATE_RATE` (`OTRGlobals.cpp:1816`), where `R_UPDATE_RATE` is a mutable
register (`SREG(30)`, `regs.h:51`) the game changes by context:
- **3 → 20 fps** — normal gameplay (`game.c:437`, `z_play.c:931/982/1016`).
- **2 → 30 fps** — Kaleido/pause setup (`z_kaleido_setup.c:60`).
- **1 → 60 fps** — pre-NMI, sample play, some transitions.

So OoT's famous "20 fps" is the *gameplay* case; the interpolation denominator tracks
`R_UPDATE_RATE` live and the accumulator resets when it changes (`OTRGlobals.cpp:1823`,
`last_update_rate != R_UPDATE_RATE`). **(Ghostship hard-codes `60/2 = 30` and never varies it.)**

**What is interpolated:** the entire matrix-stack op stream — world transforms, camera/view, actor
model matrices (with a rotation-decompose mitigation), skeleton/limb matrices, shadows, HUD hearts,
effects (sparks, blur, shield particles, soft-sprites), lens flare, rain — anything through
`sys_matrix.c` inside a recorded `OPEN_DISPS` scope. **Not interpolated:** texture coords; anything
drawn while `is_recording` is false; regions the camera-epoch/cut logic excludes.

## 2. Data model

**Op set** (`frame_interpolation.cpp:85-104`): `OpenChild, CloseChild, MatrixPush, MatrixPop,
MatrixPut, MatrixMult, MatrixTranslate, MatrixScale, MatrixRotate1Coord, MatrixRotateZYX,
MatrixTranslateRotateZYX, MatrixSetTranslateRotateYXZ, MatrixMtxFToMtx, MatrixToMtx,
MatrixReplaceRotation, MatrixRotateAxis, SkinMatrixMtxFToMtx`.

**Tree** (`:176-184`):
```cpp
typedef pair<const void*, int> label;          // :106
struct Path {
    map<label, vector<Path>> children;         // nested OpenChild scopes
    map<Op, vector<Data>>    ops;              // recorded ops bucketed by Op
    vector<pair<Op,size_t>>  items;            // ordered replay list
};
```
Two full trees: `current_recording`, `previous_recording` (`:190-191`); `current_path` is the open-
`Path*` stack. `append(op)` (`:198`) pushes an ordered `items` entry + a bucketed `Data`.

**Cross-frame identity** = the `label = (const void*, int)` on each `OpenChild`. **Two schemes
coexist in SoH:**
1. **Call-site identity** — `OPEN_DISPS(gfxCtx)` (`macros.h:206-223`) emits
   `FrameInterpolation_RecordOpenChild(__FILE__, __LINE__)`. Key = `(file-literal-ptr, line)`. Every
   draw function that opens disps gets a stable per-call-site scope for free. **(Ghostship lacks
   this — it relies only on explicit tags.)**
2. **Explicit object tags** — call sites pass a live pointer/index so multiple instances of one call
   site stay distinct: `z_actor.c:461 RecordOpenChild(actor,0)`, `z_lifemeter.c:451 (…,i)`,
   effects keyed by `this`/`elem` + an **epoch** field (`elem->epoch`, so a recycled particle slot
   gets a fresh identity), `z_view.c:405 RecordOpenChild(NULL, GetCameraEpoch())` for the camera.

**Per-matrix output key** = the destination `Mtx*` pointer. `MatrixMtxFToMtx` stores `{*src, dest}`;
the interpolated `MtxF` is written to `mtx_replacements[dest]` (`:403`, via `new_replacement`). The
interpreter looks up `gSPMatrix`'s address in this map (`interpreter.cpp:1389`). Pairing works
because OoT reuses stable per-frame `Mtx` pool slots for the same logical matrix each tick.

**Recording gate:** every `Record*` early-returns unless `is_recording`, which is armed only when
`GetInterpolationFPS() != 20` (`:457`).

## 3. Render loop — replay N times

Recording brackets are in the decomp: `FrameInterpolation_StartRecord()` … `Play_Draw()` …
`StopRecord()` at **`z_play.c:1711-1713`** (gameplay) and **`z_file_choose.c:2871-2873`** (file
select — a second live bracket Ghostship lacks).

`Graph_ProcessGfxCommands` (`OTRGlobals.cpp:1811-1851`) is the Bresenham-style distributor:
```cpp
int target_fps   = GetInterpolationFPS();
int original_fps = 60 / R_UPDATE_RATE;                 // 20 / 30 / 60
int fps = target_fps;
if (target_fps == 20 || original_fps > target_fps) fps = original_fps;               // :1819
if (last_fps != fps || last_update_rate != R_UPDATE_RATE) time = 0;                  // :1823 reset
int next_original_frame = fps, start_time = time, count = 0;
while (time + original_fps <= next_original_frame) { time += original_fps; count++; }// :1832
time -= fps;                                            // carry fraction to next tick :1837
wnd->SetTargetFps(fps);                                 // :1840 frame pacer
RunCommands(commands, start_time, step=original_fps, next_original_frame, count);    // :1851
```
`count = N ≈ target_fps / original_fps`. SoH **splits** the accumulator (here) from the replay
(`RunCommands`); Ghostship inlines both. A `GfxDebuggerIsDebugging()` path renders only the final
keyframe (`:1845`).

`RunCommands` (`OTRGlobals.cpp:1776`):
```cpp
intp->mInterpolationIndex = 0;
for (int i = 0; i < count; i++) {
    time += step;
    auto mtx = (time == denom) ? {} : FrameInterpolation_Interpolate((float)time / denom);  // :1794
    wnd->DrawAndRunGraphicsCommands(Commands, mtx);    // SAME Commands each pass :1797
    intp->mInterpolationIndex++;
}
```
**Exact keyframe (`time == denom`) pushes an empty map** → interpreter substitutes nothing → raw
fixed-point matrices render verbatim. `mInterpolationIndex` also selects per-sub-frame segment
addresses via `G_MW_SEGMENT_INTERP` (`interpreter.cpp:2288/2314`).
- 20→60: `t=1/3, 2/3`, keyframe → N=3. 20→30: `t=1/2`, keyframe; the carried fraction makes N
  alternate to average 1.5.

## 4. The interpolation factor & how it's applied

`FrameInterpolation_Interpolate(step)` (`:444`) builds an `InterpolateCtx` with `step`, `w=1-step`,
then `interpolate_branch(previous, current)` (`:295`) walks the new tree's ordered `items`, finds
the positionally-matching op in the old path, and dispatches by `Op`. **Two output paths:**

- **Direct matrix lerp** — `MatrixMtxFToMtx` (`:402`): `mtx_replacements[dest] = w*old + step*new`
  element-wise (`interpolate_mtxf` `:217`). *This is Ghostship's only live path.*
- **Stack replay (the "interpolate inputs" path — LIVE in SoH, dead in Ghostship)** — SoH
  re-executes the matrix stack with interpolated inputs by calling the **real** `Matrix_*` functions:
  `MatrixPush/Pop` (`:320`), `MatrixMult` (interpolated `MtxF`, `:333`), `MatrixTranslate` (lerped
  x/y/z, `:338`), `MatrixScale` (`:345`), the rotate ops (interpolated **angles**, `:351-431`). Then
  `MatrixToMtx` (`:407`) reads the reconstructed stack into `mtx_replacements[dest]`. Live because
  `sys_matrix.c` records every op.

**Angle handling** (`interpolate_angle`):
- float radians (`:235`): wrap to `[0,2π)`, add 2π to the smaller side if `|o-n|>π`, plain lerp. The
  quarter-turn snap is **commented out here** (`:253-255`).
- s16 binary angle (`:259`): work in `u16`, pick the ±0x10000 wrap minimizing the diff, and **snap to
  the new value if `|diff| > 0x4000`** (`:267,278`) — the active quarter-turn discontinuity guard.

**Actor "paper-flip" mitigation — LIVE in SoH (dead in Ghostship).** `z_actor.c:2764` calls
`FrameInterpolation_RecordActorPosRotMatrix()` before the actor's `Matrix_SetTranslateRotateYXZ`.
That sets `next_is_actor_pos_rot_matrix`; the next `RecordMatrixSetTranslateRotateYXZ` inverts the
current matrix into `inv_actor_mtx`; subsequent `RecordMatrixToMtx` pre-multiplies by it to store the
limb matrix in **model space** (`:575-585`). At interpolation time, `MatrixSetTranslateRotateYXZ`
rebuilds `actor_mtx` from lerped **angles**, and `MatrixToMtx` does
`SkinMatrix_MtxFMtxFMult(&actor_mtx, model_space, dest)` (`:409`) — so rotation is interpolated as an
angle, not by lerping world-space matrix rows (which flattens the model through 180°).

## 5. Opt-outs / discontinuities

SoH has **no `ShouldInterpolateFrame`** (Ghostship's per-region bool). Instead:
1. **Camera-cut epoch — actively used in SoH (zero callers in Ghostship).**
   `FrameInterpolation_DontInterpolateCamera()` (`:486`) bumps `camera_epoch`; `StopRecord` latches
   it. The camera scope opens with key `(NULL, GetCameraEpoch())` (`z_view.c:405`), so after a cut
   the key differs from last tick → `interpolate_branch` misses → recurses **new-vs-new** → exact new
   matrices, no smear. Driven by a per-frame camera-motion heuristic (`z_view.c:359-398`: trips on
   large eye/lookAt/up jumps) plus explicit cuts (`z_camera.c:6880,8195`).
2. **Structural discontinuity** — a child key present this frame but absent last frame (new actor,
   recycled particle whose `epoch` bumped) recurses new-vs-new (`:305`); extra ops are skipped
   (`item.second < it->second.size()`, `:312`).
3. **Recording gate / self-heal** — `StartRecord` (`:452`) rotates `current→previous`, clears
   `current`, arms `is_recording` only when target != 20. At 20 fps the loop degenerates to one 1:1
   draw.
4. **First frame / FPS change** — `previous_recording` empty → all misses → new-vs-new; the
   accumulator resets.

## 6. FPS sources & audio sync

`GetInterpolationFPS()` (`OTRGlobals.cpp:1004`): (1) CVar `gSettings.MatchRefreshRate` → monitor Hz;
(2) else if vsync on → `min(refreshRate, InterpolationFPS)`; (3) else → `gSettings.InterpolationFPS`
(**default 20**). User control: the "Current FPS" slider (`SohMenuSettings.cpp:379`,
`CVAR_SETTING("InterpolationFPS")`, **Min 20 / Max 360**, 20 shown as "Original (20)") + "Match
Refresh Rate". At target 20, `is_recording` never arms → path bypassed.

**Audio is tied to the tick, not the render count.** `OTRAudio_Thread` (`OTRGlobals.cpp:1022`)
generates `AUDIO_FRAMES_PER_UPDATE = R_UPDATE_RATE` buffers per update, sized to average
`32000/60 = 533.33` samples/update to avoid tempo drift; the gfx thread wakes it once per tick
(`audio.processing=true` + `notify_one`, `:1806`), with a 5 ms self-pump fallback (`:1062`). The N
renders don't re-run audio. Pacing holds the tick at true rate via `SetTargetFps(fps)` → the window
backend; dropped frames skipped via `IsFrameReady()`.

## 7. LUS consumption hook (1.3.1-463)

- `Interpreter::Run` (`interpreter.cpp:4978`) stores `mCurMtxReplacements = &mtx_replacements`.
- `Interpreter::GfxSpMatrix` (`:1386-1441`): before decoding the fixed-point matrix, looks up the
  `Mtx*` in the map (`:1389`); on a hit uses the port's `MtxF`, re-quantized through 16.16 fixed
  point (`:1392-1394`).
- `Fast3dWindow::DrawAndRunGraphicsCommands` (`:194`): `IsFrameReady()` drop check → `gui->StartDraw`
  → `Run(commands, mtxReplacements)` (`:210`) → `gui->EndDraw`.

## 8. SoH vs. Ghostship — comparison

**Same shared mechanism:** record a tree of matrix ops per tick keyed by identity; keep this-tick +
last-tick trees; replay the *same* display list N times with a `map<Mtx*, MtxF>` of lerped matrices;
substitute at `gSPMatrix` in the LUS interpreter; empty map on the exact keyframe; Bresenham
distributor with a carried fraction; element-wise `MtxF` lerp; shortest-arc s16 angle interp with
quarter-turn snap; `mInterpolationIndex` drives `G_MW_SEGMENT_INTERP`; audio tied to tick;
`SetTargetFps` pacer.

**Different — SoH is the fuller original; Ghostship pared it down:**
1. **Game FPS.** SoH `60/R_UPDATE_RATE`, **varies 20/30/60**, resets the accumulator on change.
   Ghostship hard-codes **30**.
2. **Recorded ops.** SoH records the **entire matrix stack** (`sys_matrix.c`) → both the
   "interpolate inputs" stack-replay path **and** the direct-matrix path are active. In Ghostship the
   stack-replay ops are **dead code**; only `MatrixMtxFToMtx` is live.
3. **Actor rotation-decompose mitigation** — LIVE in SoH (`z_actor.c:2764`,
   `frame_interpolation.cpp:409,554-585`); **dead in Ghostship**.
4. **Camera cuts** — SoH's `DontInterpolateCamera`/`GetCameraEpoch` is **actively driven** by a
   camera-motion heuristic + explicit cut sites. In Ghostship these have **zero callers**.
5. **Region opt-out** — SoH uses epoch + structural miss + the FPS gate; Ghostship added
   `ShouldInterpolateFrame` (Goddard head / dialog text).
6. **Child identity** — SoH auto-tags every `OPEN_DISPS` scope by `(__FILE__, __LINE__)` on top of
   explicit tags; Ghostship relies on explicit `TAG_*` macros only.
7. **Second live bracket** — SoH also records the file-select screen (`z_file_choose.c:2871`).
8. **Loop factoring** — SoH splits accumulator (`Graph_ProcessGfxCommands`) from replay
   (`RunCommands`) + a debugger keyframe-only path; Ghostship inlines the loop.

## Open threads
- **`mInterpolationT`** (`OTRGlobals.cpp:1796`) is written every sub-frame but **not read anywhere in
  the LUS 463 build** — only `mInterpolationIndex` is consumed. Appears reserved/informational here.
- No SoH producer emitting distinct per-index `G_MW_SEGMENT_INTERP` segment addresses was found
  (consume side at `interpreter.cpp:2288/2314`) — same open thread as the Ghostship doc.
- The float-radian `interpolate_angle` has its quarter-turn snap **commented out** (`:253-255`); only
  the s16 path snaps. Which live callers hit the float path is untraced.
