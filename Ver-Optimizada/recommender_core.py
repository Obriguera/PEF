import heapq
import numpy as np


def prepare_data(ratings_data):
    """Matriz de utilidad."""
    utility_matrix = {}
    for r in ratings_data:
        u = r['user_id']
        m = r['movie_id']
        rating = r['rating']
        if u not in utility_matrix:
            utility_matrix[u] = {}
        utility_matrix[u][m] = rating
    return utility_matrix


def _cosine_similarity(vector_a, vector_b):
    """Calcula la similitud coseno entre dos vectores usando NumPy.

    OPTIMIZACIÓN: Reemplaza las funciones nativas de Python (sum, bucles, <genexpr>)
    por álgebra lineal vectorizada en C/C++ usando numpy.dot y numpy.linalg.norm.
    """
    if isinstance(vector_a, dict) and isinstance(vector_b, dict):
        intersection = list(set(vector_a.keys()) & set(vector_b.keys()))
        if not intersection:
            return 0.0
        inter_a = np.array([vector_a[m] for m in intersection], dtype=np.float32)
        inter_b = np.array([vector_b[m] for m in intersection], dtype=np.float32)
        norm_a = np.linalg.norm(np.array(list(vector_a.values()), dtype=np.float32))
        norm_b = np.linalg.norm(np.array(list(vector_b.values()), dtype=np.float32))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return float(np.dot(inter_a, inter_b) / (norm_a * norm_b))

    v_a = np.asarray(vector_a, dtype=np.float32)
    v_b = np.asarray(vector_b, dtype=np.float32)
    norm_a = np.linalg.norm(v_a)
    norm_b = np.linalg.norm(v_b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(v_a, v_b) / (norm_a * norm_b))


def calculate_similarity(utility_matrix):
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
    users = list(utility_matrix.keys())
    n_users = len(users)
    user_index = {user: i for i, user in enumerate(users)}

    # Extraer el universo de películas únicas
    all_movies = list({m for ratings in utility_matrix.values() for m in ratings.keys()})
    movie_index = {m: i for i, m in enumerate(all_movies)}
    n_movies = len(all_movies)

    # Matriz densa de ratings (usuarios x películas) en float32
    R = np.zeros((n_users, n_movies), dtype=np.float32)
    for user, ratings in utility_matrix.items():
        u_idx = user_index[user]
        for m, r in ratings.items():
            R[u_idx, movie_index[m]] = r

    # Cálculo vectorizado de normas L2 por fila con numpy.linalg.norm
    norms = np.linalg.norm(R, axis=1, keepdims=True)  # (n_users, 1)

    # Evitar división por cero
    norms_safe = np.where(norms == 0, 1.0, norms)

    # Producto punto matricial con numpy.dot (ejecutado en C/BLAS)
    dot_products = np.dot(R, R.T)
    denom = np.dot(norms_safe, norms_safe.T)

    similarity_matrix = np.divide(dot_products, denom, dtype=np.float32)

    # Anular filas/columnas de usuarios sin calificaciones (norma 0)
    zero_mask = (norms == 0).squeeze()
    if np.any(zero_mask):
        similarity_matrix[zero_mask, :] = 0.0
        similarity_matrix[:, zero_mask] = 0.0

    # La similitud de un usuario consigo mismo se define como 0.0
    np.fill_diagonal(similarity_matrix, 0.0)

    return similarity_matrix, user_index


def recommend_movies(user_id, utility_matrix, user_similarities, movies_data, top_n=5):
    # Desempaquetamos la tupla devuelta por calculate_similarity
    similarity_matrix, user_index = user_similarities

    target_ratings = utility_matrix.get(user_id, {})

    # OPTIMIZACIÓN: HashMap (diccionario) para búsqueda rápida O(1) de películas.
    movie_dict = {m['movie_id']: m['title'] for m in movies_data}

    # OPTIMIZACIÓN: Set para encontrar películas no vistas
    unwatched_movies = set(movie_dict.keys()) - set(target_ratings.keys())

    # Vista zero-copy de la fila de similitudes del usuario objetivo
    user_idx = user_index[user_id]
    sim_row = similarity_matrix[user_idx]   # O(1), sin copia de datos

    predictions = []

    for movie in unwatched_movies:
        numerator = 0.0
        denominator = 0.0

        for other_user, ratings in utility_matrix.items():
            if other_user != user_id and movie in ratings:
                # Acceso directo al array: más rápido que dict.get()
                sim = float(sim_row[user_index[other_user]])
                if sim > 0:
                    numerator += sim * ratings[movie]
                    denominator += sim

        if denominator > 0:
            predicted_rating = numerator / denominator
            # Guardamos como tupla (rating, id) para que el heap sepa cómo ordenar
            predictions.append((predicted_rating, movie))

    # OPTIMIZACIÓN: Uso de Heap para mantener el Top N.
    # Evitamos ordenar toda la lista O(N log N) y pasamos a O(N log K)
    top_predictions = heapq.nlargest(top_n, predictions)

    # Mapeo rápido O(1) gracias al diccionario
    final_recommendations = [movie_dict[p[1]] for p in top_predictions]

    return final_recommendations
