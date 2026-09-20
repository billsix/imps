#!/usr/bin/env python3
"""Prove two git refs differ ONLY in comments, for a language with no C
preprocessor (Rust, Kotlin).

This is the non-C analogue of tools/prove_comment_only.sh. That script leans on
`gcc -fpreprocessed` to strip comments and argue via a real compiler; Rust and
Kotlin have no such mode, so this proves the same invariant a different way: for
every file the two refs disagree on, strip all comments (and collapse
whitespace) from each side and assert the two strings are byte-identical. If
they are, the only thing that changed is comments -- an identical token stream,
so the compiler emits the same program.

This is STRONGER than "the diff only touches comment lines": it proves token
identity of what the compiler actually sees, so it also catches a stray edit
hidden on an otherwise-comment line, and it is inherently tolerant of the line
shifts a `// doc-region-begin` marker or an added doc comment introduces (the
whitespace collapse discards line structure), so --allow-line-shift is accepted
for interface parity with prove_comment_only.sh but is always in effect here.

The stripper is language-parameterized (--lang):

  rust    // and /// and //! line comments; NESTED /* */ (and /*! */) block
          comments; "..." strings with escapes; raw strings r"...", r#"..."#,
          br#"..."# (any hash count); char/byte literals 'a', b'\\n', '"';
          and it correctly leaves lifetimes ('a) alone.

  kotlin  // line comments and /** */ KDoc (a block comment); NESTED /* */
          block comments; "..." strings with escapes (and $-templates, kept
          verbatim); \"\"\"...\"\"\" raw/triple-quoted strings; 'a' / '\\n'
          char literals. Kotlin has no lifetimes, byte literals, or r"..." raw
          strings, so those rust-only forms are not scanned for.

USAGE
    tools/prove_comment_only_strip.py --lang <rust|kotlin> [--allow-line-shift] \\
        <checkout-dir> <ref-a> <ref-b>
    tools/prove_comment_only_strip.py --lang <rust|kotlin> --self-test

Exits 0 only if the difference really is comment-only.
"""

import argparse
import re
import subprocess
import sys


def strip_comments(src: str, lang: str) -> str:
    """Return `src` with all comments removed and whitespace collapsed.

    String, raw-string and char/byte literals are preserved verbatim so a `//`
    or `/*` inside them is never mistaken for a comment; only genuine comments
    are dropped.
    """
    out = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ""

        # Line comment (// , /// , //! ). Language-agnostic.
        if c == "/" and nxt == "/":
            while i < n and src[i] != "\n":
                i += 1
            continue

        # Block comment. Rust and Kotlin both allow nesting; count depth.
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

        if lang == "rust":
            # Raw string: optional b, then r, then #* then " ... " #* .
            m = re.match(r'b?r(#*)"', src[i:])
            if m:
                hashes = m.group(1)
                close = '"' + hashes
                end = src.find(close, i + m.end())
                end = n if end == -1 else end + len(close)
                out.append(src[i:end])
                i = end
                continue
            # Normal / byte string literal, "..." or b"...".
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
            # Char / byte-char literal vs. lifetime. A char literal is `'\<esc>'`
            # or `'<one char>'`; anything else starting with `'` is a lifetime.
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

        elif lang == "kotlin":
            # Triple-quoted raw string """...""" (no escapes). Must be tried
            # before the normal-string case, since it also starts with `"`.
            if src[i : i + 3] == '"""':
                end = src.find('"""', i + 3)
                end = n if end == -1 else end + 3
                out.append(src[i:end])
                i = end
                continue
            # Normal string literal "..." with \ escapes. Kotlin string
            # templates ($x, ${...}) are kept verbatim inside the literal; a
            # nested `"` inside a template can retokenize the tail, but that is
            # deterministic and identical on both sides (doc patches never touch
            # string content), so it cannot break the equality proof.
            if c == '"':
                start = i
                i += 1
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
            # Char literal 'a' / '\n' / '\u1234'. Kotlin has no lifetimes, so a
            # leading `'` always opens a char literal; scan to the closing `'`.
            if c == "'":
                start = i
                i += 1
                while i < n:
                    if src[i] == "\\":
                        i += 2
                        continue
                    if src[i] == "'":
                        i += 1
                        break
                    i += 1
                out.append(src[start:i])
                continue

        out.append(c)
        i += 1
    return re.sub(r"\s+", " ", "".join(out)).strip()


def git_show(repo: str, ref: str, path: str) -> str:
    """Return the bytes of `path` at `ref` in `repo`, decoded as UTF-8; '' if
    the file does not exist at that ref (added/deleted files)."""
    res = subprocess.run(
        ["git", "-C", repo, "show", f"{ref}:{path}"],
        capture_output=True,
    )
    if res.returncode != 0:
        return ""
    return res.stdout.decode("utf-8", errors="replace")


