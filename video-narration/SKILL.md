---
name: video-narration
description: >
  Add a spoken voice-over to a subtitled explainer video using local, offline
  neural text-to-speech (Kokoro by default, Piper as a lighter option). Turns
  each on-screen subtitle line into narration, synced automatically, with no API
  keys and no external services. Use when a user asks to "add audio / narration
  / a voice / voice-over" to a Manim video (e.g. one made with the
  educational-video skill), or to make a silent subtitled video speak. Handles
  engine setup, a drop-in narration module, spoken-text normalization (symbols →
  words), sync, and clip caching.
---

# Video narration (offline neural TTS)

Give a subtitled video a spoken voice-over. The subtitles ARE the script — each
`self.say(...)` line is synthesized and played in sync as it appears. Runs fully
offline, no API keys, and caches clips so re-renders are instant.

**Engine:** default is **Kokoro-82M** — a modern neural voice that sounds
genuinely natural (classic TTS like Piper sounds noticeably robotic). Piper is
still supported as a lighter/faster fallback. The integration is identical; only
setup differs.

Designed to pair with the **educational-video** skill (`EduScene.say()`), but
the module works with any Manim `Scene` that can call `self.add_sound()`.

> ⚠️ **The #1 narration bug — now handled automatically.** Manim caches
> rendered animation segments and skips re-rendering ones whose *visuals* are
> unchanged; a segment loaded from cache **silently drops its `add_sound()`**,
> leaving stretches with no voice (typically later scenes you didn't edit, while
> early/edited scenes still speak). **`narration.py` prevents this itself**: on
> import, if narration is enabled it sets `config.disable_caching = True` — so
> you get sound whether or not you remember the flag. Passing
> `--disable_caching` too is a harmless backup. Always still run the gap scan in
> §4 to confirm.

---

## 0. Why this design

1. **Subtitles are the narration.** No separate script to write or keep in sync
   — hook the one place subtitles are shown (`say()`), and every line gets a
   voice automatically. (Content shown via `FadeIn`/`Write` instead of `say()`
   — e.g. recap bullets — is NOT auto-narrated; narrate those explicitly, see §6.)
2. **Narration drives pacing.** Each subtitle is held for
   `max(requested_hold, clip_duration) + buffer`, so speech is never cut off.
   The video naturally lengthens a little — that's correct, not a bug.
3. **Use a genuinely natural engine.** Kokoro is worth its ~310MB model; classic
   concatenative/older TTS reads as robotic and undercuts an otherwise polished
   video.
4. **Spoken-text normalization is essential.** On-screen text is full of glyphs
   a phonemizer mangles (`CO₂`, `−18°C`, `→`, `≈`, `×`, `ppm`). The module maps
   these to words **for speech only** — the on-screen text is untouched.
5. **Cached & reversible.** Clips are cached by a hash of (engine, voice, spoken
   text); set `NARRATION=0` to render silent without code changes. Changing the
   voice invalidates the cache automatically (new key) — delete `./narration` to
   reclaim disk.

---

## 1. Quick start

```bash
SKILL=/Users/suqingliu/.claude/skills/video-narration
cd <your video project>            # dir with your <topic>.py, ./env, ./bin, etc.

# 1) install Kokoro + model into ./kokoro  (reuses the project's env)
bash "$SKILL/scripts/setup_narration.sh" "$PWD" kokoro af_heart

# 2) drop the narration module next to your scene file
cp "$SKILL/assets/narration.py" .
```

Then wire it into your scene (§3) and render:

```bash
manim -qh topic.py Scene                      # narration.py disables the anim
                                              # cache itself; adding
                                              # --disable_caching is optional
```

First render synthesizes and caches every line (in `./narration`); later renders
reuse those clips instantly. `narration.py` auto-disables Manim's *animation*
cache (not the narration clip cache) so `add_sound()` is never dropped — see the
warning above.

> Lighter alternative: `setup_narration.sh "$PWD" piper en_US-amy-medium`
> (smaller/faster, but more robotic).

---

## 2. Setup script

`scripts/setup_narration.sh <project_dir> [engine=kokoro] [voice]`

- Installs the engine into the project's local micromamba env
  (`./bin/micromamba` + `./env`, as created by educational-video) or the
  `python`/`pip` on `PATH`.
- **Kokoro:** `pip install kokoro-onnx soundfile` + downloads
  `kokoro-v1.0.onnx` (~310MB) and `voices-v1.0.bin` (~27MB) into
  `<project>/kokoro/`. All voices live in the one `.bin`; pick per render.
- **Piper:** `pip install piper-tts` + downloads `<voice>.onnx` (+ `.json`)
  into `<project>/voices/`.
- Smoke-tests synthesis and prints the resolved engine/voice.

**Recommended voices**

