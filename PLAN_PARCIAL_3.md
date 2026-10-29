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
| 1. Código que pase los controles | Ruff, type hints, refactor a A, cobertura ≥ 80 % | 🔄 PR #2 |
| 2. Rendimiento y memoria | `benchmark.py` → pytest-benchmark con línea base, test de memoria con tracemalloc, job de profiling | ⏳ |
| 3. Seguridad | Bandit, Gitleaks y pip-audit en el CI, Dependabot, CodeQL, `SECURITY.md` con la política y las excepciones | ⏳ (Bandit, Gitleaks y pip-audit ya están en `tasks.py`) |
| 4. Pipeline | `.github/workflows/ci.yml` + protección de `master` (la configura el dueño del repo) | ⏳ |
| 5. Documentación | `mkdocs.yml` y `docs/` con las 9 secciones, diagrama en Mermaid, publicación en Pages, página de mantenimiento | ⏳ |
| 6. Evolución entre versiones | `evolucion/medir.py` (subcomandos `medir`, `graficar`, `todo`), métricas en JSON, gráficos PNG para el README, MkDocs y las diapositivas | ⏳ |

### Pipeline previsto (Fase 4)

```
setup (pip con hashes + caché)
  ├─► calidad-estática: ruff · mypy · xenon · bandit · gitleaks   (en paralelo)
  ├─► tests: pytest + cobertura ≥ umbral
  ├─► deps-y-docs: pip-audit · mkdocs --strict · markdownlint · lychee
  └─► rendimiento (needs: tests): benchmark vs. línea base · memoria · profiling
         └─► resultado: resumen en GITHUB_STEP_SUMMARY + artefactos
```

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
