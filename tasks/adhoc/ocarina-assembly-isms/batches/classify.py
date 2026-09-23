#!/usr/bin/env python3
"""Read-only classifier over soh/src decomp files.

Modes (argv[1]):
  pads     - every `pad*`/`padding*`/`filler*` declaration: function-local vs struct member,
             and whether the name is referenced again inside the enclosing function.
  deadinit - every function-local `type name = <expr>;` whose name never appears again in the
             function; flags those whose initialiser contains a call `(`.
  slots    - functions ranked by number of sp<hex>/temp_/phi_/new_var declarations.
"""
import os
import re
import sys
from collections import Counter, defaultdict
import subprocess
_ROOT = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip() + "/"

SRC = _ROOT + "n64/OcarinaOfTime/Shipwright/soh/src"
DIRS = ["code", "overlays", "boot", "libultra", "buffers"]

FUNC_OPEN = re.compile(r"^[A-Za-z_][A-Za-z_0-9 \*]*[\s\*]([A-Za-z_][A-Za-z_0-9]*)\s*\([^;]*\)\s*\{\s*$")
FUNC_OPEN2 = re.compile(r"^([A-Za-z_][A-Za-z_0-9]*)\s*\(")  # continuation lines "void f(\n...) {" handled loosely
STRUCT_OPEN = re.compile(r"^(typedef\s+)?(struct|union)\b[^;]*\{\s*$")
STRUCT_CLOSE = re.compile(r"^\}\s*[A-Za-z_0-9]*\s*;")
FUNC_CLOSE = re.compile(r"^\}\s*$")

PAD_DECL = re.compile(
    r"^\s+(?:UNUSED\s+)?(?:static\s+)?(?:const\s+)?(?:volatile\s+)?"
    r"(?:struct\s+)?[A-Za-z_][A-Za-z_0-9]*\s+\**((?:pad|padding|unk_pad|filler)[A-Za-z_0-9]*)"
    r"((?:\[[^\]]*\])*)\s*;\s*(//.*)?$"
)
LOCAL_INIT = re.compile(
    r"^\s+(?:UNUSED\s+)?(?:static\s+)?(?:const\s+)?(?:struct\s+)?"
    r"[A-Za-z_][A-Za-z_0-9]*\s+\**([A-Za-z_][A-Za-z_0-9]*)\s*=\s*([^;]+);\s*(//.*)?$"
)
SLOT_DECL = re.compile(
    r"^\s+(?:static\s+)?(?:const\s+)?(?:struct\s+)?[A-Za-z_][A-Za-z_0-9]*\s+\**"
    r"((?:sp[0-9A-F]{1,3}|temp_[a-z0-9_]+|phi_[a-z0-9_]+|new_var[0-9]*))\b\s*(?:\[[^\]]*\])?\s*(?:=|;|,)"
)


def files():
    for d in DIRS:
        for root, _, names in os.walk(os.path.join(SRC, d)):
            for n in sorted(names):
                if n.endswith((".c", ".h")):
                    yield os.path.join(root, n)


def rel(p):
    return "soh/src/" + os.path.relpath(p, SRC)


def functions(lines):
    """Yield (name, start_idx, end_idx) for column-0 function definitions."""
    i = 0
    n = len(lines)
    while i < n:
        m = FUNC_OPEN.match(lines[i])
        if not m:
            # multi-line signature: "ret name(args,\n   more) {"
            if re.match(r"^[A-Za-z_][A-Za-z_0-9 \*]*[\s\*][A-Za-z_][A-Za-z_0-9]*\s*\([^;{]*$", lines[i]):
                j = i
                while j < n and not lines[j].rstrip().endswith("{") and not lines[j].rstrip().endswith(";"):
                    j += 1
                if j < n and lines[j].rstrip().endswith("{"):
                    name = re.search(r"([A-Za-z_][A-Za-z_0-9]*)\s*\(", lines[i]).group(1)
                    k = j + 1
                    while k < n and not FUNC_CLOSE.match(lines[k]):
                        k += 1
                    yield name, i, k
                    i = k + 1
                    continue
            i += 1
            continue
        name = m.group(1)
        k = i + 1
        while k < n and not FUNC_CLOSE.match(lines[k]):
            k += 1
        yield name, i, k
        i = k + 1