| engine | voice | style |
|---|---|---|
| Kokoro | `af_heart` | natural female — best default |
| Kokoro | `af_bella` / `af_nicole` | warm female alternatives |
| Kokoro | `am_michael` / `am_adam` | natural male narrator |
| Kokoro | `bf_emma` | British female |
| Piper  | `en_US-amy-medium` | clear female (robotic-ish) |
| Piper  | `en_US-ryan-high` | fuller male (larger model) |

Kokoro has 50+ voices in the bundled `.bin`; list them with
`Kokoro(model, voices).get_voices()`.

---

## 3. Integrate (educational-video / EduScene)

`narration.py` exposes `narrate(text) -> (wav_path | None, seconds)`. Add the
import and a few lines inside `say()`:

```python
from narration import narrate          # top of your <topic>.py

# ...inside EduScene.say(), right after the subtitle FadeIn and
#    self._subtitle = group :
        path, dur = narrate(text)       # text = the subtitle string
        if path:
            self.add_sound(path)              # plays at the current scene time
            self.wait(max(hold, dur) + 0.45)  # narration governs the hold
        else:
            self.wait(hold + 1.1)             # silent fallback (unchanged)
```

That's the whole integration for `say()` lines. The module handles
newline→space and symbol→word itself.

---

## 4. Controls & behavior

- **Toggle:** `NARRATION=0 manim -qh topic.py Scene` renders silent (no code
  edit). Any truthy/absent value = narration on.
- **Engine:** `NARRATION_ENGINE=kokoro|piper|auto` (default `auto` → Kokoro if
  its model files exist under `./kokoro`, else Piper).
- **Voice:** `NARRATION_VOICE=<name>` for Kokoro (e.g. `am_michael`) or a
  `.onnx` path for Piper (else auto-discovers `./voices/*.onnx`).
- **Cache dir:** `NARRATION_DIR=<path>` (default `./narration`). Delete it after
  switching voice/engine to reclaim disk (the key already changes, so stale
  clips are simply ignored).
- **Graceful degradation:** if the engine/model is missing, `narrate()` returns
  `(None, 0)` and the video renders silent instead of crashing.
- **Animation cache:** handled automatically — `narration.py` sets
  `config.disable_caching = True` on import when narration is on (see the warning
  up top), so cached segments can't drop their audio. `--disable_caching` on the
  command line is an optional backup. On import you'll see the line
  `narration: disabled Manim animation cache ...` confirming it's active.
- **Verify output:** the MP4 gains an AAC track automatically.
  `ffprobe -v error -show_entries stream=codec_type -of csv=p=0 out.mp4`;
  check it isn't silent with `ffmpeg -i out.mp4 -af volumedetect -f null -`
  (speech ≈ −20 to −30 dB mean; silence ≈ −90 dB).
- **Scan for silent gaps** (catches both the caching bug and un-narrated
  `FadeIn`/`Write` scenes) — find any contiguous silence ≥3s:
  ```
  ffmpeg -i out.mp4 -af silencedetect=noise=-45dB:d=3 -f null - 2>&1 | grep silence
  ```
  A long `silence_duration` = a chunk with no voice; map its start time to a
  scene. A silent END usually means a closing scene uses `FadeIn`/`Write`
  instead of `say()` (see §6); a silent MIDDLE chunk usually means you forgot
  `--disable_caching`.

---

## 5. Spoken-text normalization

`narration.py` ships a `_SPOKEN_SUBS` table mapping symbols to words, e.g.:

```
CO₂ → "C O two"      −18°C → "minus 18 degrees Celsius"     ≈ → "approximately"
280→420 → "280 to 420"   × → "times"   ÷ → "divided by"   ppm → "P P M"
```

Extend that list for your video's domain terms. It only affects speech; the
on-screen subtitle is unchanged.

---

## 6. Narrate non-`say()` content (recaps, big reveals)

Text shown with `FadeIn`/`Write` (titles, recap bullets, closing lines) is
silent unless you narrate it explicitly. For each such line:

```python
self.play(FadeIn(item))
path, dur = narrate(item_text)
if path:
    self.add_sound(path)
    self.wait(dur + 0.35)
else:
    self.wait(1.0)
```

Always volume-check the last ~30s of a long render — a silent tail almost always
means the closing scene uses `FadeIn`/`Write` instead of `say()`.

---

## 7. Tips

- **Pick the voice before the big render.** Test a couple of lines from the
  setup output first.
- **Keep a silent master** (`NARRATION=0`) if you want to add your own VO/music.
- **Background music:** add a second quiet track with
  `self.add_sound(music.mp3, gain=-18)` at scene start (out of scope here).

---

## 8. Files in this skill

- `scripts/setup_narration.sh` — installs Kokoro (or Piper) + downloads the
  model/voice into the project.
- `assets/narration.py` — drop-in module: `narrate()` (synthesize + cache +
  duration), `spoken_text()`/`_SPOKEN_SUBS` (normalization), Kokoro/Piper
  auto-select, env-var controls, graceful silent fallback.
