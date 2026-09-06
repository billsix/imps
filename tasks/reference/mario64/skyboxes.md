# Reference: Skyboxes — a camera-locked scrolling textured backdrop

> **Provenance:** authored 2026-09-06 against Ghostship pin `49c5312a`.
> Anchors in `src/game/skybox.c`. Part of the mario64 graphics set — map at
> [`README.md`](README.md). Companions: `field-of-view-and-projection.md`,
> `textures-and-texture-mapping.md`, `camera-system.md`.

## TL;DR

SM64's sky is **not** a cube around the world; it is a **flat grid of
textured tiles drawn behind everything**, positioned by the camera's yaw so
it looks like a distant panorama. `skybox.c` splits a wide sky image into an
**8-row** grid of tiles (`SKYBOX_ROWS`, `:52`), picks the tiles under the
camera's current facing via `calculate_skybox_scaled_x` (`:139`), and draws
them as camera-facing quads at a **fixed 90° FOV** (`:132`). Rotate the
camera and the sky scrolls horizontally; it never moves with translation, so
it reads as infinitely far away.

## 1. Yaw → horizontal scroll (`calculate_skybox_scaled_x:139`)

The one clever line. The camera's yaw (a binary angle,
`rotation-euler-vs-rotors.md`) is mapped to an X offset into a scaled sky
image:

```
scaledX ≈ (360 / fov) * (yaw / 65536) * SCREEN_WIDTH
```

i.e. *(how many fov-sized wedges fit in a full circle) × (how far around the
camera has turned, 0..1) × (screen width)*. With `fov` pinned to **90°**, a
quarter turn scrolls the sky by one screen width. Only **yaw** matters —
pitch and position are ignored — which is what makes the backdrop feel
distant and stable.

## 2. The tile grid (`draw_skybox_tile_grid:227`, `make_vertex:212`)

The visible region is drawn as a grid of textured quads. `make_vertex`
(`:212`) builds each corner with position, texture coordinates (`31 << 5` =
the tile's far texel edge in the N64's fixed-point S/T units), and a vertex
color from `sSkyboxColors`. `draw_skybox_tile_grid` (`:227`) indexes the
per-tile textures out of `sSkyboxTextures[background]` (`:77`, a
segmented-address table), covering the screen with just the tiles the camera
can see — not the whole panorama every frame.

## 3. Drawn first, behind everything

The skybox renders as a background pass before the 3D scene, at max depth, so
every opaque object draws over it. It has its own tiny pipeline (build quads
→ draw), independent of the geo tree, because it is a 2D-ish backdrop, not
world geometry.

## How this relates to the course

- **Neither course has a skybox** (no environment/background beyond the clear
  color, `modelviewprojection` ch03). So this is a gap-fill on "how does a
  game draw a sky/horizon?" — and the answer is instructive precisely
  because it is *not* the obvious "textured cube": it is a **camera-locked 2D
  backdrop scrolled by yaw**, cheaper and simpler than a cube map.
- **A neat applied use of the binary-angle yaw** (`rotation-euler-vs-rotors.md`):
  the same `0x10000`-per-turn angle that drives orientation here drives a
  texture scroll. It shows an angle being used as a *coordinate*, not a
  rotation.
- **Ties FOV to the effect:** the fixed 90° here connects to
  `field-of-view-and-projection.md` — the backdrop's math assumes a specific
  FOV even as the world's FOV varies.

## Candidate doc-region spans (for the later Sphinx pass — not yet added)

- `src/game/skybox.c` around `calculate_skybox_scaled_x` (`:139`): region
  `skybox_yaw_scroll` — yaw → horizontal offset (the heart of the effect).
- `src/game/skybox.c` around `draw_skybox_tile_grid` (`:227-239`): region
  `skybox_tile_grid` — drawing only the visible tiles.
