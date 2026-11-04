#!/usr/bin/env bash
# Prepara las dos ramas de la demo del pipeline (ver DEMO.md).
#
#   ./preparar_demo.sh          crea y sube demo/sin-error y demo/con-error, y muestra los links para abrir los PR
#   ./preparar_demo.sh limpiar  borra las dos ramas (remotas y locales) cuando termina la demo
#
# Las dos salen de origin/master:
#   demo/sin-error  -> una nota visible en docs/evolucion.md (es lo que se ve después en GitHub Pages)
#   demo/con-error  -> la misma nota + una función con 7 parámetros (el límite es 5): Calidad estática la rechaza
# Subir una rama no dispara el CI: solo corre con un push a master o un PR hacia master.
set -euo pipefail

OK="demo/sin-error"
MAL="demo/con-error"
REPO_URL="https://github.com/RicLagoria/PEF"

cd "$(git rev-parse --show-toplevel)"

if [ "${1:-}" = "limpiar" ]; then
    git push origin --delete "$OK" "$MAL" 2>&1 || true
    git branch -D "$OK" "$MAL" 2>&1 || true
    echo "Listo: ramas de la demo borradas."
    exit 0
fi

git diff --quiet && git diff --cached --quiet || { echo "Hay cambios sin commitear: guardalos antes de seguir." >&2; exit 1; }
for rama in "$OK" "$MAL"; do
    if git show-ref --quiet "refs/heads/$rama" || [ -n "$(git ls-remote --heads origin "$rama")" ]; then
        echo "La rama $rama ya existe. Corré primero: ./presentacion/preparar_demo.sh limpiar" >&2
        exit 1
    fi
done

ORIGEN="$(git rev-parse --abbrev-ref HEAD)"
git fetch origin master
git checkout -q -b "$OK" origin/master

printf '\n!!! info "Demo en vivo"\n    Esta nota llegó a Pages desde un pull request que pasó todos los controles del pipeline (%s).\n' "$(date '+%Y-%m-%d %H:%M')" >> docs/evolucion.md
git add docs/evolucion.md
git commit -q -m "Demo: nota visible en la página de evolución"

git checkout -q -b "$MAL"
cat >> Ver-Optimizada/recommender_core.py <<'PY'


def _demo_demasiados_parametros(a: int, b: int, c: int, d: int, e: int, f: int, g: int) -> int:
    """Función de la demo: tiene 7 parámetros y el límite es 5, así que Calidad estática la rechaza."""
    return a + b + c + d + e + f + g
PY
git add Ver-Optimizada/recommender_core.py
git commit -q -m "Demo: función con 7 parámetros (el control de calidad debe rechazarla)"

git push -u origin "$OK" "$MAL"
git checkout -q "$ORIGEN"

echo
echo "Listo. Abrí los dos pull requests (unos 10 minutos antes de presentar):"
echo "  con error: $REPO_URL/compare/master...$MAL?expand=1"
echo "  sin error: $REPO_URL/compare/master...$OK?expand=1"
