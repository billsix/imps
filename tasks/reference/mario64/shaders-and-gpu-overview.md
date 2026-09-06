# Orientation (L1): Shaders that are generated, not written

> **Provenance:** LUS `c151cc91`, 2026-09-06. **L1**
> (understand-without-code). Capsule (L0) in [`README.md`](README.md);
> full mechanism (L2) in [`shaders-and-gpu.md`](shaders-and-gpu.md).

A graphics course teaches shaders as something you write: you type a little
program that runs on the GPU for every vertex and every pixel, and you hand
it to the graphics driver to compile and run. SM64's port does something that
sounds strange at first and is worth sitting with: **nobody writes its
shaders.** They are manufactured, automatically, while the game runs.

The reason goes back to the hardware. The N64 didn't have programmable
shaders; it had a small fixed mixing unit that each material *configured* — a
handful of settings that said "take this texture, multiply by the lighting
color, add this tint." A modern GPU has no such unit; it only runs shader
programs. So the port bridges the gap by **reading the old material's mixing
settings and generating a shader program that computes the same thing.** The
first time it sees a given material, it builds the matching shader source,
hands it to the graphics driver to compile, and remembers the result so the
same material never has to be built again.

Because the port supports several graphics systems, this generation happens
in slightly different dialects. For OpenGL it produces the shader in GLSL,
the usual text form, and lets the driver compile it. For Vulkan, which wants
a pre-compiled binary form, it produces GLSL and then runs it through a
compiler that turns it into that binary (SPIR-V) ahead of time. Same idea —
generate a program from the material — two output formats for two GPUs.

There's a division of labor worth remembering. The **lighting** is computed
earlier, per vertex, and arrives at the generated shader as a ready-made
color; the generated shader's job is just to **mix** that lit color with the
textures and material tints according to the old combiner formula. So the
manufactured shader is mostly a mixer, not a lighting calculator.

The takeaway that reframes the course: a shader is a program the GPU runs,
but it doesn't have to be a program a *person* wrote. Here it is the output
of a tiny compiler that translates 1996 material settings into modern GPU
code, cached one-per-material. Once you've seen that, "the programmable
pipeline" stops being only about hand-authoring and starts being about *who
or what produces the program* — which, in a shipping cross-platform port,
is a code generator.
