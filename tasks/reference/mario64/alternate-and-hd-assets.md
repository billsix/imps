# Reference: Alternate & HD assets — swapping in high-res textures at runtime

> **Provenance:** authored 2026-09-06 against LUS submodule `c151cc91`
> (1.3.1-544 fork). Anchors in `libultraship/src/fast/interpreter.cpp` and
> `ship/resource/ResourceManager.cpp`. Part of the mario64 graphics set —
> map at [`README.md`](README.md). **Extends** `asset-pipeline.md` (the
> ROM→`.o2r`→runtime story) with the *replacement* path; companions:
> `textures-and-texture-mapping.md`, `sampling-and-mipmapping.md`.

## TL;DR

The reason texture packs "look great" is a **transparent replacement**
mechanism: when alt assets are enabled, a request for a base texture named
`"name"` is redirected to a high-res one at `"alt/name"` if it exists.
`ResourceManager::IsAltAssetsEnabled` (`ResourceManager.cpp:452`) gates it;
the interpreter resolves the `alt/` prefix (`interpreter.cpp:747-781`),
falling back to vanilla when no HD version is present, and can **decode the
HD texture asynchronously** on a thread pool while the vanilla one renders.
HD replacements carry constraints (clamp/mask handling) so they line up with
the geometry that expected the original.

## 1. The `alt/` naming convention (`interpreter.cpp:747`)

Vanilla and HD assets coexist under one archive namespace, distinguished by
a prefix (comment at `:747-750`):

> vanilla (`"name"`) and HD (`"alt/name"`) live under the same … the `alt/`
> prefix matches what the ResourceManager uses itself.

So a texture pack ships its high-res images at `alt/<same path>`, and the
loader picks them up without the game code knowing. This is why an HD pack is
"drop a `.o2r` in `mods/`" (see `asset-pipeline.md` on mod layering) — no code
change, just names that shadow the originals.

## 2. Resolution + fallback (`:755`)

```c
if (!rm->IsAltAssetsEnabled() || alreadyAlt) { /* use vanilla */ }
// else try "alt/name"; if absent, fall back to vanilla
```

Two guards: alt assets must be **enabled**, and you must not already be
resolving an alt path (`alreadyAlt`, avoiding infinite redirection). If the
HD variant is missing, it uses the base — so a **partial** texture pack works
(only the textures it provides are upgraded). `GetBaseTexturePath` (`:849`)
strips the prefix to find the vanilla key.

## 3. Async HD decode (`:781`)

HD textures are large, so decoding them inline would stall the frame. The
fork decodes the HD (`alt/name`) variant **on a thread pool while the vanilla
renders** (`:781`), swapping to the HD result once ready. This is why a
texture pack pops in smoothly rather than hitching — a real
producer/consumer, off-thread-work pattern.

## 4. Replacement bookkeeping (`mMaskedTextures`, `importReplacement`)

The `importReplacement` flag threads through the `ImportTexture*` decoders
(`textures-and-texture-mapping.md`); when set, a decoder pulls its bytes from
`mMaskedTextures[...].replacementData` (`:920`) instead of the ROM texture.
HD-clamp handling (`:938`, `:1008`) trims an HD texture to the region the
original occupied, so the replacement samples the same way the vanilla did —
the constraint that keeps a 4× texture aligned to geometry authored for 1×.

## How this relates to the course

- **Neither course covers asset systems at all**, let alone hot-swappable
  HD replacement. This is a pure applied gap-fill, and a satisfying one: it
  answers "how do fan HD packs work without touching the game?" — by a
  naming convention, a runtime lookup with fallback, and async decoding.
- **A software-engineering lesson as much as a graphics one:** transparent
  redirection (the game asks for `name`, gets `alt/name`), graceful fallback
  (partial packs), and off-thread work to hide latency. The graphics course
  has no reason to teach any of it, but it's exactly the machinery a shipping
  port needs.
- **Ties the texture docs together:** the replacement rides the same
  `ImportTexture` decoders (`textures-and-texture-mapping.md`) and benefits
  from the same mip/sampler path (`sampling-and-mipmapping.md`) — HD packs
  are why the mip chain matters.

## Candidate doc-region spans (for the later Sphinx pass — not yet added)

- `libultraship/src/fast/interpreter.cpp` around the alt resolution
  (`:747-781`): region `alt_asset_resolution` — prefix, fallback, async
  decode.
- `libultraship/src/ship/resource/ResourceManager.cpp` around
  `IsAltAssetsEnabled` (`:452`): region `alt_assets_gate`.
