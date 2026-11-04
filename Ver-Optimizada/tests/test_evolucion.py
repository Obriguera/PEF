"""Tests de las funciones puras de la Fase 6 (evolucion/medir.py) y del worker. Las mediciones largas no se prueban."""

import json
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "evolucion"))

import medir  # noqa: E402
import trabajador  # noqa: E402

ETAPAS = {e: 1.0 for e in medir.ETAPAS}


def test_total_ms_suma_las_cuatro_etapas() -> None:
    assert (
        medir.total_ms(
            {"prepare_data": 1.0, "calculate_similarity": 2.0, "recommend_movies": 3.0, "analyze_popularity": 4.5}
        )
        == 10.5
    )


def test_aceleracion_mayor_a_uno_es_mejora() -> None:
    assert medir.aceleracion(100.0, 25.0) == 4.0
    assert medir.aceleracion(25.0, 100.0) == 0.25
    assert medir.aceleracion(1.0, 0.0) == math.inf


def test_exponente_empirico_recupera_el_orden_de_crecimiento() -> None:
    tamanos = [250, 500, 1000, 2000]
    assert medir.exponente_empirico(tamanos, [n**2 * 0.001 for n in tamanos]) == 2.0
    assert medir.exponente_empirico(tamanos, [n * 0.5 for n in tamanos]) == 1.0


def test_repeticiones_son_menos_donde_el_costo_es_alto() -> None:
    assert medir.repeticiones_para("Base", 2000) == 1
    assert medir.repeticiones_para("Optimizada", 2000) > medir.repeticiones_para("Base", 2000)


def test_dataset_del_worker_es_reproducible_y_del_tamano_pedido() -> None:
    peliculas, calificaciones = trabajador.generar_datos(10)
    assert (peliculas, calificaciones) == trabajador.generar_datos(10)
    assert len(calificaciones) == 10 * trabajador.RATINGS_PER_USER
    assert len(peliculas) == trabajador.MOVIES


def test_worker_mide_optimizada_y_devuelve_las_cuatro_etapas(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(Path(__file__).resolve().parent.parent)
    resultado = trabajador.medir(20, 1)
    assert set(resultado["ms"]) == set(medir.ETAPAS)
    assert resultado["pico_mb"] > 0
    json.dumps(resultado)  # tiene que ser serializable: el orquestador lo lee de la salida estándar


def test_metricas_de_codigo_de_optimizada() -> None:
    codigo = medir.metricas_de_codigo(medir.OPTIMIZADA)
    assert codigo["cc_maxima"] <= 5
    assert codigo["sloc"] > 0
