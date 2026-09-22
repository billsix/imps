#!/usr/bin/env bash
# discover.sh — census of "assembly-isms" (mechanically-lifted-from-MIPS idioms) in the Ship of
# Harkinian OoT decomp tree (soh/src/), one log per pattern class under data/. The OoT twin of
# tasks/adhoc/mario64-assembly-isms/discover.sh: same classes (so the two projects' SUMMARY.txt
# compare line for line) plus the zeldaret idioms that SM64 does not have (`if (1) {}`, `temp_`/
# `phi_`/`sp` names, `PAD`/`padding` fillers, `UNK_TYPE`, `! @bug`, block-comment matching notes).
# The logs are the worklog of tasks/ocarina-de-disassemble-ugly-c.md. Paths are relative to the
# repo root; the checkout is expected at n64/OcarinaOfTime/Shipwright (fetch.sh), on the BARE PIN
# (the `personal` rename stream changes names and file names — census the tree the standard-c
# stream is written against). Port-layer C++ (soh/soh/) is excluded on purpose: not decomp output.
#
#   bash tasks/adhoc/ocarina-assembly-isms/discover.sh      # writes data/<class>.txt + data/SUMMARY.txt
set -u
cd "$(dirname "$0")"
DATA=data; mkdir -p "$DATA"
SRC=../../../n64/OcarinaOfTime/Shipwright/soh/src
FILES=$(find "$SRC/code" "$SRC/overlays" "$SRC/boot" "$SRC/libultra" "$SRC/buffers" "$SRC/dmadata" \
        "$SRC/elf_message" -type f \( -name '*.c' -o -name '*.h' \) | sort)

# class NAME REGEX [grep-flags] — one log per class: file:line:text, plus a one-line summary.
: > "$DATA/SUMMARY.txt"
class() {
    local name=$1 re=$2; shift 2
    grep -n -E "$@" "$re" $FILES > "$DATA/$name.txt" 2>/dev/null || true
    printf '%-34s %6d hits %5d files\n' "$name" "$(wc -l < "$DATA/$name.txt")" \
        "$(cut -d: -f1 "$DATA/$name.txt" | sort -u | wc -l)" | tee -a "$DATA/SUMMARY.txt"
}

# --- control flow ---------------------------------------------------------------------------
class goto                 '\bgoto\b'
class labels               '^\s*[A-Za-z_][A-Za-z_0-9]*:\s*(//.*)?$'
class infinite_loop        '\bwhile \(TRUE\)|\bwhile \(1\)|\bwhile \(true\)|\bfor \(;;\)'
class do_while_0           'while \(0\);'
class empty_then           'if \([^)]*\) \{\s*\}'
class if_1                 '\bif \(1\)'
class if_else_ladder_num   '\} else if \([A-Za-z_>.-]+ == -?[0-9A-Fx]+\)'
class single_stmt_nested_if '^\s+if \([^{]*\) \{\s*$'   # coarse: every braced if; the readers grep the nested shape
class matching_comments    -i 'to match|needed to match|fake ?match|required to match|matches|for matching|no-op|regalloc|fake temp'
class avoid_ub             'AVOID_UB|NON_MATCHING|NON_EQUIVALENT|OOT_DEBUG'
class volatile_kw          '\bvolatile\b'

# --- naming residue -------------------------------------------------------------------------
class register_keyword     '\bregister\b'
class stack_named_locals   '\b(sp[0-9A-F]{1,3}|temp_[a-z0-9_]+|phi_[a-z0-9_]+|new_var[0-9]*)\b'
class arg_params           '\barg[0-9]\b'
class unused_macro         '\bUNUSED\b'
class filler_fields        '\b(pad|padding|unk_pad|filler)[A-Za-z_0-9]*\[|\bPAD\b|\bunk_[0-9A-F]{2,4}\b|\bUNK_TYPE[0-9]*\b'
class unk_names            '\b(unk_|D_|func_)[0-9A-Fa-f_]{4,}'

# --- booleans / comparisons -----------------------------------------------------------------
class bool_vs_TRUEFALSE    '(== TRUE|!= FALSE|== FALSE|!= TRUE|== true|== false)\b'
class cmp_zero             '(!= 0|== 0)\b'
class todo_bug_comments    '//! ?@?bug|//!|FAKE|HACK|FIXME'

# --- raw memory / numeric -------------------------------------------------------------------
class rawdata_union        '\brawData\b|\bunk_[0-9A-F]+\[|\basF32\[|\basS32\[|\basU32\['
class bit_masking_16       '& 0xFFFF\b|<< ?16 ?\) ?>> ?16|<< 16 >> 16'
class shift_as_mul         '(<< [1-5]\b|>> [1-5]\b)'
class byte_pointers        '\(u8 \*\)|\(s8 \*\)|\(uintptr_t\)|\(u32\) ?&'
class angle_constants      '0x[0-9A-F]{4}\b'
class hex_magic            '\b0x[0-9A-Fa-f]{2,8}\b'
class cast_s16             '\(s16\)'
class cast_s32             '\(s32\)'
class cast_f32             '\(f32\)'
class double_literals      '[^A-Za-z_0-9.][0-9]+\.[0-9]*([^0-9fF.eE]|$)'
class div_const            '/ [0-9]+\.[0-9]*f?\b'
class binang_deg           'BINANG|DEG_TO_BINANG|BINANG_TO_DEG'
