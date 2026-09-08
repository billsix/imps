#!/usr/bin/env python3
"""Squash the one-rename-per-commit series into one commit per definition file.

WHY
    One rename per commit was the right way to PRODUCE the work -- it isolates
    variables, so a breakage localises to a single symbol.  It is the wrong
    grain to REVIEW: nobody wants to read thirty consecutive commits renaming
    thirty entries of one function-pointer array.  This regroups the history
    into units a human would read and merge -- one per DEFINITION file, each
    still carrying the whole cross-file rename -- WITHOUT losing any of the
    per-symbol reasoning the original messages carry.

HOW IT IS SAFE
    Units are runs of CONSECUTIVE commits sharing a definition file, and each
    unit's commit is built with `git read-tree --reset -u <last sha of unit>`.
    That sets the tree to an exact tree that already exists in history -- no
    patch is applied, so there is nothing to conflict and the final tree is
    byte-identical to the pre-squash tip by construction.  The script asserts
    that at the end (`git diff <backup> HEAD` must be empty).

    `runDir/` is a sibling of the checkout, so no git operation here can reach
    it.  Commit signing is off repo-locally (see fetch.sh); passed again here.

USAGE (from the imps repo root)
    tools/squash_series.py [<Project>] [--dry-run]

    <Project> is a directory under n64/ (default: OcarinaOfTime). Its checkout
    must carry a `squash-backup` branch marking the unsquashed tip -- make it
    yourself first, and never write to it; it is the undo.

    Read tasks/reference/imps/squashing-a-produced-series-for-review.md before
    using this. That is the method; this is only the mechanism.

Re-runnable: it rebuilds the work branch from the pin every time, so a second
run reproduces the same history rather than stacking onto the first.
"""
import os
import re
import subprocess
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))

# Every n64 project has the same shape -- a fetch.sh holding the pin and one
# upstream checkout beside it -- so the project name is the only per-project
# fact this needs. Pass another on the command line to squash its series.
PROJECT = "OcarinaOfTime"


def project_dir():
    return os.path.join(ROOT, "n64", PROJECT)


def checkout_dir():
    """The upstream checkout: the one directory beside fetch.sh that is a repo."""
    base = project_dir()
    for name in sorted(os.listdir(base)):
        if os.path.isdir(os.path.join(base, name, ".git")):
            return os.path.join(base, name)
    raise SystemExit(f"no checkout under {base} -- run its fetch.sh first")

BACKUP = "squash-backup"      # the undo; never written after it is made
WORK = "squash-rebuild"       # the regrouped history
MARKERS = ("LLM generated name", "Name from zeldaret/oot")
# Attribution only. The session URL Claude Code appends by default is
# deliberately omitted: it is useless to any reader of this repo and leaks a
# session identifier into a series meant for upstream (Bill, 2026-09-08).
TRAILER = "Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"


def git(*args, check=True, **kw):
    r = subprocess.run(("git", "-C", checkout_dir()) + args,
                       capture_output=True, text=True, **kw)
    if check and r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed:\n{r.stderr}")
    return r.stdout


def pin_sha():
    """The pinned upstream base -- fetch.sh is the single source of truth."""
    text = open(os.path.join(project_dir(), "fetch.sh"),
                encoding="utf-8").read()
    return re.search(r"PIN_SHA=([0-9a-f]{40})", text).group(1)


# --------------------------------------------------------------------------
# reading the series
# --------------------------------------------------------------------------

def read_series(pin):
    """Every commit since the pin: sha, subject, message, and the file its
    provenance marker landed in (the symbol's definition site).

    Reads BACKUP, never HEAD. The unsquashed series is the source of truth for
    the per-symbol reasoning, and after one successful run HEAD is already the
    squashed output -- reading it would re-squash the squash into 488 units of
    one, silently (caught 2026-09-08 while re-running to fix commit wording).
    """
    raw = git("log", "--reverse", "--format=%x00%H%x01%B%x02", "-p",
              "--no-renames", f"{pin}..{BACKUP}")
    commits = []
    for chunk in raw.split("\x00")[1:]:
        head, rest = chunk.split("\x02", 1)
        sha, message = head.split("\x01", 1)
        path, marker_file, adds = None, None, {}
        for line in rest.splitlines():
            if line.startswith("+++ b/"):
                path = line[6:]
            elif line.startswith("+") and not line.startswith("+++") and path:
                adds[path] = adds.get(path, 0) + 1
                if marker_file is None and any(m in line for m in MARKERS):
                    marker_file = path
        if marker_file is None:
            source = [p for p in adds if p.endswith((".c", ".inc"))]
            marker_file = (max(source, key=lambda p: adds[p]) if source else
                           max(adds, key=lambda p: adds[p]) if adds else "?")
        subject = message.strip().splitlines()[0]
        # the 18 file renames are one idea, so they share a key of their own
        old = subject.split()[2] if subject.startswith("soh: rename ") else ""
        commits.append({"sha": sha, "subject": subject,
                        "message": message.strip("\n"),
                        "file": "@file-renames" if old.endswith(".c")
                                else marker_file})
    return commits


