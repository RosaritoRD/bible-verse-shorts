"""Partes puras del pipeline (sin ffmpeg): leer el lote, repartir tiempos y
escribir los subtítulos ASS que ffmpeg quema en el video."""
import re

from referencias import formatear

ANCHO, ALTO = 1080, 1920
# Altura (px desde arriba) donde empieza la cita. Por debajo de ~1440 la tapan
# el título y los botones de YouTube.
Y_CITA = 1180

# Segundos que se queda cada versículo en pantalla: lo que tarda alguien en
# leerlo con calma (~2,4 palabras/s) más un respiro, nunca menos de 4 s.
MINIMO_S = 4.0
BASE_S = 1.5
POR_PALABRA_S = 0.42


def _slug(s):
    s = re.sub(r"[^\w]+", "-", s.lower(), flags=re.UNICODE).strip("-")
    s = (s.replace("á", "a").replace("é", "e").replace("í", "i")
          .replace("ó", "o").replace("ú", "u").replace("ñ", "n")
          .replace("ü", "u"))
    return re.sub(r"[^a-z0-9-]", "", s) or "short"


def leer_lote(texto, biblia=None):
    """Un short por bloque; los bloques se separan con una línea '---'.
    Una línea con solo la cita toma el texto de `biblia` (ver biblia.py)."""
    shorts, actual = [], None

    def nuevo():
        return {"clip": None, "musica": None, "nombre": None, "versiculos": []}

    for n, cruda in enumerate(texto.splitlines(), 1):
        linea = cruda.strip()
        if not linea or linea.startswith("#"):
            continue
        if linea == "---":
            if actual and not actual["versiculos"]:
                raise ValueError(f"línea {n}: el bloque de arriba está sin "
                                 f"versículos (¿falta la cita?)")
            if actual:
                shorts.append(actual)
            actual = None
            continue
        actual = actual or nuevo()
        m = re.match(r"^(clip|musica|música|nombre)\s*:\s*(.+)$", linea, re.I)
        if m:
            clave = m.group(1).lower().replace("ú", "u")
            actual[clave] = m.group(2).strip()
            continue
        if "|" in linea:
            ref, verso = (p.strip() for p in linea.split("|", 1))
            actual["versiculos"].append((formatear(ref), verso))
            actual["texto_propio"] = True
            continue
        cita = formatear(linea)
        if biblia is None:
            raise ValueError(f"línea {n}: falta el texto. Formato: "
                             f"'Salmos 3:4 | texto' (o prepara la Biblia: "
                             f"python3 scripts/biblia.py preparar)")
        uno_a_uno = biblia.versiculos(cita)
        if not uno_a_uno:
            raise ValueError(f"línea {n}: no encontré {cita} en la Biblia. "
                             f"Revisa la cita o pon el texto: 'cita | texto'")
        if not actual["versiculos"]:  # el nombre sale de la cita entera
            actual["cita_lote"] = cita
        actual["versiculos"].extend(uno_a_uno)
    if actual and not actual["versiculos"]:
        raise ValueError("el último bloque está sin versículos (¿falta la cita?)")
    if actual:
        shorts.append(actual)
    vistos = {}
    for s in shorts:
        base = _slug(s["nombre"]) if s["nombre"] else _slug(
            re.sub(r"cap[ií]tulo|vers[ií]culos?|\bal\b", "",
                   s.pop("cita_lote", None) or s["versiculos"][0][0]))
        s.pop("cita_lote", None)
        vistos[base] = vistos.get(base, 0) + 1
        s["nombre"] = base if vistos[base] == 1 else f"{base}-{vistos[base]}"
    return shorts


def repartir_tiempos(versiculos):
    tiempos, t = [], 0.0
    for _, verso in versiculos:
        dur = max(MINIMO_S, BASE_S + len(verso.split()) * POR_PALABRA_S)
        tiempos.append((round(t, 2), round(t + dur, 2)))
        t += dur
    return tiempos


