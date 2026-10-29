"""Tests de caracterización: fijan el comportamiento observable previo al refactor de la Fase 1.

Comparan por igualdad exacta (sin tolerancia) contra la salida del tag ``parcial3-fase0``,
de modo que cualquier cambio numérico introducido por el refactor los rompe.
"""

import json

import numpy as np
import pytest
from golden import FIXTURE, compute, datasets

from large_file_handler import stream_ratings_in_batches
from recommender_core import calculate_similarity, prepare_data, recommend_movies

GOLDEN = json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("dataset", ["real", "sintetico"])
def test_recomendador_igual_al_golden_master(dataset):
    actual = compute(*datasets()[dataset])
    esperado = GOLDEN[dataset]
    assert actual["user_index"] == esperado["user_index"]
    assert actual["similarity_matrix"] == esperado["similarity_matrix"]
    assert actual["recommendations"] == esperado["recommendations"]


def test_matriz_de_similitud_es_float32():
    sim_matrix, _ = calculate_similarity(prepare_data(datasets()["real"][0]))
    assert sim_matrix.dtype == np.float32


def test_usuario_con_norma_cero_no_recibe_recomendaciones():
    ratings, movies = datasets()["sintetico"]
    utility_matrix = prepare_data(ratings)
    sims = calculate_similarity(utility_matrix)
    fila = sims[0][sims[1][999]]
    assert not fila.any()
    assert recommend_movies(999, utility_matrix, sims, movies) == []


def test_usuario_inexistente_lanza_key_error():
    # Comportamiento actual (no necesariamente el deseado): el refactor no debe cambiarlo.
    ratings, movies = datasets()["real"]
    utility_matrix = prepare_data(ratings)
    with pytest.raises(KeyError):
        recommend_movies(12345, utility_matrix, calculate_similarity(utility_matrix), movies)


def test_stream_omite_encabezado_y_filas_invalidas_y_respeta_los_lotes(tmp_path):
    csv_path = tmp_path / "ratings.csv"
    csv_path.write_text(
        "\n".join(
            [
                "user_id,movie_id,rating,timestamp",
                "1,10,4.5,0",
                "",  # fila vacía: se omite
                "2,20",  # menos de 3 columnas: se omite
                "3,30,2.0,0",
                "4,40,1.5",  # sin timestamp: es válida
                "5,50,5.0,0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    lotes = list(stream_ratings_in_batches(str(csv_path), batch_size=2))
    assert lotes == [
        [
            {"user_id": 1, "movie_id": 10, "rating": 4.5},
            {"user_id": 3, "movie_id": 30, "rating": 2.0},
        ],
        [
            {"user_id": 4, "movie_id": 40, "rating": 1.5},
            {"user_id": 5, "movie_id": 50, "rating": 5.0},
        ],
    ]


def test_stream_archivo_solo_con_encabezado_no_produce_lotes(tmp_path):
    csv_path = tmp_path / "vacio.csv"
    csv_path.write_text("user_id,movie_id,rating,timestamp\n", encoding="utf-8")
    assert list(stream_ratings_in_batches(str(csv_path))) == []


def test_stream_archivo_inexistente(tmp_path):
    with pytest.raises(FileNotFoundError):
        next(stream_ratings_in_batches(str(tmp_path / "no_existe.csv")))
