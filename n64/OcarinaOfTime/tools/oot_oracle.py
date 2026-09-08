#!/usr/bin/env python3
"""Ask zeldaret/oot what SoH's address-named functions are really called.

WHEN TO RUN IT
    After a PIN BUMP. zeldaret/oot keeps naming symbols, so a newer SoH pin
    (or simply a later oot revision) can turn symbols this repo still calls
    func_8xxxxxxx into names with real upstream authority. Re-running replaces
    oracle.tsv; rows whose verdict is ADOPT are free, verified names.

    Needs network access (it fetches raw files from github).

ORIGIN
    Promoted from tasks/adhoc/ (2026-09-08) after it had yielded 770 adopted
    names. Method and conventions: tasks/reference/ocarina/decomp-renaming.md.

SoH's decomp IS the zeldaret/oot decomp at the same ROM addresses, so SoH's
`func_800A9F30` is oot's function at 0x800A9F30. oot has named most of the game.
This fetches oot's counterpart of each SoH file, aligns the two function
sequences, and reports what oot calls each still-un-named SoH function.

Why alignment rather than address lookup: oot renamed the symbols, so the
addresses are gone from its source. But oot lists functions in address order
within a file, exactly as SoH does -- so position N in one file is position N in
the other. The alignment is only trusted when the sequences have the SAME LENGTH
and every already-named SoH function matches oot's name at its position; that
agreement is strong evidence the files are the same revision. Anything else is
reported as UNSAFE and left for a human.

Covers BOTH functions and DATA symbols (`D_`). They are aligned as two separate
sequences, because a file's functions and its statics are two independent
address-ordered lists; mixing them would destroy the anchors.

Output: oracle.tsv -- soh_file, kind, index, soh_name, oot_name, verdict
  ADOPT   oot has a real name for a function SoH leaves address-named
  BOTH    both leave it address-named -> needs a deduced name, no oracle
  UNSAFE  sequences disagree; do not trust position

Run from the imps repo root:
    python3 tasks/adhoc/ocarina-decomp-rename-and-cleanup/oot_oracle.py [file ...]
With no arguments it does every SoH file that still has an un-named definition.
Fetches are cached under .cache/ so re-runs are free.
"""
import difflib
import os
import re
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
# <project>/tools/oot_oracle.py -> <project>
PROJECT = os.path.dirname(HERE)
CHECKOUT = os.path.join(PROJECT, "Shipwright")
# Generated output and the fetch cache belong beside the checkout, not inside
# tools/ -- they are regenerable data, and both are gitignored.
CACHE = os.path.join(PROJECT, ".oot-oracle-cache")
ORACLE_TSV = os.path.join(PROJECT, "oracle.tsv")
# Try several oot revisions and keep the best answer per symbol. `main` has the
# most names, but it has drifted years from SoH's snapshot -- files get renamed
# or moved away, and function sequences diverge past what alignment can bridge.
# An older revision is closer to SoH and still carries upstream names, so it
# recovers symbols `main` cannot reach (padutils.c and z_kaleido_scope_PAL.c,
# for instance, exist at the 2022 revision but not at main's paths).
REVISIONS = (
    "main",
    "fa1ea37d5428c66bf783039117568bc3c5f4b645",   # 2022-05-31, nearer SoH
)
RAW = "https://raw.githubusercontent.com/zeldaret/oot/{rev}/"

# A function DEFINITION at column 0. The parameter list may WRAP, in which case
# the first line ends in a comma rather than `)` -- 23 SoH definitions do, and an
# earlier version of this pattern silently could not see any of them (found via
# the four Skin_DrawImpl wrappers in z_skin.c, 2026-09-07). Accept both shapes.
DEF_RE = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_ \t\*]*?\b([A-Za-z_][A-Za-z0-9_]*)\s*"
    r"\((?:[^;]*\)\s*\{?|[^;)]*,)\s*$")
