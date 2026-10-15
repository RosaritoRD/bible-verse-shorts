#!/usr/bin/env python3
"""Shorts de versículos en serie.

    python3 scripts/hacer_versiculos.py                 # usa entrada/lote.txt
    python3 scripts/hacer_versiculos.py otro-lote.txt
    python3 scripts/hacer_versiculos.py --solo salmo-3  # rehacer uno

Fondos en entrada/fondos/, música en entrada/musica/ (de la Biblioteca de
audio de YouTube). Si un short no dice qué clip o música usar, se elige uno
al azar. Resultado en salida/<nombre>.mp4 y, al lado, salida/<nombre>.txt con título,
descripción y hashtags para copiar al subir. Si la canción pide atribución,
pon el texto en un .txt con el mismo nombre que el audio
(entrada/musica/piano.mp3 -> entrada/musica/piano.txt) y saldrá en la ficha.
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
MAXIMO_S = 180  # tope de YouTube para un Short
IDEAL_S = 60    # más largo se puede, pero la gente lo termina menos


class Fallo(Exception):
    pass


def elegir(carpeta, nombre, tipos, que):
    if nombre:
        p = carpeta / nombre
        if not p.exists():
            raise Fallo(f"no existe {que}: {p.relative_to(RAIZ)}")
        return p
    opciones = sorted(p for p in carpeta.glob("*") if p.suffix.lower() in tipos)
    return random.choice(opciones) if opciones else None


def render(short, fondo, musica, destino):
    tiempos = repartir_tiempos(short["versiculos"])
    total = tiempos[-1][1] + 1.0  # un segundo de aire al final
    if total > MAXIMO_S:
        raise Fallo(f"dura {total:.0f} s y un Short admite {MAXIMO_S}. "
                    f"Pártelo en dos.")

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
    # Llenar 9:16 recortando lo que sobre, oscurecer un poco para que el
    # texto se lea, y quemar los subtítulos.
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
            destino.unlink(missing_ok=True)  # no dejar un video a medias
            raise Fallo("ffmpeg falló: " + (r.stderr.strip().splitlines() or ["?"])[-1])
    finally:
        Path(ass).unlink(missing_ok=True)
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lote", nargs="?", default=str(ENTRADA / "lote.txt"))
    ap.add_argument("--solo", help="hacer solo el short con este nombre")
    args = ap.parse_args()

    try:
        shorts = leer_lote(Path(args.lote).read_text(encoding="utf-8"),
                           biblia=cargar_biblia())
    except (OSError, ValueError) as e:
        sys.exit(f"✗ {args.lote}: {e}")
    if args.solo:
        shorts = [s for s in shorts if s["nombre"] == args.solo]
    if not shorts:
        sys.exit("✗ No hay shorts que hacer en el lote.")
    SALIDA.mkdir(exist_ok=True)

    fallos = []
    for i, s in enumerate(shorts, 1):
        print(f"[{i}/{len(shorts)}] {s['nombre']}", end="  ", flush=True)
        try:
            fondo = elegir(ENTRADA / "fondos", s["clip"], VIDEO, "el clip")
            musica = elegir(ENTRADA / "musica", s["musica"], AUDIO, "la música")
            print(f"fondo={fondo.name if fondo else 'color liso'}  "
                  f"música={musica.name if musica else 'sin música'}")
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
        aviso = (f"  ⚠ pasa de {IDEAL_S} s: se puede subir, pero retiene peor"
                 if dur > IDEAL_S else "")
        print(f"      ✓ {destino.relative_to(RAIZ)} ({dur:.0f} s){aviso}")

    print(f"\nListos {len(shorts) - len(fallos)} de {len(shorts)}.")
    if fallos:
        sys.exit("Fallaron: " + ", ".join(fallos))


if __name__ == "__main__":
    main()
