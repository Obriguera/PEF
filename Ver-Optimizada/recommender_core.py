import heapq
from collections.abc import Iterable

import numpy as np
import numpy.typing as npt

from data_models import Movie, Rating

# user_id -> {movie_id: rating}
UtilityMatrix = dict[int, dict[int, float]]
# (matriz de similitud usuarios x usuarios, user_id -> índice de fila/columna)
UserSimilarities = tuple[npt.NDArray[np.float32], dict[int, int]]


def prepare_data(ratings_data: Iterable[Rating]) -> UtilityMatrix:
    """Matriz de utilidad."""
    utility_matrix: UtilityMatrix = {}
    for r in ratings_data:
        u = r["user_id"]
        m = r["movie_id"]
        rating = r["rating"]
        if u not in utility_matrix:
            utility_matrix[u] = {}
        utility_matrix[u][m] = rating
    return utility_matrix


def calculate_similarity(utility_matrix: UtilityMatrix) -> UserSimilarities:
    """Cálculo de similitudes totalmente vectorizado con NumPy.

    OPTIMIZACIÓN ALGORÍTMICA Y DE RENDIMIENTO:
    En lugar de iterar con un doble bucle for en Python puro y calcular sum()
    con expresiones generadoras (<genexpr>) sobre sets O(N^2) veces, se
    construye la matriz de utilidad R (usuarios x películas) y se vectoriza
    el producto punto y las normas con numpy.dot y numpy.linalg.norm en C/BLAS.

    Returns:
        tuple: (similarity_matrix np.ndarray[float32], user_index dict)
               user_index mapea user_id -> índice de fila/columna en la matriz.
    """
    user_index = {user: i for i, user in enumerate(utility_matrix)}
    ratings_matrix = _build_ratings_matrix(utility_matrix, user_index, _index_movies(utility_matrix))
    return _cosine_matrix(ratings_matrix), user_index


def _index_movies(utility_matrix: UtilityMatrix) -> dict[int, int]:
    """Asigna a cada película calificada una columna de la matriz de ratings."""
    all_movies = list({m for ratings in utility_matrix.values() for m in ratings})
    return {m: i for i, m in enumerate(all_movies)}


def _build_ratings_matrix(
    utility_matrix: UtilityMatrix, user_index: dict[int, int], movie_index: dict[int, int]
) -> npt.NDArray[np.float32]:
    """Matriz densa de ratings (usuarios x películas) en float32."""
    ratings_matrix = np.zeros((len(user_index), len(movie_index)), dtype=np.float32)
    for user, ratings in utility_matrix.items():
        u_idx = user_index[user]
        for m, r in ratings.items():
            ratings_matrix[u_idx, movie_index[m]] = r
    return ratings_matrix


def _cosine_matrix(ratings_matrix: npt.NDArray[np.float32]) -> npt.NDArray[np.float32]:
    """Similitud coseno entre todas las filas, con la diagonal y los usuarios sin ratings en 0.0."""
    # Cálculo vectorizado de normas L2 por fila con numpy.linalg.norm
    norms = np.linalg.norm(ratings_matrix, axis=1, keepdims=True)  # (n_users, 1)

    # Evitar división por cero
    norms_safe = np.where(norms == 0, 1.0, norms)

    # Producto punto matricial con numpy.dot (ejecutado en C/BLAS)
    dot_products = np.dot(ratings_matrix, ratings_matrix.T)
    denom = np.dot(norms_safe, norms_safe.T)

    similarity_matrix: npt.NDArray[np.float32] = np.divide(dot_products, denom, dtype=np.float32)

    # Anular filas/columnas de usuarios sin calificaciones (norma 0)
    zero_mask = (norms == 0).squeeze()
    if np.any(zero_mask):
        similarity_matrix[zero_mask, :] = 0.0
        similarity_matrix[:, zero_mask] = 0.0

    # La similitud de un usuario consigo mismo se define como 0.0
    np.fill_diagonal(similarity_matrix, 0.0)
    return similarity_matrix


def recommend_movies(
    user_id: int,
    utility_matrix: UtilityMatrix,
    user_similarities: UserSimilarities,
    movies_data: Iterable[Movie],
    top_n: int = 5,
) -> list[str]:
    """Recomienda las ``top_n`` películas no vistas con mayor rating predicho.

    El rating predicho es el promedio de los ratings de los demás usuarios, ponderado por su
    similitud (positiva) con el usuario objetivo.

    Raises:
        KeyError: si ``user_id`` no está en la matriz de similitud.
    """
    # Desempaquetamos la tupla devuelta por calculate_similarity
    similarity_matrix, user_index = user_similarities

    target_ratings = utility_matrix.get(user_id, {})

    # OPTIMIZACIÓN: HashMap (diccionario) para búsqueda rápida O(1) de películas.
    movie_dict = {m["movie_id"]: m["title"] for m in movies_data}

    # OPTIMIZACIÓN: Set para encontrar películas no vistas
    unwatched_movies = set(movie_dict.keys()) - set(target_ratings.keys())

    # Vista zero-copy de la fila de similitudes del usuario objetivo
    sim_row = similarity_matrix[user_index[user_id]]  # O(1), sin copia de datos

    neighbors = _Neighbors(user_id, utility_matrix, sim_row, user_index)
    predictions = [(rating, movie) for movie in unwatched_movies if (rating := neighbors.predict(movie)) is not None]

    # OPTIMIZACIÓN: Uso de Heap para mantener el Top N.
    # Evitamos ordenar toda la lista O(N log N) y pasamos a O(N log K)
    top_predictions = heapq.nlargest(top_n, predictions)

    # Mapeo rápido O(1) gracias al diccionario
    return [movie_dict[movie] for _, movie in top_predictions]


class _Neighbors:
    """Los demás usuarios vistos desde el usuario objetivo, indexados por película.

    ``raters`` es un índice invertido ``movie_id -> [(índice del vecino, rating)]``: cada predicción
    recorre solo a quienes calificaron la película, en lugar de a todos los usuarios. Se construye
    recorriendo ``utility_matrix`` en su orden, así que las sumas se acumulan en el mismo orden.
    """

    def __init__(
        self,
        user_id: int,
        utility_matrix: UtilityMatrix,
        sim_row: npt.NDArray[np.float32],
        user_index: dict[int, int],
    ) -> None:
        self.sim_row = sim_row
        self.raters: dict[int, list[tuple[int, float]]] = {}
        for other_user, ratings in utility_matrix.items():
            if other_user == user_id:
                continue
            other_idx = user_index[other_user]
            for movie, rating in ratings.items():
                self.raters.setdefault(movie, []).append((other_idx, rating))

    def predict(self, movie: int) -> float | None:
        """Promedio de ratings ponderado por similitud; ``None`` si ningún vecino similar la calificó."""
        numerator = 0.0
        denominator = 0.0
        # Suma explícita en el orden original: sum() usa suma compensada desde Python 3.12
        for other_idx, rating in self.raters.get(movie, ()):
            # Acceso directo al array: más rápido que dict.get()
            sim = float(self.sim_row[other_idx])
            if sim > 0:
                numerator += sim * rating
                denominator += sim
        if denominator > 0:
            return numerator / denominator
        return None
