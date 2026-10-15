"""Verse text: Reina-Valera 1909 (public domain, eBible.org).

    python3 scripts/biblia.py preparar   # once: creates biblia/rv1909.json

The 1909 spelling is modernized as little as possible ("á Jehová" -> "a Jehová",
"fué" -> "fue") without touching the words: it is still the 1909 text.
"""
import json
import re
import sys
from pathlib import Path

from referencias import LIBROS

RAIZ = Path(__file__).resolve().parent.parent
JSON = RAIZ / "biblia" / "rv1909.json"
VPL = RAIZ / "biblia" / "spaRV1909_vpl.txt"
FUENTE = "https://ebible.org/Scriptures/spaRV1909_vpl.zip"

# eBible codes in the order of LIBROS (without "Salmo", which is an alias).
CODIGOS = ("GEN EXO LEV NUM DEU JOS JDG RUT 1SA 2SA 1KI 2KI 1CH 2CH EZR NEH "
           "EST JOB PSA PRO ECC SOL ISA JER LAM EZE DAN HOS JOE AMO OBA JON "
           "MIC NAH HAB ZEP HAG ZEC MAL MAT MAR LUK JOH ACT ROM 1CO 2CO GAL "
           "EPH PHI COL 1TH 2TH 1TI 2TI TIT PHM HEB JAM 1PE 2PE 1JO 2JO 3JO "
           "JUD REV").split()
_NOMBRES = [l for l in LIBROS if l != "Salmo"]
assert len(CODIGOS) == len(_NOMBRES) == 66

# In 1909 standalone conjunctions and prepositions, and some one-syllable
# words, carried an accent they no longer have.
_SUELTAS = {"á": "a", "Á": "A", "é": "e", "É": "E", "ó": "o", "Ó": "O",
            "ú": "u", "Ú": "U"}
_MONOSILABOS = {"fué": "fue", "Fué": "Fue", "fuí": "fui", "Fuí": "Fui",
                "vió": "vio", "Vió": "Vio", "dió": "dio", "Dió": "Dio",
                "dí": "di", "ví": "vi", "Ví": "Vi", "pié": "pie", "fuíste": "fuiste"}
_PALABRA = re.compile(r"\b\w+\b", re.UNICODE)


def modernizar(texto):
    def cambio(m):
        w = m.group(0)
        return _SUELTAS.get(w) or _MONOSILABOS.get(w) or w
    texto = _PALABRA.sub(cambio, texto)
    # "EN el principio", "¡OH Jehová": the small caps at the start of a chapter.
    return re.sub(r"^([¡¿\"(]?)([A-ZÁÉÍÓÚÑ])([A-ZÁÉÍÓÚÑ]+)\b",
                  lambda m: m.group(1) + m.group(2) + m.group(3).lower(),
                  texto, count=1)


_VERSALITA = re.compile(r"([¡¿]?)\b[A-ZÁÉÍÓÚÑ]{2,}\b")


def limpiar(codigo, versiculo, texto):
    """Whatever in the printed Bible is not part of the verse as read aloud."""
    texto = re.sub(r"\s*\(Selah[.,]?\)", "", texto).strip()
    # Brackets marked words the translator added; they are read all the same.
    texto = re.sub(r"\[([^\]]*)\]", r"\1", texto)
    if codigo == "PSA" and versiculo == "1":
        # The psalm's title ("Salmo de David.", "ALEPH.") is glued to verse 1;
        # the verse starts at the word in small caps ("JEHOVÁ es...").
        # "Aleluya." IS part of what is read.
        m = next((m for m in _VERSALITA.finditer(texto)
                  if texto[m.end():m.end() + 1] != "."), None)
        if m and m.start() > 0:
            pre = "Aleluya. " if texto.startswith("Aleluya.") else ""
            texto = texto[m.start():]
            primera = re.match(r"([¡¿]?)([A-ZÁÉÍÓÚÑ]+)", texto)
            texto = (pre + primera.group(1) + primera.group(2).capitalize()
                     + texto[primera.end():])
    return modernizar(texto)


_CITA = re.compile(r"^(.+) capítulo (\d+), versículos? (\d+)(?: al (\d+))?$")


class Biblia:
    def __init__(self, libros):
        self.libros = libros

    def buscar(self, cita):
        """Takes the already formatted reference ("Juan capítulo 3, versículo 16")."""
        m = _CITA.match(cita)
        if not m:
            return None
        libro, cap, v1, v2 = m.groups()
        libro = "Salmos" if libro == "Salmo" else libro
        capitulo = self.libros.get(libro, {}).get(cap)
        if not capitulo:
            return None
        versos = [capitulo.get(str(v)) for v in range(int(v1), int(v2 or v1) + 1)]
        if not all(versos):
            return None
        return " ".join(versos)

    def versiculos(self, cita):
        """Like buscar(), but one (reference, text) per verse: in a Short a
        range reads better one verse per screen."""
        m = _CITA.match(cita)
        if not m or not self.buscar(cita):
            return []
        libro, cap, v1, v2 = m.groups()
        return [(f"{libro} capítulo {cap}, versículo {v}",
                 self.buscar(f"{libro} capítulo {cap}, versículo {v}"))
                for v in range(int(v1), int(v2 or v1) + 1)]


def cargar():
    if not JSON.exists():
        return None
    return Biblia(json.loads(JSON.read_text(encoding="utf-8")))


def preparar():
    if not VPL.exists():
        sys.exit(f"✗ Missing {VPL}. Download it from {FUENTE} and unzip it into biblia/.")
    nombre = dict(zip(CODIGOS, _NOMBRES))
    libros = {}
    for linea in VPL.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(\w+) (\d+):(\d+) (.*)$", linea)
        if not m:
            continue
        cod, cap, ver, texto = m.groups()
        libros.setdefault(nombre[cod], {}).setdefault(cap, {})[ver] = \
            limpiar(cod, ver, texto.strip())
    JSON.write_text(json.dumps(libros, ensure_ascii=False), encoding="utf-8")
    total = sum(len(v) for c in libros.values() for v in c.values())
    print(f"✓ {JSON.relative_to(RAIZ)}: {len(libros)} books, {total} verses")


if __name__ == "__main__":
    if sys.argv[1:] == ["preparar"]:
        preparar()
    else:
        sys.exit("usage: python3 scripts/biblia.py preparar")
