# OcarinaOfTime: interactive save-file generator (Python CLI)

**Status:** proposed — needs go-ahead
**Priority:** 4
**Difficulty:** 6

## BLUF

Study the full Ship of Harkinian source to understand its save-file format
— every field that gets saved — then write an interactive command-line
Python program that interviews the user about the save they want (most
important questions first: which dungeons are beaten, with listed options;
then progressively finer detail with progression-consistent defaults;
full stocks assumed for every item type owned), writes the save file
locally, and finishes by telling the user exactly where to install it and
how to back up their existing save. Done when a generated save loads in
the game and matches what the user asked for.

## Context

Work in `OcarinaOfTime/Shipwright/` **at the pin with the patch series
applied** (the agent contract in the master `CLAUDE.md`) — note the decomp
rename patch renames some `soh/src/code/` files, so study the applied
tree, not upstream's.

What to read first (verify paths at the pin before trusting):

- **`soh/soh/SaveManager.cpp` / `.h`** — the port's save system. SoH saves
  are **JSON**, not N64 SRAM images, which is what makes this generator
  tractable: no binary layout or checksum, but there IS structure to get
  right — save sections, per-section version numbers, slot naming, and
  the base/main-quest vs randomizer split. Map all of it.
- **`soh/include/z64save.h`** and the decomp save context — the actual
  data model: inventory slots, quest items (medallions/stones), equipment,
  upgrades (wallet/quiver/bomb bag/…), hearts/magic, rupees, scene flags,
  `eventChkInf`.
- **The dungeon-completion encoding** — the intellectual core of the
  program: "Forest Temple beaten" is not one field; it's event flags,
  medallion/stone quest bits, possibly scene flags (boss door, blue warp).
  Enumerate, per dungeon (child: Deku Tree, Dodongo's Cavern, Jabu-Jabu;
  adult: Forest, Fire, Water, Shadow, Spirit; plus Ganon's-path gates),
  exactly which bits mean "beaten" as the game checks them.
- **A real save as ground truth:** the maintainer has played saves in
  `OcarinaOfTime/runDir/Save/` — diff a real file against the code-derived
  model; generate → load in-game → compare is the verification loop.
- `tasks/reference/ocarina/port-layer.md` (SaveManager section) and
  `decomp-map.md` for orientation — banner caveats apply.
- **Online research is explicitly authorized and encouraged** (maintainer,
  2026-09-01): search the web for OoT save-format and progression
  knowledge — the zeldaret/oot decomp docs, community wikis on
  `eventChkInf`/scene-flag meanings, item progression order, and any
  existing OoT/SoH save editors (prior art for field semantics). The code
  at the pin remains the authority where sources disagree; cite what was
  used in the reference doc.

## Deliverables

1. `OcarinaOfTime/tools/save_generator.py` — the program (below).
2. **`tasks/reference/ocarina/save-file-generator.md`** — a standing
   reference doc describing everything: the SoH save-file structure
   (sections, versions, slot naming, where files live), the field model
   (inventory, quest bits, flags — especially the per-dungeon "beaten"
   encoding), the generator's design (question order, how defaults are
   derived from progression, the full-stocks rule), decisions made with
   rationale (base-quest-only, fixed values chosen for unasked fields),
   verification results, and the online sources consulted. Written per
   the reference-doc conventions (this is the durable knowledge; the task
   doc stays the work log).

## The program (requirements from the maintainer, 2026-09-01)

Python 3, command line, interactive Q&A, living at
`OcarinaOfTime/tools/save_generator.py` (native imps file, not a patch).

1. **Most important first: dungeon completion.** List the dungeons with
   options (e.g. per-dungeon yes/no plus convenience presets like "all
   child dungeons" / "everything up through Water Temple" / "all").
2. **Then decreasing detail, with good defaults derived from the answers
   so far.** Item classes the user has (bow, bombs, hookshot tier, songs,
   tunics, boots, …): default each to what a player who beat the chosen
   dungeons would plausibly have (progression-consistent — beating Forest
   Temple implies the Fairy Bow, etc.), and let the user override.
3. **Full stocks assumed.** For every item type the user has, fill
   consumables/ammo to the capacity of their upgrade level (deku sticks,
   nuts, bombs, arrows, magic, rupees to wallet cap, hearts full).
4. **Output:** write the save file into the current directory (or a
   `--output` path); then print (a) the exact install destination —
   `OcarinaOfTime/runDir/Save/<slot file>`, using the real slot naming
   SaveManager expects — and (b) how to back up an existing save first
   (a one-line `cp` the user can paste). The program never installs or
   overwrites anything itself.

Also: pick sensible fixed values for everything not asked about (name,
age/era, entrance — study what a fresh-but-valid save needs so the game
doesn't reject or misbehave), and validate the result loads.

## Verification

- Generate a save, install per the program's own instructions, launch via
  `./run.sh`, load the slot, and check: dungeon state, inventory,
  stocks match the answers. A save the game silently resets or that
  crashes on load is a failure even if the JSON "looks right".
- Cross-check at least one generated file field-by-field against a real
  played save with similar progression.

## Decisions

- **Base-quest saves only** (William Emerison Six <billsix@gmail.com>,
  2026-09-01). Randomizer saves — with their seed/check-state section —
  are out of scope; the program errors out politely if asked for one.

## Open questions

None.
