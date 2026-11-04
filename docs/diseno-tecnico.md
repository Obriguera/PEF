# Diseño técnico

## El problema de fondo

La operación crítica es **comparar a cada usuario con todos los demás**. Con U usuarios hay U² pares: con 2.000
usuarios son unos 4 millones de comparaciones, y duplicar los usuarios cuadruplica el cómputo. En la implementación
inicial cada comparación buscaba las películas en común con un doble bucle en Python puro, y una sola recomendación
tardaba casi 4 minutos con 2.000 usuarios, 500 películas y 30 calificaciones por usuario.

La regla de trabajo fue **medir antes de optimizar**: cProfile mostró que el 99,88 % del tiempo estaba en una sola
función (la similitud coseno), así que optimizar cualquier otra cosa era irrelevante.

## El algoritmo

Filtrado colaborativo *user-user* con similitud coseno.

**Similitud** entre los usuarios `a` y `b`, con `r_a` y `r_b` sus vectores de calificaciones (0 donde no
calificaron):

```text
sim(a, b) = (r_a · r_b) / (‖r_a‖ · ‖r_b‖)
```

**Predicción** de la calificación del usuario `u` para la película `m`, sobre los demás usuarios `v` que la calificaron
y cuya similitud con `u` es positiva:

```text
pred(u, m) = Σ_v sim(u, v) · r(v, m)  /  Σ_v sim(u, v)
```

Se recomiendan las `top_n` películas no vistas con mayor predicción.

## Estructuras de datos

| Estructura | Tipo | Para qué |
|---|---|---|
| Matriz de utilidad | `dict[int, dict[int, float]]`: usuario → {película → puntaje} | Entrada del cálculo; permite iterar solo lo calificado. |
| Matriz de calificaciones | `ndarray` `float32` de usuarios × películas | Base del cálculo vectorizado. |
| Matriz de similitudes | `ndarray` `float32` de usuarios × usuarios | Resultado; la fila de un usuario da su similitud con todos. |
| Índice de usuarios | `dict[int, int]`: `user_id` → fila | Traduce identificadores a posiciones del arreglo. |
| Índice invertido | `dict[int, list[tuple[int, float]]]`: película → [(vecino, puntaje)] | Predecir recorriendo solo a quienes calificaron la película. |

Los tipos de los datos de entrada y salida (`Movie`, `User`, `Rating`, `PopularMovie`) son `TypedDict`
definidos en `data_models.py`.

## Decisiones de diseño

### 1. Similitud con álgebra lineal vectorizada

Se construye la matriz densa de calificaciones `R` (usuarios × películas) y **todas** las similitudes salen de
un solo producto matricial:

```text
normas       = ‖R‖ por fila
similitudes  = (R · Rᵀ) / (normas · normasᵀ)      # ejecutado en C/BLAS
```

Después se ponen en 0 la diagonal y las filas y columnas de los usuarios sin calificaciones (norma cero).

- **Por qué:** el doble bucle en Python pasa a una llamada que se ejecuta en C. El cálculo bajó de ~15–20 s a
  **0,06 s** en el benchmark.
- **Por qué `float32`:** ocupa la mitad que `float64` y la precisión alcanza para calificaciones de 1 a 5. Un test
  de memoria detecta si el `dtype` cambia por accidente.
- **Límite:** la matriz es **densa**: la memoria crece con U². Con 2.000 usuarios son 16 MB; con 100.000 serían
  40 GB. Con datasets reales como MovieLens, donde la matriz está llena en menos del 5 %, convendría una matriz
  dispersa.

### 2. Top N con un heap

`heapq.nlargest` mantiene solo los N mejores: cuesta O(n log N) en lugar de ordenar todo en O(n log n). Como la
lista contiene tuplas `(predicción, película)`, el identificador de la película desempata y el resultado es
determinístico.

### 3. Índice invertido para predecir

