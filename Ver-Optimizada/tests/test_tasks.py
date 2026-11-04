"""Tests de las piezas de tasks.py que usa el CI: el resumen, el commit base de los benchmarks y las excepciones."""

import json
import subprocess
from datetime import date
from pathlib import Path

import pytest

import tasks

JUNIT = (
    '<?xml version="1.0" encoding="utf-8"?><testsuites name="pytest tests">'
    '<testsuite name="pytest" errors="1" failures="2" skipped="3" tests="50" time="1.0"></testsuite></testsuites>'
)
COVERAGE = '<coverage lines-valid="10" lines-covered="9" branches-valid="10" branches-covered="9"></coverage>'


def write_json(path: Path, content: object) -> None:
    path.write_text(json.dumps(content), encoding="utf-8")


@pytest.fixture
def reports(tmp_path):
    (tmp_path / "junit.xml").write_text(JUNIT, encoding="utf-8")
    (tmp_path / "coverage.xml").write_text(COVERAGE, encoding="utf-8")
    write_json(
        tmp_path / "radon-cc.json",
        {"a.py": [{"rank": "A", "complexity": 2}, {"rank": "B", "complexity": 8}]},
    )
    write_json(tmp_path / "bandit.sarif", {"runs": [{"results": [{}, {}]}]})
    write_json(tmp_path / "gitleaks.sarif", {"runs": [{"results": []}]})
    write_json(
        tmp_path / "pip-audit-requirements-dev.json",
        {"dependencies": [{"name": "x", "vulns": [{"id": "A"}, {"id": "B"}]}, {"name": "y", "vulns": []}]},
    )
    write_json(
        tmp_path / "benchmark.json", {"benchmarks": [{"name": "test_a", "stats": {"min": 0.001, "mean": 0.002}}]}
    )
    return tmp_path


def test_el_resumen_incluye_todos_los_controles(reports):
    text = tasks.build_summary(reports)
    assert "| Pruebas | 50 ejecutadas, 3 fallidas, 3 omitidas |" in text  # fallos + errores
    assert "| Cobertura (líneas y ramas) | 90.00 % |" in text
    assert "| Complejidad ciclomática | promedio 5.00, máxima 8, 1 bloques peores que A |" in text
    assert "| Bandit (código inseguro) | 2 hallazgos |" in text
    assert "| Gitleaks (secretos) | 0 hallazgos |" in text
    assert "| pip-audit (requirements-dev) | 2 vulnerabilidades |" in text
    assert "| test_a | 1.00 | 2.00 |" in text


def test_el_resumen_omite_los_reportes_que_faltan(tmp_path):
    (tmp_path / "junit.xml").write_text(JUNIT, encoding="utf-8")
    text = tasks.build_summary(tmp_path)
    assert "Pruebas" in text
    assert "Cobertura" not in text
    assert "Benchmarks" not in text


def test_el_resumen_sin_reportes(tmp_path):
    assert tasks.build_summary(tmp_path) == "Sin reportes.\n"


def test_la_tarea_summary_escribe_en_github_step_summary(reports, tmp_path, monkeypatch):
    destino = tmp_path / "step_summary.md"
    monkeypatch.setattr(tasks, "REPORTS", reports)
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(destino))
    tasks.summary()
    tasks.summary()  # se agrega, no se pisa: otros pasos también escriben ahí
    assert destino.read_text(encoding="utf-8").count("| Control | Resultado |") == 2


@pytest.mark.parametrize("sha", ["", "0" * 40, "f" * 40])
def test_un_commit_base_inutilizable_no_se_usa(sha, tmp_path):
    assert tasks.checkout_base(sha, tmp_path / "base") is False
    assert not (tmp_path / "base").exists()


def test_el_commit_base_se_extrae_en_un_worktree(tmp_path):
    head = tasks.git("rev-parse", "HEAD")
    if head.returncode != 0:
        pytest.skip("no es un repositorio git")
    destino = tmp_path / "base"
    try:
        assert tasks.checkout_base(head.stdout.strip(), destino) is True
        assert (destino / tasks.ROOT.name / "tests" / "test_benchmarks.py").exists()
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(destino)], cwd=tasks.ROOT, capture_output=True)
        subprocess.run(["git", "worktree", "prune"], cwd=tasks.ROOT, capture_output=True)


