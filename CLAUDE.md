# shorts-versiculos

## Qué es
Fábrica en serie de YouTube Shorts verticales para canales cristianos:
(A) versículo en pantalla sobre un fondo de stock con música de la Biblioteca de
audio de YouTube; (B) clips para campañas de clipping (pago por vistas) con
subtítulos y cartel de cita bíblica.

## Estado (01/10/2026)
Pipeline construido y probado con material sintético (`./probar.sh` en verde,
42 tests). Todavía **sin fondos, música ni canal reales**: `entrada/` está vacía
a propósito (si se deja material de prueba, el azar lo mete en shorts reales).
Guía de uso: `COMO-USAR.md`.

## Panel web (01/10/2026)
También se usa desde **el panel de Oraflow → pestañas Shorts y Clipping** (Oraflow,
`Oraflow`, `utils/shorts-studio-service.js`). El contenedor
de Oraflow monta esta carpeta en `/shorts` (SHORTS_DIR) y corre los mismos scripts
con su Python 3.10 (faster-whisper instalado en la imagen). `entrada/` y `salida/` son
del uid 1000 (pwuser) para que el contenedor escriba. No dejar material de prueba en
`entrada/`: el sorteo de fondos/música lo usaría en shorts reales.

## Pipeline
- `scripts/referencias.py`: "Salmos 3:4" → "Salmos capítulo 3, versículo 4"
  (formato elegido para que suene natural). Con números manda el orden bíblico (cap:vers); con
  palabras ("Juan versículo 3 capítulo 5") manda cada palabra. `detectar()` busca
  citas en lo hablado (Whisper escribe "Juan 3 16", sin dos puntos).
- `scripts/biblia.py`: RV1909 de eBible.org (dominio público) → `biblia/rv1909.json`.
  Modernización mínima (á→a, fué→fue, versalitas), quita títulos de salmos,
  "(Selah.)" y corchetes. No cambia palabras.
- `scripts/lote.py` (puro, testeado): lote.txt → shorts, tiempos (~2,4 palabras/s,
  mín. 4 s), subtítulos ASS, ficha de subida (título/descr./hashtags/atribución).
- `scripts/hacer_versiculos.py` / `hacer_clipping.py`: ffmpeg + libass;
  clipping usa faster-whisper (small, CPU int8) en `.venv`.
- Instalar en máquina nueva: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && python3 scripts/biblia.py preparar`
- `SHORTS_DIR` cambia la carpeta de trabajo (lo usa `probar.sh`).

## Trampas
- faster-whisper lee el audio con PyAV, que falla en Python 3.14
  (`metadata_errors`) → se le pasa el audio ya decodificado por ffmpeg (`audio_16k`).
- Los estilos ASS son f-strings: si falta la `f`, el margen queda como texto
  literal y libass coloca el texto donde quiere (hay un test que lo vigila).
- La RV1909 de eBible numera distinto Job 39–41 (39:30 junta varios versículos
  y Job 40:1 = 40:6 moderno). Documentado en COMO-USAR; no se corrige solo.
- La zona inferior (~25 %) la tapan el título y los botones de Shorts: la cita
  va en y=1180 y el versículo crece hacia arriba desde ahí.

## Reglas
- Nada de resubir contenido ajeno sin permiso (strikes que tumban todos los
  canales relacionados). Clipping solo de campañas con permiso.
- The Chosen: solo si confirman que lo permiten.
- Biblias modernas (RVR1960, NVI) tienen copyright → por defecto la 1909.

## No mezclar
Este proyecto es independiente: no necesita Oraflow para funcionar.