Para predecir una película hay que sumar sobre los usuarios que la calificaron. En lugar de recorrer a **todos** los
usuarios por cada película no vista, `_Neighbors` arma una vez por consulta un índice película → vecinos. En el
benchmark (400 usuarios × 300 películas, 40 recomendaciones) la consulta pasó de 447 ms a 198 ms.

!!! warning "Un detalle que importa: el orden de las sumas"
    Las sumas se hacen con un bucle explícito, en el mismo orden que la versión original, y no con `sum()`. Desde
    Python 3.12, `sum()` usa suma compensada y puede cambiar el último bit del resultado. Como las pruebas de
    caracterización comparan los resultados **exactamente**, cambiar el orden de las sumas las rompe aunque el
    cambio sea correcto.

El costo es que el índice se reconstruye en cada consulta (O(total de calificaciones)). Cachearlo sería la
siguiente mejora, a cambio de invalidarlo cuando entre una calificación.

### 4. Caché de popularidad con invalidación

El Top 5 de películas más calificadas se calcula una vez y se guarda en una variable de módulo; las lecturas
posteriores son O(1). `POST /api/rate` lo invalida, para no servir datos viejos. Es un **caché** (un dato de acceso
frecuente con una regla de invalidación), no una memoización.

### 5. Archivos grandes: buffer, lotes y procesos

El procesamiento de un CSV de 500.000 filas combina tres técnicas:

| Técnica | Implementación | Por qué |
|---|---|---|
| **Buffer** | `open(..., buffering=64 KB)` | Menos llamadas al sistema operativo. |
| **Lotes** | Un generador entrega bloques de 25.000 filas | La memoria queda acotada al tamaño del lote, no al del archivo. |
| **Procesos** | `ProcessPoolExecutor` con contexto `spawn`, hasta 4 procesos | Es trabajo de CPU: con hilos, el GIL impediría el paralelismo real. |

**Contrapresión.** El proceso principal mantiene como máximo `2 × max_workers` lotes en vuelo; al llegar al tope espera
a que termine alguno antes de leer más. Sin esto, se enviaban todos los lotes al pool antes de consumir ningún
resultado y los pendientes se acumulaban en memoria: el pico del proceso principal crecía con el archivo (de 18 a 67 MB
entre 100.000 y 400.000 filas). Con la contrapresión queda plano en ~9,3 MB.

## Alternativas descartadas

| Alternativa | Por qué no |
|---|---|
| Factorización de matrices (SVD) | Predice mejor, pero el costo de entrenamiento no se justifica para este caso. |
| Multiprocessing para atender peticiones | Replicaría los datos en cada proceso; los hilos de FastAPI alcanzan porque las lecturas son concurrentes y no se modifican. |
| Matriz dispersa (SciPy) | Con el dataset de demostración, que es chico y denso, agrega complejidad sin beneficio. Es el paso lógico si se usan datos reales grandes. |
| `fork()` para los procesos hijos | Desde un proceso con hilos puede dejarlos trabados. Se usa `spawn`, con ~70–100 ms fijos de arranque. |

## Complejidad por función

| Función | Costo | Nota |
|---|---|---|
| `prepare_data` | O(R) | R = total de calificaciones |
| `calculate_similarity` | O(U² · M) en BLAS, memoria O(U²) | U usuarios, M películas |
| `recommend_movies` | O(R) para el índice + O(raters de cada película no vista) | más O(n log N) del heap |
| `analyze_popularity` | O(R) la primera vez, O(1) con caché | |
| `stream_ratings_in_batches` | O(filas), memoria O(lote) | generador |
| `process_large_file_parallel` | O(filas / procesos), memoria O(`2 × procesos × lote`) | con contrapresión |

La complejidad **ciclomática** de todas las funciones es A (la máxima es 5, el promedio 2,7), y el CI lo exige. También
se limita el **tamaño**: como máximo 30 sentencias y 5 parámetros por función (la más grande llegó a tener 43 sentencias
y se dividió; hoy el máximo es 23).
Ver [Mantenimiento](mantenimiento.md).
