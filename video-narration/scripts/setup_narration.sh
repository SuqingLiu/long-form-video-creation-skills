#!/usr/bin/env bash
#
# setup_narration.sh — install a local neural TTS engine + voice for narration.
#
# Usage:
#   setup_narration.sh <project_dir> [engine=kokoro] [voice]
#     engine = kokoro   (default, most natural) | piper (lighter/faster)
#     voice  = kokoro: a voice NAME (default af_heart; picked at render time)
#              piper : a model name (default en_US-amy-medium; downloaded here)
#
# Kokoro downloads kokoro-v1.0.onnx (+ voices bin) into <project>/kokoro/.
# Piper downloads <voice>.onnx (+ .json) into <project>/voices/.
set -euo pipefail

PROJ="${1:?usage: setup_narration.sh <project_dir> [engine] [voice]}"
ENGINE="${2:-kokoro}"
PROJ="$(cd "$PROJ" && pwd)"

# --- choose python/pip: project-local conda env, else system --------------
if [ -x "$PROJ/bin/micromamba" ] && [ -d "$PROJ/env" ]; then
  RUN() { ( cd "$PROJ" && MAMBA_ROOT_PREFIX="$PROJ/mamba" ./bin/micromamba run -p "$PROJ/env" "$@" ); }
  echo "using project-local env at $PROJ/env"
else
  RUN() { "$@"; }
  echo "no project env found; using python/pip on PATH"
fi

if [ "$ENGINE" = "kokoro" ]; then
  echo "installing kokoro-onnx + soundfile ..."
  RUN pip install --quiet kokoro-onnx soundfile
  RUN python -c "import kokoro_onnx, soundfile" 2>/dev/null && echo "kokoro-onnx: OK" || {
    echo "error: kokoro-onnx failed to import" >&2; exit 1; }

  mkdir -p "$PROJ/kokoro"
  REL="https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
  echo "downloading Kokoro model (~310MB) + voices (~27MB) ..."
  [ -s "$PROJ/kokoro/kokoro-v1.0.onnx" ] || curl -fsSL -o "$PROJ/kokoro/kokoro-v1.0.onnx" "$REL/kokoro-v1.0.onnx"
  [ -s "$PROJ/kokoro/voices-v1.0.bin"  ] || curl -fsSL -o "$PROJ/kokoro/voices-v1.0.bin"  "$REL/voices-v1.0.bin"

  SZ=$(wc -c < "$PROJ/kokoro/kokoro-v1.0.onnx" | tr -d ' ')
  [ "$SZ" -gt 100000000 ] || { echo "error: kokoro model download looks truncated ($SZ bytes)" >&2; exit 1; }

  echo "smoke test ..."
  RUN python -c "
from kokoro_onnx import Kokoro; import soundfile as sf
k = Kokoro('$PROJ/kokoro/kokoro-v1.0.onnx','$PROJ/kokoro/voices-v1.0.bin')
s,sr = k.create('Narration is ready.', voice='${3:-af_heart}', speed=1.0, lang='en-us')
print('voices available:', len(k.get_voices()))
print('synthesis OK, %.2fs' % (len(s)/sr))
" 2>&1 | grep -vE "Warning|warn" | tail -3
  echo
  echo "ENGINE=kokoro  VOICE=${3:-af_heart}  MODEL=$PROJ/kokoro/kokoro-v1.0.onnx"
  echo "good voices: af_heart, af_bella, af_nicole, am_michael, am_adam, bf_emma"

else  # ---- piper ----
  VOICE="${3:-en_US-amy-medium}"
  echo "installing piper-tts ..."
  RUN pip install --quiet piper-tts
  RUN python -c "import piper" 2>/dev/null && echo "piper: OK" || {
    echo "error: piper failed to import" >&2; exit 1; }

  LOCALE="${VOICE%%-*}"; REST="${VOICE#*-}"; NAME="${REST%-*}"; QUAL="${REST##*-}"; LANG="${LOCALE%%_*}"
  BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main/$LANG/$LOCALE/$NAME/$QUAL"
  mkdir -p "$PROJ/voices"
  ONNX="$PROJ/voices/$VOICE.onnx"; JSON="$PROJ/voices/$VOICE.onnx.json"
  echo "downloading Piper voice '$VOICE' ..."
  curl -fsSL -o "$ONNX" "$BASE/$VOICE.onnx"
  curl -fsSL -o "$JSON" "$BASE/$VOICE.onnx.json"
  SZ=$(wc -c < "$ONNX" | tr -d ' ')
  [ "$SZ" -gt 1000000 ] || { echo "error: model only $SZ bytes — bad voice name '$VOICE'?" >&2; rm -f "$ONNX" "$JSON"; exit 1; }
  echo "smoke test ..."
  echo "Narration is ready." | RUN python -m piper -m "$ONNX" -f "$PROJ/voices/.smoke.wav" >/dev/null 2>&1 \
    && rm -f "$PROJ/voices/.smoke.wav" && echo "synthesis: OK" || echo "warning: smoke synth failed" >&2
  echo
  echo "ENGINE=piper  VOICE_MODEL=$ONNX"
fi

echo "done. Next: cp <skill>/assets/narration.py \"$PROJ\" and hook say() (see SKILL.md §3)."