ADDR_RE = re.compile(r"^(func_[0-9A-Fa-f]{6,8}|D_[0-9A-Fa-f]{6,8})$")
KEYWORDS = {"if", "for", "while", "switch", "return", "else", "do", "sizeof"}


def soh_to_oot(path):
    """Map a SoH source path to its oot counterpart. oot moved the audio code
    out of src/code/ into src/audio/; everything else is a straight strip of the
    leading `soh/`."""
    p = path[len("soh/"):] if path.startswith("soh/") else path
    # oot reorganised the audio code out of src/code/ into src/audio/, split
    # into game/ (the game-facing API) and internal/ (the synthesis engine).
    # Verified against the live repo tree 2026-09-07 -- an earlier guess of
    # "src/audio/lib/" 404'd and silently cost us these files.
    moved = {
        "src/code/audio_thread.c": "src/audio/internal/thread.c",
        "src/code/audio_heap.c": "src/audio/internal/heap.c",
        "src/code/audio_synthesis.c": "src/audio/internal/synthesis.c",
        "src/code/audio_playback.c": "src/audio/internal/playback.c",
        "src/code/audio_effects.c": "src/audio/internal/effects.c",
        "src/code/audio_load.c": "src/audio/internal/load.c",
        "src/code/audio_seqplayer.c": "src/audio/internal/seqplayer.c",
        "src/code/audio_data.c": "src/audio/internal/data.c",
        "src/code/audio_seq.c": "src/audio/game/sequence.c",
        "src/code/audio_sfx.c": "src/audio/game/sfx.c",
        "src/code/audio_general.c": "src/audio/game/general.c",
        # padutils/system_heap have no oot counterpart under those names.
    }
    return moved.get(p, p)


def fetch(oot_path, rev="main"):
    """oot source for `oot_path` at `rev`, cached on disk. None if absent."""
    cached = os.path.join(CACHE, f"{rev[:8]}__" + oot_path.replace("/", "__"))
    if os.path.exists(cached):
        text = open(cached, encoding="utf-8", errors="replace").read()
        return text or None
    os.makedirs(CACHE, exist_ok=True)
    try:
        url = RAW.format(rev=rev) + oot_path
        with urllib.request.urlopen(url, timeout=30) as response:
            text = response.read().decode("utf-8", "replace")
    except Exception:
        text = ""                      # cache the miss so we do not refetch
    open(cached, "w", encoding="utf-8").write(text)
    return text or None


def functions(text, bodies=False):
    """Function names defined in `text`, in source (= address) order.
    With bodies=True, also return each function's body text."""
    names, blobs, lines = [], [], text.splitlines()
    for index, line in enumerate(lines):
        match = DEF_RE.match(line)
        if not match or match.group(1) in KEYWORDS:
            continue
        names.append(match.group(1))
        if bodies:
            # From the definition to the next line that closes it at column 0.
            end = index + 1
            while end < len(lines) and not lines[end].startswith("}"):
                end += 1
            blobs.append("\n".join(lines[index:end + 1]))
    return (names, blobs) if bodies else names


# A DATA definition: a top-level declaration that is not a function -- no "("
# before the first "=" or ";". Covers `static s16 D_80A65F38[] = {`, `u8 D_x;`.
DATA_RE = re.compile(
    r"^(?:static\s+|extern\s+|const\s+)*[A-Za-z_][A-Za-z0-9_]*\s[^;()=]*?"
    r"\b([A-Za-z_][A-Za-z0-9_]*)\s*(?:\[[^\]]*\]\s*)*\s*(?:=|;)")


def data_symbols(text, bodies=False):
    """Data symbols defined in `text`, in source (= address) order."""
    names, blobs, lines = [], [], text.splitlines()
    for index, line in enumerate(lines):
        if DEF_RE.match(line):            # a function, not data
            continue
        match = DATA_RE.match(line)
        if not match or match.group(1) in KEYWORDS:
            continue
        names.append(match.group(1))
        if bodies:
            end = index
            while (end < len(lines) and not lines[end].rstrip().endswith(";")
                   and end - index < 400):
                end += 1
            blobs.append("\n".join(lines[index:end + 1]))
    return (names, blobs) if bodies else names


