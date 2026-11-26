#!/usr/bin/env python3
"""Prove that a pure-rename stream changes no code: compare assembly across the renames.

`tools/asmdiff.sh` compiles the old and the new version of a file inside ONE tree, which cannot work
for a rename stream: the old source calls names the new headers no longer declare, and every renamed
symbol shows up as a difference. This tool compiles each side in its OWN worktree (old source with
old headers, new source with new headers), rewrites the old side's assembly with the stream's
`old -> new` rename pairs, and compares.

For every `.c` and `.cpp` file of the game's own tree that differs between the two refs (renamed files are
paired by git's rename detection):

    IDENTICAL   the assembly is the same once the old side's symbols are renamed
    DIFF        it is not; the first lines of the difference are logged
    SKIP        the build does not compile the file (no compile command), or it exists on one side only
    ERROR       a side failed to compile

Only translation units are compiled; an included file (no compile command of its own) is covered
through the units that include it only when those units differ too, so SKIPs must be read.

The build directory is a CONFIGURED cmake tree of the checkout (its `compile_commands.json`), as for
`tools/asmdiff.sh`; nothing is built. The checkout itself is not touched: both sides are compiled in
temporary worktrees that are removed afterwards. Submodule include paths keep pointing at the
checkout, so its submodules must be at the commits the refs expect.

usage:
    asmdiff_across_renames.py --project OcarinaOfTime --build <configured tree> \
        --patches n64/OcarinaOfTime/patches/upstreamable-rename-decomp <ref-before> <ref-after>

Exits 0 when no file is DIFF or ERROR, 3 otherwise.
"""

import argparse
import concurrent.futures
import dataclasses
import json
import pathlib
import re
import shlex
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import resolve_rename_conflicts

REPO_ROOT: pathlib.Path = pathlib.Path(__file__).resolve().parents[1]
NORMALISER: pathlib.Path = REPO_ROOT / "tools" / "asmdiff_normalise.py"
IDENTIFIER: re.Pattern[str] = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")
FILE_RENAME_LINE: re.Pattern[str] = re.compile(
    r"^\s*\*\s+(\S+\.c)\s+->\s+(\S+\.c)\s*$", re.MULTILINE
)
# `-c <source>`: the recorded command names its own source file as -c's value; it is replaced below.
DROPPED_FLAGS_WITH_VALUE: frozenset[str] = frozenset({"-o", "-c", "-MF", "-MT"})
DROPPED_FLAGS: frozenset[str] = frozenset({"-MD"})
SOURCE_SUFFIXES: tuple[str, ...] = (".c", ".cpp")


@dataclasses.dataclass(frozen=True)
class Project:
    """Where a project's checkout lives, and the subtree of it that holds the game's own sources."""

    checkout: pathlib.Path
    checkout_name: str
    tree_prefix: str


PROJECTS: dict[str, Project] = {
    "OcarinaOfTime": Project(
        REPO_ROOT / "n64/OcarinaOfTime/Shipwright", "Shipwright", "soh"
    ),
    "SuperMario64": Project(
        REPO_ROOT / "n64/SuperMario64/Ghostship", "Ghostship", "src"
    ),
}


@dataclasses.dataclass(frozen=True)
class Result:
    """The verdict for one file."""

    status: str
    path: str
    detail: str


