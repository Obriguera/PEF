import numpy as np
import pytest

from recommender_core import _cosine_similarity, calculate_similarity, prepare_data, recommend_movies


def test_prepare_data():
    ratings = [
        {"user_id": 1, "movie_id": 10, "rating": 4.5},
        {"user_id": 1, "movie_id": 20, "rating": 3.0},
        {"user_id": 2, "movie_id": 10, "rating": 5.0},
    ]
    matrix = prepare_data(ratings)
    assert 1 in matrix
    assert 2 in matrix
    assert matrix[1][10] == 4.5
    assert matrix[1][20] == 3.0
    assert matrix[2][10] == 5.0


def test_cosine_similarity_vectors():
    v1 = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    v2 = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    sim = _cosine_similarity(v1, v2)
    assert pytest.approx(sim, 0.0001) == 1.0

    v_zero = np.array([0.0, 0.0, 0.0], dtype=np.float32)
    assert _cosine_similarity(v1, v_zero) == 0.0


def test_calculate_similarity_symmetry_and_diagonal():
    ratings = [
        {"user_id": 101, "movie_id": 1, "rating": 5.0},
        {"user_id": 101, "movie_id": 2, "rating": 4.0},
        {"user_id": 102, "movie_id": 1, "rating": 5.0},
        {"user_id": 102, "movie_id": 2, "rating": 4.0},
        {"user_id": 103, "movie_id": 3, "rating": 5.0},
    ]
    matrix = prepare_data(ratings)
    sim_matrix, user_index = calculate_similarity(matrix)

    assert sim_matrix.shape == (3, 3)
    # Diagonal debe ser 0.0
    for i in range(3):
        assert sim_matrix[i, i] == 0.0

    # Simetría sim(101, 102) == sim(102, 101)
    idx1 = user_index[101]
    idx2 = user_index[102]
    assert pytest.approx(sim_matrix[idx1, idx2], 0.0001) == sim_matrix[idx2, idx1]
    # Deben ser idénticos (similitud 1.0)
    assert pytest.approx(sim_matrix[idx1, idx2], 0.0001) == 1.0


def test_recommend_movies():
    ratings = [
        {"user_id": 1, "movie_id": 1, "rating": 5.0},
        {"user_id": 1, "movie_id": 2, "rating": 4.0},
        {"user_id": 2, "movie_id": 1, "rating": 5.0},
        {"user_id": 2, "movie_id": 3, "rating": 4.5},
    ]
    movies = [
        {"movie_id": 1, "title": "Peli 1"},
        {"movie_id": 2, "title": "Peli 2"},
        {"movie_id": 3, "title": "Peli 3"},
    ]
    u_matrix = prepare_data(ratings)
    sims = calculate_similarity(u_matrix)
    recs = recommend_movies(1, u_matrix, sims, movies, top_n=2)

    # El usuario 1 no vio Peli 3, y el usuario 2 similar la valoró alto
    assert "Peli 3" in recs
