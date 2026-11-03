# Plan del Parcial 3

Reconstruido a partir de la sesión de planificación del 28/10/2026, que analizó el enunciado
(`Parcial-3.docx`). Este archivo resume los requerimientos; no reemplaza al enunciado.

## Qué pide el enunciado

**A. Documentación externa** compartida, con control de acceso y colaborativa. Tiene 9 secciones:
funcional, arquitectura (con diagrama de componentes), instalación, diseño técnico, API, pruebas,
rendimiento, seguridad y mantenimiento. Además debe explicar cómo correr en local los mismos
controles que corre el CI.

**B. Pipeline de CI** que se dispare en cada push y en cada PR a la rama principal. Cada control
debe tener herramienta, comando reproducible, reporte y criterio de aprobación o rechazo.

| Control | Herramienta | Criterio de rechazo |
|---|---|---|
| Tests | pytest | Falla 1 test o más |
| Cobertura | pytest-cov | Menos del 80 % |
| Análisis estático | Ruff | Cualquier error de las reglas activas |
| Tipado | mypy | Errores en los módulos del núcleo |
| Complejidad | Radon + Xenon | Alguna función peor que A (se decidió refactorizar en lugar de aceptar B) |
| Seguridad del código | Bandit (SARIF) + CodeQL | Severidad media o más con confianza media o más |
| Secretos | Gitleaks | Cualquier hallazgo |
| Dependencias | pip-audit + Dependabot | Una vulnerabilidad sin excepción documentada |
| Documentación | MkDocs `--strict`, markdownlint, Lychee | Falla el build o hay un link roto |
| Benchmark | pytest-benchmark contra una línea base | Regresión mayor al 25 % |
| Profiling | cProfile o pyinstrument | No bloquea: publica el reporte como artefacto |
| Memoria | tracemalloc en un test | Pico mayor a N MB (medido y justificado) |

Seguridad exige además una **política de bloqueo por severidad**, al menos un reporte en JSON o
SARIF y un registro documentado de falsos positivos y excepciones.

**C. Requerimiento propio: evolución de la eficiencia** entre entregas, con gráficos en el
README, en la documentación y en las diapositivas.

## Decisiones tomadas

- El CI y los controles cubren solo `Ver-Optimizada/`. Base y Eficiente son el grupo de control.
- La documentación se hace con MkDocs Material dentro del repo y se publica en GitHub Pages.
  Sphinx se mantiene en paralelo.
- Plataforma de CI: GitHub Actions. Toda la configuración vive en `pyproject.toml`, y `tasks.py`
  es la única fuente de los comandos (los usa el desarrollador en local y también el CI).
- Umbral de cobertura: 80 %. Complejidad: se refactoriza hasta rango A.
- La rama principal del fork `RicLagoria/PEF` es **`master`**: el CI debe apuntar a esa rama.
- Los perfiles de Scalene y el `.prof` siguen versionados como evidencia de los Parciales 1 y 2.

## Fases y estado

| Fase | Contenido | Estado |
|---|---|---|
| 0. Preparar el repo | Locks con hashes, `pyproject.toml`, `tasks.py`, `.gitignore` | ✅ PR #1, tag `parcial3-fase0` |
| 1. Código que pase los controles | Ruff, type hints, refactor a A, cobertura ≥ 80 % | ✅ PR #2, tag `parcial3-fase1` |
| 2. Rendimiento y memoria | Benchmarks con pytest-benchmark y línea base, tests de memoria con tracemalloc, tarea de profiling; `spawn` en el `ProcessPoolExecutor`, contrapresión y `records_processed` real | ✅ en PR (tag `parcial3-fase2` tras el merge) |
| 3. Seguridad | `SECURITY.md` (política por severidad, registro de excepciones, modelo de amenazas), excepciones de Bandit y pip-audit, validación de entradas de la API, workflow de CodeQL y Dependabot | ✅ en PR (tag `parcial3-fase3` tras el merge). CodeQL y Dependabot **sin ejecutar** en GitHub |
| 4. Pipeline | `.github/workflows/ci.yml`: calidad, secretos, pruebas en Python 3.11/3.12/3.13, dependencias, documentación, benchmarks contra el commit base, perfilado y un job `resultado` que agrega todo. La protección de `master` (exigir el check **Resultado**) la configura el dueño del repo | ✅ en PR (tag `parcial3-fase4` tras el merge). **Sin ejecutar en GitHub** |
| 5. Documentación | `mkdocs.yml` y `docs/` con las 9 secciones, diagrama en Mermaid, publicación en Pages, página de mantenimiento | ⏳ |
| 6. Evolución entre versiones | `evolucion/medir.py` (subcomandos `medir`, `graficar`, `todo`), métricas en JSON, gráficos PNG para el README, MkDocs y las diapositivas | ⏳ |

### Decisiones y hallazgos de la Fase 2

