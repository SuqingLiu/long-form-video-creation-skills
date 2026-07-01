"""
narration.py — drop-in offline neural voice-over for Manim explainer videos.

Copy this next to your <topic>.py, then in EduScene.say() (or any caption point):

    from narration import narrate
    ...
    path, dur = narrate(text)                 # text = the subtitle string
    if path:
        self.add_sound(path)                  # plays at the current scene time
        self.wait(max(hold, dur) + 0.45)      # narration governs the hold
    else:
        self.wait(hold + 1.1)                 # silent fallback

Each line is synthesized once and cached by a hash of (engine, voice, spoken
text), so re-renders are instant. Fully offline; no API keys.

Engines (Kokoro preferred — much more natural than Piper):
  - Kokoro : needs ./kokoro/kokoro-v1.0.onnx + ./kokoro/voices-v1.0.bin,
             plus `pip install kokoro-onnx soundfile`. Voice = a name like
             "af_heart" (default), "am_michael", "bf_emma", ...
  - Piper  : needs ./voices/<voice>.onnx (+ .onnx.json), `pip install piper-tts`.

Environment controls:
  NARRATION=0              render silent (any other/absent value = on)
  NARRATION_ENGINE=auto    auto (default) | kokoro | piper
  NARRATION_VOICE=<v>      Kokoro: a voice name (af_heart) OR a voices .bin path;
                           Piper:  a .onnx path (else auto-find ./voices/*.onnx)
  NARRATION_DIR=<path>     clip cache dir (default ./narration)
"""

import os
import re
import glob
import wave
import hashlib

_HERE = os.path.dirname(os.path.abspath(__file__))


def _enabled():
    return os.environ.get("NARRATION", "1").lower() not in ("0", "false", "off", "no")


def _cache_dir():
    return os.environ.get("NARRATION_DIR") or os.path.join(os.getcwd(), "narration")


# --- CRITICAL: force-disable Manim's animation cache when narrating ----------
# Manim caches rendered animation segments and skips re-rendering unchanged ones
# — but a segment loaded from cache SILENTLY DROPS its add_sound(), leaving
# stretches with no voice. Setting config.disable_caching here (at import, before
# rendering) makes correct behavior automatic, so callers can't forget the
# --disable_caching flag. Harmless if narration is off or Manim isn't present.
if _enabled():
    try:
        from manim import config as _manim_config
        if not _manim_config.disable_caching:
            _manim_config.disable_caching = True
            print("narration: disabled Manim animation cache "
                  "(required so add_sound() is not dropped)")
    except Exception:
        pass


# --- spoken-text normalization ---------------------------------------------
# Symbols a phonemizer would mangle -> how they should be SPOKEN (order matters).
# Extend this for your video's domain terms; it only affects speech, not the
# on-screen subtitle.
_SPOKEN_SUBS = [
    ("CO₂", "C O two"), ("CH₄", "C H four"), ("N₂O", "N two O"), ("H₂O", "H two O"),
    ("₂", " two"), ("₃", " three"), ("₄", " four"), ("²", " squared"), ("³", " cubed"),
    ("°C", " degrees Celsius"), ("°F", " degrees Fahrenheit"), ("°", " degrees"),
    ("≈", " approximately "), ("≠", " not equal to "), ("≥", " at least "),
    ("≤", " at most "), ("→", " to "), ("←", " from "),
    ("×", " times "), ("÷", " divided by "), ("±", " plus or minus "),
    ("½", " one half "), ("¼", " one quarter "), ("¾", " three quarters "),
    ("−", " minus "), ("–", " to "), ("—", ", "),
    ("&", " and "), ("%", " percent"), ("ppm", " P P M "), ("ppb", " P P B "),
]


def spoken_text(text):
    """Turn on-screen subtitle text into something a TTS voice reads cleanly."""
    s = " ".join(str(text).split("\n"))
    for a, b in _SPOKEN_SUBS:
        s = s.replace(a, b)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# --- engine selection & lazy loading ---------------------------------------
_KOKORO_MODEL = os.path.join(os.getcwd(), "kokoro", "kokoro-v1.0.onnx")
_KOKORO_VOICES = os.path.join(os.getcwd(), "kokoro", "voices-v1.0.bin")

_SYNTH = None           # cached (engine, voice_id, fn) once resolved
_SYNTH_FAILED = False


def _pick_engine():
    eng = os.environ.get("NARRATION_ENGINE", "auto").lower()
    if eng in ("kokoro", "piper"):
        return eng
    # auto: prefer Kokoro if its model is present, else Piper
    if os.path.exists(_KOKORO_MODEL) and os.path.exists(_KOKORO_VOICES):
        return "kokoro"
    return "piper"


def _find_piper_model():
    env = os.environ.get("NARRATION_VOICE")
    if env and env.endswith(".onnx") and os.path.exists(env):
        return env
    for root in (os.getcwd(), _HERE):
        hits = sorted(glob.glob(os.path.join(root, "voices", "*.onnx")))
        if hits:
            return hits[0]
    return None


