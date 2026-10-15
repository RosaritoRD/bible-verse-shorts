from biblia import modernizar, Biblia

TEXTO = {
    "Salmos": {"23": {"1": "Jehová es mi pastor; nada me faltará.",
                      "2": "En lugares de delicados pastos me hará yacer.",
                      "3": "Confortará mi alma."}},
    "Juan": {"3": {"16": "Porque de tal manera amó Dios al mundo."}},
}


def test_modernizar_quita_acentos_de_1909():
    assert modernizar("Y llamó Dios á la luz Día") == "Y llamó Dios a la luz Día"
    assert modernizar("Á ti, oh Jehová") == "A ti, oh Jehová"
    assert modernizar("y fué la tarde, y vió Dios, y dió fruto") == \
        "y fue la tarde, y vio Dios, y dio fruto"
    assert modernizar("plata ó oro") == "plata o oro"


def test_modernizar_baja_la_mayuscula_de_inicio_de_capitulo():
    assert modernizar("EN el principio crió Dios") == "En el principio crió Dios"
    assert modernizar("¡OH Jehová, cuánto") == "¡Oh Jehová, cuánto"
    assert modernizar("Y JEHOVÁ dijo") == "Y JEHOVÁ dijo"  # only at the start


def test_buscar_un_versiculo_y_un_rango():
    b = Biblia(TEXTO)
    assert b.buscar("Salmos capítulo 23, versículo 1") == "Jehová es mi pastor; nada me faltará."
    assert b.buscar("Salmos capítulo 23, versículos 1 al 3") == (
        "Jehová es mi pastor; nada me faltará. En lugares de delicados pastos "
        "me hará yacer. Confortará mi alma.")


def test_salmo_en_singular_busca_en_salmos():
    assert Biblia(TEXTO).buscar("Salmo capítulo 23, versículo 1").startswith("Jehová")


def test_cita_que_no_existe_devuelve_none():
    b = Biblia(TEXTO)
    assert b.buscar("Juan capítulo 3, versículo 99") is None
    assert b.buscar("Juan capítulo 3") is None  # whole chapter: too long
    assert b.buscar("Mi frase") is None


def test_limpiar_quita_titulo_de_salmo_y_selah():
    from biblia import limpiar
    assert limpiar("PSA", "1", "Salmo de David. JEHOVÁ es mi pastor; nada me faltará.") == \
        "Jehová es mi pastor; nada me faltará."
    assert limpiar("PSA", "1", "Salmo de David, cuando huía de Absalom. ¡OH Jehová, cuánto") == \
        "¡Oh Jehová, cuánto"
    assert limpiar("PSA", "4", "y él me respondió. (Selah.)") == "y él me respondió."
    # Outside a psalm's verse 1 nothing is trimmed.
    assert limpiar("JOH", "1", "EN el principio era el Verbo") == "En el principio era el Verbo"


def test_limpiar_letra_hebrea_aleluya_y_corchetes():
    from biblia import limpiar
    assert limpiar("PSA", "1", "ALEPH. BIENAVENTURADOS los perfectos") == \
        "Bienaventurados los perfectos"
    # "Aleluya" IS read as part of the verse.
    assert limpiar("PSA", "1", "Aleluya. ALABAD á Dios") == "Aleluya. Alabad a Dios"
    assert limpiar("PSA", "5", "respondióme JAH, [poniéndome] en anchura") == \
        "respondióme JAH, poniéndome en anchura"


def test_rango_se_reparte_en_un_versiculo_por_pantalla():
    assert Biblia(TEXTO).versiculos("Salmos capítulo 23, versículos 1 al 2") == [
        ("Salmos capítulo 23, versículo 1", "Jehová es mi pastor; nada me faltará."),
        ("Salmos capítulo 23, versículo 2", "En lugares de delicados pastos me hará yacer."),
    ]
    assert Biblia(TEXTO).versiculos("Juan capítulo 3, versículo 99") == []
