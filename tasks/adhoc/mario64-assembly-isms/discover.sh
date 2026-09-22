#!/usr/bin/env bash
# discover.sh — census of "assembly-isms" (mechanically-lifted-from-MIPS idioms) in the Ghostship
# (Super Mario 64 decomp + port) tree, one log per pattern class under data/. The logs are the
# worklog of tasks/mario64-assembly-isms-to-standard-c.md; the catalogue in the task and the
# patterns reference doc (tasks/reference/mario64/assembly-isms-in-the-decomp.md) were written from
# them. Re-run after a pin bump to see what moved. Paths are relative to the repo root; the
# checkout is expected at n64/SuperMario64/Ghostship (fetch.sh). Port-layer code (src/port/) is
# excluded on purpose — it is new C++ code, not decomp output.
#
#   bash tasks/adhoc/mario64-assembly-isms/discover.sh      # writes data/<class>.txt + data/SUMMARY.txt
set -u
cd "$(dirname "$0")"
DATA=data; mkdir -p "$DATA"
SRC=../../../n64/SuperMario64/Ghostship/src
FILES=$(find "$SRC/game" "$SRC/engine" "$SRC/audio" "$SRC/goddard" "$SRC/menu" "$SRC/buffers" \
        -type f \( -name '*.c' -o -name '*.h' \) | sort)

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
class infinite_loop        '\bwhile \(TRUE\)|\bwhile \(1\)|\bfor \(;;\)'
class do_while_0           'while \(0\)'
class empty_then           'if \([^;{]*\) \{\s*\}|if \([^;{]*\)\s*;\s*$'
class if_else_ladder_num   'else if \([^;{]*== *-?[0-9]+\)'
class single_stmt_nested_if '^\s*if \([^;{]*\)\s*$'

# --- naming left over from the disassembler --------------------------------------------------
class stack_named_locals   '\b(s8|u8|s16|u16|s32|u32|f32|f64|void|struct [A-Za-z0-9_]+|[A-Z][A-Za-z0-9]*)\s*\**\s*sp[0-9A-F]{1,3}\b'
class temp_phi_var_locals  '\b(temp|phi|var)_[a-z0-9]+\b'
class arg_params           '\barg[0-9]\b'
class unnamed_funcs        '\bfunc_80[0-9A-Fa-f]{6}\b'
class unnamed_data         '\bD_80[0-9A-Fa-f]{6}\b'
class register_keyword     '\bregister\b'

# --- matching hacks / memory-layout artefacts ------------------------------------------------
class matching_comments    'fake ?match|fakematch|\bhack\b|non[- ]matching|to match|for matching|\bmatches\b' -i
class avoid_ub_macros      'AVOID_UB|GLOBAL_ASM|NON_MATCHING|FORCE_BSS|ALIGNED[0-9]|__attribute__'
class unused_macro         '\bUNUSED\b'
class filler_fields        '\b(filler|pad|padding|unused)[0-9A-Za-z_]*\s*\['
class volatile_kw          '\bvolatile\b'

# --- raw memory idioms -----------------------------------------------------------------------
class raw_byte_pointer     '\((u8|s8|char|uint8_t) \*\)|\(uintptr_t\)|\(u32\) *\(.*\*\)|\(s32\) *&'
class type_pun_deref       '\*\((s16|u16|s32|u32|f32|s8|u8) \*\) *[&(]'
class rawdata_union        'rawData\.|OBJECT_FIELD_'
class bit_masking_16       '& 0x(FFFF|ffff)\b|>> 16\)|<< 16\)'
class hex_magic            '\b0x[0-9A-Fa-f]{2,}\b'
class angle_constants      '\b0x(4000|8000|C000|c000|10000|2000|1000)\b'

# --- boolean / comparison idioms -------------------------------------------------------------
class bool_vs_TRUEFALSE    '(!= FALSE|== TRUE|== FALSE|!= TRUE)'
class cmp_zero             '(!= 0\)|== 0\))'
class return_bool_cmp      'return \(?[A-Za-z_][A-Za-z_0-9.>-]* (!=|==) (0|TRUE|FALSE)\)?;'

# --- casts / numeric ---------------------------------------------------------------------------
class cast_s16             '\(s16\) *[(a-zA-Z]'
class cast_s32             '\(s32\) *[(a-zA-Z]'
class cast_f32             '\(f32\) *[(a-zA-Z0-9]'
class double_literals      '[^A-Za-z_0-9.][0-9]+\.[0-9]+([eE][-+]?[0-9]+)?([^0-9fF.]|$)'
class shift_as_mul         '<< [1-9]\b|>> [1-9]\b'
class div_by_const_float   '/ [0-9]+\.[0-9]+f?'

# --- comments the decomp left ---------------------------------------------------------------
class todo_bug_comments    '//! ?@bug|//!|\bTODO\b|\bFIXME\b|\bXXX\b'

echo; echo "logs in $DATA/ ; summary in $DATA/SUMMARY.txt"
