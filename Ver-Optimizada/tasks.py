"""Runner de controles de calidad de la Versión Optimizada.

Es la única fuente de verdad de los comandos: el pipeline de CI llama a estas
mismas tareas, así que lo que pasa en local pasa en el CI (y lo que falla, también).
Solo usa la biblioteca estándar para funcionar igual en Windows, Linux y macOS.

Uso:
    python tasks.py <tarea> [<tarea> ...]
    python tasks.py --list

Ejemplos:
    python tasks.py install          # Entorno de desarrollo con dependencias fijadas
    python tasks.py lint test        # Varias tareas en orden
    python tasks.py ci               # Todos los controles bloqueantes
"""

import argparse
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"
PY = sys.executable

# Fuentes analizadas (los tests quedan fuera del análisis de seguridad y complejidad)
SOURCES = ["recommender_core.py", "analysis_utils.py", "large_file_handler.py", "main.py", "data_models.py"]

TASKS: dict[str, tuple[Callable[[], None], str]] = {}


def task(description: str) -> Callable[[Callable[[], None]], Callable[[], None]]:
    """Registra una función como tarea ejecutable desde la línea de comandos."""

    def register(func: Callable[[], None]) -> Callable[[], None]:
        TASKS[func.__name__.replace("_", "-")] = (func, description)
        return func

    return register


def run(*cmd: str) -> None:
    """Ejecuta un comando y corta la ejecución con su código de salida si falla."""
    print(f"\n$ {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        sys.exit(result.returncode)


def tool(name: str) -> str:
    """Devuelve el ejecutable de una herramienta externa (no pip) o falla con un mensaje claro."""
    path = shutil.which(name)
    if path is None:
        sys.exit(f"'{name}' no está instalado. Ver la sección de mantenimiento de la documentación.")
    return path


# ------------------------------------------------------------ preparación


@task("Instala las dependencias de desarrollo fijadas (con verificación de hashes)")
def install() -> None:
    run(PY, "-m", "pip", "install", "--require-hashes", "-r", "requirements-dev.txt")


@task("Regenera requirements.txt y requirements-dev.txt a partir de los .in (requiere uv)")
def lock() -> None:
    uv = tool("uv")
    common = ["pip", "compile", "--universal", "--python-version", "3.11", "--generate-hashes", "--quiet"]
    run(uv, *common, "requirements.in", "-o", "requirements.txt")
    run(uv, *common, "requirements-dev.in", "-o", "requirements-dev.txt")


# ------------------------------------------------------- calidad estática


@task("Ruff: errores potenciales, estilo y complejidad de McCabe")
def lint() -> None:
    run(PY, "-m", "ruff", "check", ".")
    run(PY, "-m", "ruff", "format", "--check", ".")


@task("Ruff: aplica correcciones automáticas y formatea el código")
def format_code() -> None:
    run(PY, "-m", "ruff", "check", "--fix", ".")
    run(PY, "-m", "ruff", "format", ".")


@task("mypy: tipado estático")
def typecheck() -> None:
    run(PY, "-m", "mypy")


@task("Radon + Xenon: complejidad ciclomática e índice de mantenibilidad")
def complexity() -> None:
    REPORTS.mkdir(exist_ok=True)
    run(PY, "-m", "radon", "cc", "-s", "-a", *SOURCES)
    run(PY, "-m", "radon", "mi", "-s", *SOURCES)
    run(PY, "-m", "radon", "cc", "-j", "-O", str(REPORTS / "radon-cc.json"), *SOURCES)
    # Rechazo: alguna función peor que A, algún módulo peor que A o un promedio peor que A
    run(PY, "-m", "xenon", "--max-absolute", "A", "--max-modules", "A", "--max-average", "A", *SOURCES)


@task("Bandit: patrones de código inseguro (reporte legible + SARIF)")
def sast() -> None:
    REPORTS.mkdir(exist_ok=True)
    run(PY, "-m", "bandit", "-c", "pyproject.toml", "-r", *SOURCES,
        "-f", "sarif", "-o", str(REPORTS / "bandit.sarif"), "--exit-zero")
    # Rechazo: severidad media o más con confianza media o más
    run(PY, "-m", "bandit", "-c", "pyproject.toml", "-r", *SOURCES, "--severity-level", "medium",
        "--confidence-level", "medium")


@task("Gitleaks: detección de secretos en el historial de git")
def secrets() -> None:
    REPORTS.mkdir(exist_ok=True)
    run(tool("gitleaks"), "git", "..", "--report-format", "sarif",
        "--report-path", str(REPORTS / "gitleaks.sarif"), "--redact")


@task("Etapa de calidad estática completa")
def static() -> None:
    lint()
    typecheck()
    complexity()
    sast()


# ---------------------------------------------------------------- pruebas


@task("pytest + cobertura con umbral mínimo (ver pyproject.toml)")
def test() -> None:
    REPORTS.mkdir(exist_ok=True)
    run(PY, "-m", "pytest", "--cov", "--cov-report=term-missing",
        f"--cov-report=xml:{REPORTS / 'coverage.xml'}",
        f"--junitxml={REPORTS / 'junit.xml'}")


# -------------------------------------------- dependencias y documentación


@task("pip-audit: vulnerabilidades conocidas en las dependencias fijadas")
def audit() -> None:
    REPORTS.mkdir(exist_ok=True)
    for lockfile in ("requirements.txt", "requirements-dev.txt"):
        report = REPORTS / f"pip-audit-{Path(lockfile).stem}.json"
        run(PY, "-m", "pip_audit", "--strict", "--require-hashes", "--disable-pip",
            "-r", lockfile, "-f", "json", "-o", str(report))


@task("Sphinx: genera la referencia de la API desde los docstrings (falla ante advertencias)")
def docs_sphinx() -> None:
    run(PY, "-m", "sphinx", "-W", "--keep-going", "-b", "html", "docs", "docs/_build/html")


# ------------------------------------------------------------- agregados


@task("Todos los controles bloqueantes, en el mismo orden que el CI")
def ci() -> None:
    static()
    test()
    audit()
    docs_sphinx()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("tasks", nargs="*", metavar="tarea")
    parser.add_argument("--list", action="store_true", help="lista las tareas disponibles")
    args = parser.parse_args()

    if args.list or not args.tasks:
        width = max(map(len, TASKS))
        for name, (_, description) in TASKS.items():
            print(f"  {name:<{width}}  {description}")
        return

    unknown = [name for name in args.tasks if name not in TASKS]
    if unknown:
        parser.error(f"tareas desconocidas: {', '.join(unknown)}")
    for name in args.tasks:
        TASKS[name][0]()


if __name__ == "__main__":
    main()
