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
from datetime import date
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
        sys.exit(f"'{name}' no está instalado. Ver «Cómo correr los controles» en SECURITY.md.")
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
    run(
        PY,
        "-m",
        "bandit",
        "-c",
        "pyproject.toml",
        "-r",
        *SOURCES,
        "-f",
        "sarif",
        "-o",
        str(REPORTS / "bandit.sarif"),
        "--exit-zero",
    )
    # Rechazo: severidad media o más con confianza media o más
    run(
        PY,
        "-m",
        "bandit",
        "-c",
        "pyproject.toml",
        "-r",
        *SOURCES,
        "--severity-level",
        "medium",
        "--confidence-level",
        "medium",
    )


@task("Gitleaks: detección de secretos en el historial de git")
def secrets() -> None:
    REPORTS.mkdir(exist_ok=True)
    run(
        tool("gitleaks"),
        "git",
        "..",
        "--report-format",
        "sarif",
        "--report-path",
        str(REPORTS / "gitleaks.sarif"),
        "--redact",
    )


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
    run(
        PY,
        "-m",
        "pytest",
        "--cov",
        "--cov-report=term-missing",
        f"--cov-report=xml:{REPORTS / 'coverage.xml'}",
        f"--junitxml={REPORTS / 'junit.xml'}",
    )


# ------------------------------------------------------------ rendimiento

# Las líneas base se guardan por plataforma y versión de Python (p. ej. Linux-CPython-3.13-64bit): en otra
# combinación no hay con qué comparar y el control avisa en lugar de fallar.
BENCH_STORAGE = ROOT / "metrics" / "benchmarks"
# Se compara el mínimo y no la media: el ruido de una máquina compartida solo suma tiempo, así que el mínimo
# es la estadística estable. Medido en 5 corridas, su peor desvío fue 15 % (la media llegó a 25 %).
BENCH_MAX_REGRESSION = "min:25%"


def bench_command() -> list[str]:
    """Comando base de pytest-benchmark: solo los benchmarks, con las mediciones activadas."""
    return [
        PY,
        "-m",
        "pytest",
        "tests/test_benchmarks.py",
        "--benchmark-enable",
        "--benchmark-only",
        f"--benchmark-storage={BENCH_STORAGE}",
        "--benchmark-columns=min,mean,median,stddev,rounds",
    ]


def has_baseline() -> bool:
    """¿Hay una línea base guardada para esta plataforma y esta versión de Python?"""
    from pytest_benchmark.utils import get_machine_id  # disponible después de `install`

    return any((BENCH_STORAGE / get_machine_id()).glob("*.json"))


@task("Benchmarks: falla si algo empeora más de 25 % (mínimo) respecto de la última línea base")
def bench() -> None:
    REPORTS.mkdir(exist_ok=True)
    command = [*bench_command(), f"--benchmark-json={REPORTS / 'benchmark.json'}"]
    if has_baseline():
        run(*command, "--benchmark-compare", f"--benchmark-compare-fail={BENCH_MAX_REGRESSION}")
    else:
        # pytest-benchmark aborta con un error de uso si se pide --benchmark-compare-fail sin línea base
        print(
            "\n⚠ SIN LÍNEA BASE para esta plataforma: se mide, pero NO se compara. Crearla: python tasks.py bench-save"
        )
        run(*command)


@task("Benchmarks: guarda una nueva línea base en metrics/benchmarks/ (tras una mejora o al cambiar de máquina)")
def bench_save() -> None:
    run(*bench_command(), "--benchmark-save=baseline")


@task("Perfiles de cProfile y pyinstrument sobre benchmark.py; no bloquea, deja los reportes en reports/")
def profile() -> None:
    REPORTS.mkdir(exist_ok=True)
    run(PY, "-m", "cProfile", "-o", str(REPORTS / "profile.prof"), "benchmark.py")
    run(PY, "-m", "pyinstrument", "--renderer", "html", "--outfile", str(REPORTS / "profile.html"), "benchmark.py")


# -------------------------------------------- dependencias y documentación


# Excepciones documentadas de pip-audit: id de la vulnerabilidad -> (justificación, vence AAAA-MM-DD).
# Cada una debe figurar también en el registro de SECURITY.md. Una excepción vencida hace fallar la auditoría,
# para que no quede vigente por olvido.
AUDIT_EXCEPTIONS: dict[str, tuple[str, str]] = {}


def audit_ignore_args(exceptions: dict[str, tuple[str, str]], today: date) -> list[str]:
    """Argumentos --ignore-vuln de las excepciones vigentes; corta si alguna venció."""
    args: list[str] = []
    for vuln_id, (_reason, expires) in exceptions.items():
        if date.fromisoformat(expires) < today:
            sys.exit(f"La excepción de pip-audit {vuln_id} venció el {expires}: revisarla en SECURITY.md.")
        args += ["--ignore-vuln", vuln_id]
    return args


@task("pip-audit: vulnerabilidades conocidas en las dependencias fijadas")
def audit() -> None:
    REPORTS.mkdir(exist_ok=True)
    ignore = audit_ignore_args(AUDIT_EXCEPTIONS, date.today())
    for lockfile in ("requirements.txt", "requirements-dev.txt"):
        report = REPORTS / f"pip-audit-{Path(lockfile).stem}.json"
        run(
            PY,
            "-m",
            "pip_audit",
            "--strict",
            "--require-hashes",
            "--disable-pip",
            *ignore,
            "-r",
            lockfile,
            "-f",
            "json",
            "-o",
            str(report),
        )


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
