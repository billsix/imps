#!/usr/bin/env bash
# Headless proofs for the PaperMario ROM-import unit (imps, 2026-09-22; kept under
# tasks/adhoc/papermario-rom-import/ as the record of how the series was verified).
#
# Runs the TEST build of PaperBoat under Xvfb with software GL and checks the observable outcome
# of six scenarios. The TEST build is the checkout's `imps-test` branch: the imps series
# (`imps-work`: two game-tree patches + the libultraship-lane Vulkan fix in the submodule) plus two
# THROWAWAY instrumentation commits that are never exported as patches — re-create them with
# patch_autoclick.py and patch_trace.py in this directory (PAPERBOAT_AUTOCLICK=1 takes every popup's
# first button; `[trace]` lines on stderr for popups, ROM loads and the extractor's inputs). ImGui
# popups cannot be clicked under Xvfb (the GL window's contents are not capturable, so xdotool has
# nothing to aim at), which is why the hook exists. The port swallows stdout — traces go to stderr.
#
# Inputs (ROMs are outside imps; no defaults on purpose):
#   GOOD_ROM  a supported 40 MB US ROM (SHA-1 3837f44c…)
#   BAD_ROM   a 64 MB over-dump of the same cart (its first 40 MB hash to the recipe)
#
# usage: GOOD_ROM=… BAD_ROM=… bash tasks/adhoc/papermario-rom-import/test_paperboat.sh [scratch dir]
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
PM=$(cd "$HERE/../../../n64/PaperMario" && pwd)
S=${1:-$(mktemp -d)}; S=$(cd "$S" && pwd)
BIN="$PM/PaperBoat/build/ninja-release/Paperboat"
: "${GOOD_ROM:?set GOOD_ROM to the 40 MB US ROM}" "${BAD_ROM:?set BAD_ROM to the 64 MB over-dump}"
status=0
pass() { echo "  ok   $*"; }
fail() { echo "  FAIL $*"; status=1; }
check() { local d=$1; shift; if "$@"; then pass "$d"; else fail "$d"; fi; }

pgrep -x Xvfb >/dev/null || { Xvfb :99 -screen 0 1280x720x24 >/dev/null 2>&1 & sleep 1; }
export DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1 PAPERBOAT_AUTOCLICK=1
export PATH="$HERE/zenity-shim:$PATH"   # fake zenity: answers the file dialog with $FAKE_ZENITY_PICK
# The game ignores SIGTERM and a leaked instance can grow to tens of GB (2026-09-22: two
# forgotten copies reached ~19 GB RSS each and swapped the host). Every launch below uses a
# hard timeout, and this trap reaps anything left when the harness exits for ANY reason.
trap 'pkill -9 -x Paperboat 2>/dev/null; pkill -9 -f build/ninja-release/Paperboat 2>/dev/null' EXIT
pkill -9 -x Paperboat 2>/dev/null; sleep 0.5

# launch NAME SECONDS [args...] — runs the binary with cwd = fresh dir $S/t_NAME (the app dir; NOT
# SHIP_HOME, which makes libultraship double its config path), under gdb so a crash leaves a
# backtrace; env FAKE_ZENITY_PICK / PRESEED_O2R shape the dir. The app ignores SIGTERM: KILL.
launch() {
    local name=$1 secs=$2; shift 2
    RUN="$S/t_$name"; rm -rf "$RUN"; mkdir -p "$RUN"
    [ -n "${PRESEED_O2R:-}" ] && cp "$PRESEED_O2R" "$RUN/pm64.o2r"
    ( cd "$RUN" && FAKE_ZENITY_LOG="$RUN/zenity.log" timeout -s KILL "$secs" \
        gdb -q --batch -ex run -ex "bt 8" --args "$BIN" "$@" > "$RUN/out.log" 2>&1 )
    TRACE=$(grep -a "^\[trace\]\|^\[autoclick\]" "$RUN/out.log" | cut -c1-200)
    CRASH=$(grep -a -c "received signal SIGSEGV" "$RUN/out.log")
}
t()   { grep -q -- "$1" <<<"$TRACE"; }        # trace contains
nt()  { ! grep -q -- "$1" <<<"$TRACE"; }      # trace does not contain