- **Umbral de benchmarks: `min:25%`, no `mean:25%` como decía el plan.** En 5 corridas completas el peor
  desvío entre corridas fue 25,4 % para la media (igual al umbral: falsos rojos), 48,8 % para la mediana
  y 15,1 % para el mínimo. Contrapartida: una regresión menor al 25 % no se detecta. Validado: una
  lentitud pura de +126,8 % hace fallar `bench` con exit 1; tres corridas sin cambios pasaron las tres.
- **Los benchmarks no están en `ci`** (dependen de la máquina). Son `bench`, `bench-save` y `profile`.
  Sin línea base para la plataforma, `bench` mide y avisa que no comparó.
- **La memoria del procesamiento paralelo crecía con el archivo** (18 → 67 MB entre 100.000 y 400.000
  filas), contra lo que documenta el Punto 3. El test falló antes del arreglo; con contrapresión
  (`2 × max_workers` lotes en vuelo) queda plano en ~9,3 MB. Límites absolutos de `tests/test_memory.py`
  con margen sobre lo medido: 2 MB (lectura), 5 MB (paralelo) y 3 MB (`calculate_similarity`, que atrapa
  una regresión de float32 a float64).
- **`spawn`** en lugar de `fork`: ~70–100 ms fijos de arranque. Cualquier script que llame a
  `process_large_file_parallel` necesita el guard `if __name__ == "__main__"`.
- **El lock tenía una combinación rota:** `pytest-benchmark 5.3.0` con `pytest 9.2` (falla con
  `AttributeError: _nodeid`). Se exige `pytest-benchmark>=5.3.1`, publicada el 2026-11-01 (un día antes de
  adoptarla). Alternativa más conservadora si se prefiere esperar: `pytest<9.2`.

### Decisiones y hallazgos de la Fase 3

- **Los controles se probaron con casos positivos, no solo con el repo limpio.** Gitleaks detecta un token con
  formato de GitHub aunque un commit posterior lo borre; Bandit rechaza `shell=True` y `pickle.loads`; pip-audit
  falla con `jinja2 2.10` (12 avisos) y pasa al ignorarlos. El repo real no tiene hallazgos.
- **Gitleaks escanea 21 de los 29 commits:** los otros 8 son merges sin cambios propios.
- **Los 3 hallazgos de Bandit (B311) son falsos positivos** (datos sintéticos): se marcan con `# nosec B311` y
  se registran en `SECURITY.md`. Las excepciones de pip-audit llevan vencimiento (`AUDIT_EXCEPTIONS`).
- **Lo que Bandit no ve, y se encontró revisando los endpoints:** `records` sin tope (un pedido anónimo podía
  agotar disco y CPU), usuario inexistente → HTTP 500, y puntajes arbitrarios en `POST /api/rate`. Se validan
  con 12 tests escritos antes del cambio. `index.html` mostraba "undefined" ante un 422 y se corrigió.
- **Las acciones de GitHub se fijan por SHA de commit.** Cuidado al resolverlos: en etiquetas anotadas,
  `git ls-remote` muestra primero el SHA del objeto-etiqueta; el del commit es el de la línea `^{}`.
- **Pendiente de validar en GitHub:** el workflow de CodeQL y `dependabot.yml` solo se validaron
  estructuralmente (no se pudo correr `actionlint`). Dependabot puede proponer cambios sin hashes en los locks;
  el CI los rechazaría de forma segura.
- **Pendiente del dueño del repo** (Settings): Dependabot alerts y security updates, secret scanning con push
  protection, private vulnerability reporting y protección de `master` (lista en `SECURITY.md`).

### Decisiones y hallazgos de la Fase 4

- **Cada job llama a `python tasks.py <tarea>`:** una sola fuente de verdad. Los pasos de calidad corren por
  separado con `!cancelled()`, para que un fallo de Ruff no oculte los de mypy o Bandit.
- **El job `resultado` es el único check a exigir** en la protección de rama. Falla si algún job no terminó en
  `success` (incluso omitido o cancelado); `perfilado` queda afuera porque es informativo.
- **La matriz 3.11/3.12/3.13 se verificó de verdad,** instalando el lock con `pip` y hashes en tres entornos
  limpios (no con `uv`, como en las fases anteriores): 57 tests y 100 % de cobertura en las tres, aunque NumPy
  difiera entre versiones (2.4.6 en 3.11 y 2.5.4 en 3.12 y 3.13), con el golden master comparando floats por
  igualdad exacta.
- **Benchmarks: se mide el commit base en el mismo runner** (`bench-vs-base`), porque la línea base versionada
  en `metrics/benchmarks/` es de otra máquina. El código del commit base se mide con el comando del `tasks.py`
  actual, para que el resultado no dependa de qué `tasks.py` tenga ese commit. Probado con git real: sin cambios
  pasa; con una lentitud de +108 % falla. Cuando no hay commit base utilizable, mide y avisa que no comparó.
