# shorts-versiculos

## What it is
A batch factory for vertical YouTube Shorts for Spanish-language Christian channels:
(A) a Bible verse on screen over stock footage with music from the YouTube Audio
Library; (B) clips for clipping campaigns (paid per view) with subtitles and a
Bible-reference title card.

On-screen text, references and upload sheets are **Spanish on purpose** — that's
the product. Code comments, CLI messages and docs are in English.

## Status
The pipeline is built and tested with synthetic material (`./probar.sh` green,
51 tests). `entrada/` ships empty on purpose: if test material is left there, the
random picker will put it into real Shorts.
Usage guide: `HOW-TO-USE.md`.

## Web dashboard (optional)
It can also be driven from the **Oraflow dashboard → Shorts and Clipping tabs**
(`utils/shorts-studio-service.js` in Oraflow). The Oraflow container mounts this
folder at `/shorts` (SHORTS_DIR) and runs the same scripts with its own Python
(faster-whisper installed in the image). `entrada/` and `salida/` must be writable
by the container's user (uid 1000).

## Pipeline
- `scripts/referencias.py`: "Salmos 3:4" → "Salmos capítulo 3, versículo 4"
  (chosen because it sounds natural when read). With numbers the Bible order wins
  (chapter:verse); with words ("Juan versículo 3 capítulo 5") each word says what
  it is. `detectar()` finds references in speech (Whisper writes "Juan 3 16",
  without the colon).
- `scripts/biblia.py`: RV1909 from eBible.org (public domain) → `biblia/rv1909.json`.
  Minimal modernization (á→a, fué→fue, small caps), strips psalm titles,
  "(Selah.)" and brackets. Never changes words.
- `scripts/lote.py` (pure, tested): lote.txt → Shorts, timing (~2.4 words/s,
  min 4 s), ASS subtitles, upload sheet (title/description/hashtags/attribution).
- `scripts/hacer_versiculos.py` / `hacer_clipping.py`: ffmpeg + libass;
  clipping uses faster-whisper (small, CPU int8) in `.venv`.
- Install on a new machine: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && python3 scripts/biblia.py preparar`
- `SHORTS_DIR` changes the working folder (used by `probar.sh`).

## Gotchas
- faster-whisper reads audio with PyAV, which fails on Python 3.14
  (`metadata_errors`) → it gets audio already decoded by ffmpeg (`audio_16k`).
- The ASS styles are f-strings: drop the `f` and the margin becomes literal text
  and libass puts the text wherever it likes (a test guards this).
- eBible's RV1909 numbers Job 39–41 differently (39:30 merges several verses and
  Job 40:1 = modern 40:6). Documented in HOW-TO-USE; not fixed automatically.
- The bottom ~25 % is covered by the Shorts title and buttons: the reference sits
  at y=1180 and the verse grows upward from there.

## Rules
- Never re-upload other people's content without permission (strikes can take
  down every related channel). Clipping only from campaigns that allow it.
- Modern Bibles (RVR1960, NVI) are copyrighted → the 1909 by default.

## Don't mix
This project is independent: it doesn't need Oraflow to work.
