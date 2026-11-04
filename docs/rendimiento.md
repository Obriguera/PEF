# Rendimiento

## Evolución entre versiones

Mismo benchmark para las tres versiones (2.000 usuarios, 500 películas, 30 calificaciones por usuario), medido con
Scalene:

| Versión | Tiempo | Memoria pico | Qué cambió |
|---|---:|---:|---|
| Base | 171,5 s | 230,5 MB | Python puro, bucles anidados y búsquedas O(N) |
| Eficiente (Parcial 1) | 186,3 s\* | 230,6 MB | Sets, heap, diccionarios O(1), caché y API FastAPI |
| Optimizada (Parcial 2) | **20,3 s** | **36,4 MB** | Matriz NumPy `float32` y similitud en C/BLAS |

\* Sin perfilador, la Eficiente **mejora** a la Base: de 231,4 s a 185,6 s. Scalene instrumenta cada línea y su
sobrecarga no es uniforme: castiga más a las estructuras nativas que a un bucle explícito. El perfilador sirve para
**encontrar** el cuello de botella, no para comparar versiones.

Otras métricas de la versión optimizada: el cálculo de similitudes pasó de ~15–20 s a **0,06 s**, y con
`cProfile` el programa hace 683.884 llamadas en 0,84 s.

## Qué se mejoró en el Parcial 3

El refactor de complejidad ciclomática, con una prueba de caracterización exacta de por medio, fue también una
optimización:

| Medida | Antes | Después |
|---|---:|---:|
| `recommend_movies`, 40 usuarios, 400 × 300 | 447 ms | **198 ms** (2,2×) |
| Pico de memoria del procesamiento paralelo, 400.000 filas, lotes de 5.000 | 67 MB, crece con el archivo | **~9,3 MB**, plano |

La primera versión del refactor, que metía un generador dentro del bucle caliente, quedaba un 13 % **más lenta** que
la original. Se detectó midiendo antes de confirmar el cambio, y se corrigió con el índice invertido descrito en
[Diseño técnico](diseno-tecnico.md#3-índice-invertido-para-predecir).

### Procesamiento de archivos grandes

La demostración del Punto 3 (500.000 filas) compara leer todo con `readlines()` contra buffer, lotes y procesos:

| | Aumento de RAM |
|---|---:|
| Enfoque ingenuo | +174 MB |
| Enfoque optimizado | +26 a +28 MB (**−84 %**) |

El argumento de este punto es la **memoria**. El tiempo de la demostración es muy variable (en seis corridas, el
cociente entre el enfoque ingenuo y el optimizado osciló entre 0,7× y 2,0×) porque el ingenuo depende del estado del
caché de disco; no conviene citarlo como una mejora.

## Cómo se mide

| Herramienta | Qué mide | Comando |
|---|---|---|
| `benchmark.py` | Tiempo de cada etapa con 2.000 usuarios | `python benchmark.py` |
| pytest-benchmark | 7 benchmarks con datos determinísticos | `python tasks.py bench` |
| cProfile y pyinstrument | Dónde se va el tiempo | `python tasks.py profile` (deja `reports/profile.prof` y `reports/profile.html`) |
| Scalene | Tiempo y memoria por línea | `scalene --html --outfile reporte_scalene.html benchmark.py` |
| tracemalloc | Pico de memoria | `python tasks.py test` (ver [Pruebas](pruebas.md)) |

## Cómo se evita empeorar el rendimiento

El CI compara cada cambio contra el commit base con `python tasks.py bench-vs-base`:

- **Los dos lados se miden en la misma máquina.** Una línea base medida en otra máquina no es comparable: en un
  runner de GitHub los tiempos absolutos resultaron entre ~1,1× y ~2,1× más lentos que en el entorno de desarrollo,
  según la prueba.
- **Rondas intercaladas** (base, actual, base, actual, base, actual) y se comparan los **mejores tiempos** de cada
  lado. El mínimo es la estadística estable, porque el ruido de una máquina compartida solo suma tiempo.
- **La misma definición de benchmark en ambos lados**: la del commit actual, aplicada al código de cada commit. Si
  cada lado usara la suya, un cambio en un benchmark compararía cosas distintas.
- **Umbral de 25 %.** Una regresión menor no se detecta.

### Por qué es así: el ruido, medido

Estas decisiones salieron de medir el ruido sobre **código idéntico**, no de suponerlo:

| Diseño | Razones segunda/primera medición | Corridas en rojo falso |
|---|---|---|
| Una medición contra otra, vueltas de ~1 ms | 0,77 a 1,28 | 2 de 10 |
| Una medición contra otra, vueltas de 12 ms o más | 0,69 a 1,24 | 0 de 10 |
| Mejor de 3 rondas intercaladas | 0,91 a 1,08 | 0 de 6 |

Los benchmarks rápidos repiten el trabajo dentro de cada vuelta para durar al menos ~10 ms: con ~1 ms por vuelta, el
jitter del reloj y del planificador era de ±20 %. Y el control **sí detecta**: una lentitud deliberada de +40 %
marcó solo el benchmark afectado.

### Una ejecución real en GitHub

Resultado del job de benchmarks en un runner de GitHub (mejor de 3 rondas, en ms):

| Prueba | Base | Actual | Razón |
|---|---:|---:|---:|
| `test_agregacion_de_un_lote` | 23,810 | 23,827 | 1,00 |
| `test_analyze_popularity_sin_cache` | 32,838 | 32,643 | 0,99 |
| `test_calculate_similarity` | 30,482 | 30,856 | 1,01 |
| `test_lectura_en_lotes` | 47,828 | 47,450 | 0,99 |
| `test_prepare_data` | 13,571 | 14,582 | 1,07 |
| `test_procesamiento_paralelo` | 155,938 | 155,440 | 1,00 |
| `test_recommend_movies` | 72,360 | 71,956 | 0,99 |

Es una sola ejecución: indica que el ruido en el runner es bajo, pero no lo garantiza.