def in_struct_spans(lines):
    spans = []
    i = 0
    while i < len(lines):
        if STRUCT_OPEN.match(lines[i]) or re.match(r"^\s+(typedef\s+)?(struct|union)\b[^;]*\{\s*$", lines[i]):
            j = i + 1
            depth = 1
            while j < len(lines) and depth > 0:
                depth += lines[j].count("{") - lines[j].count("}")
                j += 1
            spans.append((i, j))
            i = j
        else:
            i += 1
    return spans


def word_uses(body_lines, name):
    pat = re.compile(r"\b%s\b" % re.escape(name))
    cnt = 0
    for ln in body_lines:
        code = ln.split("//")[0]
        cnt += len(pat.findall(code))
    return cnt


def mode_pads():
    local_unref, local_ref, struct_member, other = [], [], [], []
    for p in files():
        lines = open(p, errors="replace").read().split("\n")
        funcs = list(functions(lines))
        sspans = in_struct_spans(lines)
        for idx, ln in enumerate(lines):
            m = PAD_DECL.match(ln)
            if not m:
                continue
            name = m.group(1)
            f = next(((nm, s, e) for nm, s, e in funcs if s < idx < e), None)
            st = any(s <= idx < e for s, e in sspans)
            entry = (rel(p), idx + 1, ln.strip(), f[0] if f else "-")
            if f and not st:
                body = lines[f[1] + 1 : f[2]]
                uses = word_uses(body, name)
                if uses <= 1:
                    local_unref.append(entry)
                else:
                    local_ref.append(entry + (uses,))
            elif st:
                struct_member.append(entry)
            else:
                other.append(entry)
    print("FUNCTION-LOCAL, never referenced again: %d" % len(local_unref))
    print("FUNCTION-LOCAL, REFERENCED (unsafe to delete): %d" % len(local_ref))
    for e in local_ref:
        print("  REF", *e)
    print("STRUCT MEMBER (in .c/.h struct body): %d" % len(struct_member))
    print("OTHER (file scope / unclassified): %d" % len(other))
    for e in other[:40]:
        print("  OTHER", *e)
    print("--- per-dir (function-local unref) ---")
    c = Counter(e[0].split("/")[2] for e in local_unref)
    for k, v in c.most_common():
        print("  %6d %s" % (v, k))
    print("--- hot files (function-local unref) ---")
    c = Counter(e[0] for e in local_unref)
    for k, v in c.most_common(25):
        print("  %6d %s" % (v, k))
    print("--- shapes (function-local unref) ---")
    c = Counter(re.sub(r"\s+", " ", e[2]) for e in local_unref)
    for k, v in c.most_common(30):
        print("  %6d %s" % (v, k))
    print("--- struct-member files ---")
    c = Counter(e[0] for e in struct_member)
    for k, v in c.most_common(40):
        print("  %6d %s" % (v, k))
    with open(os.path.join(os.path.dirname(__file__), "pads_local_unref.txt"), "w") as fh:
        for e in local_unref:
            fh.write("%s:%d:%s [%s]\n" % e)
    with open(os.path.join(os.path.dirname(__file__), "pads_struct.txt"), "w") as fh:
        for e in struct_member:
            fh.write("%s:%d:%s\n" % e[:3])


def mode_deadinit():
    hits = []
    for p in files():
        if not p.endswith(".c"):
            continue
        lines = open(p, errors="replace").read().split("\n")
        for name, s, e in functions(lines):
            body = lines[s + 1 : e]
            for k, ln in enumerate(body):
                m = LOCAL_INIT.match(ln)
                if not m:
                    continue
                var, init = m.group(1), m.group(2)
                # only declaration-shaped lines: first token must be a type, not an lvalue like this->x
                if "->" in ln.split("=")[0] or "." in ln.split("=")[0]:
                    continue
                if var in ("pad", "padding") or var.startswith("pad"):
                    pass
                rest = body[k + 1 :] + body[:k]
                if word_uses(rest, var) == 0:
                    call = "(" in init
                    hits.append((rel(p), s + 1 + k + 1, ln.strip(), name, call))
    print("dead-after-init locals: %d (with call initialiser: %d)" % (len(hits), sum(1 for h in hits if h[4])))
    for h in hits:
        if h[4]:
            print("  CALL", h[0], h[1], h[2], "[in %s]" % h[3])
    print("--- non-call examples (first 40) ---")
    for h in [h for h in hits if not h[4]][:40]:
        print("  ", h[0], h[1], h[2], "[in %s]" % h[3])


