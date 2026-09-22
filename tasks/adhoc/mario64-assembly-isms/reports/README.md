# Survey reports (raw input to the catalogue)

Four read-only readers, one per pattern group, each sampled the `../data/*.txt` census logs against
the source at pin `49c5312a` (+ the imps series) on 2026-09-22 and reported what the hits really
are, with `file:line` anchors, proposed rewrites and risk ratings. These files are their reports,
kept verbatim as the evidence the task catalogue (`tasks/mario64-assembly-isms-to-standard-c.md`)
and the patterns reference (`tasks/reference/mario64/assembly-isms-in-the-decomp.md`) were
distilled from. A claim in those docs that is not in a report was verified directly.

- `naming-register-unused-filler.md` — stack/register-named locals and params, `func_/D_`
  clustering, `register`, `UNUSED`, filler members.
- `control-flow-and-matching.md` — goto/labels, loops, empty branches, if/else ladders,
  matching comments, AVOID_UB/volatile.
- `raw-memory-and-numeric.md` — byte-pointer casts, rawData, 16-bit masking, magic/angle
  constants, casts, double literals, division by constants, shifts.
- `booleans-comments-whole-functions.md` — TRUE/FALSE comparisons, `!= 0`, the decomp's `//!
  @bug` notes, plus whole-function reads for shape the regexes miss.
