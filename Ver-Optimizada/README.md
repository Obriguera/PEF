# Versión Optimizada (Parcial 2)

Versión final del motor de recomendaciones: NumPy vectorizado, archivos grandes con buffer, lotes y paralelismo, documentación Sphinx, análisis de calidad con Flake8 y Radon, tests con pytest y API FastAPI.

La documentación completa (caso de uso, planteo del problema, evolución desde el Parcial 1, decisiones de diseño, resultados y cómo ejecutar) está en el [README principal](../README.md).

## Inicio rápido

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --require-hashes -r requirements-dev.txt
uvicorn main:app --reload --port 8000
```

Otros documentos de esta carpeta:

- [PARCIAL_2_REPORTE_FINAL.md](PARCIAL_2_REPORTE_FINAL.md): resumen del Parcial 2 para la defensa.
- [quality_report.md](quality_report.md): reporte de Flake8 y Radon.
- [LINEA_BASE_FASE1.md](LINEA_BASE_FASE1.md): métricas de calidad antes y después de la Fase 1 del Parcial 3.
- [`metrics/`](metrics/): las mismas métricas en JSON, una por versión, para los gráficos de evolución.
- [PLAN_PARCIAL_3.md](../PLAN_PARCIAL_3.md): requerimientos y plan del Parcial 3.
- [SECURITY.md](../SECURITY.md): política de seguridad, excepciones registradas y modelo de amenazas.
- [`.github/workflows/ci.yml`](../.github/workflows/ci.yml): el pipeline de CI; cada job llama a una tarea de `tasks.py` (ver la sección 7.7 del README principal).
- `docs/_build/html/index.html`: documentación generada con Sphinx (`python tasks.py docs-sphinx`).
- `pyproject.toml` y `tasks.py`: configuración y comandos de los controles de calidad (los mismos que corre el CI).
- [`metrics/`](metrics/): métricas por fase y líneas base de los benchmarks (`python tasks.py bench`, `bench-save`, `profile`).
