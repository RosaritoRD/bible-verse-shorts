#!/usr/bin/env python3
"""Verse Shorts in batches.

    python3 scripts/hacer_versiculos.py                 # uses entrada/lote.txt
    python3 scripts/hacer_versiculos.py otro-lote.txt
    python3 scripts/hacer_versiculos.py --solo salmo-3  # redo just one

Backgrounds in entrada/fondos/, music in entrada/musica/ (from the YouTube
Audio Library). If a Short doesn't say which clip or music to use, one is
picked at random. Output in salida/<name>.mp4 and, next to it, salida/<name>.txt
with the title, description and hashtags to copy when uploading. If a track
requires attribution, put the text in a .txt with the same name as the audio
(entrada/musica/piano.mp3 -> entrada/musica/piano.txt) and it goes in the sheet.
"""
import argparse
import os
import random
import subprocess
import sys
import tempfile
from pathlib import Path

from biblia import cargar as cargar_biblia
from lote import ANCHO, ALTO, ass_versiculos, ficha, leer_lote, repartir_tiempos

RAIZ = Path(os.environ.get("SHORTS_DIR") or Path(__file__).resolve().parent.parent)
ENTRADA, SALIDA = RAIZ / "entrada", RAIZ / "salida"
VIDEO = {".mp4", ".mov", ".mkv", ".webm"}
AUDIO = {".mp3", ".wav", ".m4a", ".ogg", ".aac"}
MAXIMO_S = 180  # YouTube's limit for a Short
IDEAL_S = 60    # longer is allowed, but fewer people finish it


class Fallo(Exception):
    pass


def elegir(carpeta, nombre, tipos, que):
    if nombre:
        p = carpeta / nombre
        if not p.exists():
            raise Fallo(f"{que} not found: {p.relative_to(RAIZ)}")
        return p
    opciones = sorted(p for p in carpeta.glob("*") if p.suffix.lower() in tipos)
    return random.choice(opciones) if opciones else None


def render(short, fondo, musica, destino):
    tiempos = repartir_tiempos(short["versiculos"])
    total = tiempos[-1][1] + 1.0  # one second of breathing room at the end
    if total > MAXIMO_S:
        raise Fallo(f"it lasts {total:.0f} s and a Short allows {MAXIMO_S}. "
                    f"Split it in two.")

    with tempfile.NamedTemporaryFile("w", suffix=".ass", delete=False,
                                     encoding="utf-8") as f:
        f.write(ass_versiculos(short["versiculos"], tiempos))
        ass = f.name

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    if fondo:
        cmd += ["-stream_loop", "-1", "-i", str(fondo)]
    else:
        cmd += ["-f", "lavfi", "-i", f"color=c=0x101418:s={ANCHO}x{ALTO}:r=30"]
    if musica:
        cmd += ["-stream_loop", "-1", "-i", str(musica)]
    # Fill 9:16 cropping whatever is left over, darken a little so the text
    # reads, and burn in the subtitles.
    vf = (f"scale={ANCHO}:{ALTO}:force_original_aspect_ratio=increase,"
          f"crop={ANCHO}:{ALTO},fps=30,eq=brightness=-0.10:saturation=0.9,"
          f"ass={ass}")
    cmd += ["-filter_complex", f"[0:v]{vf}[v]", "-map", "[v]"]
    if musica:
        af = (f"afade=t=in:d=1,afade=t=out:st={total - 2:.2f}:d=2,"
              "volume=0.9")
        cmd += ["-map", "1:a", "-af", af, "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-t", f"{total:.2f}", "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(destino)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            destino.unlink(missing_ok=True)  # never leave a half-written video
            raise Fallo("ffmpeg failed: " + (r.stderr.strip().splitlines() or ["?"])[-1])
    finally:
        Path(ass).unlink(missing_ok=True)
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lote", nargs="?", default=str(ENTRADA / "lote.txt"))
    ap.add_argument("--solo", help="only make the Short with this name")
    args = ap.parse_args()

    try:
        shorts = leer_lote(Path(args.lote).read_text(encoding="utf-8"),
                           biblia=cargar_biblia())
    except (OSError, ValueError) as e:
        sys.exit(f"✗ {args.lote}: {e}")
    if args.solo:
        shorts = [s for s in shorts if s["nombre"] == args.solo]
    if not shorts:
        sys.exit("✗ No Shorts to make in the batch.")
    SALIDA.mkdir(exist_ok=True)

    fallos = []
    for i, s in enumerate(shorts, 1):
        print(f"[{i}/{len(shorts)}] {s['nombre']}", end="  ", flush=True)
        try:
            fondo = elegir(ENTRADA / "fondos", s["clip"], VIDEO, "clip")
            musica = elegir(ENTRADA / "musica", s["musica"], AUDIO, "music")
            print(f"background={fondo.name if fondo else 'plain color'}  "
                  f"music={musica.name if musica else 'no music'}")
            destino = SALIDA / f"{s['nombre']}.mp4"
            dur = render(s, fondo, musica, destino)
            atrib = musica.with_suffix(".txt") if musica else None
            destino.with_suffix(".txt").write_text(
                ficha(s, atrib.read_text(encoding="utf-8")
                      if atrib and atrib.exists() else None), encoding="utf-8")
        except Fallo as e:
            print(f"\n      ✗ {e}")
            fallos.append(s["nombre"])
            continue
        aviso = (f"  ⚠ over {IDEAL_S} s: it can be uploaded, but retention is worse"
                 if dur > IDEAL_S else "")
        print(f"      ✓ {destino.relative_to(RAIZ)} ({dur:.0f} s){aviso}")

    print(f"\nDone: {len(shorts) - len(fallos)} of {len(shorts)}.")
    if fallos:
        sys.exit("Failed: " + ", ".join(fallos))


if __name__ == "__main__":
    main()
