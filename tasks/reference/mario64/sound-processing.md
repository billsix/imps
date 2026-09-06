# Reference: Sound processing — software synthesis, then a modern device

> **Provenance:** authored 2026-09-06 against Ghostship pin `49c5312a` /
> LUS `c151cc91`. Anchors in `src/audio/synthesis.c`, `seqplayer.c`,
> `mixer.c`, and `libultraship/src/ship/audio/AudioPlayer.cpp`. Part of the
> mario64 graphics set — map at [`README.md`](README.md). (Audio is
> adjacent to graphics, included because both courses omit it.)

## TL;DR

SM64 **synthesizes its audio in software** and libultraship **plays** the
result on a modern device. A **sequence player** (`seqplayer.c`) reads MIDI-
like music sequences and decides which **notes** should sound; the
**synthesizer** (`synthesis.c`) turns each note into samples by
**resampling** an instrument sample to the right pitch and applying an
**envelope** (volume shape over time), then the **mixer** (`mixer.c`) sums
everything, adds **reverb**, and produces a buffer. That buffer is handed
across the port boundary (`libultraship-integration.md` §5) to
`AudioPlayer::Init`/play (`AudioPlayer.cpp:10`) on an SDL/WASAPI/CoreAudio
backend. This is a small but complete **DSP pipeline**.

## 1. Sequence → notes (`seqplayer.c`)

Music is stored as **sequences** — compact, MIDI-like note/tempo/instrument
event streams. The sequence player interprets them each audio frame: advance
the tempo, start/stop notes, pick instruments (soundfonts). Its output is a
set of **active notes**, each with a pitch, a target volume, and an
instrument sample — the "score reader" of the engine.

## 2. Notes → samples: resample + envelope (`synthesis.c`)

The synthesizer builds an audio command list; the two core operations
(declared `synthesis.c:54-61`):

- **`final_resample`** — pitch-shift an instrument's recorded sample by
  **resampling** it (reading it faster/slower) to the note's pitch. This is
  the audio analogue of texture sampling: reconstruct a continuous signal and
  re-sample it at a new rate.
- **`process_envelope`** — apply an **ADSR-style envelope**: scale the note's
  volume over time (attack/decay/sustain/release) plus stereo/headset pan, so
  a note swells and fades rather than clicking on and off.

## 3. Mix + reverb (`mixer.c`, `synthesis.c`)

All active notes are **summed** by the mixer, and
`synthesis_resample_and_mix_reverb` folds in a **reverb** send (a delayed,
attenuated copy of the mix) for space. The result is a finished stereo sample
buffer for this frame. Historically this ran on the N64's RSP microcode; the
decomp does the identical DSP **in C on the CPU**.

## 4. Play it (LUS `AudioPlayer`)

The port hands the buffer to libultraship each frame under a condition-
variable handshake (`libultraship-integration.md` §5). `AudioPlayer`
(`AudioPlayer.cpp`) is the device abstraction, implemented per platform
(`SDLAudioPlayer`, `WasapiAudioPlayer`, `CoreAudioAudioPlayer`) — the audio
twin of the graphics backend split (`graphics-pipeline.md` §3): synthesize
once, play on any OS.

## How this relates to the course

- **Neither course covers sound.** So this is a pure adjacent gap-fill,
  included because the same student who wants "the parts a course leaves out"
  usually finds audio is the biggest omission of all.
- **Sampling shows up again, in a new domain.** `final_resample` is the same
  reconstruct-and-resample idea as texture sampling
  (`sampling-and-mipmapping.md`) — pitch-shifting a sound is minifying/
  magnifying a signal in time. Pointing that out ties audio to a graphics
  concept the student already has.
- **The backend split repeats:** synthesize in portable code, play through a
  thin per-OS device layer — structurally identical to the generate-shaders/
  per-GPU-backend pattern. Recognizing the same architecture in two
  subsystems is the transferable lesson.

## Candidate doc-region spans (for the later Sphinx pass — not yet added)

- `src/audio/synthesis.c` around `final_resample`/`process_envelope`
  (`:54-61`): region `synth_core` — resample + envelope, the note→samples
  step.
- `libultraship/src/ship/audio/AudioPlayer.cpp` around `Init` (`:10`):
  region `audio_device` — the per-OS playback abstraction.
