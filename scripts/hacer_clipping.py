#!/usr/bin/env python3
"""Subtitled vertical clips for clipping campaigns.

    .venv/bin/python scripts/hacer_clipping.py                     # all of entrada/clipping/
    .venv/bin/python scripts/hacer_clipping.py video.mp4 --desde 1:20 --hasta 2:05

Keeps the original audio (campaigns almost always require it), transcribes
with Whisper, puts the phrase on screen in time with the voice and, when
someone quotes the Bible ("Juan 3:16"), shows the card "Juan 3, versículo 16".
Output in salida/clipping/<name>.mp4.
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
    """'1:20' -> 80.0, '1:00:05' -> 3605.0. None if not given."""
    if t is None:
        return None
    s = 0.0
    try:
        for parte in str(t).split(":"):
            s = s * 60 + float(parte)
    except ValueError:
        raise ValueError(f"can't read the time {t!r}: use 1:20 or 1:00:05") from None
    return s


def calcular_tramo(desde_txt, hasta_txt, dur):
    """The (start, end) segment in seconds, already checked against the duration.

    An error here comes out as a clear message before spending time on Whisper,
    instead of a negative -t that ffmpeg rejects with a cryptic error."""
    desde = segundos(desde_txt) or 0.0
    hasta = segundos(hasta_txt)
    if desde >= dur:
        raise ValueError(f"starts at {desde:.0f} s but the video lasts {dur:.0f} s")
    if hasta is None or hasta > dur:
        hasta = dur
    if hasta <= desde:
        raise ValueError(f"--hasta ({hasta:.0f} s) must come after --desde ({desde:.0f} s)")
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
    """Mono 16 kHz audio, the way Whisper wants it. Decoded with ffmpeg because
    the reader bundled with faster-whisper (PyAV) fails on Python 3.14."""
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
    """recorte: fills the screen by cropping the sides (fine if the speaker is
    centered). entero: the whole video in the middle over a blurred copy of
    itself (nothing in the frame is lost)."""
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
    ap.add_argument("--desde", help="segment start, e.g. 1:20")
    ap.add_argument("--hasta", help="segment end, e.g. 2:05")
    ap.add_argument("--ajuste", choices=["recorte", "entero"], default="recorte",
                    help="recorte = fill the screen; entero = whole video "
                         "over a blurred background")
    ap.add_argument("--modelo", default="small",
                    help="tiny/base/small/medium (bigger = better and slower)")
    args = ap.parse_args()

    videos = ([Path(v) if Path(v).exists() else ENTRADA / v for v in args.videos]
              or sorted(p for p in ENTRADA.glob("*") if p.suffix.lower() in VIDEO))
    if not videos:
        sys.exit(f"✗ No videos in {ENTRADA}")
    if (args.desde or args.hasta) and len(videos) > 1:
        sys.exit("✗ --desde/--hasta only works with a single video.")

    from faster_whisper import WhisperModel  # slow to load: only when needed
    print(f"Loading Whisper ({args.modelo})…")
    modelo = WhisperModel(args.modelo, device="cpu", compute_type="int8")
    SALIDA.mkdir(parents=True, exist_ok=True)

    fallos = []
    for i, video in enumerate(videos, 1):
        try:
            procesar(i, len(videos), video, args, modelo)
        except SinImagen:
            print(f"      ✗ {video.name}: has no picture (audio only?)")
            fallos.append(video.name)
        except ValueError as e:  # bad segment: this video fails, the batch goes on
            print(f"      ✗ {video.name}: {e}")
            fallos.append(video.name)
        except subprocess.CalledProcessError as e:
            err = e.stderr or b""
            err = (err.decode(errors="replace") if isinstance(err, bytes)
                   else err).strip().splitlines()
            print(f"      ✗ {video.name}: ffmpeg failed: {err[-1] if err else e}")
            (SALIDA / f"{video.stem}.mp4").unlink(missing_ok=True)
            fallos.append(video.name)
    print(f"\nDone: {len(videos) - len(fallos)} of {len(videos)}.")
    if fallos:
        sys.exit("Failed: " + ", ".join(fallos))


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
        print(f"[{i}/{n}] {nombre}: ⚠ lasts {pedido:.0f} s; "
              f"cut to {MAXIMO_S} s (a Short's limit).")
    print(f"[{i}/{n}] {nombre}: transcribing…")
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
    extra = f", references: {', '.join(c for _, _, c in citas)}" if citas else ""
    print(f"      ✓ {destino.relative_to(RAIZ)}{extra}")


if __name__ == "__main__":
    main()