COMMENT_RE = re.compile(r"//.*?$|/\*.*?\*/", re.S | re.M)
IDENT_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
NUM_RE = re.compile(r"\b(0[xX][0-9a-fA-F]+|\d+\.?\d*[fFuUlL]*)\b")
# Keywords carry the control flow; everything else is a name we blank out.
STRUCT_KEEP = {"if", "else", "for", "while", "do", "switch", "case", "break",
               "continue", "return", "goto", "default", "sizeof", "static",
               "const", "void"}


def structure_similarity(a, b):
    """How alike two bodies are once identifiers and literals are blanked.

    Second tier, for bodies that fail the literal comparison. oot has renamed
    fields and introduced named constants since SoH's snapshot
    (`gSaveContext.cutsceneIndex` -> `gSaveContext.save.cutsceneIndex`, `0xFFF0`
    -> `CS_INDEX_0`), which wrecks a text match while leaving control flow,
    operators and call shape untouched. Those survive here.
    """
    def norm(text):
        t = COMMENT_RE.sub(" ", text).split("{", 1)[-1]
        t = NUM_RE.sub("N", t)
        t = IDENT_RE.sub(lambda m: m.group(0) if m.group(0) in STRUCT_KEEP
                         else "X", t)
        return re.sub(r"\s+", "", t)
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return 0.0
    return difflib.SequenceMatcher(a=na, b=nb, autojunk=False).ratio()


def body_similarity(a, b):
    """How alike two function bodies are, 0..1.

    Positional alignment is a LEAD, not proof -- the reference-doc rule is that
    anything a later reader will trust without re-checking must be verified. So
    strip comments and whitespace (they differ freely between the two decomps)
    and compare what is left. Identifiers may legitimately differ, since oot has
    renamed things SoH has not, which is why the threshold is not 1.0.
    """
    def norm(text):
        text = COMMENT_RE.sub(" ", text)
        text = text.split("{", 1)[-1]          # drop the signature line
        return re.sub(r"\s+", "", text)
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return 0.0
    return difflib.SequenceMatcher(a=na, b=nb, autojunk=False).ratio()


def align(soh_fns, oot_fns):
    """Map SoH function index -> oot function name, tolerating local drift.

    oot's main branch has moved on from SoH's snapshot: functions are added,
    removed and reordered, so whole-file positional matching fails on most
    files. Instead, use the names the two files ALREADY AGREE ON as anchors
    (difflib's matching blocks), and map only within the gaps between anchors --
    and only when a gap has the same length on both sides, which means nothing
    was added or removed there. Anything else stays unmapped rather than
    guessed: a wrong "authoritative" name is worse than no name.
    """
    matcher = difflib.SequenceMatcher(a=soh_fns, b=oot_fns, autojunk=False)
    mapping = {}
    prev_a = prev_b = 0
    for a, b, size in matcher.get_matching_blocks():
        gap_a, gap_b = soh_fns[prev_a:a], oot_fns[prev_b:b]
        if gap_a and len(gap_a) == len(gap_b):
            for offset in range(len(gap_a)):
                mapping[prev_a + offset] = gap_b[offset]
        for offset in range(size):     # the anchors themselves
            mapping[a + offset] = oot_fns[b + offset]
        prev_a, prev_b = a + size, b + size
    return mapping


def git(*args):
    return subprocess.run(("git", "-C", CHECKOUT) + args,
                          capture_output=True, text=True).stdout


def soh_files_with_unnamed():
    """Files still holding ANY address-named symbol.

    This used to look only for un-named FUNCTION definitions, which silently
    skipped every file whose only un-named symbols were DATA -- 646 `D_` symbols
    and 40 functions were never checked against upstream at all (found
    2026-09-07 while working out an honest progress denominator). Match any
    address name, and let the per-kind alignment sort out what is there.
    """
    out = git("grep", "-lE", r"\b(func_|D_)[0-9A-Fa-f]{8}\b",
              "HEAD", "--", "soh/src")
    return sorted(l.split(":", 1)[1] for l in out.split() if ":" in l)


