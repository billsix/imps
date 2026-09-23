#!/usr/bin/env python3
"""Batch 3 — goto that is a keyword, and loops with the exit test hoisted into the body.
usage: patch_batch3.py <checkout> <group>   (group: copt|load|koopa|gdmath|loops)"""
import sys
from pathlib import Path

root = Path(sys.argv[1])
group = sys.argv[2]


def patch(rel, pairs):
    p = root / rel
    s = p.read_text()
    for old, new in pairs:
        n = s.count(old)
        assert n == 1, f"{rel}: expected exactly one match for {old[:60]!r}, got {n}"
        s = s.replace(old, new)
    p.write_text(s)
    print("patched", rel)


COPT = "src/audio/copt/seq_channel_layer_process_script_copt.inc.c"

if group == "copt":
    patch(COPT, [
    ("""                    layer->playPercentage = sp3A;
                    goto l1090;

                case 0x40: // layer_note1 (play percentage, velocity)
                    M64_READ_COMPRESSED_U16(state, sp3A);
                    vel = *((*state).pc++);
                    layer->noteDuration = 0;
                    layer->playPercentage = sp3A;
                    goto l1090;

                case 0x80: // layer_note2 (velocity, duration; uses last play percentage)
                    sp3A = layer->playPercentage;
                    vel = *((*state).pc++);
                    layer->noteDuration = *((*state).pc++);
                    goto l1090;
            }
l1090:
            cmdSemitone = cmd - (cmd & 0xc0);""",
     """                    layer->playPercentage = sp3A;
                    break;

                case 0x40: // layer_note1 (play percentage, velocity)
                    M64_READ_COMPRESSED_U16(state, sp3A);
                    vel = *((*state).pc++);
                    layer->noteDuration = 0;
                    layer->playPercentage = sp3A;
                    break;

                case 0x80: // layer_note2 (velocity, duration; uses last play percentage)
                    sp3A = layer->playPercentage;
                    vel = *((*state).pc++);
                    layer->noteDuration = *((*state).pc++);
                    break;
            }
            cmdSemitone = cmd - (cmd & 0xc0);"""),
    ("""                    layer->playPercentage = sp3A;
                    goto l1138;

                case 0x40: // play note, type 1 (uses default play percentage)
                    sp3A = layer->shortNoteDefaultPlayPercentage;
                    goto l1138;

                case 0x80: // play note, type 2 (uses last play percentage)
                    sp3A = layer->playPercentage;
                    goto l1138;
            }
l1138:
""",
     """                    layer->playPercentage = sp3A;
                    break;

                case 0x40: // play note, type 1 (uses default play percentage)
                    sp3A = layer->shortNoteDefaultPlayPercentage;
                    break;

                case 0x80: // play note, type 2 (uses last play percentage)
                    sp3A = layer->playPercentage;
                    break;
            }
"""),
    ("""                                sp24 = temp_f2;
                                freqScale = temp_f12;
                                goto l13cc;

                            case PORTAMENTO_MODE_2:
                            case PORTAMENTO_MODE_4:
                                freqScale = temp_f2;
                                sp24 = temp_f12;
                                goto l13cc;
                        }
l13cc:
""",
     """                                sp24 = temp_f2;
                                freqScale = temp_f12;
                                break;

                            case PORTAMENTO_MODE_2:
                            case PORTAMENTO_MODE_4:
                                freqScale = temp_f2;
                                sp24 = temp_f12;
                                break;
                        }
"""),
    ])

elif group == "load":
    patch("src/audio/load.c", [
    ("""        if (sSampleDmas[gSampleDmaNumListItems].buffer == NULL) {
#if defined(VERSION_EU)
            break;
#else
            goto out1;
#endif
        }""",
     """        if (sSampleDmas[gSampleDmaNumListItems].buffer == NULL) {
            break;
        }"""),
    ("""        gSampleDmaNumListItems++;
    }
#if defined(VERSION_JP) || defined(VERSION_US)
out1:
#endif
""",
     """        gSampleDmaNumListItems++;
    }
"""),
    ("""        if (sSampleDmas[gSampleDmaNumListItems].buffer == NULL) {
#if defined(VERSION_EU)
            break;
#else
            goto out2;
#endif
        }""",
     """        if (sSampleDmas[gSampleDmaNumListItems].buffer == NULL) {
            break;
        }"""),
    ("""        gSampleDmaNumListItems++;
    }
#if defined(VERSION_JP) || defined(VERSION_US)
out2:
#endif
""",
     """        gSampleDmaNumListItems++;
    }
"""),
    ])

elif group == "koopa":
    patch("src/game/behaviors/koopa.inc.c", [
    ("""            cur_obj_set_model(MODEL_KOOPA_WITH_SHELL);
            obj_mark_for_deletion(shell);
            goto end;
        }""",
     """            cur_obj_set_model(MODEL_KOOPA_WITH_SHELL);
            obj_mark_for_deletion(shell);
            return;
        }"""),
    ("""    } else if (cur_obj_init_anim_and_check_if_end(6)) {
        o->oAction = KOOPA_UNSHELLED_ACT_RUN;
    }

end:;
}""",
     """    } else if (cur_obj_init_anim_and_check_if_end(6)) {
        o->oAction = KOOPA_UNSHELLED_ACT_RUN;
    }
}"""),
    ])

elif group == "gdmath":
    patch("src/goddard/gd_math.c", [
    ("""    if (run < 0) {
        goto end;
    }

    if ((j = i + 1) >= 4) {
        j = 1;
    }

    if ((k = j + 1) >= 4) {
        k = 1;
    }

    jVal = quat[j];
    kVal = quat[k];
    uVec.x = quat[0];
    uVec.y = quat[i];
    uVec.z = zHalf + zHalf;

end:
    vec->x = tVec.x;""",
     """    if (run >= 0) {
        if ((j = i + 1) >= 4) {
            j = 1;
        }

        if ((k = j + 1) >= 4) {
            k = 1;
        }

        jVal = quat[j];
        kVal = quat[k];
        uVec.x = quat[0];
        uVec.y = quat[i];
        uVec.z = zHalf + zHalf;
    }

    vec->x = tVec.x;"""),
    ])

elif group == "loops":
    patch("src/game/print.c", [
    ("""        // Increments the number of digits until length is long enough.
        while (TRUE) {
            powBase = int_pow(base, numDigits);

            if (powBase > (u32) n) {
                break;
            }

            numDigits++;
        }""",
     """        // Increments the number of digits until length is long enough.
        while ((powBase = int_pow(base, numDigits)) <= (u32) n) {
            numDigits++;
        }"""),
    ])
    patch("src/game/macro_special_objects.c", [
    ("""        offset = 0;
        while (TRUE) {
            if (SpecialObjectPresets[offset].preset_id == presetID) {
                break;
            }

            if (SpecialObjectPresets[offset].preset_id == 0xFF) {
            }

            offset++;
        }
""",
     """        offset = 0;
        while (SpecialObjectPresets[offset].preset_id != presetID) {
            offset++;
        }
"""),
    ("""        offset = 0;

        while (TRUE) {
            if (SpecialObjectPresets[offset].preset_id == presetID) {
                break;
            }
            offset++;
        }
""",
     """        offset = 0;

        while (SpecialObjectPresets[offset].preset_id != presetID) {
            offset++;
        }
"""),
    ])
else:
    sys.exit("unknown group " + group)
print("done", group)
