#!/usr/bin/env python3
"""Report rename progress against the PLANNED denominator.

Planned scope = the 4,235 address-named symbols censused at the start of the
deduction task, minus the sets we decided not to attempt:
  720  the three huge files (z_player.c, z_en_zl3.c, z_en_zl2.c)
    5  segmented asset addresses (D_0x..., not RAM)
    1  code_800FBCE0.c (RCP)
=> 3,509 planned.

Renamed = the number of symbol-rename commits on the patch series, which
check_renames.py already verifies is one rename per commit.

Run from the imps repo root.
"""
import subprocess

TOTAL = 4235
EXCLUDED = 720 + 5 + 1
PLANNED = TOTAL - EXCLUDED

out = subprocess.run(
    ["python3", "tools/check_renames.py", "series"],
    cwd="n64/OcarinaOfTime", capture_output=True, text=True).stdout
renamed = int(next(l for l in out.splitlines()
                   if "symbol-rename commits" in l).split(":")[1])

print(f"renamed            : {renamed}")
print(f"planned scope      : {PLANNED} (of {TOTAL} total; {EXCLUDED} excluded by decision)")
print(f"progress (planned) : {100 * renamed / PLANNED:.1f}%")
print(f"progress (all)     : {100 * renamed / TOTAL:.1f}%")
