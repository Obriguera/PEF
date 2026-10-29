import os

import pytest

from large_file_handler import (
    _process_chunk_worker,
    generate_large_ratings_csv,
    process_large_file_parallel,
    run_point_3_demonstration,
    stream_ratings_in_batches,
    write_aggregated_results_buffered,
)


@pytest.fixture
def temp_csv_file(tmp_path):
    csv_path = str(tmp_path / "test_ratings.csv")
    generate_large_ratings_csv(csv_path, num_records=2000, num_users=50, num_movies=10)
    return csv_path


def test_stream_ratings_in_batches(temp_csv_file):
    batch_size = 500
    batches = list(stream_ratings_in_batches(temp_csv_file, batch_size=batch_size))
    # 2000 registros en batches de 500 = 4 batches
    assert len(batches) == 4
    for b in batches:
        assert len(b) == 500
        assert "user_id" in b[0]
        assert "movie_id" in b[0]
        assert "rating" in b[0]


def test_process_large_file_parallel(temp_csv_file, tmp_path):
    stats = process_large_file_parallel(temp_csv_file, batch_size=500, max_workers=2)
    assert len(stats) > 0
    # La suma de conteos de todas las pelis debe dar exactamente 2000
    total_count = sum(d["count"] for d in stats.values())
    assert total_count == 2000

    out_file = str(tmp_path / "aggregated.csv")
    write_aggregated_results_buffered(out_file, stats)
    assert os.path.exists(out_file)
    assert os.path.getsize(out_file) > 0


def test_worker_agrega_suma_y_conteo_por_pelicula():
    chunk = [
        {"user_id": 1, "movie_id": 10, "rating": 4.0},
        {"user_id": 2, "movie_id": 10, "rating": 2.5},
        {"user_id": 3, "movie_id": 20, "rating": 5.0},
    ]
    assert _process_chunk_worker(chunk) == {10: {"sum": 6.5, "count": 2}, 20: {"sum": 5.0, "count": 1}}


def test_procesamiento_paralelo_coincide_con_el_secuencial(temp_csv_file):
    todas = [r for lote in stream_ratings_in_batches(temp_csv_file) for r in lote]
    secuencial = _process_chunk_worker(todas)
    paralelo = process_large_file_parallel(temp_csv_file, batch_size=300, max_workers=2)
    assert paralelo.keys() == secuencial.keys()
    for movie_id, esperado in secuencial.items():
        assert paralelo[movie_id]["count"] == esperado["count"]
        # Los lotes cambian el orden de las sumas de floats: se compara con tolerancia
        assert paralelo[movie_id]["sum"] == pytest.approx(esperado["sum"])


def test_generacion_escribe_lotes_completos_y_encabezado(tmp_path):
    # 20.000 registros = exactamente un lote de escritura, sin remanente
    csv_path = generate_large_ratings_csv(
        str(tmp_path / "sub" / "r.csv"), num_records=20000, num_users=5, num_movies=3
    )
    with open(csv_path, encoding="utf-8") as f:
        lineas = f.read().splitlines()
    assert lineas[0] == "user_id,movie_id,rating,timestamp"
    assert len(lineas) == 20001
    user_id, movie_id, rating, _ = lineas[1].split(",")
    assert 1 <= int(user_id) <= 5
    assert 1 <= int(movie_id) <= 3
    assert 1.0 <= float(rating) <= 5.0


def test_escritura_de_resultados_agregados(tmp_path):
    out = write_aggregated_results_buffered(
        str(tmp_path / "agg.csv"), {7: {"sum": 9.0, "count": 2}, 8: {"sum": 0.0, "count": 0}}
    )
    with open(out, encoding="utf-8") as f:
        assert f.read().splitlines() == ["movie_id,total_ratings,average_rating", "7,2,4.5", "8,0,0.0"]


def test_demostracion_del_punto_3(tmp_path):
    t_naive, t_opt = run_point_3_demonstration(str(tmp_path), num_records=2000)
    assert t_naive > 0
    assert t_opt > 0
    assert os.path.getsize(tmp_path / "massive_ratings_aggregated.csv") > 0
