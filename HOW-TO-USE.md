# How to use — Verse Shorts and clipping

Everything runs from this folder:

    cd shorts-versiculos

The videos come out in **Spanish** (verse, reference and upload sheet); the
commands and messages are in English.

---

## A. Verse Shorts (for your channels)

### 1. Add backgrounds
Landscape, sky, water or light videos go in `entrada/fondos/`. They can be
horizontal or vertical; they're cropped to vertical automatically. If a clip is
shorter than the Short, it loops.

Free sources with a commercial license: **Pexels** and **Pixabay** (videos).
Don't use videos taken from Google or from other channels.

### 2. Add music
Tracks from the **YouTube Studio Audio Library** (YouTube Studio → Audio Library
→ Download) go in `entrada/musica/`.

Some tracks require **attribution** ("Attribution required"). In that case, copy
the text YouTube gives you into a `.txt` with the same name as the audio:

    entrada/musica/Soft Piano.mp3
    entrada/musica/Soft Piano.txt   ← the attribution text

It then appears automatically in each Short's description.

### 3. Write the batch
Open `entrada/lote.txt`. Each Short is a block, and blocks are separated by `---`:

    Salmos 3:4
    ---
    nombre: confianza
    Proverbios 3:5-6
    Filipenses 4:13
    ---
    Salmos 23:1-3

- The **reference** is enough: the text comes from the Reina-Valera 1909.
- On screen it reads: **Salmos capítulo 3, versículo 4**.
- A range (`Salmos 23:1-3`) becomes one screen per verse.
- Prefer your own text? `Juan 3:16 | your text here`
- Optional lines at the top of a block: `clip: x.mp4`, `musica: y.mp3`, `nombre: my-short`.
- ⚠ In **Job 39 to 41** the 1909 Bible numbers verses differently from modern
  ones: type the text by hand there with `|`.

### 4. Make them
    ./versiculos.sh

They're all made, one after another. For each one, `salida/` gets:
- `name.mp4` → the Short (1080×1920, vertical)
- `name.txt` → title, description and hashtags to copy when uploading

Redo just one? `./versiculos.sh --solo confianza`

---

## B. Clipping (campaigns that pay per view)

### 1. Add the videos
The videos the campaign gives you go in `entrada/clipping/`.

### 2. Make them
    ./clipping.sh                                          # all of them
    ./clipping.sh sermon.mp4 --desde 12:30 --hasta 13:20    # just one segment
    ./clipping.sh --ajuste entero                          # without cropping the sides

- Keeps the **original audio** (campaigns almost always require it).
- Puts what's said on screen, in time with the voice.
- When someone quotes the Bible ("Juan 3:16"), the card
  **Juan capítulo 3, versículo 16** appears at the top.
- `--ajuste entero`: the whole video over a blurred background. Use it when there
  are several people or the speaker isn't centered.
- `--modelo medium`: better transcription, but about 3× slower.

Output goes to `salida/clipping/`.

⚠ **Read each campaign's rules** before uploading: some don't allow music on top,
require a hashtag or a mention, or have a minimum length.

---

## Check that everything works
    ./probar.sh          # everything, ~40 s
    ./probar.sh rapido   # without the Whisper part

## Rules to keep your channel
- Only use backgrounds from Pexels or Pixabay, music from the YouTube Audio
  Library and clips from campaigns that give you permission.
- **Don't re-upload videos from other channels** without permission: it leads to
  claims, strikes and the shutdown of *all* your related channels.
- The RVR1960 and NVI are copyrighted; the 1909 used here is not.
