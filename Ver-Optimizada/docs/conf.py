import os
import sys

# Agregar la raíz del proyecto al sys.path para que autodoc encuentre los módulos
sys.path.insert(0, os.path.abspath(".."))

project = "Movie Recommender - Versión Optimizada"
copyright = "2026, Programación Eficiente - UBP"
author = "Equipo PEF"
release = "2.0.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
