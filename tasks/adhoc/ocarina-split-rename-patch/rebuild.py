#!/usr/bin/env python3
"""Rebuild the personal/ patch stream as one commit per rename.

Strategy -- peel BACKWARDS, replay forwards.

The safe direction is backwards. Starting from the finished tree and peeling one
rename off at a time must land exactly on the pin; if it does, the decomposition
is provably complete and the forward replay cannot invent or lose anything.
Re-deriving each rename forwards from the pin would give no such guarantee.

Peeling one rename R = (old -> new) off a tree state:
  1. delete the provenance comment lines citing `old` (the long definition
     comment plus its continuation lines, and the short inline declaration tag);
  2. inside R's SCOPE ONLY, rewrite `new` back to `old`.

Scope is the set of files that contained `old` at the pin -- exact, and the
reason file-local statics are safe: D_80A65F38 lives in one file, so undoing
sColChkInfoInit there cannot touch the 60 other files that have their own static
of that name.

Replay order:
  Phase A -- 18 file renames (code_<addr>.c -> a meaningful name), one commit
             each: the `git mv`, plus any in-tree comment that referenced the
             old filename.
  Phase B -- 207 symbol renames, one commit each, grouped by defining file so a
             reviewer stays in one area at a time. Each commit renames that one
             symbol everywhere it occurs and adds its provenance comments --
             never two symbols in one commit.

Only the ~145 files the original commit touched are considered; nothing else can
change, and restricting to them keeps the peel fast.

Run from anywhere (rewrites the checkout's split-rebuild branch):
    python3 tasks/adhoc/ocarina-split-rename-patch/rebuild.py
"""
import csv
import os
import re
import subprocess
import sys

from _common import CHECKOUT, git, is_marker_line, pin_sha

HERE = os.path.dirname(os.path.abspath(__file__))
BRANCH = "split-rebuild"
TARGET = "target-tree"
BASELINE = "baseline-renames"

# The three file renames git reports as add+delete rather than R (the content
# changed too much for its similarity threshold).
EXPLICIT_RENAMES = {
    "soh/src/code/z_rumble.c": "soh/src/code/code_800A9F30.c",
    "soh/src/code/audio_stop_all_sfx.c": "soh/src/code/code_800C3C20.c",
    "soh/src/code/debug_ctrlr2.c": "soh/src/code/code_800D31A0.c",
}


def run(*args, **kw):
    """Run a command in the checkout, raising with its stderr on failure."""
    result = subprocess.run(args, cwd=CHECKOUT, capture_output=True, text=True, **kw)
    if result.returncode != 0:
        raise SystemExit(f"{' '.join(args)} failed:\n{result.stderr}")
    return result.stdout


def load_table():
    with open(os.path.join(HERE, "rename_table.tsv")) as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def file_renames():
    """{post path: pin path} for every renamed decomp file."""
    out = dict(EXPLICIT_RENAMES)
    for line in git("show", "--name-status", "--find-renames=40%", "--pretty=",
                    BASELINE).splitlines():
        fields = line.split("\t")
        if fields[0].startswith("R") and fields[1] != fields[2]:
            out[fields[2]] = fields[1]
    return out


def universe(renames):
    """The files that may change, as POST-rename paths."""
    paths = set()
    for line in git("show", "--name-only", "--pretty=", BASELINE).splitlines():
        if line.strip():
            paths.add(line.strip())
    # Deleted pin paths are represented by their post-rename counterpart.
    pin_paths = set(renames.values())
    return {p for p in paths if p not in pin_paths}