def _load_synth():
    """Return (voice_id, synth_fn) where synth_fn(spoken, out_path) writes a wav."""
    global _SYNTH, _SYNTH_FAILED
    if _SYNTH is not None or _SYNTH_FAILED:
        return _SYNTH
    engine = _pick_engine()
    try:
        if engine == "kokoro":
            from kokoro_onnx import Kokoro
            import soundfile as sf
            voices = os.environ.get("NARRATION_VOICE")
            voices = voices if (voices and voices.endswith(".bin")) else _KOKORO_VOICES
            name = os.environ.get("NARRATION_VOICE", "af_heart")
            name = name if not name.endswith(".bin") else "af_heart"
            k = Kokoro(_KOKORO_MODEL, voices)

            def _fn(spoken, out_path):
                samples, sr = k.create(spoken, voice=name, speed=1.0, lang="en-us")
                sf.write(out_path, samples, sr)

            _SYNTH = ("kokoro:" + name, _fn)
        else:
            from piper import PiperVoice
            model = _find_piper_model()
            if not model:
                raise RuntimeError("no Piper .onnx under ./voices")
            v = PiperVoice.load(model)

            def _fn(spoken, out_path):
                with wave.open(out_path, "wb") as wf:
                    v.synthesize_wav(spoken, wf)

            _SYNTH = ("piper:" + os.path.basename(model), _fn)
    except Exception as exc:
        print("narration: TTS unavailable (%s); rendering silent" % exc)
        _SYNTH_FAILED = True
        return None
    return _SYNTH


def narrate(text):
    """Synthesize spoken `text` to a cached wav.

    Returns (wav_path, duration_seconds), or (None, 0.0) when narration is
    disabled, the text is empty, or TTS is unavailable — so the caller can fall
    back to a silent hold instead of crashing.
    """
    if not _enabled():
        return None, 0.0
    spoken = spoken_text(text)
    if not spoken:
        return None, 0.0

    synth = _load_synth()
    if synth is None:
        return None, 0.0
    voice_id, fn = synth

    cache = _cache_dir()
    os.makedirs(cache, exist_ok=True)
    key = hashlib.md5((voice_id + "|" + spoken).encode("utf-8")).hexdigest()[:16]
    path = os.path.join(cache, key + ".wav")

    if not os.path.exists(path):
        try:
            fn(spoken, path)
        except Exception as exc:
            print("narration: synth failed for %r: %s" % (spoken[:40], exc))
            if os.path.exists(path):
                os.remove(path)
            return None, 0.0

    try:
        with wave.open(path, "rb") as wf:
            dur = wf.getnframes() / float(wf.getframerate())
    except Exception:
        return None, 0.0
    return path, dur


# ===========================================================================
#  Sound effects (synthesized, offline; cached in ./sfx)
# ===========================================================================
# A few tasteful effects lift production value a lot — especially a whoosh +
# deep boom on the intro and each chapter card, and a soft chime on a key
# reveal. Usage in a scene:
#     from narration import sfx
#     p = sfx("boom")
#     if p: self.add_sound(p)
# Built-in names: "boom", "whoosh", "chime", "tick". Returns a wav path (cached)
# or None if numpy/soundfile aren't available (degrades silently).
SFX_DIR = os.path.join(os.getcwd(), "sfx")
SFX_SR = 44100


def _sfx_samples(name):
    import numpy as np
    sr = SFX_SR
    if name == "boom":                      # deep title / impact hit
        t = np.linspace(0, 0.75, int(sr * 0.75), False)
        freq = 120 * np.exp(-t * 3.0) + 44
        tone = np.sin(2 * np.pi * np.cumsum(freq) / sr) * np.exp(-t * 4.5)
        thud = (np.random.RandomState(1).randn(len(t)) * np.exp(-t * 45)) * 0.35
        s = (tone + thud) * 0.55
    elif name == "whoosh":                  # airy transition
        t = np.linspace(0, 0.6, int(sr * 0.6), False)
        n = np.random.RandomState(2).randn(len(t))
        n = np.convolve(n, np.ones(35) / 35, mode="same")   # soften (lowpass)
        env = np.sin(np.pi * np.linspace(0, 1, len(t))) ** 2
        s = n * env * 0.5
    elif name == "chime":                   # soft positive reveal
        t = np.linspace(0, 0.8, int(sr * 0.8), False)
        s = (np.sin(2 * np.pi * 880 * t) * 0.6 +
             np.sin(2 * np.pi * 1320 * t) * 0.3 +
             np.sin(2 * np.pi * 1760 * t) * 0.15) * np.exp(-t * 4.0) * 0.38
    elif name == "tick":                    # subtle click
        t = np.linspace(0, 0.13, int(sr * 0.13), False)
        s = np.sin(2 * np.pi * 1150 * t) * np.exp(-t * 42) * 0.3
    else:
        return None, sr
    k = int(sr * 0.006)                      # short fades to kill clicks
    if len(s) > 2 * k:
        s[:k] *= np.linspace(0, 1, k)
        s[-k:] *= np.linspace(1, 0, k)
    return s.astype(np.float32), sr


def sfx(name):
    """Return a cached wav path for a synthesized sound effect, or None."""
    path = os.path.join(SFX_DIR, name + ".wav")
    if not os.path.exists(path):
        try:
            import soundfile as sf
            samples, sr = _sfx_samples(name)
            if samples is None:
                return None
            os.makedirs(SFX_DIR, exist_ok=True)
            sf.write(path, samples, sr)
        except Exception:
            return None
    return path
