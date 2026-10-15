#!/usr/bin/env bash
# Makes every Short in entrada/lote.txt  (./versiculos.sh --solo name  for just one)
cd "$(dirname "$0")" && exec python3 scripts/hacer_versiculos.py "$@"
