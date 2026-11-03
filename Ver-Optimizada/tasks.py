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
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
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


def bench_command(storage: Path) -> list[str]:
    """Comando base de pytest-benchmark: solo los benchmarks, con las mediciones activadas."""
    return [
        PY,
        "-m",
        "pytest",
        "tests/test_benchmarks.py",
        "--benchmark-enable",
        "--benchmark-only",
        f"--benchmark-storage={storage}",
        "--benchmark-columns=min,mean,median,stddev,rounds",
    ]


def has_baseline(storage: Path) -> bool:
    """¿Hay una línea base guardada en ``storage`` para esta plataforma y esta versión de Python?"""
    from pytest_benchmark.utils import get_machine_id  # disponible después de `install`

    return any((storage / get_machine_id()).glob("*.json"))


def run_bench(storage: Path) -> None:
    """Mide y, si hay línea base en ``storage``, falla ante una regresión mayor al umbral."""
    REPORTS.mkdir(exist_ok=True)
    command = [*bench_command(storage), f"--benchmark-json={REPORTS / 'benchmark.json'}"]
    if has_baseline(storage):
        run(*command, "--benchmark-compare", f"--benchmark-compare-fail={BENCH_MAX_REGRESSION}")
    else:
        # pytest-benchmark aborta con un error de uso si se pide --benchmark-compare-fail sin línea base
        print(
            "\n⚠ SIN LÍNEA BASE para esta plataforma: se mide, pero NO se compara. Crearla: python tasks.py bench-save"
        )
        run(*command)


@task("Benchmarks: falla si algo empeora más de 25 % (mínimo) respecto de la última línea base")
def bench() -> None:
    run_bench(BENCH_STORAGE)


@task("Benchmarks: guarda una nueva línea base en metrics/benchmarks/ (tras una mejora o al cambiar de máquina)")
def bench_save() -> None:
    run(*bench_command(BENCH_STORAGE), "--benchmark-save=baseline")


