#!/bin/sh
set -eu
BLENDER_BIN="${BLENDER_BIN:-/Applications/Blender.app/Contents/MacOS/Blender}"
"$BLENDER_BIN" --background "Panelki Blocks.blend" --python scripts/export_assets.py
