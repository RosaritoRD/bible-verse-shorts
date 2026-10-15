#!/usr/bin/env bash
# Hace todos los shorts de entrada/lote.txt  (./versiculos.sh --solo nombre  para uno)
cd "$(dirname "$0")" && exec python3 scripts/hacer_versiculos.py "$@"
