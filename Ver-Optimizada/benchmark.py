"""Dataset sintético y benchmark manual de la versión optimizada.

- Como módulo, ``generate_massive_data`` provee datos reproducibles (con semilla) a los tests de
  rendimiento y de memoria.
- Como script (``python benchmark.py``), mide cada etapa y sirve de objetivo para los perfiladores
  (cProfile, Scalene, pyinstrument).

Las mediciones automáticas con línea base y umbral de regresión están en ``tests/test_benchmarks.py``
(``python tasks.py bench``).
"""

import random
import time
from collections.abc import Callable
from typing import TypeVar

from analysis_utils import analyze_popularity
from data_models import Movie, Rating
from recommender_core import calculate_similarity, prepare_data, recommend_movies

T = TypeVar("T")


def generate_massive_data(
    num_users: int = 2000, num_movies: int = 500, ratings_per_user: int = 30, seed: int = 42
) -> tuple[list[Movie], list[Rating]]:
    """Genera un dataset sintético masivo en Python puro. Con la misma semilla, siempre los mismos datos."""
    rng = random.Random(seed)
    movies_data: list[Movie] = [
        {"movie_id": i, "title": f"Pelicula_{i}", "genre": "Action", "duration": 120} for i in range(1, num_movies + 1)
    ]

    ratings_data: list[Rating] = []
    for user_id in range(1, num_users + 1):
        # Cada usuario califica un puñado de películas al azar
        watched = rng.sample(range(1, num_movies + 1), ratings_per_user)
        for movie_id in watched:
            ratings_data.append({"user_id": user_id, "movie_id": movie_id, "rating": round(rng.uniform(1.0, 5.0), 1)})

    return movies_data, ratings_data


def _timed(label: str, func: Callable[[], T]) -> T:
    """Ejecuta ``func``, imprime cuánto tardó y devuelve su resultado."""
    start = time.perf_counter()
    result = func()
    print(f"  {label}: {(time.perf_counter() - start) * 1000:.1f} ms")
    return result


def run_baseline_test() -> None:
    print("Generando dataset masivo... ⏳")
    movies_data, ratings_data = generate_massive_data(num_users=2000, num_movies=500, ratings_per_user=30)

    print(f"Dataset listo: 2000 usuarios, 500 películas y {len(ratings_data)} ratings.")
    print("Corriendo el benchmark (esto va a demorar un poco)...")

    # 1. Preparar matrices
    utility_matrix = _timed("prepare_data", lambda: prepare_data(ratings_data))
    user_similarities = _timed("calculate_similarity", lambda: calculate_similarity(utility_matrix))

    # 2. Medir recomendación (elegimos el usuario 1)
    _timed("recommend_movies", lambda: recommend_movies(1, utility_matrix, user_similarities, movies_data, top_n=5))

    # 3. Medir popularidad
    _timed("analyze_popularity", lambda: analyze_popularity(ratings_data, movies_data))

    print("¡Terminado!")


if __name__ == "__main__":
    run_baseline_test()


# Concurrencia (decisión del Parcial 1): las peticiones a la API se atienden
# en paralelo porque FastAPI ejecuta los endpoints `def` en su pool de hilos.
# Las recomendaciones solo leen la matriz compartida, así que no hay
# condiciones de carrera. Se descartó ProcessPoolExecutor para este caso
# porque replicaría la matriz en cada proceso. Por el GIL, los hilos dan
# concurrencia de peticiones, no paralelismo del cálculo.
# El paralelismo real con procesos está en large_file_handler.py (Parcial 2).
