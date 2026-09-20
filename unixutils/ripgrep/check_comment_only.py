#!/usr/bin/env python3
"""Prove that a patch stream changes only comments.

Rust has no C preprocessor, so the `-fpreprocessed` trick that
`../tools/check_comment_only_streams.sh` uses for C does not apply here. This is
the Rust analogue: for every file the stream touches, strip all comments (and
collapse whitespace) from the pinned upstream version and from the
stream-applied working-tree version, and assert the two are byte-identical. If
they are, the only thing the stream changed is comments.

The stripper is Rust-aware: it skips line comments (`//`, `///`, `//!`), nested
block comments (`/* ... */`, `/*! ... */`), string literals (with escapes), raw
strings (`r"..."`, `r#"..."#`, `br#"..."#`, any hash count) and char/byte
literals (`'a'`, `b'\\n'`, `'"'`), and correctly leaves lifetimes (`'a`) alone.

Usage:
    check_comment_only.py <pin-sha> <file> [<file> ...]

Each <file> is a repo-relative path inside the checkout; the script must be run
from the checkout root. Exits non-zero (naming the offender) if any file's
non-comment content differs from the pin.
"""

import re
import subprocess
import sys


def strip_comments(src: str) -> str:
    """Return `src` with all comments removed and whitespace collapsed."""
    out = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        # Line comment.
        if c == "/" and nxt == "/":
            while i < n and src[i] != "\n":
                i += 1
            continue
        # Block comment (Rust allows nesting).
        if c == "/" and nxt == "*":
            depth = 1
            i += 2
            while i < n and depth > 0:
                if src[i] == "/" and i + 1 < n and src[i + 1] == "*":
                    depth += 1
                    i += 2
                elif src[i] == "*" and i + 1 < n and src[i + 1] == "/":
                    depth -= 1
                    i += 2
                else:
                    i += 1
            continue
        # Raw string: optional b, then r, then #* then ".
        m = re.match(r'b?r(#*)"', src[i:])
        if m:
            hashes = m.group(1)
            close = '"' + hashes
            end = src.find(close, i + m.end())
            end = n if end == -1 else end + len(close)
            out.append(src[i:end])
            i = end
            continue
        # Normal / byte string literal.
        if c == '"' or (c == "b" and nxt == '"'):
            start = i
            i += 2 if c == "b" else 1
            while i < n:
                if src[i] == "\\":
                    i += 2
                    continue
                if src[i] == '"':
                    i += 1
                    break
                i += 1
            out.append(src[start:i])
            continue
        # Char / byte-char literal vs. lifetime. A char literal is `'\<esc>'` or
        # `'<one char>'`; anything else starting with `'` is a lifetime.
        if c == "'" or (c == "b" and nxt == "'"):
            q = i + 1 if c == "b" else i
            after = src[q + 1 : q + 2]
            if after == "\\":
                end = src.find("'", q + 2)
                if end != -1:
                    out.append(src[i : end + 1])
                    i = end + 1
                    continue
            elif src[q + 2 : q + 3] == "'":
                out.append(src[i : q + 3])
                i = q + 3
                continue
            # Lifetime: emit the leading char(s) verbatim and move on.
            out.append(src[i : q + 1])
            i = q + 1
            continue
        out.append(c)
        i += 1
    return re.sub(r"\s+", " ", "".join(out)).strip()


def pin_blob(pin: str, path: str) -> str:
    res = subprocess.run(
        ["git", "show", f"{pin}:{path}"], capture_output=True, text=True
    )
    if res.returncode != 0:
        sys.exit(f"cannot read {path} at pin {pin}: {res.stderr.strip()}")
    return res.stdout


def main() -> int:
    if len(sys.argv) < 3:
        sys.exit("usage: check_comment_only.py <pin-sha> <file> [<file> ...]")
    pin, files = sys.argv[1], sys.argv[2:]
    bad = []
    for path in files:
        try:
            with open(path, encoding="utf-8") as fh:
                cur = fh.read()
        except OSError as err:
            sys.exit(f"cannot read working-tree {path}: {err}")
        if strip_comments(pin_blob(pin, path)) != strip_comments(cur):
            bad.append(path)
            print(f"NOT comment-only: {path}", file=sys.stderr)
        else:
            print(f"comment-only OK:  {path}")
    if bad:
        print(f"\nFAIL: {len(bad)} file(s) changed non-comment content.")
        return 1
    print(f"\nOK: all {len(files)} file(s) differ from the pin only in comments.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