echo "== T2 CLI import (game-tree 0001): 'Paperboat <good rom>' extracts with no prompt, then runs"
launch cli_good 75 "$GOOD_ROM"
check "argv path taken: RunStandalone, no 'No O2R Files' prompt"  eval 't "RunStandalone $GOOD_ROM" && nt "No O2R Files"'
check "extraction ran to Done"                grep -a -q "Done! Took" "$RUN/logs/Paperboat.log"
check "pm64.o2r written (40 MB)"              eval '[ "$(stat -c %s "$RUN/pm64.o2r" 2>/dev/null || echo 0)" -gt 40000000 ]'
check "then 'Run PaperBoat' prompt, game starts, no crash" eval 't "Run PaperBoat -> Yes" && [ "$CRASH" -eq 0 ]'
ARCHIVE="$S/t_cli_good/pm64.o2r"

echo "== T1 Vulkan fix (LUS 0001): archive present, default backend (Vulkan), game must run 30 s without SIGSEGV"
PRESEED_O2R="$ARCHIVE" launch vulkan 30
check "no popups, straight to the game"      t "anyRomArchive=1"
check "no crash in 30 s (was: SIGSEGV in BuildVulkanShader)" [ "$CRASH" -eq 0 ]
check "the Vulkan backend was in use (config Id 4)" eval 'grep -A2 "\"Backend\"" "$RUN/paperboat.cfg.json" | grep -q "\"Id\": 4"'
unset PRESEED_O2R

echo "== T3 CLI import with the 64 MB over-dump: refused with the ROM Error prompt, nothing extracted"
launch cli_bad 25 "$BAD_ROM"
check "RunStandalone rejected it"             eval 't "RunStandalone $BAD_ROM" && t "RegisterPopup \"PaperBoat ROM Error\""'
check "no extraction"                         eval 'nt "GenerateOTRTo" && [ ! -e "$RUN/pm64.o2r" ]'

echo "== T4 picker validation (game-tree 0002): dialog returns the 64 MB over-dump"
FAKE_ZENITY_PICK="$BAD_ROM" launch pick_bad 25
check "picker path taken (LoadRomFromPath)"   t "LoadRomFromPath $BAD_ROM"
check "refused with the ROM Error prompt"     t "RegisterPopup \"PaperBoat ROM Error\""
check "no extraction into an empty archive"   eval 'nt "GenerateOTRTo" && [ ! -e "$RUN/pm64.o2r" ]'

echo "== T5 picker with the good ROM still extracts"
FAKE_ZENITY_PICK="$GOOD_ROM" launch pick_good 75
check "LoadRomFromPath then GenerateOTRTo"    eval 't "LoadRomFromPath $GOOD_ROM" && t "GenerateOTRTo"'
check "extraction ran to Done"                grep -a -q "Done! Took" "$RUN/logs/Paperboat.log"

echo "== T6 run.sh: trims an over-dump, rejects junk, seeds OpenGL"
RD="$PM/runDir"; rm -rf "$RD"
( cd "$PM" && timeout -s KILL 75 ./run.sh "$BAD_ROM" > "$S/t_runsh_bad.log" 2>&1 )
check "over-dump trimmed into runDir/pm64.z64 (40 MB)" eval '[ "$(stat -c %s "$RD/pm64.z64" 2>/dev/null || echo 0)" = 41943040 ]'
check "run.sh said so"                        grep -q "padded cart" "$S/t_runsh_bad.log"
check "OpenGL seeded in runDir/paperboat.cfg.json" grep -q '"Id": 2' "$RD/paperboat.cfg.json"
check "extraction ran from the trimmed copy"  eval '[ "$(stat -c %s "$RD/pm64.o2r" 2>/dev/null || echo 0)" -gt 40000000 ]'
head -c 1000 "$GOOD_ROM" > "$S/junk.z64"
( cd "$PM" && ./run.sh "$S/junk.z64" > "$S/t_runsh_junk.log" 2>&1 ); rc=$?
check "junk ROM rejected before launch (exit $rc)" eval '[ "$rc" -ne 0 ] && grep -q "ROM rejected" "$S/t_runsh_junk.log"'
( cd "$PM" && timeout -s KILL 30 ./run.sh > "$S/t_runsh_play.log" 2>&1 )
check "plain ./run.sh with the archive present: game ran 30 s on OpenGL, no crash" eval '! grep -a -q "Signal: 11\|INVALID ACCESS" "$S/t_runsh_play.log" && grep -A2 "\"Backend\"" "$RD/paperboat.cfg.json" | grep -q "\"Id\": 2"'

pkill -9 -x Paperboat 2>/dev/null
echo; [ "$status" -eq 0 ] && echo "ALL PASS" || echo "FAILURES"
exit "$status"
