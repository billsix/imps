#!/usr/bin/env python3
"""Find `if (A) { if (B) { if (C) { <stmts> } } }` chains: each `if` is the ONLY statement in
its parent's block and has no else — i.e. a single `&&` chain. Reports depth>=3 and depth==2."""
import os, re, sys
import subprocess
_ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip() + "/"
ROOT = _ROOT + "n64/OcarinaOfTime/Shipwright/soh/src/"
DIRS = ["code", "overlays", "boot", "libultra", "buffers"]
if_re = re.compile(r'^(\s*)if \(.*\) \{\s*$')
res = {2: [], 3: []}
for d in DIRS:
    for dp, _, fns in os.walk(ROOT + d):
        for fn in fns:
            if not fn.endswith(".c"):
                continue
            p = os.path.join(dp, fn)
            src = open(p, encoding="utf-8", errors="replace").read().split("\n")
            n = len(src)
            for i, line in enumerate(src):
                m = if_re.match(line)
                if not m:
                    continue
                ind = m.group(1)
                # chain: next non-blank line must be an `if (...) {` at ind+4, recursively
                depth = 1
                j = i
                cur_ind = ind
                ok = True
                while True:
                    k = j + 1
                    while k < n and src[k].strip() == "":
                        k += 1
                    if k >= n:
                        break
                    m2 = if_re.match(src[k])
                    if not m2 or m2.group(1) != cur_ind + "    ":
                        break
                    # the inner if must be the only statement: find its closing brace at its indent,
                    # then the next non-blank must be the parent's closing `}` (not `} else`)
                    inner_ind = m2.group(1)
                    e = k + 1
                    while e < n and not (src[e].startswith(inner_ind + "}") and not src[e].startswith(inner_ind + " ")):
                        e += 1
                    if e >= n or src[e].strip() != "}":
                        break
                    f = e + 1
                    while f < n and src[f].strip() == "":
                        f += 1
                    if f >= n or src[f].strip() != "}" or not src[f].startswith(cur_ind + "}"):
                        break
                    depth += 1
                    j = k
                    cur_ind = inner_ind
                if depth >= 3:
                    res[3].append((p.replace(ROOT, "soh/src/"), i + 1, depth))
                elif depth == 2:
                    res[2].append((p.replace(ROOT, "soh/src/"), i + 1, depth))
print("## depth>=3 single-statement nested ifs (no else, inner if is the only statement) [%d]" % len(res[3]))
for p, l, d in sorted(res[3]):
    print("%s:%d depth=%d" % (p, l, d))
print("## depth==2 count: %d" % len(res[2]))
for p, l, d in sorted(res[2])[:40]:
    print("%s:%d" % (p, l))
