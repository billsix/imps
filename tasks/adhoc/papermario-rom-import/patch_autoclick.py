#!/usr/bin/env python3
"""THROWAWAY test instrumentation (never exported as a patch): with PAPERBOAT_AUTOCLICK=1 in the
environment, every modal popup takes its first button immediately, so the extractor's popup flow
can be driven headlessly under Xvfb (no way to click an ImGui button there — the GL window's
contents are not capturable, so xdotool has nothing to aim at)."""

import sys
from pathlib import Path

TARGET: str = "src/port/ui/PaperboatModals.cpp"
OLD: str = """void PaperboatModalWindow::DrawElement() {
    if (modals.size() > 0) {
        PaperboatModal curModal = modals.at(0);
"""
NEW: str = """void PaperboatModalWindow::DrawElement() {
    if (modals.size() > 0) {
        PaperboatModal curModal = modals.at(0);
        // TEST INSTRUMENTATION (imps, not for upstream): headless runs take button 1 at once.
        if (const char* ac = std::getenv("PAPERBOAT_AUTOCLICK"); ac != nullptr && ac[0] == '1') {
            printf("[autoclick] %s -> %s\\n", curModal.title_.c_str(), curModal.button1_.c_str());
            fflush(stdout);
            modals.erase(modals.begin());
            if (curModal.button1callback_ != nullptr) {
                curModal.button1callback_();
            }
            return;
        }
"""
IMGUI_INCLUDE: str = "#include <imgui.h>\n"
EXTRA_INCLUDES: str = "#include <imgui.h>\n#include <cstdio>\n#include <cstdlib>\n"


def main(argv: list[str]) -> None:
    p: Path = Path(argv[1]) / TARGET
    s: str = p.read_text()
    assert s.count(OLD) == 1
    s = s.replace(OLD, NEW)
    if "#include <cstdlib>" not in s:
        s = s.replace(IMGUI_INCLUDE, EXTRA_INCLUDES, 1)
    p.write_text(s)
    print("autoclick instrumentation applied")


if __name__ == "__main__":
    main(sys.argv)
