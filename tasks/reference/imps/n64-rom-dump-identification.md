# N64 ROM dumps: how the ports validate them, and how to tell a bad dump from a good one

**Reference document** — what a HarbourMasters port actually checks when you hand it a ROM, the
ways a cart dump differs from what it wants (padding, byte order, save images mistaken for ROMs),
and the one-liners that settle it. Learned on Paper Mario 2026-09-21/22
(`tasks/reference/papermario/rom-overdump-and-trimming.md`); the rules are the same for every
Torch-based port. ROMs themselves stay out of imps. Written 2026-09-22 by William Emerison Six
<billsix@gmail.com> (agent-assisted). Update in place.

## What the port checks

Torch-based ports (PaperBoat, Ghostship, Lighthouse, current SoH) compute the **SHA-1 of the whole
file** (`Companion::CalculateHash`) and look it up as a key in the port's `config.yml`; only an
exact match is "a ROM". There is no header sniffing, no size heuristic, no truncation. So the
question is never "is this the right game" but "is this file byte-for-byte the image the recipe
was written for". Find the accepted hashes with

```sh
sed -n 's/^\([0-9a-f]\{40\}\):.*/\1/p' <checkout>/config.yml     # e.g. PaperBoat: 3837f44c… (US)
```

## Sizes and headers

| Game (US) | image size | bytes | header |
|---|---|---|---|
| Super Mario 64 | 8 MB | 8,388,608 | `80 37 12 40` |
| Banjo-Kazooie | 16 MB | 16,777,216 | `80 37 12 40` |
| Ocarina / Majora | 32 MB | 33,554,432 | `80 37 12 40` |
| **Paper Mario** | **40 MB** | **41,943,040** | `80 37 12 40` |

`xxd -l 64 rom` shows the header, the title at 0x20 (`PAPER MARIO`) and the game ID at 0x3B
(`NMQE` = US). `ls -l` shows whether the size is one of the above.

## The three ways a dump goes wrong

1. **Over-dump / padding.** A cart reader that cannot identify the CIC (`CartTest.txt`: `CIC -
   Failed`, `Romsize - 64MB`) reads the whole address space; the file is the game plus trailing
   `00`/`0f`/`ff`. Whole-file hash ≠ recipe → silently "not a ROM". Test and fix:
   ```sh
   head -c 41943040 rom.z64 | sha1sum        # == the recipe key? then only padding followed
   head -c 41943040 rom.z64 > trimmed.z64    # (use the game's size from the table)
   ```
   Nothing is lost; no re-dump is needed. `n64/PaperMario/run.sh <ROM>` does this automatically.
2. **Byte order.** `.n64`/`.v64` files are the same data byte- or word-swapped (`37 80 40 12`,
   title `APEP RAMIR O`); they hash differently and the port wants big-endian `.z64`. Convert
   (swap every 2 bytes for `.n64`) rather than re-dump.
3. **Not a ROM at all.** `ROM.fla` / `ROMF.flash` (128 KB) are FlashRAM save images (they start
   with a save title such as `Mario Story 006`); `.eep`/`.sra` likewise. Keep them for the save,
   never feed them to the extractor.

## What each port does with a bad file

- Scan of the app dir (`FindSupportedRoms`): an unsupported file is simply not offered.
- File dialog: pristine PaperBoat accepted anything, ran Torch, got "No config found", and showed
  the generic **"No ROM O2R file detected"** — the extractor had not really run. imps patch
  `n64/PaperMario/patches/upstream-candidates/0002` turns that into a "not a supported ROM" popup
  naming the size and the usual causes.
- Command line: dead on Linux until imps patch `0001`; `run.sh <ROM>` checks the hash before the
  app even starts and prints the accepted hashes on mismatch.

## Checklist when "the ROM won't load"

1. `ls -l` — is the size in the table? Bigger → over-dump (case 1). Tiny → a save file (case 3).
2. `xxd -l 4` — `80 37 12 40`? Else byte order (case 2).
3. `sha1sum` vs the `config.yml` keys — the only test the port makes.
4. If all three pass and it still "fails to load", the ROM is not the problem: read
   `runDir/logs/<app>.log` for Torch's `Done!` line — if extraction finished, the failure is after
   it (see `lus-render-backend-selection.md` for the first-frame crash).
