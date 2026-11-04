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
│   ├── tasks.py                # Runner de controles: lint, tipos, tests, seguridad y benchmarks
│   ├── pyproject.toml          # Configuración de pytest, coverage, Ruff, mypy y Bandit
│   ├── metrics/                # Métricas por fase (JSON) y líneas base de los benchmarks
│   ├── index.html              # Interfaz web que consume la API
│   ├── tests/                  # Suite de pytest (35 tests: unitarios, golden master, memoria y benchmarks)
│   ├── docs/                   # Documentación Sphinx (fuentes y HTML generado)
│   ├── scalene-profile.*       # Perfil de Scalene
│   ├── mi_programa.prof        # Perfil de cProfile (se visualiza con SnakeViz)
│   ├── quality_report.md       # Reporte de Flake8 y Radon
│   └── PARCIAL_2_REPORTE_FINAL.md
├── .github/           # Workflows de CI y CodeQL, y Dependabot
├── PLAN_PARCIAL_3.md  # Requerimientos, decisiones y estado del Parcial 3
├── SECURITY.md        # Política de seguridad, controles, excepciones y modelo de amenazas
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

**Parcial 3:**

- **Contrapresión.** Medir con `tracemalloc` mostró que la lectura en lotes mantenía la memoria constante, pero el procesamiento paralelo enviaba *todos* los lotes al pool antes de consumir resultados, y el pico del proceso principal crecía con el archivo (de 18 a 67 MB entre 100.000 y 400.000 filas, con lotes de 5.000). Ahora hay como máximo `2 × max_workers` lotes en vuelo y el pico queda plano en ~9,3 MB (`tests/test_memory.py`).
- **`spawn` en lugar de `fork`.** Crear procesos con `fork()` desde un proceso con hilos (el pool de FastAPI) puede dejarlos trabados, y Python 3.14 ya no lo usa por defecto en Linux. Cuesta ~70–100 ms fijos de arranque.
- Re-medición de la demo con estos cambios: +26–28 MB contra +174 MB del método ingenuo (−84 %). La cifra de arriba es la original del Parcial 2.

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

> **Actualización del Parcial 3.** Estas cifras son las del Parcial 2. Después del refactor de la Fase 1, **todas las funciones están en rango A** (complejidad máxima 5, promedio 2,70), `_cosine_similarity` se eliminó por no tener uso en producción, y el análisis se hace con Ruff (en lugar de Flake8) y Xenon. Ver [`Ver-Optimizada/LINEA_BASE_FASE1.md`](Ver-Optimizada/LINEA_BASE_FASE1.md).

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

**Parcial 3: 35 tests.** Se suman:

- `test_characterization.py` (8): comparan por igualdad exacta la salida del recomendador contra un *golden master* generado con el código del Parcial 2, para poder refactorizar sin cambiar resultados.
- `test_memory.py` (3): pico de memoria con `tracemalloc`; la lectura y el procesamiento paralelo no crecen con el tamaño del archivo, y la matriz de similitud se mantiene en float32.
- `test_benchmarks.py` (7): benchmarks con línea base (se miden con `python tasks.py bench`).
- Más casos en `test_api.py` (archivos grandes, registros reales procesados) y `test_large_file.py` (worker, consistencia paralelo/secuencial, demo del Punto 3).

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

**Calidad en el Parcial 3** (detalle en [`Ver-Optimizada/LINEA_BASE_FASE1.md`](Ver-Optimizada/LINEA_BASE_FASE1.md)):

| Control | Punto de partida (Parcial 2) | Parcial 3 |
|---|---|---|
| Complejidad (Xenon) | 4 funciones en rango B | todas en A (máximo 5, promedio 2,70) |
| Cobertura | 70,67 % | 100 % (umbral: 80 %) |
| mypy | 6 errores | 0 |
| Ruff | 33 hallazgos | 0 |
| `recommend_movies` (40 usuarios, 400 × 300) | 447 ms | 198 ms (2,2×) |
| Pico de memoria del procesamiento paralelo (400.000 filas, lotes de 5.000) | 67 MB, crece con el archivo | ~9,3 MB, plano |

## 7. Cómo ejecutar el proyecto

Requisitos: **Python 3.11 o superior**. Todos los comandos se ejecutan dentro de `Ver-Optimizada/` (las otras versiones se corren igual).

