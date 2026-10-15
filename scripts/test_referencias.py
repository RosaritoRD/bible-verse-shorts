from referencias import formatear, detectar


def test_capitulo_y_versiculo():
    assert formatear("Salmos 3:4") == "Salmos capítulo 3, versículo 4"


def test_rango_de_versiculos():
    assert formatear("Salmos 23:1-3") == "Salmos capítulo 23, versículos 1 al 3"


def test_solo_capitulo():
    assert formatear("Salmos 23") == "Salmos capítulo 23"


def test_libro_con_numero():
    assert formatear("1 Corintios 13:4") == "1 Corintios capítulo 13, versículo 4"


def test_espacios_y_coma_como_separador():
    assert formatear("  Juan 3,16 ") == "Juan capítulo 3, versículo 16"


def test_texto_que_no_es_referencia_se_devuelve_igual():
    assert formatear("Mi frase") == "Mi frase"


def test_detecta_cita_con_dos_puntos_en_lo_hablado():
    assert detectar("como dice Juan 3:16, de tal manera") == ["Juan capítulo 3, versículo 16"]


def test_detecta_cita_dicha_en_palabras():
    texto = "leamos Salmos capítulo 3 versículo 4 que dice"
    assert detectar(texto) == ["Salmos capítulo 3, versículo 4"]


def test_detecta_libro_con_numero_y_tilde():
    assert detectar("en 1 Corintios 13:4 el amor") == ["1 Corintios capítulo 13, versículo 4"]
    assert detectar("Génesis 1:1") == ["Génesis capítulo 1, versículo 1"]


def test_no_inventa_citas_con_palabras_comunes():
    assert detectar("tengo 3:15 minutos y juan llegó a las 4") == []


def test_con_palabras_respeta_lo_que_dice_cada_numero():
    assert formatear("Juan capítulo 3 versículo 5") == "Juan capítulo 3, versículo 5"
    assert formatear("Juan versiculo 3 capitulo 5") == "Juan capítulo 5, versículo 3"


def test_detecta_dicho_al_reves():
    assert detectar("en Juan versículo 5 del capítulo 3") == ["Juan capítulo 3, versículo 5"]


def test_detecta_numeros_separados_solo_por_espacio_como_los_escribe_whisper():
    assert detectar("hoy leemos Juan 3 16, porque") == ["Juan capítulo 3, versículo 16"]


def test_espacio_solo_no_convierte_un_capitulo_suelto_en_cita():
    assert detectar("en Juan 3 vemos") == []


def test_un_numero_menor_despues_de_a_no_es_rango():
    assert detectar("Juan 3:16 a 5 personas") == ["Juan capítulo 3, versículo 16"]
