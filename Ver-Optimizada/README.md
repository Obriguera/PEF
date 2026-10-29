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
- `docs/_build/html/index.html`: documentación generada con Sphinx (`python tasks.py docs-sphinx`).
- `pyproject.toml` y `tasks.py`: configuración y comandos de los controles de calidad (los mismos que corre el CI).
