# Pruebas

La suite tiene **88 tests** y una cobertura del **100 %** (líneas y ramas) sobre el código de la aplicación; el umbral
que exige el CI es 80 %. Corre en Python 3.11, 3.12 y 3.13.

```bash
python tasks.py test                          # toda la suite, con cobertura y umbral
python -m pytest tests/test_api.py -q         # un solo archivo
```

!!! warning "Sobre el 100 %"
    Es un código chico (unas 300 sentencias). Vale más lo que las pruebas fijan que el porcentaje: ver las
    categorías de abajo. Además, `coverage` no mide los subprocesos de `ProcessPoolExecutor`, así que el *worker*
    se prueba llamándolo directamente.

## Qué hay y para qué

| Archivo | Tests | Qué fija |
|---|---:|---|
| `test_recommender.py` | 3 | Propiedades del recomendador: matriz de utilidad, simetría y diagonal de la similitud, Top N. |
| `test_characterization.py` | 8 | La salida del recomendador es **exactamente** la de la versión de referencia (ver abajo). |
| `test_analysis.py` | 1 | El caché de popularidad devuelve el mismo objeto y se invalida. |
| `test_api.py` | 18 | Los endpoints, con `TestClient`: respuestas, validaciones (404 y 422) y límites. |
| `test_large_file.py` | 7 | Lectura por lotes, escritura, *worker*, paralelo contra secuencial y la demostración. |
| `test_memory.py` | 3 | El pico de memoria no crece con el tamaño del archivo (ver abajo). |
| `test_benchmarks.py` | 7 | Benchmarks; se miden con `python tasks.py bench` (ver [Rendimiento](rendimiento.md)). |
| `test_tasks.py` | 34 | Las piezas de `tasks.py` que usa el CI: resumen, comparación de benchmarks, excepciones de `pip-audit` y verificación de enlaces. |
| `test_evolucion.py` | 7 | Las funciones puras de la medición de evolución entre versiones y el *worker* (ver [Evolución](evolucion.md)). |

## Pruebas de caracterización (*golden master*)

Fijan el **comportamiento observable** del recomendador antes de refactorizarlo. Se generó una salida de referencia
con el código del tag `parcial3-fase0` sobre dos conjuntos de datos (los reales y uno sintético determinístico, sin
generador aleatorio, que incluye un usuario con norma cero) y las pruebas comparan **por igualdad exacta**, sin
tolerancia: matriz de similitud, índice de usuarios y ranking completo de cada usuario.

- **Por qué exacta:** una tolerancia dejaría pasar cambios numéricos sutiles introducidos por un refactor.
- **Costo:** cualquier cambio que altere el orden de las sumas de `float` rompe las pruebas, aunque sea correcto. Si
  un cambio así es intencional, se regenera la referencia con `python tests/golden.py` y se justifica en el commit.
- **Comprobación cruzada:** una prueba diferencial adicional contra el tag, con 400 usuarios y 20.000 calificaciones,
  dio matriz, índice y rankings idénticos.

## Pruebas de memoria

Usan `tracemalloc` sobre el proceso principal. El control principal es **relativo** (el mismo código sobre archivos
de distinto tamaño), así que no depende de la máquina:

| Control | Medido | Límite |
|---|---:|---:|
| Lectura por lotes de 2.000 filas | 0,98 MB | 2 MB |
| Procesamiento paralelo (lote de 2.000, 2 procesos) | 2,1 a 2,5 MB | 5 MB |
| `calculate_similarity` con 400 usuarios × 300 películas | 2,32 MB | 3 MB |

El último valida el `dtype`: en `float32` la teoría da 2,29 MB y en `float64` serían ~4,6 MB, así que el límite de
3 MB detecta una regresión de tipo.

## Casos de prueba y resultados

Casos representativos, con lo que se espera de cada uno:

| Caso | Resultado esperado |
|---|---|
| Usuario sin calificaciones (norma cero) | Similitud 0 con todos; no recibe recomendaciones |
| Usuario inexistente | `KeyError` en el núcleo; **404** en la API |
| CSV con filas vacías, con menos de 3 columnas o sin *timestamp* | Se omiten las dos primeras; la tercera es válida |
| Archivo inexistente al leer por lotes | `FileNotFoundError` |
| Puntaje 0,99 · 5,01 · −3 · 1e308 | **422** y no se agrega nada; 1,0 y 5,0 se aceptan |
| `records` = 0, −5 o 1.000.001 | **422** y no se crea ningún archivo |
| Procesamiento paralelo contra secuencial | Mismos conteos; las sumas coinciden con tolerancia |
| Caché de popularidad | Mismo objeto mientras no se invalide; uno nuevo e igual después |
| Memoria de la lectura y del paralelo, con archivos de 50.000 y 200.000 filas | No crece con el tamaño del archivo |
| Mismos datos, dos ejecuciones | Misma salida, bit a bit (*golden master*) |

**Resultados de la última verificación completa:**

| Control | Resultado |
|---|---|
| Tests en Python 3.11, 3.12 y 3.13 | 88 de 88 en las tres versiones |
| Cobertura (líneas y ramas) | 100 % en los cinco módulos de la aplicación; umbral 80 % |
| Complejidad ciclomática | todas las funciones en rango A (máxima 5) |
| Tipado | 0 errores de mypy, y el núcleo también con `--strict` |

Cada ejecución del CI repite estos controles y deja `junit.xml` y `coverage.xml` como artefactos (ver
[Mantenimiento](mantenimiento.md)).

## Aislamiento

`POST /api/rate` modifica una lista y un caché globales. `test_api.py` los restaura después de cada test con un
*fixture*; cualquier test nuevo de la API tiene que conservar ese aislamiento, o contaminará a los que corren después.

## Convenciones

- **Primero el test, y rojo.** Cada corrección de comportamiento se escribió con un test que falla antes del cambio y
  pasa después (por ejemplo, la validación de entradas de la API y la memoria del procesamiento paralelo).
- **Propiedades, no solo valores.** Por ejemplo, que la matriz de similitud sea simétrica con diagonal cero.
- **Los controles también se prueban.** Un escaneo limpio no dice nada si la herramienta no puede detectar nada: ver
  en [Seguridad](seguridad.md#estado-de-verificación) los casos positivos con los que se verificó cada control.

## Lo que no se prueba

- La interfaz web (`index.html`) se probó a mano; no hay pruebas automáticas del navegador.
- No hay pruebas de extremo a extremo contra un servidor `uvicorn` real: la API se prueba con `TestClient`.
- Windows y macOS no están cubiertos por el CI.
