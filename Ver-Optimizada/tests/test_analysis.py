from analysis_utils import analyze_popularity, invalidar_cache_popularidad


def test_popularity_caching():
    invalidar_cache_popularidad()
    ratings = [
        {"user_id": 1, "movie_id": 1, "rating": 5.0},
        {"user_id": 2, "movie_id": 1, "rating": 4.0},
        {"user_id": 3, "movie_id": 2, "rating": 4.5},
    ]
    movies = [
        {"movie_id": 1, "title": "Peli Top"},
        {"movie_id": 2, "title": "Peli Segunda"},
    ]

    res1 = analyze_popularity(ratings, movies)
    assert res1[0]["title"] == "Peli Top"
    assert res1[0]["count"] == 2

    # El resultado en caché debe ser idéntico por referencia
    res2 = analyze_popularity(ratings, movies)
    assert res1 is res2

    # Al invalidar, se recalcula un nuevo objeto
    invalidar_cache_popularidad()
    res3 = analyze_popularity(ratings, movies)
    assert res3 == res1
    assert res3 is not res1