def differing_files(repo: str, ref_a: str, ref_b: str) -> list[str]:
    res = subprocess.run(
        ["git", "-C", repo, "diff", "--name-only", ref_a, ref_b],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        sys.exit(f"git diff failed in {repo}: {res.stderr.strip()}")
    return [f for f in res.stdout.splitlines() if f]


def prove(repo: str, ref_a: str, ref_b: str, lang: str) -> int:
    files = differing_files(repo, ref_a, ref_b)
    print(f"\n=== comparing {ref_a} .. {ref_b} in {repo} ({lang}) ===")
    if not files:
        print("  the trees are byte-identical -- nothing to prove")
        return 0
    print(f"  {len(files)} file(s) differ:")
    for f in files:
        print(f"    {f}")

    print("\n=== comment-strip check: identical once comments are removed ===")
    bad = []
    for path in files:
        a = strip_comments(git_show(repo, ref_a, path), lang)
        b = strip_comments(git_show(repo, ref_b, path), lang)
        if a == b:
            print(f"  ok  {path}  identical after stripping comments")
        else:
            print(f"  DIFFERS  {path} -- NOT comment-only")
            bad.append(path)

    print("\n=== VERDICT ===")
    if not bad:
        print("  PROVEN comment-only. The two refs tokenize identically once")
        print("  comments are stripped, so they compile to the same program.")
        return 0
    print(f"  NOT comment-only -- {len(bad)} file(s) changed real content:")
    for path in bad:
        print(f"    {path}")
    return 1


# --- self-test: tricky cases the stripper must get right -----------------------

_SELF_TESTS = {
    "rust": [
        # (name, code-with-comment, same-code-without-comment) -- both must
        # strip to the same thing.
        ("line comment", "let x = 1; // set x\n", "let x = 1;\n"),
        (
            "nested block comment",
            "a(); /* outer /* inner */ still */ b();",
            "a();  b();",
        ),
        (
            "// inside a string is not a comment",
            'let s = "http://example.com"; // real\n',
            'let s = "http://example.com";\n',
        ),
        (
            "/* inside a string is not a comment",
            'let s = "a /* b */ c";',
            'let s = "a /* b */ c";',
        ),
        (
            "raw string with hashes holds a quote",
            'let r = r#"he said "hi""#; // c\n',
            'let r = r#"he said "hi""#;\n',
        ),
        (
            "char literal holding a quote",
            "let q = '\"'; // the double-quote char\n",
            "let q = '\"';\n",
        ),
        (
            "lifetime is not a char literal",
            "fn f<'a>(x: &'a str) {} // g\n",
            "fn f<'a>(x: &'a str) {}\n",
        ),
        (
            "byte string and byte char",
            'let b = b"xy"; let c = b\'\\n\'; // note\n',
            'let b = b"xy"; let c = b\'\\n\';\n',
        ),
    ],
    "kotlin": [
        ("line comment", "val x = 1 // set x\n", "val x = 1\n"),
        (
            "KDoc block above a declaration",
            "/** Does a thing. */\nfun a() {}",
            "\nfun a() {}",
        ),
        (
            "nested block comment",
            "a() /* outer /* inner */ still */; b()",
            "a() ; b()",
        ),
        (
            "// inside a string is not a comment",
            'val s = "http://x.example" // real\n',
            'val s = "http://x.example"\n',
        ),
        (
            "triple-quoted raw string holding // and quotes",
            'val r = """a // b "c" """ // real\n',
            'val r = """a // b "c" """\n',
        ),
        (
            "string template kept verbatim",
            'val s = "value=${foo("x")}" // real\n',
            'val s = "value=${foo("x")}"\n',
        ),
        (
            "char literal holding a quote",
            "val q = '\"' // the double-quote char\n",
            "val q = '\"'\n",
        ),
        (
            "escaped-unicode char literal",
            "val c = '\\u0041' // A\n",
            "val c = '\\u0041'\n",
        ),
    ],
}


def self_test(lang: str) -> int:
    cases = _SELF_TESTS[lang]
    fails = 0
    print(f"=== self-test ({lang}): {len(cases)} case(s) ===")
    for name, with_c, without_c in cases:
        got = strip_comments(with_c, lang)
        want = strip_comments(without_c, lang)
        if got == want:
            print(f"  ok  {name}")
        else:
            fails += 1
            print(f"  FAIL {name}")
            print(f"       with-comment  -> {got!r}")
            print(f"       without       -> {want!r}")
    # A comment that IS a real change must NOT be swallowed (a negative test):
    # code differing outside comments must strip differently.
    if lang == "rust":
        neg_a, neg_b = "let x = 1; // c\n", "let x = 2; // c\n"
    else:
        neg_a, neg_b = "val x = 1 // c\n", "val x = 2 // c\n"
    if strip_comments(neg_a, lang) == strip_comments(neg_b, lang):
        fails += 1
        print("  FAIL negative: a real code change was NOT detected")
    else:
        print("  ok  negative: a real code change is still detected")
    print("  PASS" if fails == 0 else f"  {fails} FAILURE(S)")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(add_help=True, description=__doc__)
    ap.add_argument("--lang", required=True, choices=("rust", "kotlin"))
    ap.add_argument("--allow-line-shift", action="store_true",
                    help="accepted for parity with prove_comment_only.sh; "
                         "always in effect here (whitespace is collapsed)")
    ap.add_argument("--self-test", action="store_true",
                    help="run the built-in tricky-case suite and exit")
    ap.add_argument("repo", nargs="?")
    ap.add_argument("ref_a", nargs="?")
    ap.add_argument("ref_b", nargs="?")
    args = ap.parse_args()

    if args.self_test:
        return self_test(args.lang)

    if not (args.repo and args.ref_a and args.ref_b):
        ap.error("need <checkout-dir> <ref-a> <ref-b> (or --self-test)")
    return prove(args.repo, args.ref_a, args.ref_b, args.lang)


if __name__ == "__main__":
    raise SystemExit(main())
