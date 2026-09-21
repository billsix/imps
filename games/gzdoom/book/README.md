# How a Doom Engine Works — the GZDoom book

A Sphinx teaching book that reads the [GZDoom](https://github.com/ZDoom/gzdoom)
source to show how a real game engine starts up, finds its data, and runs. The
**beginning** of the book: launch → main loop; IWADs, PWADs and the lump
filesystem; then the OpenGL renderer (how a scene becomes GL draw calls) and the
Vulkan renderer (the same frame, recorded into a command buffer instead).

## Build

```
[CONTAINER] make html      # HTML  -> output/html/
[CONTAINER] make epub      # EPUB  -> output/epub/
[CONTAINER] make pdf       # PDF   -> output/latex/ (LuaLaTeX)
[CONTAINER] make all       # all three
[HOST]      python3 -m sphinx -b html docs output/html   # quick HTML, no container
```

> The chapters `literalinclude` code from `../checkout/gzdoom/` by **named
> doc-region**, so the GZDoom checkout must be fetched and patched first
> (`cd .. && ./fetch.sh && ./apply.sh`). `apply.sh` applies the `book/` patch
> stream, which adds the comment-only doc-region markers the chapters cite; the
> book does **not** build against a bare checkout.

The book's `Makefile` mounts the parent `games/gzdoom/` dir at `/work` so the
`../../checkout/gzdoom/src/...` paths in `docs/*.rst` resolve inside the
container.

## What it pulls, and from where

Every code excerpt is the real GZDoom source at pin `g4.14.2`, selected by a
named region (never a line number, so it cannot drift):

| Chapter | Source | Regions |
|---|---|---|
| From launch to the main loop | `src/d_main.cpp` | `game_main_entry`, `startup_to_loop`, `doom_loop` |
| IWADs, PWADs, and the lump filesystem | `src/d_iwad.cpp`, `src/common/filesystem/source/filesystem.cpp` | `scan_iwad`, `iwad_picker_decision`, `init_multiple_files` |
| The OpenGL renderer | `src/common/rendering/hwrenderer/data/hw_renderstate.h`, `src/rendering/hwrenderer/hw_entrypoint.cpp`, `src/rendering/hwrenderer/scene/hw_drawinfo.cpp`, `src/common/rendering/gl/gl_renderstate.cpp`, `src/common/rendering/gl/gl_framebuffer.cpp` | `renderstate_draw_api`, `render_one_viewpoint`, `process_scene`, `draw_scene`, `create_scene`, `render_scene`, `gl_apply`, `gl_draw`, `gl_frame_update` |
| The Vulkan renderer | `src/common/rendering/vulkan/renderer/vk_renderstate.cpp`, `src/common/rendering/vulkan/system/vk_commandbuffer.cpp`, `src/common/rendering/vulkan/system/vk_renderdevice.cpp` | `vk_draw`, `vk_apply`, `vk_apply_renderpass`, `vk_get_draw_commands`, `vk_wait_for_commands`, `vk_frame_update` |

The markers are a comment-only patch (`../patches/book/`) — adding a marker must
never change the program. Proven with `tools/prove_comment_only.sh --allow-line-shift
checkout/gzdoom <pin> HEAD` (the shared `check_comment_only_streams.sh` wrapper can't
yet *discover* the `games/` layout — see `../CLAUDE.md`; fix tracked in
`tasks/extend-comment-only-gate-to-games-family.md`).

Carrier + build details: `../CLAUDE.md`. Port/patch plan:
`../../../tasks/gzdoom-port-and-cli-wad-patch.md`.
