#!/usr/bin/env python3
"""THROWAWAY trace instrumentation for RunExtract / GameExtractor (repro branch only, never
exported): print every popup registration, every ROM load, and the extractor's inputs to stdout,
so a headless run shows the real control flow instead of a guessed one."""
import sys
from pathlib import Path

root = Path(sys.argv[1])


def patch(rel, pairs):
    p = root / rel
    s = p.read_text()
    for old, new in pairs:
        n = s.count(old)
        assert n == 1, f"{rel}: expected exactly one match for {old[:70]!r}, got {n}"
        s = s.replace(old, new)
    p.write_text(s)
    print("patched", rel)


patch("src/port/ui/PaperboatGui.cpp", [
("""    mModalWindow->RegisterPopup(title, message, button1, button2, button1callback, button2callback);
}""",
"""    printf("[trace] RegisterPopup \\"%s\\" [%s] [%s]\\n", title.c_str(), button1.c_str(), button2.c_str());
    fflush(stdout);
    mModalWindow->RegisterPopup(title, message, button1, button2, button1callback, button2callback);
}"""),
])

patch("src/port/extractor/GameExtractor.cpp", [
("""bool GameExtractor::LoadRomFromPath(const std::string& romPath) {
    if (!std::filesystem::exists(romPath)) {""",
"""bool GameExtractor::LoadRomFromPath(const std::string& romPath) {
    printf("[trace] LoadRomFromPath %s\\n", romPath.c_str());
    fflush(stdout);
    if (!std::filesystem::exists(romPath)) {"""),
("""bool GameExtractor::RunStandalone(std::string rom, const std::string& configDir) {
    if (!std::filesystem::exists(rom)) {""",
"""bool GameExtractor::RunStandalone(std::string rom, const std::string& configDir) {
    printf("[trace] RunStandalone %s\\n", rom.c_str());
    fflush(stdout);
    if (!std::filesystem::exists(rom)) {"""),
("""    totalAssets = PAPERBOAT_ASSET_YAML_COUNT;
    assetCount = 0;
""",
"""    totalAssets = PAPERBOAT_ASSET_YAML_COUNT;
    assetCount = 0;
    printf("[trace] GenerateOTRTo romPath=%s bytes=%zu assets=%s game=%s\\n", mGamePath.generic_string().c_str(),
           this->mGameData.size(), assetsPath.c_str(), gamePath.c_str());
    fflush(stdout);
"""),
])

patch("src/port/Engine.cpp", [
("""    std::vector<std::string> args;
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
"""),
("""                    case PS_LOCAL: {
                        extract = GameExtractor();""",
"""                    case PS_LOCAL: {
                        printf("[trace] PS_LOCAL scanning %s and %s\\n", installPath.c_str(),
                               Ship::Context::GetAppDirectoryPath("boat").c_str());
                        fflush(stdout);
                        extract = GameExtractor();"""),
])
if "#include <cstdio>" not in (root / "src/port/Engine.cpp").read_text():
    p = root / "src/port/Engine.cpp"; s = p.read_text(); p.write_text("#include <cstdio>\n" + s)
if "#include <cstdio>" not in (root / "src/port/ui/PaperboatGui.cpp").read_text():
    p = root / "src/port/ui/PaperboatGui.cpp"; s = p.read_text(); p.write_text("#include <cstdio>\n" + s)
if "#include <cstdio>" not in (root / "src/port/extractor/GameExtractor.cpp").read_text():
    p = root / "src/port/extractor/GameExtractor.cpp"; s = p.read_text(); p.write_text("#include <cstdio>\n" + s)
print("trace instrumentation applied")