def mode_slots():
    per_func = []
    per_dir = Counter()
    per_file = Counter()
    tp = defaultdict(list)
    for p in files():
        lines = open(p, errors="replace").read().split("\n")
        for name, s, e in functions(lines):
            body = lines[s + 1 : e]
            decls = [(s + 2 + k, SLOT_DECL.match(ln).group(1)) for k, ln in enumerate(body) if SLOT_DECL.match(ln)]
            if decls:
                per_func.append((len(decls), rel(p), s + 1, name, decls))
                per_dir[rel(p).split("/")[2]] += len(decls)
                per_file[rel(p)] += len(decls)
                for lineno, v in decls:
                    if v.startswith(("temp_", "phi_", "new_var")):
                        tp[rel(p)].append((lineno, v, name))
    print("functions with slot-named declarations: %d; declarations: %d" % (len(per_func), sum(x[0] for x in per_func)))
    print("--- per dir ---")
    for k, v in per_dir.most_common():
        print("  %6d %s" % (v, k))
    print("--- hot files (declaration count) ---")
    for k, v in per_file.most_common(30):
        print("  %6d %s" % (v, k))
    print("--- top functions ---")
    for n, f, ln, name, decls in sorted(per_func, reverse=True)[:60]:
        print("  %3d %s:%d %s  %s" % (n, f, ln, name, " ".join(v for _, v in decls)[:120]))
    print("--- temp_/phi_/new_var declarations per file ---")
    for f, lst in sorted(tp.items(), key=lambda kv: -len(kv[1]))[:25]:
        print("  %4d %s" % (len(lst), f))
    with open(os.path.join(os.path.dirname(__file__), "slot_funcs.txt"), "w") as fh:
        for n, f, ln, name, decls in sorted(per_func, reverse=True):
            fh.write("%3d %s:%d %s %s\n" % (n, f, ln, name, " ".join("%d:%s" % d for d in decls)))


LOCAL_DECL = re.compile(
    r"^\s+(?:static\s+)?(?:const\s+)?(?:struct\s+)?[A-Za-z_][A-Za-z_0-9]*\s+\**([A-Za-z_][A-Za-z_0-9]*)\s*;\s*(//.*)?$"
)


def mode_deadassign():
    """Locals declared without initialiser whose every later reference is a plain assignment
    statement `name = <expr>;` where <expr> contains a call — value never read (class-5 trap)."""
    hits = []
    for p in files():
        if not p.endswith(".c"):
            continue
        lines = open(p, errors="replace").read().split("\n")
        for name, s, e in functions(lines):
            body = lines[s + 1 : e]
            for k, ln in enumerate(body):
                m = LOCAL_DECL.match(ln)
                if not m:
                    continue
                var = m.group(1)
                if var in ("pad", "padding") or var.startswith("pad") or "->" in ln or "(" in ln:
                    continue
                pat = re.compile(r"\b%s\b" % re.escape(var))
                refs = [(j, l2) for j, l2 in enumerate(body) if j != k and pat.search(l2.split("//")[0])]
                if not refs:
                    continue
                assign = re.compile(r"^\s*%s\s*=\s*[^=].*\(.*\)\s*;\s*(//.*)?$" % re.escape(var))
                if all(assign.match(l2) for _, l2 in refs):
                    hits.append((rel(p), s + 1 + k + 1, ln.strip(), name, [(s + 2 + j, l2.strip()) for j, l2 in refs]))
    print("locals assigned only from call expressions and never read: %d" % len(hits))
    for h in hits:
        print("  %s:%d %s [in %s]" % (h[0], h[1], h[2], h[3]))
        for lineno, l2 in h[4][:3]:
            print("      %d| %s" % (lineno, l2[:140]))


if __name__ == "__main__":
    {"pads": mode_pads, "deadinit": mode_deadinit, "slots": mode_slots, "deadassign": mode_deadassign}[sys.argv[1]]()