def _hms(seg):
    cs = int(round(seg * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _limpio(t):
    # Las llaves abren comandos en ASS; un salto de línea real rompe la fila.
    return t.replace("{", "(").replace("}", ")").replace("\n", " ")


def _tamano(verso):
    """Letra más chica para los versículos largos, para que no se salgan por
    arriba (a 76 px caben ~11 líneas sobre la cita)."""
    palabras = len(verso.split())
    if palabras > 60:
        return "\\fs50"
    if palabras > 38:
        return "\\fs62"
    return ""


def _partir_cita(cita, largo=26):
    """Una cita larga se parte en la coma ("Proverbios capítulo 3," /
    "versículos 5 al 6") en vez de donde caiga."""
    if len(cita) > largo and ", " in cita:
        libro_cap, resto = cita.split(", ", 1)
        return f"{libro_cap},\\N{resto}"
    return cita


def _cabecera(estilos):
    return (
        "[Script Info]\nScriptType: v4.00+\n"
        f"PlayResX: {ANCHO}\nPlayResY: {ALTO}\nWrapStyle: 0\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        + "".join(estilos) +
        "\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, "
        "MarginR, MarginV, Effect, Text\n"
    )


def ass_versiculos(versiculos, tiempos, fuente="DejaVu Serif"):
    estilos = [
        # Versículo: blanco con borde negro para leerse sobre cualquier fondo.
        # Va anclado por ABAJO justo encima de la cita: si es largo crece hacia
        # arriba y nunca se monta sobre ella.
        f"Style: Versiculo,{fuente},76,&H00FFFFFF,&H00FFFFFF,&H00000000,"
        f"&H64000000,-1,0,0,0,100,100,0,0,1,5,2,2,110,110,{ALTO - Y_CITA + 40},1\n",
        # Cita (Salmos 3, versículo 4): dorada, debajo del texto.
        # Cita (Salmos capítulo 3, versículo 4): dorada sobre una franja
        # oscura semitransparente, para que se lea aunque el fondo sea dorado.
        f"Style: Cita,{fuente},52,&H0037AFD4,&H0037AFD4,&H70000000,"
        f"&H70000000,-1,0,0,0,100,100,0,0,3,14,0,8,110,110,{Y_CITA},1\n",
    ]
    filas = []
    for (cita, verso), (ini, fin) in zip(versiculos, tiempos):
        a, b = _hms(ini), _hms(fin)
        filas.append(f"Dialogue: 0,{a},{b},Versiculo,,0,0,0,,"
                     f"{{\\fad(500,400){_tamano(verso)}}}{_limpio(verso)}\n")
        filas.append(f"Dialogue: 0,{a},{b},Cita,,0,0,0,,"
                     f"{{\\fad(700,400)}}{_partir_cita(_limpio(cita))}\n")
    return _cabecera(estilos) + "".join(filas)


def agrupar_palabras(palabras, maximo=3, pausa=0.6):
    """[(ini, fin, palabra)] -> bloques de hasta `maximo` palabras; una pausa
    larga también corta el bloque para que el texto no se adelante a la voz."""
    grupos, actual = [], []
    for p in palabras:
        if actual and (len(actual) >= maximo or p[0] - actual[-1][1] > pausa):
            grupos.append((actual[0][0], actual[-1][1],
                           " ".join(w for _, _, w in actual)))
            actual = []
        actual.append(p)
    if actual:
        grupos.append((actual[0][0], actual[-1][1],
                       " ".join(w for _, _, w in actual)))
    return grupos


def ass_clipping(grupos, citas, fuente="DejaVu Sans"):
    """Subtítulos de lo que se dice + cartel con la cita cuando la nombran.
    citas = [(ini, fin, 'Juan 3, versículo 16')]"""
    estilos = [
        f"Style: Habla,{fuente},84,&H00FFFFFF,&H00FFFFFF,&H00000000,"
        "&H64000000,-1,0,0,0,100,100,0,0,1,6,2,2,80,80,560,1\n",
        f"Style: Cita,{fuente},58,&H00FFFFFF,&H00FFFFFF,&H0037AFD4,"
        "&H0037AFD4,-1,0,0,0,100,100,0,0,3,18,0,8,80,80,260,1\n",
    ]
    filas = [f"Dialogue: 0,{_hms(a)},{_hms(b)},Habla,,0,0,0,,"
             f"{_limpio(t).upper()}\n" for a, b, t in grupos]
    filas += [f"Dialogue: 1,{_hms(a)},{_hms(b)},Cita,,0,0,0,,"
              f"{{\\fad(300,300)}}{_limpio(c)}\n" for a, b, c in citas]
    return _cabecera(estilos) + "".join(filas)


def _cita_corta(cita):
    """"Juan capítulo 3, versículos 16 al 17" -> "Juan 3:16-17" (para títulos)."""
    m = re.match(r"^(.+) capítulo (\d+)(?:, versículos? (\d+)(?: al (\d+))?)?$", cita)
    if not m:
        return cita
    libro, cap, v1, v2 = m.groups()
    return f"{libro} {cap}" + (f":{v1}" if v1 else "") + (f"-{v2}" if v2 else "")


def ficha(short, atribucion=None, version="Reina-Valera 1909"):
    """Texto listo para copiar al subir el Short."""
    vs = short["versiculos"]
    primero = _cita_corta(vs[0][0])
    gancho = vs[0][1].split(".")[0].split(";")[0].split(":")[0].strip()
    titulo = f"{gancho} | {primero}"
    if len(titulo) > 100:  # tope de YouTube para el título
        titulo = f"{gancho[:100 - len(primero) - 4].rstrip()}… | {primero}"
    cuerpo = "\n\n".join(f"{texto}\n— {cita}" for cita, texto in vs)
    libros = {re.sub(r"\s+", "", c.split(" capítulo")[0]).lower() for c, _ in vs}
    tags = " ".join(["#shorts", "#biblia", "#versiculodeldia", "#dios"]
                    + [f"#{_slug(l).replace('-', '')}" for l in sorted(libros)])
    partes = [f"TÍTULO: {titulo}", "", "DESCRIPCIÓN:", cuerpo]
    if not short.get("texto_propio"):
        partes += ["", f"Texto bíblico: {version} (dominio público)."]
    if atribucion:
        partes += ["", atribucion.strip()]
    partes += ["", tags]
    return "\n".join(partes) + "\n"