def group(commits):
    """Runs of consecutive commits sharing a definition file."""
    units, run = [], []
    for c in commits:
        if run and run[-1]["file"] != c["file"]:
            units.append(run)
            run = []
        run.append(c)
    if run:
        units.append(run)
    return units


# --------------------------------------------------------------------------
# composing the squashed message
# --------------------------------------------------------------------------

PREAMBLE = """\
SoH carries the Ocarina of Time decomp, in which several thousand symbols are
still named after their ROM address. This commit names every such symbol DEFINED
IN ONE FILE, so the work can be reviewed a file at a time.

The file names the unit; it does not bound it. Each rename is applied wherever
the symbol occurs -- the declaration in the header, the definition, and every
call site -- so this commit reaches into whatever other files use these symbols
and leaves no dangling reference. It is a pure rename: no behaviour changes, and
the only edits that are not renames are the provenance comments described below.

Two name sources are used, and every name says which it came from:

  * zeldaret/oot -- SoH's decomp IS zeldaret/oot at the same ROM addresses, so
    where oot has already named a symbol, that name is adopted verbatim. The
    definition gets a "Name from zeldaret/oot" comment and every declaration a
    short "// was <addr> [oot]" tag.

  * DEDUCED -- oot leaves a great many symbols address-named too, so those
    names are inferred from the body and its callers, and are marked as OURS
    rather than passed off as upstream. The definition gets
    "LLM generated name (HIGH|GUESS), was <addr>: <reason>" and the short tag
    reads "[LLM:HIGH]" or "[LLM:GUESS]". A GUESS is tagged at every call site
    as well, not only the declaration, so a reader who meets the name anywhere
    knows it is inferred. "git grep '[LLM:'" lists every place the decomp
    leans on an inference.

The justification recorded for each individual name follows, one entry per
symbol, in the order the renames were made. Nothing is summarised away: these
are the per-commit reasons from the unsquashed history, with the boilerplate
that was identical in every one of them hoisted into the text above."""

FILE_RENAME_PREAMBLE = """\
Eighteen files in soh/src/code/ were named after the ROM address of their first
function rather than after what they contain. Each is renamed to its subject,
cross-checked against zeldaret/oot's own layout. Content is untouched; only the
paths and the #include lines that reach them change."""

SOURCE_RE = re.compile(r"^Name source: (.*)$", re.M)
REASON_RE = re.compile(r"^Reason: (.*?)(?=\n[A-Z]|\nTagged|\nProvenance|\Z)",
                       re.M | re.S)
VERIFIED_RE = re.compile(r"^(?:Structure|Body) verified against upstream at "
                         r"([0-9.]+)\.$", re.M)


def entry(commit):
    """One symbol's block: what it was, what it became, and why."""
    message = commit["message"]
    match = re.match(r"soh: rename (\S+) -> (\S+)$", commit["subject"])
    if not match:                       # not a rename -- keep it whole
        return textwrap.indent(message, "    ")
    old, new = match.groups()

    source = SOURCE_RE.search(message)
    source = source.group(1).rstrip(".") if source else "unrecorded"
    if "DEDUCED" in source or "deduced" in source:
        confidence = "GUESS" if "GUESS" in source else "HIGH"
        lead = f"deduced, confidence {confidence}"
    else:
        lead = "zeldaret/oot (same decomp, same ROM address)"
        verified = VERIFIED_RE.search(message)
        if verified:
            kind = "structure" if "Structure" in verified.group(0) else "body"
            lead += f"; {kind} verified against upstream at {verified.group(1)}"

    reason = REASON_RE.search(message)
    reason = " ".join(reason.group(1).split()) if reason else ""
    text = f"{lead}: {reason}" if reason else lead
    # Never split a word: breaking on a hyphen would turn "joint-sphere" into
    # "joint- sphere" across a newline, which silently alters a recorded reason
    # (caught by check_lossless on 2026-09-08 -- 12 reasons, all hyphenated).
    body = textwrap.fill(text, width=76,
                         initial_indent="    ", subsequent_indent="    ",
                         break_long_words=False, break_on_hyphens=False)
    return f"  * {old} -> {new}\n{body}"