def blob(rev, path):
    out = subprocess.run(("git", "-C", CHECKOUT, "show", f"{rev}:{path}"),
                         capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else None


def peel(tree, old, new, scope):
    """Undo one rename on a {path: text} mapping. Mirrors decompose.peel()."""
    word = re.compile(rf"\b{re.escape(new)}\b")
    inline = re.compile(rf"(?:\s*//)?[\s,]*was\s+{re.escape(old)}\s*\[[^\]]*\]")
    cites_old = re.compile(rf"\b{re.escape(old)}\b")
    for path, text in list(tree.items()):
        if text is None:
            continue
        out, dropping, touched = [], False, False
        for line in text.splitlines():
            if is_marker_line(line) and cites_old.search(line):
                dropping, touched = True, True
                continue
            if dropping:
                if line.lstrip().startswith("//") and not is_marker_line(line):
                    touched = True
                    continue
                dropping = False
            if inline.search(line):
                line, touched = inline.sub("", line), True
            if path in scope and word.search(line):
                line, touched = word.sub(old, line), True
            out.append(line)
        if touched:
            tree[path] = "\n".join(out) + ("\n" if text.endswith("\n") else "")
    return tree


def write(path, text):
    full = os.path.join(CHECKOUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as handle:
        handle.write(text)


def main():
    table = load_table()
    renames = file_renames()
    pin = pin_sha()
    paths = universe(renames)
    pin_to_post = {v: k for k, v in renames.items()}

    print(f"file renames : {len(renames)}")
    print(f"symbol renames: {len(table)}")
    print(f"files in play : {len(paths)}")

    # --- derive the state before each rename, by peeling backwards -----------
    tree = {p: blob(TARGET, p) for p in paths}
    states = []                       # states[i] = tree BEFORE table[i]
    for row in reversed(table):
        scope = {pin_to_post.get(p, p)
                 for p in row["scope"].split(",") if p} & paths
        tree = peel(tree, row["old"], row["new"], scope)
        states.append(dict(tree))
    states.reverse()                  # states[i] pairs with table[i]

    # --- verify the fully-peeled state is the pin (modulo the file renames) --
    base = states[0]
    mismatch = []
    for post_path, text in base.items():
        pin_path = renames.get(post_path, post_path)
        if blob(pin, pin_path) != text:
            mismatch.append(post_path)
    print(f"files differing from pin after full peel: {len(mismatch)}")
    for path in mismatch:
        print(f"    {path}")
    expected = set(renames)           # only the stale-path comment carriers
    if not set(mismatch) <= expected | {
            "soh/src/code/audio_general.c", "soh/src/code/audio_sfx.c",
            "soh/src/code/audio_seq.c"}:
        raise SystemExit("unexpected residue -- refusing to rebuild")

    # --- replay forward ------------------------------------------------------
    # A previous aborted run can leave staged renames behind, and `checkout -B`
    # does not discard those -- reset hard and sweep untracked files first.
    run("git", "checkout", "-q", "-B", BRANCH, pin)
    run("git", "reset", "-q", "--hard", pin)
    run("git", "clean", "-qfd", "soh")

    # Phase A: file renames, one commit each.
    for post_path in sorted(renames):
        pin_path = renames[post_path]
        run("git", "mv", pin_path, post_path)
        old_base = os.path.basename(pin_path)[:-2]          # drop ".c"
        # Adopt any line of the base state that mentions the old filename -- a
        # comment cross-referencing the file we just renamed. Files not yet
        # renamed simply are not on disk under their post-rename name; skip them
        # and their own rename commit will pick the line up.
        for other, text in base.items():
            # `other` is a POST-rename path; a file whose own rename has not
            # happened yet is still on disk under its pin path, so try both.
            full = os.path.join(CHECKOUT, other)
            if not os.path.isfile(full) and other in renames:
                full = os.path.join(CHECKOUT, renames[other])
            if not os.path.isfile(full):
                continue
            with open(full, encoding="utf-8") as handle:
                current = handle.read()
            if old_base not in text or current == text:
                continue
            cur_lines, tgt_lines = current.splitlines(), text.splitlines()
            if len(cur_lines) != len(tgt_lines):
                continue                       # not a same-shape comment fix
            merged = [t if old_base in t else c
                      for c, t in zip(cur_lines, tgt_lines)]
            rel = os.path.relpath(full, CHECKOUT)
            write(rel, "\n".join(merged) + "\n")
        run("git", "add", "-A", "soh")
        run("git", "commit", "-q", "-m",
            f"soh: rename {os.path.basename(pin_path)} -> "
            f"{os.path.basename(post_path)}\n\n"
            f"The file was named after its ROM address; name it for what it "
            f"contains.\nPart of the decomp renaming effort -- see "
            f"tasks/reference/ocarina/decomp-renaming.md.")

    # Confirm phase A landed exactly on the base state.
    for post_path, text in base.items():
        actual = open(os.path.join(CHECKOUT, post_path), encoding="utf-8").read()
        if actual != text:
            raise SystemExit(f"phase A drift in {post_path}")
    print("phase A verified: tree == fully-peeled base state")

    # Phase B: one commit per symbol rename.
    for index, row in enumerate(table):
        after = states[index + 1] if index + 1 < len(states) else \
            {p: blob(TARGET, p) for p in paths}
        for path, text in after.items():
            if states[index].get(path) != text:
                write(path, text)
        run("git", "add", "-A", "soh")
        status = run("git", "status", "--porcelain")
        if not status.strip():
            print(f"  WARNING: no change for {row['old']} -> {row['new']}")
            continue
        source = ("zeldaret/oot" if row["provenance"] == "oot"
                  else f"deduced from the code (confidence {row['confidence']})")
        run("git", "commit", "-q", "-m",
            f"soh: rename {row['old']} -> {row['new']}\n\n"
            f"Name source: {source}.\n"
            f"Defined in {row['def_file']}.\n\n"
            f"Provenance comments accompany the definition and every header "
            f"declaration,\nso the name can be re-derived or overturned later. "
            f"See\ntasks/reference/ocarina/decomp-renaming.md.")

    tip = run("git", "rev-parse", "--short", "HEAD").strip()
    count = run("git", "rev-list", "--count", f"{pin}..HEAD").strip()
    print(f"\nrebuilt {count} commits, tip {tip}")


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    main()
