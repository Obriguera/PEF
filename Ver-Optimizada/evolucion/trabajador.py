"""Worker de la Fase 6: mide UNA versión con UN tamaño, en su propio proceso.

Los tres directorios (``Ver-Base``, ``Ver-Eficiente``, ``Ver-Optimizada``) tienen módulos con el mismo nombre
(``recommender_core``...), así que no se pueden importar en el mismo intérprete: el orquestador (``medir.py``) lanza este
script una vez por (versión, tamaño) con ``cwd`` en el directorio a medir. Imprime un JSON en la última línea.

Uso: ``python trabajador.py <usuarios> <repeticiones>``
"""

from __future__ import annotations

import json
import random
import resource
import statistics
import sys
import time
from collections.abc import Callable
from typing import Any

MOVIES = 500
RATINGS_PER_USER = 30
SEED = 42


def generar_datos(usuarios: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Mismo dataset para todas las versiones (semilla fija). Solo Python puro: no depende de la versión medida."""
    rng = random.Random(SEED)
    movies = [{"movie_id": i, "title": f"Pelicula_{i}", "genre": "Action", "duration": 120} for i in range(1, MOVIES + 1)]
    ratings = []
    for user_id in range(1, usuarios + 1):
        for movie_id in rng.sample(range(1, MOVIES + 1), RATINGS_PER_USER):
            ratings.append({"user_id": user_id, "movie_id": movie_id, "rating": round(rng.uniform(1.0, 5.0), 1)})
    return movies, ratings


def cronometrar(func: Callable[[], Any]) -> tuple[float, Any]:
    inicio = time.perf_counter()
    resultado = func()
    return time.perf_counter() - inicio, resultado


def medir(usuarios: int, repeticiones: int) -> dict[str, Any]:
    """Mide las cuatro etapas; devuelve la mediana de cada una en milisegundos y el pico de memoria del proceso."""
    # Se importa acá (y no arriba) porque el módulo depende de cwd, que fija el orquestador.
    sys.path.insert(0, ".")
    import analysis_utils
    import recommender_core

    movies, ratings = generar_datos(usuarios)
    tiempos: dict[str, list[float]] = {"prepare_data": [], "calculate_similarity": [], "recommend_movies": [], "analyze_popularity": []}
    recomendacion: list[str] = []
    for _ in range(repeticiones):
        # Un caché de popularidad vigente (versiones 2 y 3) taparía el costo real de calcularla.
        getattr(analysis_utils, "invalidar_cache_popularidad", lambda: None)()
        t, matriz = cronometrar(lambda: recommender_core.prepare_data(ratings))
        tiempos["prepare_data"].append(t)
        t, sims = cronometrar(lambda: recommender_core.calculate_similarity(matriz))
        tiempos["calculate_similarity"].append(t)
        t, recomendacion = cronometrar(lambda: recommender_core.recommend_movies(1, matriz, sims, movies, top_n=5))
        tiempos["recommend_movies"].append(t)
        t, _ = cronometrar(lambda: analysis_utils.analyze_popularity(ratings, movies))
        tiempos["analyze_popularity"].append(t)

    return {
        "usuarios": usuarios,
        "repeticiones": repeticiones,
        "ratings": len(ratings),
        "ms": {etapa: round(statistics.median(v) * 1000, 3) for etapa, v in tiempos.items()},
        # En Linux ru_maxrss está en KiB. Incluye el dataset (igual para todas las versiones) y el intérprete.
        # Control de equivalencia: las tres versiones deben recomendar lo mismo con los mismos datos.
        "recomendacion": recomendacion,
        "pico_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
    }


if __name__ == "__main__":
    print(json.dumps(medir(int(sys.argv[1]), int(sys.argv[2]))))
