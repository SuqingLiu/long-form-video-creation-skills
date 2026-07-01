#!/usr/bin/env bash
#
# setup_video_env.sh — sudo-free Manim toolchain bootstrap for the
# educational-video skill. Installs NOTHING system-wide: everything lives
# under the target project dir (bin/micromamba, env/, mamba/).
#
# Why micromamba/conda-forge: manim needs cairo+pango+pycairo+ffmpeg. On
# locked-down machines you often can't use sudo/Homebrew, and pycairo has no
# wheel (it compiles, needing pkg-config). conda-forge ships all of it prebuilt.
#
# Usage:
#   bash setup_video_env.sh [PROJECT_DIR]      # defaults to $PWD
#
# After it finishes, render with:
#   MAMBA_ROOT_PREFIX="$PROJECT_DIR/mamba" \
#     "$PROJECT_DIR/bin/micromamba" run -p "$PROJECT_DIR/env" \
#     manim -qh scene.py SceneName
#
set -euo pipefail

PROJECT_DIR="${1:-$PWD}"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

run_in_env() {
  MAMBA_ROOT_PREFIX="$PROJECT_DIR/mamba" \
    "$PROJECT_DIR/bin/micromamba" run -p "$PROJECT_DIR/env" "$@"
}

# 1) Reuse an existing, working env (don't re-download hundreds of MB).
if [ -x "$PROJECT_DIR/bin/micromamba" ] && [ -d "$PROJECT_DIR/env" ]; then
  if run_in_env manim --version >/dev/null 2>&1; then
    echo "✓ manim env already present and working at $PROJECT_DIR/env"
    run_in_env manim --version
    exit 0
  fi
fi

# 2) Detect platform for the micromamba download.
OS="$(uname -s)"; ARCH="$(uname -m)"
case "$OS-$ARCH" in
  Darwin-arm64)   PLAT="osx-arm64" ;;
  Darwin-x86_64)  PLAT="osx-64" ;;
  Linux-x86_64)   PLAT="linux-64" ;;
  Linux-aarch64)  PLAT="linux-aarch64" ;;
  *) echo "Unsupported platform: $OS-$ARCH" >&2; exit 1 ;;
esac
echo "Platform: $PLAT"

# 3) Bootstrap micromamba (static binary; no sudo, no package manager).
if [ ! -x "$PROJECT_DIR/bin/micromamba" ]; then
  echo "Downloading micromamba..."
  curl -Ls "https://micro.mamba.pm/api/micromamba/${PLAT}/latest" \
    | tar -xvj bin/micromamba
fi
"$PROJECT_DIR/bin/micromamba" --version

# 4) Create the isolated env with manim + native deps + ffmpeg (all prebuilt).
echo "Creating conda env (this downloads a few hundred MB the first time)..."
MAMBA_ROOT_PREFIX="$PROJECT_DIR/mamba" \
  "$PROJECT_DIR/bin/micromamba" create -y -p "$PROJECT_DIR/env" \
  -c conda-forge python=3.12 manim

# 5) Verify. (No LaTeX is installed — author LaTeX-free; see SKILL.md §3.)
echo "----------------------------------------------------------------"
run_in_env manim --version
run_in_env ffmpeg -version | head -1
echo "✓ Ready. Render with:"
echo "  MAMBA_ROOT_PREFIX=\"$PROJECT_DIR/mamba\" \"$PROJECT_DIR/bin/micromamba\" run -p \"$PROJECT_DIR/env\" manim -qh scene.py SceneName"