def test_las_excepciones_vigentes_se_pasan_a_pip_audit():
    excepciones = {"PYSEC-1": ("motivo", "2027-01-31")}
    assert tasks.audit_ignore_args(excepciones, date(2026, 11, 3)) == ["--ignore-vuln", "PYSEC-1"]
    assert tasks.audit_ignore_args({}, date(2026, 11, 3)) == []


def test_una_excepcion_vencida_hace_fallar_la_auditoria():
    with pytest.raises(SystemExit, match="PYSEC-2 venció el 2026-11-01"):
        tasks.audit_ignore_args({"PYSEC-2": ("motivo", "2026-11-01")}, date(2026, 11, 3))


def test_compare_minimums_calcula_la_razon_y_ordena_por_nombre():
    base = {"b": 0.002, "a": 0.001, "solo_en_base": 1.0}
    actual = {"a": 0.0015, "b": 0.002}
    assert tasks.compare_minimums(base, actual) == [("a", 1.0, 1.5, 1.5), ("b", 2.0, 2.0, 1.0)]


def test_report_comparison_solo_marca_lo_que_supera_el_umbral(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(tasks, "REPORTS", tmp_path)
    rows = [("rapido", 1.0, 1.24, 1.24), ("justo", 1.0, 1.25, 1.25), ("lento", 1.0, 1.26, 1.26)]
    assert tasks.report_comparison(rows, 0.25) == ["lento"]  # exactamente 25 % no es regresión
    assert "REGRESIÓN" in capsys.readouterr().out
    guardado = json.loads((tmp_path / "benchmark-comparison.json").read_text(encoding="utf-8"))
    assert [item["name"] for item in guardado["benchmarks"]] == ["rapido", "justo", "lento"]


def test_las_mediciones_se_intercalan_y_se_queda_con_el_mejor_tiempo(tmp_path, monkeypatch):
    llamadas, tiempos = [], iter([5.0, 4.0, 3.0, 6.0, 9.0, 5.0])  # base y actual alternados, 3 rondas
    monkeypatch.setattr(
        tasks,
        "measure_minimums",
        lambda directory, json_path, storage: llamadas.append(directory) or {"x": next(tiempos)},
    )
    base, actual = tasks.interleaved_minimums(tmp_path / "base", tmp_path, 3)
    assert llamadas == [tmp_path / "base", tasks.ROOT] * 3
    assert (base, actual) == ({"x": 3.0}, {"x": 4.0})  # mejor de las rondas 1, 3 y 5 / de las rondas 2, 4 y 6


def test_las_mediciones_no_usan_benchmark_compare(tmp_path, monkeypatch):
    # El CI no puede depender de --benchmark-compare: exige el almacenamiento dentro del directorio de trabajo
    # cuando el machine_info difiere entre mediciones, y en un runner de GitHub la frecuencia de CPU varía.
    comandos = []

    def falso(command, **kwargs):
        comandos.append(command)
        json_path = Path(next(a for a in command if a.startswith("--benchmark-json=")).split("=", 1)[1])
        json_path.write_text(json.dumps({"benchmarks": [{"name": "t", "stats": {"min": 0.5}}]}), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(tasks.subprocess, "run", falso)
    assert tasks.measure_minimums(tmp_path, tmp_path / "m.json", tmp_path / "storage") == {"t": 0.5}
    assert not any("compare" in argumento for argumento in comandos[0])


@pytest.fixture
def sin_git(monkeypatch, tmp_path):
    """bench_vs_base sin tocar git ni el sistema de archivos: solo la lógica de decisión."""
    monkeypatch.setenv("BENCH_BASE_SHA", "a" * 40)
    monkeypatch.setattr(tasks, "REPORTS", tmp_path)
    monkeypatch.setattr(tasks, "checkout_base", lambda sha, destination: True)
    monkeypatch.setattr(tasks, "use_current_benchmarks", lambda base_dir: None)
    monkeypatch.setattr(tasks, "git", lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, "", ""))


@pytest.mark.parametrize(("actual", "falla"), [({"t": 1.2}, False), ({"t": 1.3}, True)])
def test_bench_vs_base_falla_solo_ante_una_regresion(monkeypatch, sin_git, actual, falla):
    resultado = ({"t": 0.001}, {nombre: valor / 1000 for nombre, valor in actual.items()})
    monkeypatch.setattr(tasks, "interleaved_minimums", lambda base_dir, tmp, rounds: resultado)
    if falla:
        with pytest.raises(SystemExit, match="Regresión de rendimiento"):
            tasks.bench_vs_base()
    else:
        tasks.bench_vs_base()


def test_si_los_benchmarks_actuales_no_corren_en_el_base_se_mide_sin_comparar(monkeypatch, sin_git, capsys):
    def no_corre(base_dir, tmp, rounds):
        raise tasks.BaseNotComparable("ImportError: función nueva")

    medidos = []
    monkeypatch.setattr(tasks, "interleaved_minimums", no_corre)
    monkeypatch.setattr(tasks, "run_bench", lambda storage: medidos.append(storage))
    tasks.bench_vs_base()  # no falla: no hay con qué comparar
    assert len(medidos) == 1
    assert "se mide sin comparar" in capsys.readouterr().out


def test_si_fallan_los_benchmarks_actuales_el_job_falla(monkeypatch, sin_git):
    def falla(base_dir, tmp, rounds):
        raise tasks.BenchError("un test de rendimiento se rompió")

    monkeypatch.setattr(tasks, "interleaved_minimums", falla)
    with pytest.raises(SystemExit, match="no pudieron correr"):
        tasks.bench_vs_base()


def test_un_fallo_del_lado_base_o_del_actual_se_distingue(tmp_path, monkeypatch):
    def mide(directory, json_path, storage):
        if directory != tasks.ROOT:
            raise tasks.BenchError("falla el base")
        raise tasks.BenchError("falla el actual")

    monkeypatch.setattr(tasks, "measure_minimums", mide)
    with pytest.raises(tasks.BaseNotComparable):
        tasks.interleaved_minimums(tmp_path / "base", tmp_path, 1)
    monkeypatch.setattr(
        tasks,
        "measure_minimums",
        lambda directory, *args: {"x": 1.0} if directory != tasks.ROOT else mide(directory, *args),
    )
    with pytest.raises(tasks.BenchError) as error:
        tasks.interleaved_minimums(tmp_path / "base", tmp_path, 1)
    assert not isinstance(error.value, tasks.BaseNotComparable)


def test_los_dos_lados_se_miden_con_la_definicion_actual_de_los_benchmarks(tmp_path):
    # Si cada lado usara los suyos, un PR que cambie un benchmark compararía cosas distintas (el CI daba ~21x).
    base = tmp_path / "Ver-Optimizada"
    (base / "tests").mkdir(parents=True)
    (base / "tests" / "test_benchmarks.py").write_text("# definición vieja", encoding="utf-8")
    (base / "benchmark.py").write_text("# dataset viejo", encoding="utf-8")
    tasks.use_current_benchmarks(base)
    assert (base / "tests" / "test_benchmarks.py").read_text(encoding="utf-8") == (
        tasks.ROOT / "tests" / "test_benchmarks.py"
    ).read_text(encoding="utf-8")
    assert (base / "benchmark.py").read_text(encoding="utf-8") == (tasks.ROOT / "benchmark.py").read_text(
        encoding="utf-8"
    )


def test_el_resumen_prefiere_la_comparacion_con_el_commit_base(tmp_path):
    write_json(
        tmp_path / "benchmark-comparison.json",
        {
            "umbral": 0.25,
            "rondas": 3,
            "benchmarks": [{"name": "t", "base_min_ms": 1.0, "actual_min_ms": 1.4, "ratio": 1.4}],
        },
    )
    text = tasks.build_summary(tmp_path)
    assert "mejor de 3 mediciones intercaladas" in text
    assert "| t | 1.000 | 1.400 | 1.40 ⚠ |" in text
