#!/usr/bin/env bash
#
# extract_qa_frames.sh — sample a video into timestamped frames for visual QA.
#
# Usage:
#   extract_qa_frames.sh <video> [out_dir=frames_qa] [step_sec=2] [scale=1280:720]
#
# Frames are named t0000.png, t0002.png, ... (zero-padded seconds) so they sort
# and map cleanly to minutes. Prints MAXSEC=<n> and FRAMES=<n> at the end.
#
# ffmpeg/ffprobe: auto-detects a project-local micromamba/conda toolchain
# (./bin/micromamba + ./env, as created by the educational-video skill) and
# uses its binaries; otherwise falls back to ffmpeg/ffprobe on PATH.
set -euo pipefail

VIDEO="${1:?usage: extract_qa_frames.sh <video> [out_dir] [step_sec] [scale]}"
OUT_DIR="${2:-frames_qa}"
STEP="${3:-2}"
SCALE="${4:-1280:720}"

if [ ! -f "$VIDEO" ]; then
  echo "error: video not found: $VIDEO" >&2
  exit 1
fi

# --- pick ffmpeg/ffprobe ----------------------------------------------------
FFMPEG="ffmpeg"
FFPROBE="ffprobe"
if [ -x "./bin/micromamba" ] && [ -d "./env" ]; then
  # run inside the project-local conda env
  PRUN() { MAMBA_ROOT_PREFIX="$PWD/mamba" ./bin/micromamba run -p "$PWD/env" "$@"; }
  FFMPEG="PRUN ffmpeg"
  FFPROBE="PRUN ffprobe"
fi
run_ffmpeg()  { if [ "$FFMPEG"  = "PRUN ffmpeg"  ]; then PRUN ffmpeg  "$@"; else ffmpeg  "$@"; fi; }
run_ffprobe() { if [ "$FFPROBE" = "PRUN ffprobe" ]; then PRUN ffprobe "$@"; else ffprobe "$@"; fi; }

# --- duration ---------------------------------------------------------------
DUR="$(run_ffprobe -v error -show_entries format=duration \
        -of default=noprint_wrappers=1:nokey=1 "$VIDEO")"
DUR_INT="$(printf '%.0f' "$DUR")"

# --- extract ----------------------------------------------------------------
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"
t=0
last=0
while [ "$t" -lt "$DUR_INT" ]; do
  fn="$(printf '%s/t%04d.png' "$OUT_DIR" "$t")"
  run_ffmpeg -y -loglevel error -ss "$t" -i "$VIDEO" \
    -vf "scale=$SCALE" -frames:v 1 "$fn"
  last="$t"
  t=$((t + STEP))
done

COUNT="$(find "$OUT_DIR" -name 't*.png' | wc -l | tr -d ' ')"
echo "OUT_DIR=$OUT_DIR"
echo "MAXSEC=$last"
echo "FRAMES=$COUNT"