- **Gitleaks:** el binario se instala con un SHA-256 fijado en el workflow (no el de la release, que cambiaría
  junto con ella). Probado con el checksum correcto (instala) y con uno incorrecto (aborta sin instalar nada).
- **Validación del workflow:** contra el esquema oficial de GitHub (SchemaStore) y con los trozos con lógica
  ejecutados en local. El esquema es útil pero no exhaustivo: de 2 errores plantados detectó 1. `actionlint` no
  se pudo usar (descarga de binario denegada).
- **Pendientes y riesgos:**
  - Nada de esto corrió todavía en GitHub; la primera ejecución puede pedir ajustes.
  - No se midió el ruido de los runners de GitHub. Si el job de benchmarks da falsos rojos, hay que sacarlo de
    los checks exigidos o subir el umbral.
  - Solo Linux. No hay job de Windows ni de macOS.
  - Hay que sincronizar `Obriguera/PEF`: tiene hasta la Fase 2 y le faltan las Fases 3 y 4.

### Evolución entre versiones (Fase 6)

- **Entre versiones** (Base → Eficiente → Optimizada → Optimizada v3): el mismo benchmark corre
  sobre cada versión, cada una en un subproceso aparte porque los módulos tienen el mismo nombre.
  Usa tamaños crecientes (250, 500, 1.000 y 2.000 usuarios) para mostrar la curva O(U²) de la
  Base contra la de NumPy. Mide tiempo (mediana de varias repeticiones) y memoria pico, junto
  con la cobertura, la complejidad y la cantidad de tests de cada entrega.
- **A lo largo de los commits**: el job de benchmark del CI guarda el resultado de cada push a
  `master` y publica un gráfico histórico.
- La Base tarda unos 3 minutos con 2.000 usuarios, así que esa medición va en un workflow
  manual o semanal, no en cada push.
- `metrics/parcial3-fase0.json` y los tags de cada fase ya sirven como puntos de comparación.

## Cómo retomar en una sesión nueva

Todo el estado del trabajo está en el repo. Para seguir:

1. Abrir una sesión con `RicLagoria/PEF` como repositorio y pedir: *"Leé `PLAN_PARCIAL_3.md`
   y seguí con la próxima fase pendiente"*.
2. Preparar el entorno en `Ver-Optimizada/`:
   `uv venv .venv && uv pip install --python .venv/bin/python --require-hashes -r requirements-dev.txt`
   (en Windows: `python -m venv .venv` y `pip install --require-hashes -r requirements-dev.txt`).
3. Verificar el punto de partida con `python tasks.py ci`, que debe terminar en verde.

### Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Requerimientos, decisiones y estado | este archivo |
| Métricas de cada versión | `Ver-Optimizada/metrics/parcial3-fase*.json` |
| Antes/después de la Fase 1, con notas | `Ver-Optimizada/LINEA_BASE_FASE1.md` |
| Comandos de todos los controles | `Ver-Optimizada/tasks.py` (`python tasks.py` los lista) |
| Configuración de las herramientas | `Ver-Optimizada/pyproject.toml` |
| Golden master del recomendador | `Ver-Optimizada/tests/golden.py` y `tests/fixtures/` |
| Historial y discusión de cada fase | PRs del fork y mensajes de commit |
| Enunciado original | `Parcial-3.docx` (fuera del repo) |

### Flujo de trabajo

- Cada fase va en una rama `claude/...` creada desde `master`, con un commit por paso y un PR.
  Después del merge, el estado se etiqueta como `parcial3-faseN`.
- Las sesiones de Claude no pueden subir tags (el proxy devuelve 403). El tag se crea y se
  sube desde una máquina local.
- El `master` del fork se sincroniza con `Obriguera/PEF` mediante PRs.

### Trampas conocidas

- **El golden master compara por igualdad exacta.** Cualquier cambio que altere el orden de las
  sumas de floats lo rompe, aunque el cambio sea correcto. Ejemplos: usar `sum()`, que desde
  Python 3.12 hace suma compensada; reordenar las columnas de la matriz; vectorizar
  `recommend_movies`. Si un cambio así es intencional (por ejemplo, una "Optimizada v3"),
  se regenera la referencia con `python tests/golden.py` y se justifica en el commit.
- **`POST /api/rate` modifica `RATINGS_DATA` de forma global.** `tests/test_api.py` lo restaura
  con un fixture; cualquier test nuevo de la API tiene que mantener ese aislamiento.
- **coverage no mide los subprocesos del `ProcessPoolExecutor`.** El worker se testea llamándolo
  en forma directa.
- **`bench` compara contra una línea base por plataforma y versión de Python** (`metrics/benchmarks/`). Los
  tiempos absolutos de otra máquina no son comparables; regenerarla con `bench-save` al cambiar de equipo.
- **Los tests de rendimiento deben medir contra el tag de la versión anterior**, con el mínimo de
  varias repeticiones. La Fase 1 midió `recommend_movies` en 447 ms → 198 ms con 400 usuarios ×
  300 películas y 20.000 ratings.

