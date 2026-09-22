#!/usr/bin/env python3
"""THROWAWAY trace instrumentation for RunExtract / GameExtractor (repro branch only, never
exported): print every popup registration, every ROM load, and the extractor's inputs to stdout,
so a headless run shows the real control flow instead of a guessed one."""

# ruff: noqa: E501  -- the OLD/NEW pairs are verbatim C++ source lines; their length is upstream's.

import sys
from pathlib import Path

Pairs = list[tuple[str, str]]


def patch(root: Path, rel: str, pairs: Pairs) -> None:
    """Replace each (old, new) pair exactly once in `root/rel`, failing loudly on 0 or 2+ matches."""
    p: Path = root / rel
    s: str = p.read_text()
    old: str
    new: str
    for old, new in pairs:
        n: int = s.count(old)
        assert n == 1, f"{rel}: expected exactly one match for {old[:70]!r}, got {n}"
        s = s.replace(old, new)
    p.write_text(s)
    print("patched", rel)


def ensure_cstdio(root: Path, rel: str) -> None:
    """Prepend `#include <cstdio>` to `root/rel` if it is not there (the traces use printf)."""
    p: Path = root / rel
    s: str = p.read_text()
    if "#include <cstdio>" not in s:
        p.write_text("#include <cstdio>\n" + s)


GUI_FILE: str = "src/port/ui/PaperboatGui.cpp"
EXTRACTOR_FILE: str = "src/port/extractor/GameExtractor.cpp"
ENGINE_FILE: str = "src/port/Engine.cpp"

GUI: Pairs = [
    (
        """    mModalWindow->RegisterPopup(title, message, button1, button2, button1callback, button2callback);
}""",
        """    printf("[trace] RegisterPopup \\"%s\\" [%s] [%s]\\n", title.c_str(), button1.c_str(), button2.c_str());
    fflush(stdout);
    mModalWindow->RegisterPopup(title, message, button1, button2, button1callback, button2callback);
}""",
    ),
]

EXTRACTOR: Pairs = [
    (
        """bool GameExtractor::LoadRomFromPath(const std::string& romPath) {
    if (!std::filesystem::exists(romPath)) {""",
        """bool GameExtractor::LoadRomFromPath(const std::string& romPath) {
    printf("[trace] LoadRomFromPath %s\\n", romPath.c_str());
    fflush(stdout);
    if (!std::filesystem::exists(romPath)) {""",
    ),
    (
        """bool GameExtractor::RunStandalone(std::string rom, const std::string& configDir) {
    if (!std::filesystem::exists(rom)) {""",
        """bool GameExtractor::RunStandalone(std::string rom, const std::string& configDir) {
    printf("[trace] RunStandalone %s\\n", rom.c_str());
    fflush(stdout);
    if (!std::filesystem::exists(rom)) {""",
    ),
    (
        """    totalAssets = PAPERBOAT_ASSET_YAML_COUNT;
    assetCount = 0;
""",
        """    totalAssets = PAPERBOAT_ASSET_YAML_COUNT;
    assetCount = 0;
    printf("[trace] GenerateOTRTo romPath=%s bytes=%zu assets=%s game=%s\\n", mGamePath.generic_string().c_str(),
           this->mGameData.size(), assetsPath.c_str(), gamePath.c_str());
    fflush(stdout);
""",
    ),
]

ENGINE: Pairs = [
    (
        """    std::vector<std::string> args;
    if (argc > 1) {
        for (int i = 1; i < argc; i++) {
            args.push_back(argv[i]);
        }
    }
""",
        """    std::vector<std::string> args;
    if (argc > 1) {
        for (int i = 1; i < argc; i++) {
            args.push_back(argv[i]);
        }
    }
    printf("[trace] RunExtract argc=%d portArchiveExists=%d anyRomArchive=%d appdir=%s bundle=%s\\n", argc,
           (int)portArchiveExists, (int)AnyRomArchiveExists(), Ship::Context::GetAppDirectoryPath("boat").c_str(),
           Ship::Context::GetAppBundlePath().c_str());
    fflush(stdout);
""",
    ),
    (
        """                    case PS_LOCAL: {
                        extract = GameExtractor();""",
        """                    case PS_LOCAL: {
                        printf("[trace] PS_LOCAL scanning %s and %s\\n", installPath.c_str(),
                               Ship::Context::GetAppDirectoryPath("boat").c_str());
                        fflush(stdout);
                        extract = GameExtractor();""",
    ),
]

TRACED_FILES: tuple[str, ...] = (ENGINE_FILE, GUI_FILE, EXTRACTOR_FILE)


def main(argv: list[str]) -> None:
    root: Path = Path(argv[1])
    patch(root, GUI_FILE, GUI)
    patch(root, EXTRACTOR_FILE, EXTRACTOR)
    patch(root, ENGINE_FILE, ENGINE)
    rel: str
    for rel in TRACED_FILES:
        ensure_cstdio(root, rel)
    print("trace instrumentation applied")


if __name__ == "__main__":
    main(sys.argv)
