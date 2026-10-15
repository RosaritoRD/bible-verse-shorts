#!/usr/bin/env bash
# Full test run: tests + one verse Short + one clip, in a temporary folder
# with the material in notas/prueba/material (doesn't touch entrada/ or salida/).
#   ./probar.sh           everything (clipping takes ~1 min because of Whisper)
#   ./probar.sh rapido    without clipping
set -euo pipefail
cd "$(dirname "$0")"
M=notas/prueba/material
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT
fallo() { echo "✗ $*"; exit 1; }

echo "== 1. Tests"
.venv/bin/python -m pytest -q scripts | tail -1

echo "== 2. Bible"
[ -f biblia/rv1909.json ] || python3 scripts/biblia.py preparar

echo "== 3. Verse Short"
mkdir -p "$T"/entrada/{fondos,musica,clipping}
cp $M/fondo-prueba.mp4 "$T/entrada/fondos/"
cp $M/musica-prueba.mp3 $M/musica-prueba.txt "$T/entrada/musica/"
printf 'nombre: prueba\nSalmos 23:1-2\nJuan 3:16 | Texto propio de prueba.\n' > "$T/entrada/lote.txt"
SHORTS_DIR="$T" python3 scripts/hacer_versiculos.py "$T/entrada/lote.txt" | tail -2
V="$T/salida/prueba.mp4"
[ -f "$V" ] || fallo "no video was produced"
dims=$(ffprobe -v error -select_streams v -show_entries stream=width,height -of csv=p=0 "$V")
[ "$dims" = "1080,1920" ] || fallo "size $dims, expected 1080,1920"
ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 "$V" | grep -q audio || fallo "no music"
grep -q "Salmos capítulo 23, versículo 2" "$T/salida/prueba.txt" || fallo "the sheet is missing the reference"
grep -q "Pista de prueba" "$T/salida/prueba.txt" || fallo "the sheet is missing the attribution"
echo "   ✓ 1080x1920 with music, sheet with references and attribution"

if [ "${1:-}" != "rapido" ]; then
  echo "== 4. Clipping (Whisper)"
  cp $M/predica-prueba.mp4 "$T/entrada/clipping/"
  out=$(SHORTS_DIR="$T" .venv/bin/python scripts/hacer_clipping.py --ajuste entero 2>&1 | grep -v Warning)
  echo "$out" | tail -2
  echo "$out" | grep -q "Juan capítulo 3, versículo 16" || fallo "did not detect Juan 3:16"
  echo "$out" | grep -q "Salmos capítulo 23, versículo 1" || fallo "did not detect Salmos 23:1"
  [ -f "$T/salida/clipping/predica-prueba.mp4" ] || fallo "no clip was produced"
  echo "   ✓ vertical clip with subtitles and both references detected"
fi

echo
echo "✓ All good."