def git(checkout: pathlib.Path, *arguments: str) -> str:
    """Run git in a checkout and return its output."""
    return subprocess.run(
        ["git", "-C", str(checkout), *arguments],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def rename_map(patch_directory: pathlib.Path) -> dict[str, str]:
    """The final name of every symbol the stream renames, chains (a -> b, later b -> c) followed."""
    direct: dict[str, str] = {}
    for patch in sorted(patch_directory.glob("*.patch")):
        for old, new in resolve_rename_conflicts.renames_of(patch):
            direct[old] = new
    final: dict[str, str] = {}
    for old in direct:
        name: str = old
        seen: set[str] = set()
        while name in direct and name not in seen:
            seen.add(name)
            name = direct[name]
        final[old] = name
    return final


def file_rename_map(patch_directory: pathlib.Path) -> dict[str, str]:
    """The file renames the stream declares (`  * old.c -> new.c` in a patch body), by base name."""
    renamed: dict[str, str] = {}
    for patch in sorted(patch_directory.glob("*.patch")):
        body: str = patch.read_text(errors="replace").split("\ndiff --git ", 1)[0]
        renamed.update(FILE_RENAME_LINE.findall(body))
    return renamed


def changed_files(
    project: Project, before: str, after: str, file_renames: dict[str, str]
) -> list[tuple[str, str | None, str | None]]:
    """The C and C++ source files that differ, as (label, path before, path after); a side is None when absent.

    Git pairs most renamed files by content. A short file can fall under its similarity threshold and
    show up as one deletion and one addition; those are paired through the stream's declared file
    renames.
    """
    output: str = git(
        project.checkout,
        "diff",
        "--name-status",
        "-M",
        before,
        after,
        "--",
        project.tree_prefix,
    )
    files: list[tuple[str, str | None, str | None]] = []
    for line in output.splitlines():
        fields: list[str] = line.split("\t")
        match fields[0][0]:
            case "M":
                files.append((fields[1], fields[1], fields[1]))
            case "R":
                files.append((fields[2], fields[1], fields[2]))
            case "A":
                files.append((fields[1], None, fields[1]))
            case "D":
                files.append((fields[1], fields[1], None))
            case _:
                files.append((fields[-1], None, None))
    added: dict[str, str] = {
        pathlib.PurePosixPath(path_after).name: path_after
        for _, path_before, path_after in files
        if path_before is None and path_after is not None
    }
    paired: list[tuple[str, str | None, str | None]] = []
    consumed: set[str] = set()
    for label, path_before, path_after in files:
        if path_before is not None and path_after is None:
            new_name: str | None = file_renames.get(
                pathlib.PurePosixPath(path_before).name
            )
            if new_name is not None and new_name in added:
                paired.append((added[new_name], path_before, added[new_name]))
                consumed.add(added[new_name])
                continue
        paired.append((label, path_before, path_after))
    return [
        entry
        for entry in paired
        if entry[0].endswith(SOURCE_SUFFIXES)
        and not (entry[1] is None and entry[2] in consumed)
    ]


def compile_to_assembly(
    command: str,
    directory: str,
    project: Project,
    worktree: pathlib.Path,
    source: str,
    output: pathlib.Path,
) -> str:
    """Compile one file of a worktree to normalised assembly; return the compiler's errors, or ''."""
    main_prefix: str = f"{project.checkout}/{project.tree_prefix}"
    arguments: list[str] = shlex.split(
        command.replace(main_prefix, f"{worktree}/{project.tree_prefix}")
    )
    kept: list[str] = []
    skip_next: bool = False
    for argument in arguments:
        if skip_next:
            skip_next = False
        elif argument in DROPPED_FLAGS_WITH_VALUE:
            skip_next = True
        elif argument not in DROPPED_FLAGS:
            kept.append(argument)
    compiled: subprocess.CompletedProcess[str] = subprocess.run(
        [
            *kept,
            "-D__LINE__=0",
            "-Wno-builtin-macro-redefined",
            "-S",
            "-o",
            str(output),
            "-c",
            str(worktree / source),
        ],
        capture_output=True,
        text=True,
        cwd=directory,
        check=False,
    )
    if compiled.returncode != 0:
        errors: list[str] = [
            line for line in compiled.stderr.splitlines() if "error" in line
        ]
        return "; ".join(errors[:2]) or compiled.stderr[-300:]
    subprocess.run([sys.executable, str(NORMALISER), str(output)], check=True)
    # A path the normaliser does not canonicalise (a C++ file's __FILE__) still names the worktree.
    output.write_text(output.read_text().replace(str(worktree), "WORKTREE"))
    return ""


def compare_one(
    entry: tuple[str, str | None, str | None],
    project: Project,
    commands: dict[str, dict[str, str]],
    renames: dict[str, str],
    worktrees: tuple[pathlib.Path, pathlib.Path],
    scratch: pathlib.Path,
) -> Result:
    """Compile both sides of one file and compare them across the renames."""
    label, path_before, path_after = entry
    if path_before is None or path_after is None:
        return Result("SKIP", label, "exists on one side only")
    recorded: dict[str, str] | None = commands.get(
        f"{project.checkout}/{path_before}"
    ) or commands.get(f"{project.checkout}/{path_after}")
    if recorded is None:
        return Result(
            "SKIP", label, "not compiled (no compile command; an included file?)"
        )
    stem: str = label.replace("/", "__")
    outputs: tuple[pathlib.Path, pathlib.Path] = (
        scratch / f"{stem}.before.s",
        scratch / f"{stem}.after.s",
    )
    for worktree, source, output in zip(
        worktrees, (path_before, path_after), outputs, strict=True
    ):
        error: str = compile_to_assembly(
            recorded["command"],
            recorded["directory"],
            project,
            worktree,
            source,
            output,
        )
        if error:
            return Result("ERROR", label, f"{output.name}: {error[:300]}")
    before_lines: list[str] = [
        IDENTIFIER.sub(lambda found: renames.get(found.group(0), found.group(0)), line)
        for line in outputs[0].read_text().split("\n")
    ]
    after_lines: list[str] = outputs[1].read_text().split("\n")
    if before_lines == after_lines:
        return Result("IDENTICAL", label, "")
    differing: list[str] = [
        f"{old!r} != {new!r}"
        for old, new in zip(before_lines, after_lines, strict=False)
        if old != new
    ]
    length_note: str = (
        ""
        if len(before_lines) == len(after_lines)
        else f" ({len(before_lines)} vs {len(after_lines)} lines)"
    )
    return Result(
        "DIFF",
        label,
        f"{len(differing)} differing line(s){length_note}; first: {differing[:1]}",
    )


def main() -> int:
    """Compare every changed file across the renames and summarise."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description=__doc__.split("\n")[0]
    )
    parser.add_argument("--project", choices=sorted(PROJECTS), required=True)
    parser.add_argument(
        "--build", type=pathlib.Path, required=True, help="configured cmake tree"
    )
    parser.add_argument(
        "--patches",
        type=pathlib.Path,
        required=True,
        help="the rename stream's patch directory",
    )
    parser.add_argument(
        "--log", type=pathlib.Path, default=None, help="write one line per file here"
    )
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("before")
    parser.add_argument("after")
    arguments: argparse.Namespace = parser.parse_args()

    project: Project = PROJECTS[arguments.project]
    renames: dict[str, str] = rename_map(arguments.patches.resolve())
    commands: dict[str, dict[str, str]] = {
        entry["file"]: entry
        for entry in json.loads((arguments.build / "compile_commands.json").read_text())
    }
    files: list[tuple[str, str | None, str | None]] = changed_files(
        project,
        arguments.before,
        arguments.after,
        file_rename_map(arguments.patches.resolve()),
    )
    print(f"{len(renames)} rename pairs, {len(files)} changed source files", flush=True)

    results: list[Result] = []
    with tempfile.TemporaryDirectory(prefix="asmdiff-renames-") as temporary:
        scratch: pathlib.Path = pathlib.Path(temporary)
        # The normaliser recognises source paths by the checkout's directory name, so keep it.
        worktrees: tuple[pathlib.Path, pathlib.Path] = (
            scratch / "before" / project.checkout_name,
            scratch / "after" / project.checkout_name,
        )
        try:
            for worktree, ref in zip(
                worktrees, (arguments.before, arguments.after), strict=True
            ):
                git(project.checkout, "worktree", "add", "--detach", str(worktree), ref)
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=arguments.jobs
            ) as pool:
                results = list(
                    pool.map(
                        lambda entry: compare_one(
                            entry, project, commands, renames, worktrees, scratch
                        ),
                        files,
                    )
                )
        finally:
            for worktree in worktrees:
                subprocess.run(
                    [
                        "git",
                        "-C",
                        str(project.checkout),
                        "worktree",
                        "remove",
                        "--force",
                        str(worktree),
                    ],
                    capture_output=True,
                    check=False,
                )

    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    if arguments.log is not None:
        arguments.log.write_text(
            "".join(f"{r.status} {r.path} {r.detail}\n" for r in results)
        )
    for result in results:
        if result.status in ("DIFF", "ERROR"):
            print(f"{result.status} {result.path}: {result.detail}")
    print(
        f"across renames {arguments.before}..{arguments.after}: {len(results)} files, "
        + ", ".join(
            f"{counts.get(status, 0)} {status.lower()}"
            for status in ("IDENTICAL", "DIFF", "ERROR", "SKIP")
        )
    )
    return 0 if counts.get("DIFF", 0) == 0 and counts.get("ERROR", 0) == 0 else 3


if __name__ == "__main__":
    sys.exit(main())
