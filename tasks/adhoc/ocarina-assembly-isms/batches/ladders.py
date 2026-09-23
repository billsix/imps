#!/usr/bin/env python3
"""Classify the `} else if (X == k)` census: (a) redundant tails after `if (X != k)`,
(b) contiguous ladders over one discriminant with >= 3 constant arms (switch candidates),
with a note on whether X is assigned inside the ladder."""
import re, sys, collections
import subprocess
_ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip() + "/"
ROOT = _ROOT + "n64/OcarinaOfTime/Shipwright/"
LOG = _ROOT + "tasks/adhoc/ocarina-assembly-isms/data/if_else_ladder_num.txt"
hit_re = re.compile(r'^(\s*)\} else if \(([A-Za-z_>.\-\[\]0-9]+) == (-?[0-9A-Fx]+)\) \{')
ne_re = re.compile(r'^(\s*)(?:\} else )?if \(([A-Za-z_>.\-\[\]0-9]+) != (-?[0-9A-Fx]+)\) \{')
first_re = re.compile(r'^(\s*)if \(([A-Za-z_>.\-\[\]0-9]+) == (-?[0-9A-Fx]+)\) \{')
files = collections.defaultdict(list)
for line in open(LOG):
    p, l, _ = line.split(":", 2)
    files[p.replace("../../../n64/OcarinaOfTime/Shipwright/", "")].append(int(l))

redundant = []
ladders = []
for f, lines in sorted(files.items()):
    src = open(ROOT + f, encoding="utf-8", errors="replace").read().split("\n")
    seen = set()
    for l in lines:
        if l in seen:
            continue
        m = hit_re.match(src[l - 1])
        if not m:
            continue
        indent, var, k = m.groups()
        # walk back to the chain head: previous line at same indent starting with `if (` or `} else if (`
        j = l - 2
        head = None
        arms = [(l, var, k)]
        while j >= 0:
            s = src[j]
            if s.startswith(indent) and not s.startswith(indent + " ") and s.strip():
                if s.lstrip().startswith("} else if ("):
                    mm = hit_re.match(s)
                    if mm and mm.group(2) == var:
                        arms.insert(0, (j + 1, mm.group(2), mm.group(3)))
                    else:
                        arms.insert(0, (j + 1, None, s.strip()[:60]))
                elif s.lstrip().startswith("if ("):
                    head = (j + 1, s.strip())
                    break
                elif s.lstrip().startswith("}"):
                    pass
                else:
                    break
            j -= 1
        if head is None:
            continue
        hl, htxt = head
        # (a) redundant tail: head is `if (X != k)` and the hit is the only other arm with the same X,k
        mne = ne_re.match(src[hl - 1])
        if mne and mne.group(2) == var and mne.group(3) == k and len(arms) == 1:
            # is the hit arm the last arm? check next non-blank line after its block close is not `} else`
            redundant.append((f, hl, l, var, k))
        # (b) ladder collection: head `if (X == k0)` plus arms
        mf = first_re.match(src[hl - 1])
        if mf and mf.group(2) == var:
            allarms = [(hl, var, mf.group(3))] + arms
            for (al, _, _) in allarms:
                seen.add(al)
            ks = [a[2] for a in allarms if a[1] == var]
            if len(ks) >= 3 and len(set(ks)) == len(ks) and all(a[1] == var for a in allarms):
                # find end of ladder: first line after last arm at same indent that starts with `}` and not `} else`
                e = allarms[-1][0]
                while e < len(src):
                    s = src[e]
                    if s.startswith(indent) and not s.startswith(indent + " ") and s.lstrip().startswith("}") :
                        if s.lstrip().startswith("} else"):
                            e += 1
                            continue
                        break
                    e += 1
                body = "\n".join(src[hl - 1:e + 1])
                # does any arm assign the discriminant?
                vre = re.escape(var)
                assigns = re.search(r'(?<![A-Za-z_0-9.>])' + vre + r'\s*(=[^=]|\+\+|--|\+=|-=)', body) is not None
                has_else = re.search(r'^' + indent + r'\} else \{', body, re.M) is not None
                ladders.append((f, hl, e + 1, var, len(ks), assigns, has_else))

print("## (a) redundant tails  if (X != k) ... } else if (X == k)   [%d]" % len(redundant))
for f, hl, l, var, k in redundant:
    print("%s:%d..%d  %s != %s / == %s" % (f, hl, l, var, k, k))
print()
print("## (b) ladders over one discriminant, >=3 distinct constant arms  [%d]" % len(ladders))
for f, hl, e, var, n, assigns, has_else in sorted(ladders, key=lambda t: (-t[4], t[0])):
    print("%s:%d-%d  %s  arms=%d  assigns_x=%s  else=%s" % (f, hl, e, var, n, assigns, has_else))
