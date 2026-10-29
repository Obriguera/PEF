import os

import pytest

from large_file_handler import (
    generate_large_ratings_csv,
    process_large_file_parallel,
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
