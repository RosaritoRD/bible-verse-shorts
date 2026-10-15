"""Referencias bíblicas: "Salmos 3:4" -> "Salmos capítulo 3, versículo 4".

formatear() da forma a una referencia escrita a mano en el lote.
detectar() busca citas dentro de lo que se dice en un clip (transcripción).

Con números ("Juan 3:5") el primero es el capítulo, como en cualquier Biblia.
Con palabras ("Juan versículo 3 capítulo 5") manda lo que dice cada palabra.
"""
import re
import unicodedata

LIBROS = [
    "Génesis", "Éxodo", "Levítico", "Números", "Deuteronomio", "Josué",
    "Jueces", "Rut", "1 Samuel", "2 Samuel", "1 Reyes", "2 Reyes",
    "1 Crónicas", "2 Crónicas", "Esdras", "Nehemías", "Ester", "Job",
    "Salmos", "Salmo", "Proverbios", "Eclesiastés", "Cantares", "Isaías",
    "Jeremías", "Lamentaciones", "Ezequiel", "Daniel", "Oseas", "Joel",
    "Amós", "Abdías", "Jonás", "Miqueas", "Nahúm", "Habacuc", "Sofonías",
    "Hageo", "Zacarías", "Malaquías", "Mateo", "Marcos", "Lucas", "Juan",
    "Hechos", "Romanos", "1 Corintios", "2 Corintios", "Gálatas", "Efesios",
    "Filipenses", "Colosenses", "1 Tesalonicenses", "2 Tesalonicenses",
    "1 Timoteo", "2 Timoteo", "Tito", "Filemón", "Hebreos", "Santiago",
    "1 Pedro", "2 Pedro", "1 Juan", "2 Juan", "3 Juan", "Judas",
    "Apocalipsis",
]


def _sin_tildes(s):
    # Quitar tildes en NFD no cambia la cantidad de letras base, así que las
    # posiciones del texto plano sirven para recortar el original.
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").lower()


_POR_CLAVE = {_sin_tildes(l): l for l in LIBROS}
# Los más largos primero: "1 Juan" antes que "Juan".
_ALT_LIBROS = "|".join(re.escape(_sin_tildes(l))
                       for l in sorted(LIBROS, key=len, reverse=True))

_V = r"(\d+)(?:\s*(?:-|al|a)\s*(\d+))?"  # versículo o rango "1 al 3"
_CAP_VER = r"\s*,?\s+capitulo\s+(\d+)\s*,?\s*(?:y\s+)?(?:el\s+)?versiculos?\s+" + _V
_VER_CAP = r"\s*,?\s+(?:el\s+)?versiculos?\s+" + _V + r"\s*,?\s*(?:del?\s+)?capitulo\s+(\d+)"
_NUM = r"\s+(?:capitulo\s+)?(\d+)(?:\s*[:,.]\s*|\s+)" + _V
_SOLO_CAP = r"\s+(?:capitulo\s+)?(\d+)"


def _formas(libro, solo_capitulo):
    """[(patrón, grupos -> (cap, v1, v2))]; el grupo 0 siempre es el libro."""
    formas = [
        (re.compile(libro + _CAP_VER), lambda g: (g[1], g[2], g[3])),
        (re.compile(libro + _VER_CAP), lambda g: (g[3], g[1], g[2])),
        (re.compile(libro + _NUM), lambda g: (g[1], g[2], g[3])),
    ]
    if solo_capitulo:
        formas.append((re.compile(libro + _SOLO_CAP), lambda g: (g[1], None, None)))
    return formas


_FORMAS_ESCRITAS = _formas(r"\s*(.+?)", solo_capitulo=True)
# En lo hablado solo cuentan libros conocidos y con versículo: "Juan 3" suelto
# es demasiado ambiguo ("en Juan 3 años...").
_FORMAS_HABLADAS = _formas(r"(?<![\w])(" + _ALT_LIBROS + r")", solo_capitulo=False)


def _componer(libro, cap, v1=None, v2=None):
    base = f"{libro} capítulo {int(cap)}"
    if not v1:
        return base
    if v2 and int(v2) > int(v1):  # "Juan 3:16 a 5 personas" no es un rango
        return f"{base}, versículos {int(v1)} al {int(v2)}"
    return f"{base}, versículo {int(v1)}"


def _libro(original, m):
    clave = m.group(1).strip()
    return _POR_CLAVE.get(clave) or original[m.start(1):m.end(1)].strip()


def formatear(ref):
    plano = _sin_tildes(ref).rstrip()
    for patron, partes in _FORMAS_ESCRITAS:
        m = patron.fullmatch(plano)
        if m:
            return _componer(_libro(ref, m), *partes(m.groups()))
    return ref.strip()


def detectar(texto):
    plano = _sin_tildes(texto)
    hallazgos = []
    for patron, partes in _FORMAS_HABLADAS:
        for m in patron.finditer(plano):
            hallazgos.append((m.start(), m.end(), _componer(_libro(texto, m),
                                                            *partes(m.groups()))))
    citas, hasta = [], -1
    for ini, fin, cita in sorted(hallazgos):
        if ini >= hasta:  # dos formas que leen la misma cita: vale la primera
            citas.append(cita)
            hasta = fin
    return citas
