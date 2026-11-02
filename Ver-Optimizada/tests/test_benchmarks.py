"""Benchmarks con pytest-benchmark: detectan regresiones de rendimiento contra una línea base.

En la suite normal están desactivados (``--benchmark-disable`` en pyproject.toml) y cada uno corre una
sola vez, como prueba de humo. Para medir de verdad:

    python tasks.py bench         # mide y compara contra la última línea base; falla si algo empeora más de 25 %
    python tasks.py bench-save    # guarda una nueva línea base (después de una mejora o de cambiar de máquina)

Los datos son determinísticos (semilla fija), 400 usuarios x 300 películas x 50 ratings.
"""

import pytest

from analysis_utils import analyze_popularity, invalidar_cache_popularidad
from benchmark import generate_massive_data
from large_file_handler import (
    _process_chunk_worker,
    generate_large_ratings_csv,
    process_large_file_parallel,
    stream_ratings_in_batches,
)
from recommender_core import calculate_similarity, prepare_data, recommend_movies

USERS_TO_RECOMMEND = 10


@pytest.fixture(scope="module")
def dataset():
    return generate_massive_data(num_users=400, num_movies=300, ratings_per_user=50)


@pytest.fixture(scope="module")
def utility_matrix(dataset):
    return prepare_data(dataset[1])


@pytest.fixture(scope="module")
def similarities(utility_matrix):
    return calculate_similarity(utility_matrix)


@pytest.fixture(scope="module")
def ratings_csv(tmp_path_factory):
    path = tmp_path_factory.mktemp("bench") / "ratings.csv"
    return generate_large_ratings_csv(str(path), num_records=50_000, num_users=500, num_movies=200)


@pytest.mark.benchmark(group="recomendador")
def test_prepare_data(benchmark, dataset):
    _, ratings = dataset
    assert len(benchmark(prepare_data, ratings)) == 400


@pytest.mark.benchmark(group="recomendador")
def test_calculate_similarity(benchmark, utility_matrix):
    matrix, user_index = benchmark(calculate_similarity, utility_matrix)
    assert matrix.shape == (400, 400)
    assert len(user_index) == 400


@pytest.mark.benchmark(group="recomendador")
def test_recommend_movies(benchmark, dataset, utility_matrix, similarities):
    movies, _ = dataset

    def recomendar_a_varios():
        return [
            recommend_movies(user, utility_matrix, similarities, movies) for user in range(1, USERS_TO_RECOMMEND + 1)
        ]

    resultado = benchmark(recomendar_a_varios)
    assert all(len(recomendaciones) == 5 for recomendaciones in resultado)


@pytest.mark.benchmark(group="recomendador")
def test_analyze_popularity_sin_cache(benchmark, dataset):
    movies, ratings = dataset

    def sin_cache():
        # El caché haría que a partir de la segunda vuelta no se calculara nada
        invalidar_cache_popularidad()
        return ((ratings, movies), {})

    top = benchmark.pedantic(analyze_popularity, setup=sin_cache, rounds=30)
    assert len(top) == 5


@pytest.mark.benchmark(group="archivos")
def test_lectura_en_lotes(benchmark, ratings_csv):
    def leer():
        return sum(len(lote) for lote in stream_ratings_in_batches(ratings_csv, batch_size=5_000))

    assert benchmark(leer) == 50_000


@pytest.mark.benchmark(group="archivos")
def test_agregacion_de_un_lote(benchmark, ratings_csv):
    lote = next(stream_ratings_in_batches(ratings_csv, batch_size=25_000))
    stats = benchmark(_process_chunk_worker, lote)
    assert sum(movie["count"] for movie in stats.values()) == 25_000


@pytest.mark.benchmark(group="archivos-paralelo")
def test_procesamiento_paralelo(benchmark, ratings_csv):
    # Incluye ~70-100 ms de arranque de procesos (spawn): el tiempo es más ruidoso que el de los demás
    stats = benchmark.pedantic(process_large_file_parallel, args=(ratings_csv, 10_000, 64 * 1024, 4), rounds=5)
    assert sum(movie["count"] for movie in stats.values()) == 50_000
