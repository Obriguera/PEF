# Línea de base de la Fase 1 (Parcial 3)

Medición tomada sobre el tag `parcial3-fase0` (commit `eb8caa1`) con las dependencias
fijadas de `requirements-dev.txt` y los mismos comandos de `tasks.py` que usará el CI.
Los valores en formato máquina están en [`metrics/parcial3-fase0.json`](metrics/parcial3-fase0.json).

## Resumen

| Control | Comando | Resultado | Meta de la Fase 1 |
|---|---|---|---|
| Complejidad (Xenon A) | `python tasks.py complexity` | ❌ 4 funciones y 1 módulo en rango B | Todo en rango A |
| Cobertura | `python tasks.py test` | ❌ 70,67 % (11 tests, todos pasan) | ≥ 80 % |
| Tipado | `python tasks.py typecheck` | ❌ 6 errores (`no-untyped-def`) | 0 errores |
| Lint | `python tasks.py lint` | ❌ 33 hallazgos, 9 archivos sin formato | 0 hallazgos |
| SAST | `python tasks.py sast` | ✅ 0 media/alta (3 bajas B311) | Se mantiene |
| Dependencias | `python tasks.py audit` | ✅ 0 vulnerabilidades | Se mantiene |
| Documentación | `python tasks.py docs-sphinx` | ✅ compila con `-W` | Se mantiene |

## Complejidad ciclomática

Promedio A (3,78) sobre 18 bloques. Xenon rechaza por estos bloques:

| Función | CC | Rango | Origen de la complejidad |
|---|---|---|---|
| `recommender_core._cosine_similarity` | 10 | B | Dos caminos (dict y vector) en una función, cada uno con sus guardas de norma cero |
| `recommender_core.recommend_movies` | 9 | B | Doble bucle anidado con tres condiciones para acumular la predicción |
| `recommender_core.calculate_similarity` | 8 | B | Construcción de la matriz, normalización y anulación de usuarios vacíos en un solo bloque |
| `large_file_handler.stream_ratings_in_batches` | 7 | B | Validación, parseo de filas y corte de lotes mezclados en el mismo bucle |

Por arrastre, el módulo `recommender_core` también queda en B.

Índice de mantenibilidad (todos en A): `data_models` 100, `analysis_utils` 88,7,
`main` 80,0, `recommender_core` 64,3, `large_file_handler` 54,1.

## Cobertura

| Módulo | Cobertura | Líneas sin cubrir |
|---|---|---|
| `analysis_utils.py` | 100 % | — |
| `data_models.py` | 100 % | — |
| `recommender_core.py` | 81 % | camino de diccionarios de `_cosine_similarity`, anulación de usuarios sin ratings |
| `main.py` | 74 % | endpoint `process_large_file_endpoint` |
| `large_file_handler.py` | 58 % | `run_point_3_demonstration`, el worker paralelo, filas inválidas, archivo inexistente |

## Tipado

mypy informa 6 funciones sin anotar en el núcleo: `prepare_data`, `_cosine_similarity`,
`calculate_similarity` y `recommend_movies` en `recommender_core.py`, y `analyze_popularity`
e `invalidar_cache_popularidad` en `analysis_utils.py`.

## Lint

33 hallazgos de Ruff: 17 UP006 y 4 UP035 (`List`/`Dict`/`Tuple` de `typing`), 8 I001
(orden de imports), 2 UP015 (modo `"r"` redundante), 1 SIM118 (`in dict.keys()`) y
1 B007 (variable de bucle sin usar). 28 se corrigen automáticamente.

## Plan de ataque

1. **Lint y formato**: aplicar las correcciones automáticas de Ruff y arreglar a mano
   SIM118 y B007. No cambia el comportamiento y deja limpio el ruido antes del refactor.
2. **Type hints** en el núcleo, apoyados en los tipos de `data_models.py`.
3. **Refactor a rango A** de las 4 funciones, extrayendo funciones auxiliares. Antes de
   tocar cada una, se agregan tests de caracterización para fijar su comportamiento.
4. **Cobertura ≥ 80 %**: tests para el endpoint de archivo grande, el procesamiento
   paralelo, las filas inválidas y los caminos de norma cero.

## Resultado de la Fase 1

Medición final sobre el commit `dc9a68e`. El detalle está en
[`metrics/parcial3-fase1.json`](metrics/parcial3-fase1.json).

| Control | Línea base | Fase 1 |
|---|---|---|
| Xenon A | ❌ 4 funciones y 1 módulo en B | ✅ todo en A, CC máxima 5 |
| CC promedio | 3,78 | 2,66 |
| Cobertura | 70,67 % (11 tests) | 100 % (24 tests) |
| mypy | 6 errores | 0 (también con `--strict` en el núcleo) |
| Ruff | 33 hallazgos | 0 |
| MI de `recommender_core` | 64,29 | 67,59 |
| `recommend_movies` (benchmark) | 447 ms | 198 ms (2,2×) |
| `python tasks.py ci` | ❌ | ✅ |

Notas para leer la tabla:

- **El comportamiento no cambió.** Los tests de caracterización comparan por igualdad exacta
  contra un golden master generado con el código del tag `parcial3-fase0`. Una prueba
  diferencial con 400 usuarios dio matriz, índice y rankings idénticos.
- **La mejora de rendimiento vino del refactor.** La primera versión, con un generador por
  película, quedaba un 13 % más lenta. Un índice invertido película → vecinos la dejó en 2,2×
  más rápida, con el mismo orden de sumas.
- **Se eliminó código muerto.** `_cosine_similarity` y sus auxiliares no tenían uso en
  producción: `calculate_similarity` está vectorizada desde el Parcial 2.
- **El 100 % de cobertura corresponde a un código chico** (293 sentencias). Vale más que los
  tests fijan comportamiento (golden master, casos borde, consistencia paralelo/secuencial) y no
  solo ejecutan líneas.
- **Corrección:** el mensaje del commit `95b0a9c` dice que el MI de `recommender_core` era 60,6.
  Ese valor se midió antes del ajuste final; el real era 61,75, y tras eliminar el código muerto
  quedó en 67,59.

Pendiente para la Fase 2: el `ProcessPoolExecutor` hace `fork()` desde un proceso multihilo
cuando lo llama el endpoint (pasar a `spawn`), y `records_processed` informa los registros
pedidos y no los procesados cuando el CSV ya existía.