### 7.1 Instalación

```powershell
cd Ver-Optimizada
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --require-hashes -r requirements-dev.txt
```

En Linux o macOS, activar el entorno con `source .venv/bin/activate`.

Las dependencias están **fijadas con versión exacta y hash** para que la instalación sea reproducible:

| Archivo | Contenido |
|---|---|
| `requirements.in` | Dependencias directas de la API (se edita a mano) |
| `requirements-dev.in` | Herramientas de tests, calidad, seguridad, rendimiento y documentación |
| `requirements.txt` / `requirements-dev.txt` | *Locks* generados con `python tasks.py lock` (no se editan a mano) |

Para producción alcanza con `pip install --require-hashes -r requirements.txt`.

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

Benchmarks con línea base y perfilado automatizados (Parcial 3):

```powershell
python tasks.py bench        # Mide y falla si algo empeora más de 25 % (mínimo) respecto de la línea base
python tasks.py bench-save   # Guarda una nueva línea base (tras una mejora o al cambiar de máquina)
python tasks.py profile      # cProfile y pyinstrument sobre benchmark.py; reportes en reports/
```

Las líneas base están en `Ver-Optimizada/metrics/benchmarks/<plataforma>/` y son **específicas de cada plataforma y versión de Python**. Si no hay una para tu combinación, `bench` mide igual pero avisa que no pudo comparar. Los tiempos dependen del hardware: conviene guardar la línea base en la misma máquina donde se va a comparar. El archivo incluye el nombre del equipo (`machine_info.node`).

Se compara el **mínimo** y no la media: el ruido de una máquina compartida solo suma tiempo. Una regresión menor al 25 % no se detecta.

`bench` compara **una** medición contra la línea base guardada, así que es orientativo: sobre código idéntico, dos mediciones consecutivas dieron razones de 0,77 a 1,28. Para decidir, usá `bench-vs-base` (abajo), que intercala varias mediciones de cada lado. Para que el ruido no domine, cada vuelta de un benchmark dura al menos ~10 ms: con ~1 ms por vuelta daba falsos rojos.

### 7.4 Archivos grandes (Punto 3)

```powershell
python large_file_handler.py
```

Genera `massive_ratings_sample.csv` (500.000 filas), lo procesa y compara la memoria del enfoque ingenuo con la del optimizado. Los CSV generados están en `.gitignore`.

### 7.5 Tests, calidad y documentación

Todos los controles se ejecutan con `tasks.py`, el mismo runner que usa el CI. La configuración de las herramientas está en `pyproject.toml`.

```powershell
python tasks.py --list     # Tareas disponibles
python tasks.py lint       # Ruff: estilo y errores potenciales
python tasks.py typecheck  # mypy
python tasks.py complexity # Radon + Xenon (umbral: rango A)
python tasks.py sast       # Bandit (reporte SARIF en reports/)
python tasks.py secrets    # Gitleaks sobre el historial de git (necesita el binario; ver SECURITY.md)
python tasks.py test       # pytest + cobertura (umbral: 80 %)
python tasks.py audit      # pip-audit sobre los locks
python tasks.py docs-sphinx  # Genera docs/_build/html
python tasks.py ci         # Todo lo anterior, en el orden del CI
```

Los reportes quedan en `Ver-Optimizada/reports/` y la documentación generada no se versiona.

`test` incluye las pruebas de memoria. Los benchmarks (`bench`) no forman parte de `ci` porque dependen de la máquina; ver 7.3.

### 7.6 Seguridad

La política de bloqueo por severidad, el registro de falsos positivos y excepciones, el modelo de amenazas y los riesgos aceptados están en [`SECURITY.md`](SECURITY.md). En resumen:

| Control | Herramienta | Rechaza si… |
|---|---|---|
| Código inseguro | Bandit (SARIF) y CodeQL | hay un hallazgo de severidad media o alta con confianza media o alta |
| Secretos | Gitleaks | hay cualquier hallazgo en el historial |
| Dependencias | pip-audit y Dependabot | hay una vulnerabilidad conocida sin excepción vigente |

Las excepciones llevan motivo y fecha; las de pip-audit, además, vencimiento.

### 7.7 Integración continua

El workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) corre en cada push y en cada pull request a `master`.
Cada job llama a la misma tarea de `tasks.py` que se usa en local, así que un fallo del CI se reproduce con un comando:

| Job | Qué controla | Reproducir en local | Rechaza si… | Reporte (artefacto) |
|---|---|---|---|---|
| Calidad estática | Ruff, mypy, Xenon y Bandit | `python tasks.py lint typecheck complexity sast` | error de Ruff o mypy, función peor que A, o hallazgo de Bandit de severidad y confianza medias o altas | `reportes-calidad` |
| Secretos | Gitleaks sobre todo el historial | `python tasks.py secrets` | cualquier hallazgo | `reportes-secretos` |
| Pruebas (3.11, 3.12 y 3.13) | pytest, cobertura y memoria | `python tasks.py test` | falla un test o la cobertura es menor a 80 % | `reportes-pruebas-*` |
| Dependencias | pip-audit sobre los locks | `python tasks.py audit` | vulnerabilidad sin excepción vigente | `reportes-auditoria` |
| Documentación | Sphinx con `-W` | `python tasks.py docs-sphinx` | advertencia o error | `documentacion-sphinx` |
| Benchmarks | pytest-benchmark contra el commit base | `BENCH_BASE_SHA=<sha> python tasks.py bench-vs-base` | el mínimo de algún benchmark empeora más de 25 % | `reportes-rendimiento` |
| Perfilado | cProfile y pyinstrument | `python tasks.py profile` | no bloquea | `perfiles` |
| **Resultado** | agrega a todos los anteriores | — | cualquier job bloqueante no terminó en éxito | resumen de la ejecución |

Cada job escribe un resumen (pruebas, cobertura, complejidad, hallazgos y tiempos) en la página de la ejecución.

**Benchmarks.** Una línea base medida en otra máquina no es comparable. Por eso el CI mide el commit base y el actual
en el mismo runner (`bench-vs-base`): 3 rondas intercaladas (base, actual, base, actual…) y se comparan los **mejores
tiempos** de cada lado. Los dos lados se miden con la **misma definición de benchmark** (la del commit actual, aplicada
al código de cada commit): si cada uno usara la suya, un PR que cambie un benchmark compararía cosas distintas. Si esa
definición no corre sobre el commit base (por ejemplo, prueba una función que todavía no existía), mide y avisa que no
pudo comparar. Si un cambio es lento a propósito, hay que mergearlo sabiéndolo: no existe una línea base que actualizar.

**Protección de la rama.** Para que el CI impida el merge, el dueño del repositorio debe exigir el check **Resultado**
en *Settings → Branches* (ver [`SECURITY.md`](SECURITY.md)). Sin esa regla, el CI avisa pero no bloquea.

**Qué no cubre.** Solo corre en Linux. Python 3.11, 3.12 y 3.13 se probaron en local con `pip` y hashes; Windows y
macOS no.

## 8. API REST

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/users` | Lista de usuarios (para el selector de la web) |
| GET | `/api/recommend/{user_id}` | Top 5 de películas recomendadas para el usuario (404 si el usuario no existe) |
| GET | `/api/popularity` | Top 5 de películas más calificadas (con caché) |
| POST | `/api/rate` | Agrega una calificación (`user_id` y `movie_id` positivos, `rating` entre 1 y 5; 422 si no) e invalida el caché |
| GET | `/api/large-files/process?records=200000` | Demo del Punto 3: genera y procesa un CSV grande (`records` entre 1 y 1.000.000; 422 si no) |

## 9. Limitaciones y próximos pasos

- **`recommend_movies`** es el nuevo cuello de botella según cProfile (170 ms): todavía recorre en Python cada película no vista. El próximo paso es vectorizarla. (Parcial 3: un índice invertido película → quién la calificó la dejó 2,2× más rápida, pero sigue recorriendo en Python cada película no vista.)
- **Índice invertido película → usuarios**, para no comparar pares de usuarios sin películas en común.
- **Matriz dispersa** (SciPy) si se usan datasets reales como MovieLens, donde la matriz está llena en menos del 5 %.
- **Caché distribuido** fuera del proceso, para escalar a varias instancias de la API.
- Los datos de la demo se cargan en memoria (`data_models.py`). El motor es modular y puede consumir CSV o bases de datos.
