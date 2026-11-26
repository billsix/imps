"""Replay SuperMario64's three cheat patches onto Ghostship aefb89b8, ported to the feature registry.

Run inside a Ghostship worktree whose HEAD is the new pin plus the standard-c stream. For each patch:
`git am --3way`; the hunks for src/port/mods/PortEnhancements.cpp are discarded and the cheat's
listener and REGISTER_EVENT lines are inserted at named anchors in upstream's reorganised file, reading
the setting with Port_FeatureInt; the cheat's row is added to sDefs in src/port/features/Features.cpp
and to the id table in docs/romhacks/DESIGN.md. Every anchor must occur exactly once or the run stops.

    python3 tasks/adhoc/mario64-bump-pin-port-cheats-to-feature-registry/port_cheats.py <worktree> <patch dir>
"""

import pathlib
import subprocess
import sys

WORKTREE: pathlib.Path = pathlib.Path(sys.argv[1])
PATCHES: pathlib.Path = pathlib.Path(sys.argv[2]).resolve()
ENHANCEMENTS: str = "src/port/mods/PortEnhancements.cpp"
FEATURES: str = "src/port/features/Features.cpp"
DESIGN: str = "docs/romhacks/DESIGN.md"

FLYING_LISTENER_END: str = """        FlyingTripleJumpLaunch* ev = (FlyingTripleJumpLaunch*)event;
        *ev->launchVelocity = 246.0f;
    });
"""
PAUSE_LISTENER_END: str = """        RenderPauseCourseOptions* ev = (RenderPauseCourseOptions*)event;
        *ev->render = true;
    });
"""

HIGH_JUMP_LISTENERS: str = """
    static bool sHighJumpActive = false;
    static f32 sHighJumpStartHeight = 0.0f;
    REGISTER_LISTENER(MarioHighJumpLaunch, EVENT_PRIORITY_NORMAL, [](IEvent* event) {
        MarioHighJumpLaunch* ev = (MarioHighJumpLaunch*)event;
        if (Port_FeatureInt("cheats.super_jump", 0) == 0 ||
            ev->action == ACT_FLYING_TRIPLE_JUMP ||
            ev->m->vel[1] <= 0.0f) {
            sHighJumpActive = false;
            return;
        }
        sHighJumpStartHeight = ev->m->pos[1];
        ev->m->vel[1] *= 3.0f;
        sHighJumpActive = true;
    });
    REGISTER_LISTENER(MarioHighJumpFallHeight, EVENT_PRIORITY_NORMAL, [](IEvent* event) {
        if (!sHighJumpActive || Port_FeatureInt("cheats.super_jump", 0) == 0) {
            return;
        }
        MarioHighJumpFallHeight* ev = (MarioHighJumpFallHeight*)event;
        f32 naturalPeak = sHighJumpStartHeight + (ev->m->peakHeight - sHighJumpStartHeight) / 9.0f;
        f32 corrected = naturalPeak - ev->m->pos[1];
        *ev->fallHeight = corrected > 0.0f ? corrected : 0.0f;
    });
"""
AIR_JUMP_LISTENER: str = """    REGISTER_LISTENER(MarioAirborneActionUpdate, EVENT_PRIORITY_NORMAL, [](IEvent* event) {
        if (Port_FeatureInt("cheats.infinite_air_jumps", 0) == 0) {
            return;
        }
        MarioAirborneActionUpdate* ev = (MarioAirborneActionUpdate*)event;
        struct MarioState* m = ev->m;
        if ((m->input & INPUT_A_PRESSED)
                && !(m->input & INPUT_Z_DOWN)
                && !(m->action & ACT_FLAG_INVULNERABLE)
                && !(m->action & ACT_FLAG_SWIMMING_OR_FLYING)
                && m->action != ACT_GROUND_POUND
                && m->action != ACT_FLYING_TRIPLE_JUMP) {
            set_mario_action(m, ACT_JUMP, 0);
            event->Cancelled = true;
        }
    });
"""
SKYBOX_LISTENER: str = """    REGISTER_LISTENER(SkyboxRender, EVENT_PRIORITY_NORMAL, [](IEvent* event) {
        if (Port_FeatureInt("enhancements.disable_skybox", 0) == 0) {
            return;
        }
        event->Cancelled = true;
    });
"""


