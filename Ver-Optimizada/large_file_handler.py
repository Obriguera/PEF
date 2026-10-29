"""Módulo de procesamiento eficiente de archivos grandes.

Punto 3 del Parcial: Escritura y lectura de archivos grandes mediante:
1. Buffering: Manejo de buffers de E/S en disco para reducir llamadas al sistema (syscalls).
2. Batching (Lotes): Procesamiento por chunks para mantener un consumo de memoria constante O(1).
3. Procesamiento en Paralelo: Distribución de lotes entre múltiples hilos o procesos (concurrent.futures).
"""

import csv
import os
import random
import time
from collections.abc import Generator
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any

DEFAULT_BUFFER_SIZE = 64 * 1024  # 64 KB de buffer de E/S
DEFAULT_BATCH_SIZE = 25000  # 25.000 registros por lote


def generate_large_ratings_csv(
    filepath: str,
    num_records: int = 500000,
    num_users: int = 5000,
    num_movies: int = 1000,
    buffer_size: int = DEFAULT_BUFFER_SIZE,
) -> str:
    """Genera un archivo CSV masivo de ratings simulando un dataset de producción.

    Aplica:
        - Buffering: open(..., buffering=buffer_size) minimiza accesos a disco.
        - Batching de escritura: escribe bloques de filas a disco en lugar de línea por línea.
    """
    print(f"[ESCRITURA BATCH/BUFFER] Generando {num_records:,} registros en '{filepath}'...")
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)

    t_start = time.perf_counter()
    batch_records = []
    batch_limit = 20000

    # Usamos buffer explícito de E/S
    with open(filepath, mode="w", newline="", encoding="utf-8", buffering=buffer_size) as f:
        writer = csv.writer(f)
        writer.writerow(["user_id", "movie_id", "rating", "timestamp"])

        current_ts = int(time.time())
        for _ in range(num_records):
            user_id = random.randint(1, num_users)
            movie_id = random.randint(1, num_movies)
            rating = round(random.uniform(1.0, 5.0), 1)
            batch_records.append([user_id, movie_id, rating, current_ts])

            # Escribir en lotes para optimizar llamadas al buffer
            if len(batch_records) >= batch_limit:
                writer.writerows(batch_records)
                batch_records.clear()

        # Escribir registros remanentes
        if batch_records:
            writer.writerows(batch_records)
            batch_records.clear()

    elapsed = time.perf_counter() - t_start
    filesize_mb = os.path.getsize(filepath) / (1024 * 1024)
    print(f"[ESCRITURA] Archivo generado: {filesize_mb:.2f} MB en {elapsed:.2f} segundos.")
    return filepath