VERDICT_RANK = {"ADOPT": 0, "ADOPT_STRUCT": 1, "BOTH": 2,
                "MISMATCH": 3, "UNSAFE": 4, "NOFILE": 5}


def emit(kind, extract, path, soh_text, oot_text, rows, stats):
    """Align one KIND of symbol (functions or data) between SoH and oot, and
    append a verdict row per still-un-named SoH symbol.

    Functions and data are aligned separately: a file's functions and its
    statics are two independent address-ordered lists, and mixing them would
    destroy the anchors the alignment depends on.
    """
    soh_syms, soh_bodies = extract(soh_text, bodies=True)
    oot_syms, oot_bodies = extract(oot_text, bodies=True)
    mapping = align(soh_syms, oot_syms)
    oot_index = {}
    for i, name in enumerate(oot_syms):
        oot_index.setdefault(name, i)

    for index, soh_name in enumerate(soh_syms):
        if not ADDR_RE.match(soh_name):
            continue
        oot_name = mapping.get(index)
        score = 0.0
        if oot_name is None:
            verdict, oot_name = "UNSAFE", "-"
        elif ADDR_RE.match(oot_name):
            verdict = "BOTH"
        else:
            # Confirm the two really are the same symbol before adopting the
            # name: positional alignment is a lead, not proof.
            j = oot_index.get(oot_name)
            score = (body_similarity(soh_bodies[index], oot_bodies[j])
                     if j is not None and index < len(soh_bodies) else 0.0)
            if score >= 0.80:
                verdict = "ADOPT"
            else:
                # Second tier: same shape, different names/constants?
                struct = (structure_similarity(soh_bodies[index], oot_bodies[j])
                          if j is not None and index < len(soh_bodies) else 0.0)
                verdict = "ADOPT_STRUCT" if struct >= 0.92 else "MISMATCH"
                if verdict == "ADOPT_STRUCT":
                    score = struct
        stats[verdict] = stats.get(verdict, 0) + 1
        rows.append((path, kind, index, soh_name, oot_name, verdict,
                     f"{score:.2f}"))


def main(argv):
    targets = argv[1:] or soh_files_with_unnamed()
    rows, stats = [], {"ADOPT": 0, "BOTH": 0, "UNSAFE": 0, "NOFILE": 0}

    for path in targets:
        soh_text = git("show", f"HEAD:{path}")
        if not soh_text:
            continue
        oot_path = soh_to_oot(path)

        # Best row per (kind, soh_name) across all revisions.
        best = {}
        seen_any = False
        for rev in REVISIONS:
            oot_text = fetch(oot_path, rev)
            if oot_text is None:
                continue
            seen_any = True
            candidate = []
            for kind, extract in (("func", functions), ("data", data_symbols)):
                emit(kind, extract, path, soh_text, oot_text, candidate, {})
            for row in candidate:
                key = (row[1], row[3])
                if (key not in best
                        or VERDICT_RANK[row[5]] < VERDICT_RANK[best[key][5]]):
                    best[key] = row
        if not seen_any:
            stats["NOFILE"] = stats.get("NOFILE", 0) + 1
            rows.append((path, "-", "-", "-", "-", "NOFILE", "0.00"))
            continue
        for row in best.values():
            stats[row[5]] = stats.get(row[5], 0) + 1
            rows.append(row)

    out_path = ORACLE_TSV
    with open(out_path, "w") as handle:
        handle.write("soh_file\tkind\tindex\tsoh_name\toot_name\tverdict\tbody_match\n")
        for row in rows:
            handle.write("\t".join(str(c) for c in row) + "\n")

    print(f"files examined : {len(targets)}")
    for k in ("ADOPT", "ADOPT_STRUCT", "MISMATCH", "BOTH", "UNSAFE", "NOFILE"):
        print(f"  {k:8s}: {stats.get(k, 0)}")
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main(sys.argv)
