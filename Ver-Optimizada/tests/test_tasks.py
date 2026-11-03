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
