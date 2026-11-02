"""Tests de memoria con tracemalloc (Punto 3: la memoria queda acotada al lote, no al archivo).

Se mide el pico de memoria de Python en el proceso principal. El control principal es **relativo**
(el mismo código sobre archivos de distinto tamaño), así que no depende de la máquina. Los límites absolutos
salen de mediciones reales (python 3.13, numpy float32) con un margen de 1,3x a 2x:

    lectura en lotes de 2.000 filas ....... medido 0,98 MB -> límite 2 MB
    paralelo (lote de 2.000, 2 workers) ... medido 2,1-2,5 MB -> límite 5 MB
    calculate_similarity (400 x 300) ...... medido 2,32 MB -> límite 3 MB
        Teórico en float32: R (0,46) + producto punto, denominador y similitud (3 x 0,61) = 2,29 MB.
        En float64 sería ~4,6 MB: el límite detecta una regresión de dtype.
"""

import tracemalloc
from collections.abc import Callable

import pytest

from benchmark import generate_massive_data
from large_file_handler import generate_large_ratings_csv, process_large_file_parallel, stream_ratings_in_batches
from recommender_core import calculate_similarity, prepare_data

SMALL = 50_000
LARGE = 200_000  # 4 veces más grande
BATCH = 2_000


def peak_mb(func: Callable[[], object]) -> float:
    """Pico de memoria (MB) que alcanza ``func`` por encima de lo que había al empezar."""
    tracemalloc.start()
    try:
        base, _ = tracemalloc.get_traced_memory()
        tracemalloc.reset_peak()
        func()
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return (peak - base) / 2**20


@pytest.fixture(scope="module")
def csv_files(tmp_path_factory):
    folder = tmp_path_factory.mktemp("memoria")
    return {
        n: generate_large_ratings_csv(str(folder / f"{n}.csv"), num_records=n, num_users=500, num_movies=200)
        for n in (SMALL, LARGE)
    }


def test_la_lectura_en_lotes_no_crece_con_el_tamano_del_archivo(csv_files):
    def consume(path):
        for _ in stream_ratings_in_batches(path, batch_size=BATCH):
            pass

    pico_chico = peak_mb(lambda: consume(csv_files[SMALL]))
    pico_grande = peak_mb(lambda: consume(csv_files[LARGE]))
    assert pico_grande < pico_chico * 1.2
    assert pico_grande < 2.0


def test_el_procesamiento_paralelo_no_crece_con_el_tamano_del_archivo(csv_files):
    def procesar(path):
        process_large_file_parallel(path, batch_size=BATCH, max_workers=2)

    pico_chico = peak_mb(lambda: procesar(csv_files[SMALL]))
    pico_grande = peak_mb(lambda: procesar(csv_files[LARGE]))
    assert pico_grande < pico_chico * 1.5
    assert pico_grande < 5.0


def test_la_matriz_de_similitud_se_calcula_en_float32():
    _, ratings = generate_massive_data(num_users=400, num_movies=300, ratings_per_user=50)
    utility_matrix = prepare_data(ratings)
    assert peak_mb(lambda: calculate_similarity(utility_matrix)) < 3.0
