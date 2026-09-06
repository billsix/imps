====================================
Appendix C: The geo-layout bytecode
====================================

Chapter :doc:`engine-math` said the scene tree is built by a small interpreter
rather than typed out by hand. That interpreter runs a **geo layout**: a compact
program in a tiny instruction set. A jump table maps each opcode to a handler,
and the crucial pair is "open node" / "close node", which push and pop the
current parent — so the *nesting* of the program becomes the *nesting* of the
tree.

This is one of **three** such little languages in the game: one builds the render
tree (this one), one scripts levels, and one drives object behavior. Seeing that
a scene is *compiled* from a declarative recipe — the 1996 ancestor of a modern
engine's scene files and prefabs — is the payoff.

Full detail: ``tasks/reference/mario64/scene-graph-and-data-structures.md``.
