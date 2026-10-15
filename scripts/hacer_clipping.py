#!/usr/bin/env python3
"""Clips verticales con subtítulos para campañas de clipping.

    .venv/bin/python scripts/hacer_clipping.py                     # todo entrada/clipping/
    .venv/bin/python scripts/hacer_clipping.py video.mp4 --desde 1:20 --hasta 2:05

Conserva el audio original (las campañas lo exigen casi siempre), transcribe
con Whisper, pone la frase en pantalla al ritmo de la voz y, cuando alguien
cita la Biblia ("Juan 3:16"), muestra el cartel "Juan 3, versículo 16".
Resultado en salida/clipping/<nombre>.mp4.
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from lote import ANCHO, ALTO, agrupar_palabras, ass_clipping
from referencias import detectar

RAIZ = Path(os.environ.get("SHORTS_DIR") or Path(__file__).resolve().parent.parent)
ENTRADA, SALIDA = RAIZ / "entrada" / "clipping", RAIZ / "salida" / "clipping"
VIDEO = {".mp4", ".mov", ".mkv", ".webm"}
MAXIMO_S = 180


def segundos(t):
    """'1:20' -> 80.0, '1:00:05' -> 3605.0. None si no se dio."""
    if t is None:
        return None
    s = 0.0
    try:
        for parte in str(t).split(":"):
            s = s * 60 + float(parte)
    except ValueError:
        raise ValueError(f"no entiendo el tiempo {t!r}: usa 1:20 o 1:00:05") from None
    return s


def calcular_tramo(desde_txt, hasta_txt, dur):
    """El tramo (desde, hasta) en segundos, ya comprobado contra la duración.

    Un error aquí sale como mensaje claro antes de gastar tiempo en Whisper,
    en vez de un -t negativo que ffmpeg rechaza con un error críptico."""
    desde = segundos(desde_txt) or 0.0
    hasta = segundos(hasta_txt)
    if desde >= dur:
        raise ValueError(f"empieza en {desde:.0f} s pero el video dura {dur:.0f} s")
    if hasta is None or hasta > dur:
        hasta = dur
    if hasta <= desde:
        raise ValueError(f"--hasta ({hasta:.0f} s) tiene que ir después de --desde ({desde:.0f} s)")
    return desde, min(hasta, desde + MAXIMO_S)


def duracion(video):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration", "-of", "csv=p=0", str(video)],
                         capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def cortar(video, desde, hasta, destino):
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-ss", f"{desde:.2f}", "-i", str(video), "-t", f"{hasta - desde:.2f}",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
           "-c:a", "aac", "-b:a", "192k", str(destino)]
    subprocess.run(cmd, check=True, capture_output=True)


def audio_16k(video):
    """Audio mono a 16 kHz como lo quiere Whisper. Se decodifica con ffmpeg
    porque el lector que trae faster-whisper (PyAV) falla con Python 3.14."""
    import numpy as np
    crudo = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error",
                            "-i", str(video), "-ac", "1", "-ar", "16000",
                            "-f", "f32le", "-"], capture_output=True, check=True)
    return np.frombuffer(crudo.stdout, dtype=np.float32)


def transcribir(modelo, video):
    segs, _ = modelo.transcribe(audio_16k(video), language="es",
                                word_timestamps=True, vad_filter=True)
    palabras, citas = [], []
    for seg in segs:
        palabras += [(w.start, w.end, w.word.strip()) for w in (seg.words or [])]
        for c in detectar(seg.text):
            citas.append((seg.start, seg.end + 2.0, c))
    return palabras, citas


def filtro(ajuste, ass):
    """recorte: llena la pantalla cortando los lados (bien si quien habla
    está al centro). entero: el video completo en medio sobre una copia
    difuminada de sí mismo (no se pierde nada del encuadre)."""
    if ajuste == "entero":
        return (f"[0:v]split[a][b];"
                f"[a]scale={ANCHO}:{ALTO}:force_original_aspect_ratio=increase,"
                f"crop={ANCHO}:{ALTO},boxblur=25:2,eq=brightness=-0.15[fondo];"
                f"[b]scale={ANCHO}:-2[frente];"
                f"[fondo][frente]overlay=(W-w)/2:(H-h)/2,fps=30,ass={ass}[v]")
    return (f"[0:v]scale={ANCHO}:{ALTO}:force_original_aspect_ratio=increase,"
            f"crop={ANCHO}:{ALTO},fps=30,ass={ass}[v]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("videos", nargs="*")
    ap.add_argument("--desde", help="inicio del tramo, p. ej. 1:20")
    ap.add_argument("--hasta", help="fin del tramo, p. ej. 2:05")
    ap.add_argument("--ajuste", choices=["recorte", "entero"], default="recorte",
                    help="recorte = llenar la pantalla; entero = video completo "
                         "con fondo difuminado")
    ap.add_argument("--modelo", default="small",
                    help="tiny/base/small/medium (más grande = mejor y más lento)")
    args = ap.parse_args()

    videos = ([Path(v) if Path(v).exists() else ENTRADA / v for v in args.videos]
              or sorted(p for p in ENTRADA.glob("*") if p.suffix.lower() in VIDEO))
    if not videos:
        sys.exit(f"✗ No hay videos en {ENTRADA}")
    if (args.desde or args.hasta) and len(videos) > 1:
        sys.exit("✗ --desde/--hasta es para un solo video.")

    from faster_whisper import WhisperModel  # tarda en cargar: solo si hace falta
    print(f"Cargando Whisper ({args.modelo})…")
    modelo = WhisperModel(args.modelo, device="cpu", compute_type="int8")
    SALIDA.mkdir(parents=True, exist_ok=True)

    fallos = []
    for i, video in enumerate(videos, 1):
        try:
            procesar(i, len(videos), video, args, modelo)
        except SinImagen:
            print(f"      ✗ {video.name}: no tiene imagen (¿es solo audio?)")
            fallos.append(video.name)
        except ValueError as e:  # tramo mal pedido: este video falla, el lote sigue
            print(f"      ✗ {video.name}: {e}")
            fallos.append(video.name)
        except subprocess.CalledProcessError as e:
            err = e.stderr or b""
            err = (err.decode(errors="replace") if isinstance(err, bytes)
                   else err).strip().splitlines()
            print(f"      ✗ {video.name}: ffmpeg falló: {err[-1] if err else e}")
            (SALIDA / f"{video.stem}.mp4").unlink(missing_ok=True)
            fallos.append(video.name)
    print(f"\nListos {len(videos) - len(fallos)} de {len(videos)}.")
    if fallos:
        sys.exit("Fallaron: " + ", ".join(fallos))


class SinImagen(Exception):
    pass


def tiene_imagen(video):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v",
                          "-show_entries", "stream=codec_type", "-of", "csv=p=0",
                          str(video)], capture_output=True, text=True)
    return "video" in out.stdout


def procesar(i, n, video, args, modelo):
    if not tiene_imagen(video):
        raise SinImagen()
    nombre = video.stem
    dur = duracion(video)
    desde, hasta = calcular_tramo(args.desde, args.hasta, dur)
    pedido = (segundos(args.hasta) or dur) - desde
    if pedido > MAXIMO_S and hasta - desde == MAXIMO_S:
        print(f"[{i}/{n}] {nombre}: ⚠ dura {pedido:.0f} s; "
              f"se corta a {MAXIMO_S} s (tope de un Short).")
    print(f"[{i}/{n}] {nombre}: transcribiendo…")
    with tempfile.TemporaryDirectory() as tmp:
        tramo = Path(tmp) / "tramo.mp4"
        cortar(video, desde, hasta, tramo)
        palabras, citas = transcribir(modelo, tramo)
        ass = Path(tmp) / "subs.ass"
        ass.write_text(ass_clipping(agrupar_palabras(palabras), citas),
                       encoding="utf-8")
        destino = SALIDA / f"{nombre}.mp4"
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                        "-i", str(tramo), "-filter_complex",
                        filtro(args.ajuste, ass), "-map", "[v]", "-map",
                        "0:a?", "-c:v", "libx264",
                        "-preset", "veryfast", "-crf", "20",
                        "-pix_fmt", "yuv420p", "-c:a", "copy",
                        "-movflags", "+faststart", str(destino)],
                       check=True, capture_output=True)
    extra = f", citas: {', '.join(c for _, _, c in citas)}" if citas else ""
    print(f"      ✓ {destino.relative_to(RAIZ)}{extra}")


if __name__ == "__main__":
    main()
