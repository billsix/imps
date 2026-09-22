#!/usr/bin/env python3
"""Insert a progress-log entry before `## Notes / decisions` in a task doc.
usage: update_progress.py <task.md> <entry-file>   (the old form `<imps-root> <entry-file>` still
targets the mario64 task, for the scripts that call it that way)"""
import sys
from pathlib import Path

target: Path = Path(sys.argv[1])
if target.is_dir():
    target = target / "tasks/mario64-assembly-isms-to-standard-c.md"
entry: str = Path(sys.argv[2]).read_text().rstrip("\n")
s: str = target.read_text()
marker: str = "\n## Notes / decisions\n"
assert s.count(marker) == 1, f"{target}: expected one '## Notes / decisions' heading"
s = s.replace(marker, "\n" + entry + "\n" + marker)
target.write_text(s)
print(f"progress entry added to {target}")
