# PEF · Motor de recomendaciones de películas

**Programación Eficiente (PEF) · Universidad Blas Pascal**
Integrantes: **Octavio Briguera** y **Ricardo Lagoria**

Sistema de recomendación de películas por filtrado colaborativo, optimizado en dos etapas (Parcial 1 y Parcial 2) midiendo cada cambio con perfiladores.

| | Versión Base | Versión Optimizada |
|---|---:|---:|
| Tiempo del benchmark (Scalene) | 171,5 s | **20,3 s** (8,5× más rápido) |
| Memoria pico (Scalene) | 230,5 MB | **36,4 MB** (−84 %) |
| Cálculo de similitudes | ~15–20 s | **0,06 s** |

---

## Índice

1. [Caso de uso](#1-caso-de-uso)
2. [Planteo del problema](#2-planteo-del-problema)
3. [Estructura del repositorio](#3-estructura-del-repositorio)
4. [Parcial 1: de la versión Base a la Eficiente](#4-parcial-1-de-la-versión-base-a-la-eficiente)
5. [Parcial 2: versión Optimizada](#5-parcial-2-versión-optimizada)
6. [Resultados](#6-resultados)
7. [Cómo ejecutar el proyecto](#7-cómo-ejecutar-el-proyecto)
8. [API REST](#8-api-rest)
9. [Limitaciones y próximos pasos](#9-limitaciones-y-próximos-pasos)

---

## 1. Caso de uso

Un usuario quiere saber qué película ver. El sistema mira qué películas calificaron los usuarios con **gustos parecidos** a los suyos y le recomienda las que todavía no vio.

- **Algoritmo:** filtrado colaborativo *user-user* con **similitud coseno** entre los vectores de calificaciones.
- **Predicción:** para cada película no vista, el promedio de las calificaciones de los demás usuarios, ponderado por su similitud.
- **Salida:** el Top 5 de películas recomendadas.
- **Funciones extra:** ranking de películas más populares y carga de nuevas calificaciones.
- **Interfaz:** una API REST con FastAPI y una página web (`index.html`) que la consume.

## 2. Planteo del problema

La operación crítica es **comparar a cada usuario con todos los demás**:

- Con U usuarios hay U² pares. Con 2.000 usuarios son unos **4 millones de comparaciones**: duplicar los usuarios cuadruplica el cómputo.
- En la implementación inicial cada comparación buscaba las películas en común con un **doble bucle en Python puro**.
- Para obtener el Top 5 se **ordenaba la lista completa** de predicciones.

Con el benchmark (2.000 usuarios, 500 películas, 30 calificaciones por usuario) **una sola recomendación tardaba casi 4 minutos**. La versión Base, además, venía de una interfaz Tkinter que bloqueaba el hilo principal.

**Objetivo:** que el sistema escale. Hay que encontrar el cuello de botella **midiendo**, eliminarlo y verificar que los resultados no cambien.

## 3. Estructura del repositorio

```
PEF/
├── Ver-Base/          # Implementación inicial (línea base de las mediciones)
├── Ver-Eficiente/     # Parcial 1: estructuras de datos, heap y caché
├── Ver-Optimizada/    # Parcial 2: NumPy vectorizado, archivos grandes, calidad, docs y tests
│   ├── recommender_core.py     # Matriz de utilidad, similitud coseno y recomendación
│   ├── analysis_utils.py       # Ranking de popularidad con caché e invalidación
│   ├── large_file_handler.py   # Lectura y escritura de archivos grandes (buffer, lotes, paralelo)
│   ├── main.py                 # API REST (FastAPI)
│   ├── data_models.py          # Dataset de demostración en memoria
│   ├── benchmark.py            # Benchmark sintético (2.000 usuarios, 500 películas)
│   ├── index.html              # Interfaz web que consume la API
│   ├── tests/                  # Suite de pytest (11 tests)
│   ├── docs/                   # Documentación Sphinx (fuentes y HTML generado)
│   ├── scalene-profile.*       # Perfil de Scalene
│   ├── mi_programa.prof        # Perfil de cProfile (se visualiza con SnakeViz)
│   ├── quality_report.md       # Reporte de Flake8 y Radon
│   └── PARCIAL_2_REPORTE_FINAL.md
└── Parcial-2.txt      # Checklist de los temas del Parcial 2
```

Las tres versiones tienen la misma interfaz (mismos módulos y funciones). Así, el "antes y después" es un cambio de implementación y no una reescritura, y se puede medir cada etapa con el mismo `benchmark.py`.

## 4. Parcial 1: de la versión Base a la Eficiente

### 4.1 Versión Base (línea base)

Es **deliberadamente ingenua**: sirve como control experimental para medir cada mejora.

- Matriz de utilidad como diccionario de diccionarios.
- Intersección de películas en común con un doble bucle en Python. Es O(n·m) por cada uno de los O(U²) pares.
- Normas recalculadas en cada comparación.
- Top N obtenido ordenando todas las predicciones: O(n log n).
- Títulos buscados con un recorrido secuencial O(N).

### 4.2 Perfilado

Usamos **cProfile** y **Scalene**. El **99,88 % del tiempo** estaba en una sola función, `_cosine_similarity`. El pico de memoria (230 MB) aparecía en la construcción de la matriz de similitudes. Conclusión: optimizar cualquier otra cosa era irrelevante.

### 4.3 Decisiones de la versión Eficiente

| Requisito | Decisión | Justificación |
|---|---|---|
| Estructuras de datos | **Sets** para la intersección y **dict** para mapear `movie_id → título` | La pertenencia en un set (tabla hash) es O(1) promedio y la intersección se resuelve en C dentro del intérprete. El mapeo de títulos pasa de O(N) a O(1). |
| Algoritmo | **Heap** (`heapq.nlargest`) para el Top 5 | Ordenar todo es O(n log n) y resuelve un problema más grande del que tenemos. Con el heap el Top K cuesta O(n log K). |
| Caché | **Caché de popularidad** con invalidación explícita | El Top 5 de populares se calcula una vez y se lee en O(1). `POST /api/rate` invalida el caché para no servir datos viejos. Es caché, no memoización: guarda un dato de acceso frecuente con una regla de invalidación. |
| Concurrencia | **Hilos** a través de FastAPI (los endpoints `def` corren en su pool de hilos) | Las recomendaciones solo leen la matriz compartida, así que no hay condiciones de carrera. Se descartó multiprocessing porque replicaría la matriz de 230 MB en cada proceso (unos 920 MB con 4 procesos). Por el GIL, esto da **concurrencia de peticiones, no paralelismo del cálculo**. |
| Arquitectura | De Tkinter (bloqueante) a **API FastAPI + web** | La interfaz deja de bloquearse y la API puede atender muchas peticiones a la vez. |
| Alternativa descartada | Factorización de matrices (SVD) | Predice mejor, pero el costo de entrenamiento no se justifica en este caso. |

### 4.4 Resultado del Parcial 1

- **Sin perfilador:** de 231,4 s a 185,6 s.
- **Bajo Scalene:** la versión Eficiente midió *peor* (186,3 s contra 171,5 s). Scalene instrumenta cada línea y su sobrecarga no es uniforme: castiga más a las estructuras nativas que a un bucle de Python explícito. Por eso el perfilador sirve para **encontrar** el cuello de botella, no para cronometrarlo.
- **Memoria pico:** prácticamente igual (230,5 MB contra 230,6 MB). El cálculo O(U²) seguía en Python puro.

**Aprendizaje que motivó el Parcial 2:** mejorar las estructuras de datos ayudó, pero el cuello de botella real, la comparación todos contra todos en Python, seguía ahí.

## 5. Parcial 2: versión Optimizada

Sobre lo hecho en el Parcial 1, se agregaron los 9 puntos pedidos.

### Punto 1 · Eliminación de código redundante

- Las normas se calculaban N² veces; ahora se calcula **una norma por usuario, una sola vez**.
- La intersección con bucles se reemplazó por el **producto matricial R·Rᵀ**.
- Las búsquedas secuenciales O(N) pasaron a dict y set O(1).

### Punto 2 · Herramientas de optimización

- **Scalene:** lo elegimos porque separa el tiempo de Python del tiempo nativo y mide memoria por línea. En la Base, el 93 % del tiempo se iba en Python y las líneas con `sum()` y generadores dentro de `_cosine_similarity` concentraban el **85 % del tiempo**. Eso justificó vectorizar en lugar de seguir ajustando estructuras.
- **Herramienta general: cProfile + SnakeViz.**
  - cProfile es un perfilador **determinístico**: cuenta cada llamada a función. Complementa a Scalene, que trabaja por **muestreo**.
  - Viene en la biblioteca estándar: no requiere instalar agentes ni levantar servidores, como New Relic o Elastic APM. SnakeViz lo visualiza.
  - En la versión Optimizada registra 683.884 llamadas en 0,84 s. `calculate_similarity` baja a 81 ms y el **nuevo cuello de botella** pasa a ser `recommend_movies` (170 ms).

### Punto 3 · Lectura y escritura de archivos grandes (`large_file_handler.py`)

Se procesa un CSV de 500.000 calificaciones.

| Técnica | Implementación | Por qué |
|---|---|---|
| Buffer | `open(..., buffering=64 KB)` | Menos llamadas al sistema operativo. |
| Lotes (batching) | Un generador entrega bloques de 25.000 filas (20.000 en el endpoint) | La memoria queda acotada al tamaño del lote, no al tamaño del archivo. |
| Paralelismo | `ProcessPoolExecutor` con 4 procesos que agregan cada lote | Es trabajo de CPU: con hilos, el GIL impediría el paralelismo real. Acá, a diferencia de la API, cada proceso recibe solo su lote y no hay que replicar una matriz grande. |

Resultado: el enfoque ingenuo con `readlines()` aumenta la RAM en 173,5 MB; el optimizado, en 23,8 MB (**−86 %**). También se expone como endpoint: `GET /api/large-files/process`.

### Punto 4 · Legibilidad y mantenibilidad (PEP 8)

- **Flake8:** 0 errores y 0 advertencias.
- Nombres descriptivos y *type hints*.
- Docstrings que explican el porqué de cada optimización.
- Constantes con nombre en lugar de números mágicos (`DEFAULT_BUFFER_SIZE`, `DEFAULT_BATCH_SIZE`).
- Un módulo por responsabilidad: núcleo, análisis, archivos y API.

### Punto 5 · Documentación (Sphinx)

Sphinx con **autodoc** y el tema Read the Docs. La documentación se genera a partir de los docstrings, así que no se desactualiza respecto del código. El HTML está en `Ver-Optimizada/docs/_build/html/index.html`.

### Punto 6 · Análisis de calidad (Radon)

Elegimos Radon en lugar de SonarQube porque es liviano, no necesita servidor y mide lo que nos interesaba.

- **Complejidad ciclomática promedio:** A (3,65). Tres funciones del núcleo quedan en rango B (8–10, riesgo moderado): `_cosine_similarity`, `recommend_movies` y `calculate_similarity`.
- **Índice de mantenibilidad:** rango A en todos los módulos.

El detalle está en `Ver-Optimizada/quality_report.md`.

### Punto 7 · Refactorización

- **NumPy vectorizado:**
  - El dict de dicts pasa a un `ndarray` **float32** contiguo, que ocupa la mitad que float64; la precisión alcanza para calificaciones de 1 a 5.
  - Las similitudes se calculan con `np.dot` y `np.linalg.norm` en C/BLAS: **de ~15–20 s a 0,06 s**.
  - Usamos una matriz **densa** porque el dataset es chico. Con datos masivos convendría una matriz dispersa (SciPy).
- **Heap para el Top N:** O(n log K) en lugar de O(n log n).
- **Caché con invalidación:** se mantiene la estrategia del Parcial 1.

### Punto 8 · Testing (pytest)

**11 de 11 tests aprobados:**

- `test_recommender.py` (4): matriz de utilidad, coseno, simetría y diagonal de la matriz de similitud, Top N.
- `test_api.py` (4): endpoints de usuarios, recomendación, popularidad y carga de calificaciones, con `TestClient`.
- `test_large_file.py` (2): lectura por lotes y procesamiento en paralelo.
- `test_analysis.py` (1): caché de popularidad.

Se prueban **propiedades** (por ejemplo, que la matriz sea simétrica con diagonal 0), no solo valores puntuales.

### Punto 9 · Framework

- **FastAPI:** validación automática con Pydantic (`NewRating`), CORS para la web y documentación interactiva en `/docs`.
- **NumPy:** motor matemático.

## 6. Resultados

| Versión | Tiempo (Scalene) | Memoria pico | Qué cambió |
|---|---:|---:|---|
| Base | 171,5 s | 230,5 MB | Python puro, bucles anidados y búsquedas O(N) |
| Eficiente (Parcial 1) | 186,3 s\* | 230,6 MB | Sets, heap, dicts O(1), caché y API FastAPI |
| Optimizada (Parcial 2) | **20,3 s** | **36,4 MB** | Matriz NumPy float32 y similitud en C/BLAS |

\* Sin perfilador, la Eficiente mejora a la Base: de 231,4 s a 185,6 s. Ver [4.4](#44-resultado-del-parcial-1).

| Otras métricas | Valor |
|---|---|
| Archivos grandes (500.000 filas) | +173,5 MB → +23,8 MB de RAM (−86 %) |
| cProfile (Optimizada) | 683.884 llamadas en 0,84 s |
| Flake8 | 0 errores |
| Radon | CC promedio A (3,65) · MI A en todos los módulos |
| pytest | 11/11 |

Las mediciones de tiempo y memoria salen de `scalene-profile.json` en cada carpeta de versión.

## 7. Cómo ejecutar el proyecto

Requisitos: **Python 3.11 o superior**. Todos los comandos se ejecutan dentro de `Ver-Optimizada/` (las otras versiones se corren igual).

### 7.1 Instalación

```powershell
cd Ver-Optimizada
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

En Linux o macOS, activar el entorno con `source .venv/bin/activate`.

### 7.2 Levantar la API y la web

```powershell
uvicorn main:app --reload --port 8000
```

- La API queda en `http://localhost:8000` y la documentación interactiva en `http://localhost:8000/docs`.
- La interfaz web se abre con `index.html` en el navegador; consume la API en `http://localhost:8000/api`.

### 7.3 Benchmark y perfilado

```powershell
python benchmark.py                                      # Benchmark (2.000 usuarios, 500 películas)
scalene --html --outfile reporte_scalene.html benchmark.py   # Perfil de Scalene
python -m cProfile -o mi_programa.prof benchmark.py      # Perfil de cProfile
snakeviz mi_programa.prof                                # Visualización del perfil
```

Para ver el reporte de Scalene ya generado, usar `scalene view` dentro de la carpeta de la versión.

### 7.4 Archivos grandes (Punto 3)

```powershell
python large_file_handler.py
```

Genera `massive_ratings_sample.csv` (500.000 filas), lo procesa y compara la memoria del enfoque ingenuo con la del optimizado. Los CSV generados están en `.gitignore`.

### 7.5 Tests, calidad y documentación

```powershell
pytest -v                                           # Tests
flake8 --max-line-length=119 --exclude=.venv,docs .  # PEP 8
radon cc -s -a .                                    # Complejidad ciclomática
radon mi -s .                                       # Índice de mantenibilidad
cd docs; sphinx-build -b html . _build/html         # Regenerar la documentación
```

## 8. API REST

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/users` | Lista de usuarios (para el selector de la web) |
| GET | `/api/recommend/{user_id}` | Top 5 de películas recomendadas para el usuario |
| GET | `/api/popularity` | Top 5 de películas más calificadas (con caché) |
| POST | `/api/rate` | Agrega una calificación (`user_id`, `movie_id`, `rating`) e invalida el caché |
| GET | `/api/large-files/process?records=200000` | Demo del Punto 3: genera y procesa un CSV grande |

## 9. Limitaciones y próximos pasos

- **`recommend_movies`** es el nuevo cuello de botella según cProfile (170 ms): todavía recorre en Python cada película no vista. El próximo paso es vectorizarla.
- **Índice invertido película → usuarios**, para no comparar pares de usuarios sin películas en común.
- **Matriz dispersa** (SciPy) si se usan datasets reales como MovieLens, donde la matriz está llena en menos del 5 %.
- **Caché distribuido** fuera del proceso, para escalar a varias instancias de la API.
- Bajar a rango A las tres funciones del núcleo que quedaron en rango B de complejidad.
- Los datos de la demo se cargan en memoria (`data_models.py`). El motor es modular y puede consumir CSV o bases de datos.