def git(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run git in the worktree."""
    return subprocess.run(["git", "-C", str(WORKTREE), *arguments], capture_output=True, text=True, check=check)


def insert_after(relative: str, anchor: str, addition: str) -> None:
    """Insert addition directly after the single occurrence of anchor."""
    path: pathlib.Path = WORKTREE / relative
    text: str = path.read_text()
    assert text.count(anchor) == 1, (relative, anchor)
    path.write_text(text.replace(anchor, anchor + addition))


def add_feature(after_id: str, after_cvar: str, feature: str, macro: str, cvar: str, prefix: str) -> None:
    """Add one toggle to sDefs and to the design doc's id table, after an existing row."""
    insert_after(
        FEATURES,
        f'    {{ "{after_id}", {after_cvar}, Kind::Toggle, 0 }},\n',
        f'    {{ "{feature}", {macro}("{cvar}"), Kind::Toggle, 0 }},\n',
    )
    design: str = (WORKTREE / DESIGN).read_text()
    rows: list[str] = [line for line in design.splitlines(keepends=True) if line.startswith(f"| `{after_id}` |")]
    assert len(rows) == 1, after_id
    insert_after(DESIGN, rows[0], f"| `{feature}` | `{prefix}.{cvar}` | 0 |\n")


def replay(patch_glob: str) -> None:
    """Apply one patch with its PortEnhancements.cpp hunks discarded; the caller re-adds them."""
    patches: list[pathlib.Path] = sorted(PATCHES.glob(patch_glob))
    assert len(patches) == 1, patch_glob
    git("-c", "core.editor=true", "am", "--3way", "--exclude", ENHANCEMENTS, str(patches[0]))


def finish(subject_check: str) -> None:
    """Fold the hand-placed changes into the commit the patch just made."""
    assert subject_check in git("log", "-1", "--format=%s").stdout
    git("add", ENHANCEMENTS, FEATURES, DESIGN)
    git("commit", "--amend", "--no-edit")


def main() -> None:
    """Replay and port the three cheats, one commit each."""
    replay("0001-*.patch")
    insert_after(ENHANCEMENTS, FLYING_LISTENER_END, HIGH_JUMP_LISTENERS)
    insert_after(
        ENHANCEMENTS,
        "    REGISTER_EVENT(FlyingTripleJumpLaunch);\n",
        "    REGISTER_EVENT(MarioHighJumpLaunch);\n    REGISTER_EVENT(MarioHighJumpFallHeight);\n",
    )
    add_feature("cheats.play_in_demo", 'CVAR_CHEAT("PlayInDemo")', "cheats.super_jump", "CVAR_CHEAT", "SuperJump", "gCheats")
    finish("high jump")

    replay("0002-*.patch")
    insert_after(ENHANCEMENTS, '#include "sm64.h"\n', '#include "game/mario.h"\n')
    insert_after(ENHANCEMENTS, FLYING_LISTENER_END, AIR_JUMP_LISTENER)
    insert_after(
        ENHANCEMENTS,
        "    REGISTER_EVENT(MarioHighJumpFallHeight);\n",
        "    REGISTER_EVENT(MarioAirborneActionUpdate);\n",
    )
    add_feature("cheats.super_jump", 'CVAR_CHEAT("SuperJump")', "cheats.infinite_air_jumps", "CVAR_CHEAT", "InfiniteAirJumps", "gCheats")
    finish("infinite jumps")

    replay("0003-*.patch")
    insert_after(ENHANCEMENTS, PAUSE_LISTENER_END, SKYBOX_LISTENER)
    add_feature(
        "enhancements.fix_file_select_button_tilt",
        'CVAR_ENHANCEMENT("FixFileSelectButtonTilt")',
        "enhancements.disable_skybox",
        "CVAR_ENHANCEMENT",
        "DisableSkybox",
        "gEnhancements",
    )
    finish("skybox")
    print(git("log", "--oneline", "-3").stdout)


if __name__ == "__main__":
    main()
