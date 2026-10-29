"""Golden master del recomendador: datasets fijos y la salida que produce sobre ellos.

La salida de referencia (``fixtures/golden_recommender.json``) se generó con el código del
tag ``parcial3-fase0``, antes del refactor de la Fase 1. Para regenerarla:

    python tests/golden.py
"""

import json
import sys
from pathlib import Path
from typing import Any

FIXTURE = Path(__file__).parent / "fixtures" / "golden_recommender.json"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data_models import MOVIES_DATA, RATINGS_DATA, Movie, Rating  # noqa: E402
from recommender_core import (  # noqa: E402
    calculate_similarity,
    prepare_data,
    recommend_movies,
)


def synthetic_dataset() -> tuple[list[Rating], list[Movie]]:
    """Dataset determinístico (sin RNG) de 30 usuarios y 25 películas.

    El usuario 999 califica todo con 0.0, así que su vector tiene norma cero.
    """
    movies: list[Movie] = [{"movie_id": m, "title": f"Peli {m}"} for m in range(1, 26)]
    ratings: list[Rating] = []
    for u in range(1, 31):
        for m in range(1, 26):
            if (u * m + u) % 3 != 0:
                ratings.append({"user_id": u, "movie_id": m, "rating": ((u * 7 + m * 13) % 9 + 1) / 2})
    ratings += [{"user_id": 999, "movie_id": m, "rating": 0.0} for m in (1, 2, 3)]
    return ratings, movies


def datasets() -> dict[str, tuple[list[Rating], list[Movie]]]:
    return {"real": (RATINGS_DATA, MOVIES_DATA), "sintetico": synthetic_dataset()}


def compute(ratings: list[Rating], movies: list[Movie]) -> dict[str, Any]:
    """Salida observable del recomendador sobre un dataset."""
    utility_matrix = prepare_data(ratings)
    similarity_matrix, user_index = calculate_similarity(utility_matrix)
    users = list(utility_matrix)
    return {
        "user_index": {str(u): i for u, i in user_index.items()},
        "similarity_matrix": similarity_matrix.tolist(),
        "recommendations": {
            str(u): recommend_movies(u, utility_matrix, (similarity_matrix, user_index), movies, top_n=len(movies))
            for u in users
        },
    }


if __name__ == "__main__":
    FIXTURE.parent.mkdir(exist_ok=True)
    golden = {name: compute(*data) for name, data in datasets().items()}
    FIXTURE.write_text(json.dumps(golden, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Golden master escrito en {FIXTURE}")