def git(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def checkout_base(sha: str, destination: Path) -> bool:
    """Crea un worktree del commit ``sha`` en ``destination``; False si no se puede usar como base."""
    if not sha or set(sha) == {"0"}:  # sin commit anterior (primer push, rama nueva)
        return False
    if git("cat-file", "-e", f"{sha}^{{commit}}").returncode != 0:
        return False
    if git("worktree", "add", "--detach", str(destination), sha).returncode != 0:
        return False
    return (destination / ROOT.name / "tests" / "test_benchmarks.py").exists()


@task("Benchmarks: compara contra el commit BENCH_BASE_SHA, medido en esta misma máquina")
def bench_vs_base() -> None:
    """Una línea base de otra máquina no sirve: se mide el commit base y el actual seguidos, en el mismo equipo.

    El código del commit base se mide con el comando de ESTE tasks.py, para que el resultado no dependa de qué
    versión de tasks.py tenga ese commit.
    """
    base_sha = os.environ.get("BENCH_BASE_SHA", "")
    with tempfile.TemporaryDirectory() as tmp:
        storage = Path(tmp) / "storage"
        worktree = Path(tmp) / "base"
        try:
            if checkout_base(base_sha, worktree):
                print(f"\nMidiendo el commit base {base_sha[:7]} para tener una línea base de esta máquina...")
                measured = subprocess.run(
                    [*bench_command(storage), "--benchmark-save=baseline"], cwd=worktree / ROOT.name
                )
                if measured.returncode != 0:
                    sys.exit(measured.returncode)
            else:
                print(f"\n⚠ Sin commit base utilizable ({base_sha or 'BENCH_BASE_SHA vacío'}): se mide sin comparar.")
            run_bench(storage)
        finally:
            git("worktree", "remove", "--force", str(worktree))
            git("worktree", "prune")


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


# ----------------------------------------------------------------- resumen

Row = tuple[str, str]


def _summary_tests(reports: Path) -> list[Row]:
    junit = reports / "junit.xml"
    if not junit.exists():
        return []
    root = ET.parse(junit).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    if suite is None:
        return []
    failed = int(suite.get("failures", 0)) + int(suite.get("errors", 0))
    return [("Pruebas", f"{suite.get('tests')} ejecutadas, {failed} fallidas, {suite.get('skipped', 0)} omitidas")]


def _summary_coverage(reports: Path) -> list[Row]:
    xml = reports / "coverage.xml"
    if not xml.exists():
        return []
    root = ET.parse(xml).getroot()
    hits = int(root.get("lines-covered", 0)) + int(root.get("branches-covered", 0))
    total = int(root.get("lines-valid", 0)) + int(root.get("branches-valid", 0))
    return [("Cobertura (líneas y ramas)", f"{100 * hits / total:.2f} %" if total else "sin datos")]


def _summary_complexity(reports: Path) -> list[Row]:
    radon = reports / "radon-cc.json"
    if not radon.exists():
        return []
    blocks = [block for file_blocks in json.loads(radon.read_text(encoding="utf-8")).values() for block in file_blocks]
    if not blocks:
        return []
    worse = sum(block["rank"] != "A" for block in blocks)
    average = sum(block["complexity"] for block in blocks) / len(blocks)
    highest = max(block["complexity"] for block in blocks)
    return [("Complejidad ciclomática", f"promedio {average:.2f}, máxima {highest}, {worse} bloques peores que A")]


def _summary_findings(reports: Path) -> list[Row]:
    rows: list[Row] = []
    for name, label in (("bandit.sarif", "Bandit (código inseguro)"), ("gitleaks.sarif", "Gitleaks (secretos)")):
        sarif = reports / name
        if sarif.exists():
            results = sum(len(run_["results"]) for run_ in json.loads(sarif.read_text(encoding="utf-8"))["runs"])
            rows.append((label, f"{results} hallazgos"))
    return rows


def _summary_audit(reports: Path) -> list[Row]:
    rows: list[Row] = []
    for report in sorted(reports.glob("pip-audit-*.json")):
        dependencies = json.loads(report.read_text(encoding="utf-8"))["dependencies"]
        vulns = sum(len(dependency.get("vulns", [])) for dependency in dependencies)
        rows.append((f"pip-audit ({report.stem.removeprefix('pip-audit-')})", f"{vulns} vulnerabilidades"))
    return rows


def _summary_benchmarks(reports: Path) -> str:
    benchmark = reports / "benchmark.json"
    if not benchmark.exists():
        return ""
    lines = ["", "**Benchmarks**", "", "| Prueba | mínimo (ms) | media (ms) |", "|---|---:|---:|"]
    for item in json.loads(benchmark.read_text(encoding="utf-8"))["benchmarks"]:
        stats = item["stats"]
        lines.append(f"| {item['name']} | {stats['min'] * 1000:.2f} | {stats['mean'] * 1000:.2f} |")
    return "\n".join(lines)


def build_summary(reports: Path) -> str:
    """Resumen en Markdown de los reportes que existan en ``reports``; omite los que faltan."""
    rows = [
        *_summary_tests(reports),
        *_summary_coverage(reports),
        *_summary_complexity(reports),
        *_summary_findings(reports),
        *_summary_audit(reports),
    ]
    benchmarks = _summary_benchmarks(reports)
    if not rows and not benchmarks:
        return "Sin reportes.\n"
    table = "| Control | Resultado |\n|---|---|\n" + "".join(f"| {control} | {result} |\n" for control, result in rows)
    return f"{table if rows else ''}{benchmarks}\n"


@task("Resumen en Markdown de los reportes de reports/ (en el CI se agrega a $GITHUB_STEP_SUMMARY)")
def summary() -> None:
    text = build_summary(REPORTS)
    target = os.environ.get("GITHUB_STEP_SUMMARY")
    if target:
        with open(target, "a", encoding="utf-8") as output:
            output.write(text)
    else:
        print(text)


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
