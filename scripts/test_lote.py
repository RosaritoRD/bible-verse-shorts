import pytest

from lote import leer_lote, repartir_tiempos, ass_versiculos, agrupar_palabras

LOTE = """
# comentario
clip: playa.mp4
musica: piano.mp3
nombre: salmo-3
Salmos 3:4 | Con mi voz clamé a Jehová, y él me respondió.
---
Juan 3:16 | Porque de tal manera amó Dios al mundo.
Romanos 8:28 | Y sabemos que a los que aman a Dios, todas las cosas les ayudan a bien.
"""


def test_lee_cada_short_separado_por_guiones():
    shorts = leer_lote(LOTE)
    assert len(shorts) == 2
    assert shorts[0]["clip"] == "playa.mp4"
    assert shorts[0]["musica"] == "piano.mp3"
    assert shorts[0]["nombre"] == "salmo-3"
    assert shorts[0]["versiculos"] == [
        ("Salmos capítulo 3, versículo 4", "Con mi voz clamé a Jehová, y él me respondió.")]
    assert shorts[1]["clip"] is None
    assert len(shorts[1]["versiculos"]) == 2


def test_nombre_por_defecto_sale_de_la_primera_cita():
    assert leer_lote(LOTE)[1]["nombre"] == "juan-3-16"


def test_linea_sin_barra_y_sin_biblia_es_un_error_claro():
    with pytest.raises(ValueError, match="line 2: the text is missing"):
        leer_lote("clip: a.mp4\nSalmos 3:4 sin texto\n")


def test_los_tiempos_crecen_con_el_largo_y_tienen_minimo():
    corto, largo = repartir_tiempos([("R", "Dios es amor."),
                                     ("R", " ".join(["palabra"] * 25))])
    assert corto == (0.0, 4.0)
    assert largo[0] == 4.0 and largo[1] - largo[0] > 8


def test_ass_lleva_texto_y_referencia_y_escapa_llaves():
    ass = ass_versiculos([("Juan capítulo 3, versículo 16", "Amó {Dios}")], [(0.0, 5.0)])
    assert "Dialogue: 0,0:00:00.00,0:00:05.00,Versiculo" in ass
    assert "Juan capítulo 3,\\Nversículo 16" in ass
    assert "{Dios}" not in ass and "(Dios)" in ass


def test_agrupa_palabras_en_bloques_cortos():
    palabras = [(0.0, 0.3, "Porque"), (0.3, 0.5, "de"), (0.5, 0.7, "tal"),
                (0.7, 1.0, "manera"), (3.0, 3.4, "amó")]
    grupos = agrupar_palabras(palabras, maximo=3)
    assert grupos == [(0.0, 0.7, "Porque de tal"), (0.7, 1.0, "manera"),
                      (3.0, 3.4, "amó")]


def test_cita_larga_se_parte_en_la_coma():
    ass = ass_versiculos([("Proverbios capítulo 3, versículos 5 al 6", "x")],
                         [(0.0, 5.0)])
    assert "Proverbios capítulo 3,\\Nversículos 5 al 6" in ass
    corta = ass_versiculos([("Juan capítulo 3", "x")], [(0.0, 5.0)])
    assert "\\N" not in corta


def test_estilos_sin_plantillas_sin_rellenar():
    cabecera = ass_versiculos([("A capítulo 1", "x")], [(0.0, 1.0)]).split("[Events]")[0]
    assert "{" not in cabecera


def test_nombres_repetidos_no_se_pisan():
    shorts = leer_lote("Juan 3:16 | a\n---\nJuan 3:16 | b\n---\nJuan 3:16 | c\n")
    assert [s["nombre"] for s in shorts] == ["juan-3-16", "juan-3-16-2", "juan-3-16-3"]


def BibliaFalsa():
    from biblia import Biblia
    return Biblia({"Juan": {"3": {"16": "Porque de tal manera amó Dios al mundo."}}})


def test_cita_sola_toma_el_texto_de_la_biblia():
    shorts = leer_lote("Juan 3:16\n", biblia=BibliaFalsa())
    assert shorts[0]["versiculos"] == [
        ("Juan capítulo 3, versículo 16", "Porque de tal manera amó Dios al mundo.")]


def test_cita_sola_que_no_existe_es_un_error_claro():
    with pytest.raises(ValueError, match="line 1: Juan capítulo 3, versículo 99 was not found"):
        leer_lote("Juan 3:99\n", biblia=BibliaFalsa())


def test_texto_propio_manda_sobre_la_biblia():
    shorts = leer_lote("Juan 3:16 | Mi versión\n", biblia=BibliaFalsa())
    assert shorts[0]["versiculos"][0][1] == "Mi versión"


def test_rango_de_la_biblia_da_una_pantalla_por_versiculo():
    from biblia import Biblia
    b = Biblia({"Salmos": {"23": {"1": "uno", "2": "dos"}}})
    shorts = leer_lote("Salmos 23:1-2\n", biblia=b)
    assert shorts[0]["versiculos"] == [("Salmos capítulo 23, versículo 1", "uno"),
                                       ("Salmos capítulo 23, versículo 2", "dos")]
    assert shorts[0]["nombre"] == "salmos-23-1-2"


def test_ficha_para_subir_lleva_titulo_versiculos_atribucion_y_hashtags():
    from lote import ficha
    short = {"nombre": "x", "versiculos": [
        ("Juan capítulo 3, versículo 16", "Porque de tal manera amó Dios al mundo."),
        ("Juan capítulo 3, versículo 17", "Porque no envió Dios.")]}
    f = ficha(short, atribucion="Música: Pista X de Autor Y (CC BY)")
    titulo = f.splitlines()[0]
    assert titulo.startswith("TITLE: ") and "Juan 3:16" in titulo and len(titulo) <= 108
    assert "Porque de tal manera amó Dios al mundo.\n— Juan capítulo 3, versículo 16" in f
    assert "Música: Pista X de Autor Y (CC BY)" in f
    assert "Reina-Valera 1909" in f and "#shorts" in f


def test_ficha_sin_atribucion_no_deja_hueco():
    from lote import ficha
    f = ficha({"nombre": "x", "versiculos": [("Salmos capítulo 23, versículo 1", "Jehová es mi pastor")]})
    assert "Música" not in f


def test_ficha_no_atribuye_la_1909_a_un_texto_propio():
    from lote import ficha
    short = leer_lote("Juan 3:16 | Mi versión del texto\n")[0]
    assert "Reina-Valera" not in ficha(short)


def test_nombre_propio_se_limpia():
    s = leer_lote("nombre: ../Mi Short Ñ/1\nJuan 3:16 | x\n")[0]
    assert s["nombre"] == "mi-short-n-1"


def test_bloque_sin_versiculos_avisa():
    with pytest.raises(ValueError, match="has no verses"):
        leer_lote("clip: a.mp4\n---\nJuan 3:16 | x\n")


def test_versiculo_largo_achica_la_letra():
    largo = " ".join(["palabra"] * 70)
    ass = ass_versiculos([("A capítulo 1", largo), ("B capítulo 1", "corto")],
                         [(0.0, 5.0), (5.0, 9.0)])
    filas = [l for l in ass.splitlines() if ",Versiculo," in l]
    assert "\\fs" in filas[0] and "\\fs" not in filas[1]
