#!/usr/bin/env bash
# Subtitled clips from entrada/clipping/  (./clipping.sh video.mp4 --desde 1:20 --hasta 2:05)
cd "$(dirname "$0")" && exec .venv/bin/python scripts/hacer_clipping.py "$@" 2> >(grep -v Warning >&2)
