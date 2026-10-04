#!/usr/bin/env bash
# Install the Python packages the tools need. Safe to run more than once.
set -euo pipefail
cd "$(dirname "$0")"
python3 -m pip install --quiet --disable-pip-version-check -r requirements.txt 2>/dev/null \
  || python3 -m pip install --quiet --disable-pip-version-check --break-system-packages -r requirements.txt
mkdir -p inputs work
python3 -c "import PIL, numpy, cv2, fontTools, imageio_ffmpeg; print('setup ok')"