def stream_ratings_in_batches(
    filepath: str, batch_size: int = DEFAULT_BATCH_SIZE, buffer_size: int = DEFAULT_BUFFER_SIZE
) -> Generator[list[dict[str, Any]], None, None]:
    """Generador que lee un archivo grande por bloques (batches) utilizando un buffer I/O.

    Ventaja de Memoria:
        Mantiene un footprint de memoria acotado a 'batch_size' registros,
        evitando cargar el archivo completo en RAM (O(batch_size) vs O(Total_Archivo)).
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No se encontró el archivo {filepath}")

    with open(filepath, encoding="utf-8", buffering=buffer_size) as f:
        reader = csv.reader(f)
        next(reader, None)  # Saltar encabezado

        current_batch: list[dict[str, Any]] = []
        for row in reader:
            if not row or len(row) < 3:
                continue

            current_batch.append({"user_id": int(row[0]), "movie_id": int(row[1]), "rating": float(row[2])})

            if len(current_batch) >= batch_size:
                yield current_batch
                current_batch = []

        if current_batch:
            yield current_batch


def _process_chunk_worker(chunk: list[dict[str, Any]]) -> dict[int, dict[str, float]]:
    """Función de trabajo para procesamiento en paralelo.

    Calcula agregaciones parciales (suma de calificaciones y conteo) por película
    para un lote de registros sin bloquear el proceso principal.
    """
    stats: dict[int, dict[str, float]] = {}
    for r in chunk:
        movie_id = r["movie_id"]
        rating = r["rating"]
        if movie_id not in stats:
            stats[movie_id] = {"sum": 0.0, "count": 0}
        stats[movie_id]["sum"] += rating
        stats[movie_id]["count"] += 1
    return stats


def process_large_file_parallel(
    filepath: str, batch_size: int = DEFAULT_BATCH_SIZE, buffer_size: int = DEFAULT_BUFFER_SIZE, max_workers: int = 4
) -> dict[int, dict[str, float]]:
    """Lee y procesa un archivo masivo combinando Buffering, Batching y Procesamiento Paralelo.

    Estrategia:
        1. El generador stream_ratings_in_batches() lee trozos del archivo en memoria acotada.
        2. Los lotes se envían a un ProcessPoolExecutor para procesar en núcleos paralelos de CPU.
        3. El proceso principal consolida los resultados parciales de cada worker.
    """
    print(f"\n[PROCESAMIENTO PARALELO] Procesando '{filepath}' con {max_workers} procesos...")
    t_start = time.perf_counter()

    total_stats: dict[int, dict[str, float]] = {}
    total_records = 0
    futures = []

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        for batch in stream_ratings_in_batches(filepath, batch_size=batch_size, buffer_size=buffer_size):
            total_records += len(batch)
            futures.append(executor.submit(_process_chunk_worker, batch))

        # Consolidar resultados a medida que los workers terminan
        for future in as_completed(futures):
            partial_stats = future.result()
            for movie_id, data in partial_stats.items():
                if movie_id not in total_stats:
                    total_stats[movie_id] = {"sum": 0.0, "count": 0}
                total_stats[movie_id]["sum"] += data["sum"]
                total_stats[movie_id]["count"] += data["count"]

    elapsed = time.perf_counter() - t_start
    print(
        f"[PROCESAMIENTO PARALELO] {total_records:,} registros procesados en {elapsed:.2f}s "
        f"({len(total_stats):,} películas calculadas)."
    )
    return total_stats


def write_aggregated_results_buffered(
    output_filepath: str, aggregated_stats: dict[int, dict[str, float]], buffer_size: int = DEFAULT_BUFFER_SIZE
) -> str:
    """Escribe los resultados procesados a disco usando buffer y streaming."""
    with open(output_filepath, mode="w", newline="", encoding="utf-8", buffering=buffer_size) as f:
        writer = csv.writer(f)
        writer.writerow(["movie_id", "total_ratings", "average_rating"])
        for movie_id, data in aggregated_stats.items():
            count = data["count"]
            avg = round(data["sum"] / count, 2) if count > 0 else 0.0
            writer.writerow([movie_id, int(count), avg])
    return output_filepath


def run_point_3_demonstration(output_dir: str = ".") -> tuple[float, float]:
    """Demostración comparativa para la defensa del Parcial:

    Compara:
        1. Enfoque Ingenuo: Cargar archivo completo en memoria RAM con readlines().
        2. Enfoque Optimizado: Buffer I/O + Streaming por Chunks + Procesamiento Paralelo.
    """
    import psutil

    process = psutil.Process(os.getpid())
    test_csv = os.path.join(output_dir, "massive_ratings_sample.csv")
    result_csv = os.path.join(output_dir, "massive_ratings_aggregated.csv")

    # 1. Generar archivo grande (500.000 registros, ~16-20 MB en disco)
    generate_large_ratings_csv(test_csv, num_records=500000, num_users=5000, num_movies=1000)

    # --- PRUEBA 1: Enfoque Ingenuo (Cargar todo en RAM de un solo golpe) ---
    print("\n" + "=" * 60)
    print(">>> 1. ENFOQUE INGENUO (Leer todo el archivo en RAM de una vez)")
    print("=" * 60)
    mem_before_naive = process.memory_info().rss / (1024 * 1024)
    t0_naive = time.perf_counter()

    with open(test_csv, encoding="utf-8") as f:
        raw_lines = f.readlines()  # Carga todo el texto en memoria
        naive_data = []
        for line in raw_lines[1:]:
            parts = line.strip().split(",")
            naive_data.append({"user_id": int(parts[0]), "movie_id": int(parts[1]), "rating": float(parts[2])})

    naive_stats = _process_chunk_worker(naive_data)
    t_naive = time.perf_counter() - t0_naive
    mem_after_naive = process.memory_info().rss / (1024 * 1024)
    mem_diff_naive = max(0.0, mem_after_naive - mem_before_naive)
    print(f"Tiempo enfoque ingenuo: {t_naive:.3f} s")
    print(f"Aumento de memoria RAM: {mem_diff_naive:.2f} MB")

    # Liberamos memoria de la prueba ingenua
    del raw_lines
    del naive_data
    del naive_stats

    # --- PRUEBA 2: Enfoque Optimizado (Buffer + Batching + Multiprocessing) ---
    print("\n" + "=" * 60)
    print(">>> 2. ENFOQUE OPTIMIZADO (Buffer I/O + Batches + Paralelismo)")
    print("=" * 60)
    mem_before_opt = process.memory_info().rss / (1024 * 1024)
    t0_opt = time.perf_counter()

    optimized_stats = process_large_file_parallel(
        filepath=test_csv, batch_size=25000, buffer_size=DEFAULT_BUFFER_SIZE, max_workers=4
    )

    write_aggregated_results_buffered(result_csv, optimized_stats)
    t_opt = time.perf_counter() - t0_opt
    mem_after_opt = process.memory_info().rss / (1024 * 1024)
    mem_diff_opt = max(0.0, mem_after_opt - mem_before_opt)

    print(f"Tiempo enfoque optimizado: {t_opt:.3f} s")
    print(f"Aumento de memoria en proceso principal: {mem_diff_opt:.2f} MB")

    speedup = t_naive / t_opt if t_opt > 0 else 1.0
    print("\n" + "=" * 60)
    print("RESUMEN COMPARATIVO:")
    print(f"- Reducción de tiempo / Aceleración: {speedup:.2f}x más rápido")

    print(f"- Control de memoria: {mem_diff_opt:.2f} MB vs {mem_diff_naive:.2f} MB del método ingenuo")
    print("=" * 60)

    return t_naive, t_opt


if __name__ == "__main__":
    run_point_3_demonstration()
