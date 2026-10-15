# Cómo usar — Shorts de versículos y clipping

Todo se hace desde esta carpeta:

    cd shorts-versiculos

---

## A. Shorts de versículos (para tus canales)

### 1. Pon los fondos
Videos de paisajes, cielo, agua o luz en `entrada/fondos/`. Pueden ser horizontales
o verticales; se recortan solos a vertical. Si el clip es más corto que el
short, se repite.

Fuentes gratis y con licencia de uso comercial: **Pexels** y **Pixabay** (videos).
No uses videos sacados de Google ni de otros canales.

### 2. Pon la música
Pistas de la **Biblioteca de audio de YouTube Studio** (YouTube Studio → Biblioteca
de audio → Descargar) en `entrada/musica/`.

Algunas pistas piden **atribución** (dice "Se requiere atribución"). En ese caso,
copia el texto que te da YouTube en un `.txt` con el mismo nombre que el audio:

    entrada/musica/Piano Suave.mp3
    entrada/musica/Piano Suave.txt   ← el texto de atribución

Así sale solo en la descripción de cada short.

### 3. Escribe el lote
Abre `entrada/lote.txt`. Cada short es un bloque y los bloques se separan con `---`:

    Salmos 3:4
    ---
    nombre: confianza
    Proverbios 3:5-6
    Filipenses 4:13
    ---
    Salmos 23:1-3

- Basta con la **cita**: el texto sale solo de la Reina-Valera 1909.
- En pantalla aparece así: **Salmos capítulo 3, versículo 4**.
- Un rango (`Salmos 23:1-3`) sale como una pantalla por versículo.
- ¿Prefieres tu propio texto? `Juan 3:16 | tu texto aquí`
- ⚠ En **Job 39 a 41** la Biblia de 1909 numera distinto que las modernas: ahí
  pon el texto a mano con `|`.

### 4. Hazlos
    ./versiculos.sh

Se hacen todos, uno detrás de otro. En `salida/` queda por cada uno:
- `nombre.mp4` → el short (1080×1920, vertical)
- `nombre.txt` → título, descripción y hashtags para copiar al subirlo

¿Quieres rehacer solo uno? `./versiculos.sh --solo confianza`

---

## B. Clipping (campañas que pagan por vistas)

### 1. Pon los videos
Los videos que te da la campaña en `entrada/clipping/`.

### 2. Hazlos
    ./clipping.sh                                          # todos
    ./clipping.sh predica.mp4 --desde 12:30 --hasta 13:20   # solo un tramo
    ./clipping.sh --ajuste entero                          # sin recortar los lados

- Deja el **audio original** (las campañas casi siempre lo exigen).
- Pone lo que se dice en pantalla, al ritmo de la voz.
- Si alguien cita la Biblia ("Juan 3:16"), sale arriba el cartel
  **Juan capítulo 3, versículo 16**.
- `--ajuste entero`: video completo con fondo difuminado. Úsalo si hay varias
  personas o si quien habla no está al centro.
- `--modelo medium`: transcribe mejor, pero tarda unas 3 veces más.

Salen en `salida/clipping/`.

⚠ **Lee las reglas de cada campaña** antes de subir: algunas no permiten
música encima, piden un hashtag o una mención, o tienen duración mínima.

---

## Comprobar que todo funciona
    ./probar.sh          # todo, ~40 s
    ./probar.sh rapido   # sin la parte de Whisper

## Reglas para no perder el canal
- Usa solo fondos de Pexels o Pixabay, música de la Biblioteca de YouTube y clips de
  campañas que te den permiso.
- **No resubas videos de otros canales** sin permiso: lleva a reclamos, strikes
  y al cierre de *todos* tus canales relacionados.
- La RVR1960 y la NVI tienen derechos de autor; la 1909 que usa esto, no.

Ejemplos ya hechos: `notas/ejemplos/`.
