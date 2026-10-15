import pytest

from hacer_clipping import MAXIMO_S, calcular_tramo, segundos


def test_segundos_acepta_mm_ss_y_hh_mm_ss():
    assert segundos("1:20") == 80
    assert segundos("1:00:05") == 3605
    assert segundos("42.5") == 42.5
    assert segundos(None) is None


def test_segundos_rechaza_texto_con_mensaje_claro():
    with pytest.raises(ValueError, match="1;20"):
        segundos("1;20")


def test_tramo_por_defecto_es_el_video_entero():
    assert calcular_tramo(None, None, 95.0) == (0.0, 95.0)


def test_tramo_respeta_desde_y_hasta():
    assert calcular_tramo("1:20", "2:05", 600.0) == (80.0, 125.0)


def test_hasta_cero_no_se_confunde_con_sin_hasta():
    with pytest.raises(ValueError, match="must come after"):
        calcular_tramo("0:10", "0", 600.0)


def test_hasta_antes_que_desde_es_un_error():
    with pytest.raises(ValueError, match="must come after"):
        calcular_tramo("2:00", "1:00", 600.0)


def test_desde_pasado_el_final_es_un_error():
    with pytest.raises(ValueError, match="lasts"):
        calcular_tramo("10:00", None, 300.0)


def test_hasta_pasado_el_final_se_ajusta_al_final():
    assert calcular_tramo("4:00", "9:00", 300.0) == (240.0, 300.0)


def test_tramo_largo_se_corta_al_tope_de_un_short():
    desde, hasta = calcular_tramo(None, None, 1000.0)
    assert hasta - desde == MAXIMO_S
