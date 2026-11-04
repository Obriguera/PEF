#!/usr/bin/env bash
# Prepara la rama de la demo del pipeline (ver DEMO.md). Uso: ./preparar_demo.sh <nombre-de-rama>
#
# La rama sale de origin/master y lleva DOS commits:
#   1. una nota visible en docs/evolucion.md (es lo que se va a ver publicado en GitHub Pages);
#   2. una función con 7 parámetros, que Calidad estática rechaza (límite: 5). Se deshace con `git revert HEAD`.
# La rama se sube, pero sin pull request el CI no corre: el CI solo se dispara con un push a master o un PR hacia master.
set -euo pipefail

RAMA="${1:?Falta el nombre de la rama. Ejemplo: ./preparar_demo.sh demo/romper-calidad}"
cd "$(git rev-parse --show-toplevel)"

git diff --quiet && git diff --cached --quiet || { echo "Hay cambios sin commitear: guardalos antes de seguir." >&2; exit 1; }
ORIGEN="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin master
git checkout -b "$RAMA" origin/master

printf '\n!!! info "Demo en vivo"\n    Esta nota llegó a Pages desde el pull request de la rama `%s` (%s).\n' "$RAMA" "$(date '+%Y-%m-%d %H:%M')" >> docs/evolucion.md
git add docs/evolucion.md
git commit -q -m "Demo: nota visible en la página de evolución"

cat >> Ver-Optimizada/recommender_core.py <<'PY'


def _demo_demasiados_parametros(a: int, b: int, c: int, d: int, e: int, f: int, g: int) -> int:
    """Función de la demo: tiene 7 parámetros y el límite es 5, así que Calidad estática la rechaza."""
    return a + b + c + d + e + f + g
PY
git add Ver-Optimizada/recommender_core.py
git commit -q -m "Demo: función con 7 parámetros (el control de calidad debe rechazarla)"

git push -u origin "$RAMA"
git checkout -q "$ORIGEN"
echo
echo "Listo. Rama '$RAMA' subida. Abrí el pull request desde GitHub cuando empiece la demo."