def compose(unit):
    """The whole message for one squashed unit."""
    if len(unit) == 1 and unit[0]["file"] != "@file-renames":
        # A file with a single rename is already a reviewable unit, and its
        # original message is already written for a reader. Keep it verbatim
        # rather than wrapping one symbol in a page of preamble.
        return f"{unit[0]['message'].strip()}\n\n{TRAILER}\n"
    if unit[0]["file"] == "@file-renames":
        subject = (f"soh: rename {len(unit)} address-named source files "
                   f"to what they contain")
        preamble = FILE_RENAME_PREAMBLE
        entries = "\n\n".join(f"  * {c['subject'][len('soh: rename '):]}"
                              for c in unit)
    else:
        name = os.path.basename(unit[0]["file"])
        subject = (f"soh: name the {len(unit)} address-named symbols "
                   f"defined in {name}")
        assert len(unit) > 1
        touched = git("diff", "--name-only",
                      f"{unit[0]['sha']}~1", unit[-1]['sha']).split()
        reach = (f"All {len(unit)} are defined in {unit[0]['file']}"
                 + (f"; updating their references touches {len(touched)} files "
                    f"in total." if len(touched) > 1 else "."))
        preamble = PREAMBLE + f"\n\n{reach}"
        entries = "\n\n".join(entry(c) for c in unit)
    return f"{subject}\n\n{preamble}\n\n{entries}\n\n{TRAILER}\n"


# --------------------------------------------------------------------------
# rebuilding the history
# --------------------------------------------------------------------------

def rebuild(units, pin, dry_run):
    if dry_run:
        return
    author = git("log", "-1", "--format=%an <%ae>", BACKUP).strip()
    if len(units) < 2:
        raise SystemExit(f"only {len(units)} unit(s) -- {BACKUP} does not look "
                         f"like the unsquashed series; refusing to rewrite")
    git("checkout", "-q", "-B", WORK, pin)
    msg_path = os.path.join(checkout_dir(), ".git", "SQUASH_UNIT_MSG")
    for index, unit in enumerate(units, 1):
        # Set the tree to one that already exists in history: no patch is
        # applied, so nothing can conflict and nothing can be dropped.
        git("read-tree", "--reset", "-u", unit[-1]["sha"])
        with open(msg_path, "w", encoding="utf-8") as handle:
            handle.write(compose(unit))
        git("-c", "commit.gpgsign=false", "commit", "-q", "--no-verify",
            f"--author={author}", "-F", msg_path)
        if index % 50 == 0 or index == len(units):
            print(f"  {index}/{len(units)} units committed", flush=True)
    os.remove(msg_path)


def check_lossless(units):
    """Every reason recorded in an original message must survive the squash.

    This is the guard on the maintainer's one hard requirement: the reasoning
    is the point, so a regrouping that quietly drops a justification is a
    failed regrouping, not a tidy one.
    """
    missing = []
    for unit in units:
        text = compose(unit)
        for commit in unit:
            found = REASON_RE.search(commit["message"])
            if not found:
                continue
            words = " ".join(found.group(1).split())
            if " ".join(words.split()) not in " ".join(text.split()):
                missing.append(f"{commit['sha'][:9]} {commit['subject']}")
    if missing:
        for item in missing[:20]:
            print(f"  LOST REASON: {item}")
        raise SystemExit(f"{len(missing)} reasons would be lost -- refusing")
    print("OK  every recorded reason survives into its squashed unit")


def main(argv):
    global PROJECT
    dry_run = "--dry-run" in argv
    named = [a for a in argv[1:] if not a.startswith("--")]
    if named:
        PROJECT = named[0]
    pin = pin_sha()
    if git("rev-parse", "--verify", "-q", BACKUP, check=False).strip() == "":
        raise SystemExit(f"{BACKUP} does not exist -- make it before rewriting")

    commits = read_series(pin)
    units = group(commits)
    check_lossless(units)
    print(f"pin      : {pin}")
    print(f"commits  : {len(commits)}")
    print(f"units    : {len(units)}")
    print(f"singleton: {sum(1 for u in units if len(u) == 1)}")
    print(f"largest  : {sorted((len(u) for u in units), reverse=True)[:8]}")
    if dry_run:
        print("\n--- sample message (largest unit) ---")
        print(compose(max(units, key=len))[:2400])
        return 0

    rebuild(units, pin, dry_run)

    # The proof: history changed, content did not.
    diff = git("diff", BACKUP, WORK)
    if diff.strip():
        raise SystemExit("TREE DIFFERS from the backup -- something was "
                         "dropped; investigate before going further")
    print(f"\nOK  git diff {BACKUP} {WORK} is empty -- trees are identical")
    print(f"OK  {len(commits)} commits regrouped into {len(units)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
