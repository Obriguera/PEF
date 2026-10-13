# Reporte de Calidad de Código (Punto 6 del Parcial)

Herramientas utilizadas:
- **Flake8**: Verificación estricta de estilo y conformidad con **PEP 8**.
- **Radon**: Medición de **Complejidad Ciclomática (CC)** e **Índice de Mantenibilidad (MI)**.

---

## 1. Conformidad PEP 8 (Flake8)
- **Resultado:** `0 errores / 0 advertencias`.
- Todas las funciones cuentan con espaciado estándar, longitud máxima de línea controlada y ausencia de imports no utilizados.

---

## 2. Complejidad Ciclomática (Radon CC)
*Escala: A (1-5, simple/bajo riesgo) | B (6-10, riesgo moderado) | C (11-20, riesgo alto)*

| Módulo | Función / Clase | Rango | Complejidad |
|---|---|:---:|:---:|
| `analysis_utils.py` | `analyze_popularity` | **A** | 5 |
| `analysis_utils.py` | `invalidar_cache_popularidad` | **A** | 1 |
| `benchmark.py` | `generate_massive_data` | **A** | 4 |
| `benchmark.py` | `run_baseline_test` | **A** | 1 |
| `large_file_handler.py` | `stream_ratings_in_batches` | **B** | 7 |
| `large_file_handler.py` | `process_large_file_parallel` | **A** | 5 |
| `large_file_handler.py` | `generate_large_ratings_csv` | **A** | 4 |
| `large_file_handler.py` | `_process_chunk_worker` | **A** | 3 |
| `large_file_handler.py` | `write_aggregated_results_buffered` | **A** | 3 |
| `large_file_handler.py` | `run_point_3_demonstration` | **A** | 3 |
| `main.py` | `process_large_file_endpoint` | **A** | 2 |
| `main.py` | `get_users` | **A** | 1 |
| `main.py` | `get_recommendations` | **A** | 1 |
| `main.py` | `get_popularity` | **A** | 1 |
| `main.py` | `add_new_rating` | **A** | 1 |
| `recommender_core.py` | `_cosine_similarity` | **B** | 10 |
| `recommender_core.py` | `recommend_movies` | **B** | 9 |
| `recommender_core.py` | `calculate_similarity` | **B** | 8 |
| `recommender_core.py` | `prepare_data` | **A** | 3 |

**Promedio general de complejidad ciclomática:** **A (3.65)** (Código simple, modular y de bajo riesgo).

---

## 3. Índice de Mantenibilidad (Radon MI)
*Escala: A (100-20, muy mantenible) | B (19-10, mantenibilidad media) | C (9-0, difícil de mantener)*

| Módulo | Calificación | Score MI |
|---|:---:|:---:|
| `analysis_utils.py` | **A** | 88.72 |
| `benchmark.py` | **A** | 86.64 |
| `main.py` | **A** | 80.04 |
| `recommender_core.py` | **A** | 64.29 |
| `large_file_handler.py` | **A** | 54.13 |

**Conclusión:** El 100% de los módulos del proyecto se ubican en la categoría **A** de mantenibilidad.

