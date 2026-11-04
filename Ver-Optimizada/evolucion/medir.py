"""Fase 6: evolución de la eficiencia entre las versiones del proyecto.

Subcomandos (desde ``Ver-Optimizada/``)::

    python evolucion/medir.py medir      # mide Base, Eficiente y Optimizada y escribe metrics/evolucion.json
    python evolucion/medir.py historial  # mide Optimizada en cada tag parcial3-faseN (y su calidad)
    python evolucion/medir.py graficar   # dibuja los PNG en ../docs/img/ a partir del JSON
    python evolucion/medir.py todo       # los tres, en orden

Cada medición corre en un subproceso aparte (ver ``trabajador.py``). Los tiempos dependen de la máquina: el JSON guarda
el entorno y los gráficos lo muestran. No se ejecuta en el CI (Base tarda minutos con 2000 usuarios).
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

AQUI = Path(__file__).resolve().parent
OPTIMIZADA = AQUI.parent
REPO = OPTIMIZADA.parent
SALIDA = OPTIMIZADA / "metrics" / "evolucion.json"
IMAGENES = REPO / "docs" / "img"
TRABAJADOR = AQUI / "trabajador.py"

VERSIONES = {"Base": "Ver-Base", "Eficiente": "Ver-Eficiente", "Optimizada": "Ver-Optimizada"}
TAMANOS = (250, 500, 1000, 2000)
ETAPAS = ("prepare_data", "calculate_similarity", "recommend_movies", "analyze_popularity")
TAGS = tuple(f"parcial3-fase{n}" for n in range(6))
# Con más usuarios las versiones lentas tardan minutos: se repite solo donde es barato.
REPETICIONES = {250: 5, 500: 3, 1000: 3, 2000: 1}
REPETICIONES_OPTIMIZADA = {250: 7, 500: 7, 1000: 5, 2000: 5}
TAMANO_HISTORIAL = 1000


def repeticiones_para(version: str, usuarios: int) -> int:
    tabla = REPETICIONES_OPTIMIZADA if version == "Optimizada" else REPETICIONES
    return tabla[usuarios]


def total_ms(ms: dict[str, float]) -> float:
    """Suma de las cuatro etapas: la 'latencia de punta a punta' de una corrida del benchmark."""
    return round(sum(ms[e] for e in ETAPAS), 3)


def aceleracion(referencia: float, valor: float) -> float:
    """Cuántas veces más rápido es ``valor`` que ``referencia`` (>1 = mejora, <1 = empeora)."""
    return round(referencia / valor, 2) if valor > 0 else float("inf")


def exponente_empirico(tamanos: list[int], tiempos: list[float]) -> float:
    """Pendiente de log(tiempo) contra log(n): si t ~ n^k, devuelve k. Estima el orden de crecimiento observado."""
    import math

    xs = [math.log(n) for n in tamanos]
    ys = [math.log(t) for t in tiempos]
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    den = sum((x - mx) ** 2 for x in xs)
    return round(sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True)) / den, 2)


def lanzar(directorio: Path, usuarios: int, repeticiones: int) -> dict[str, Any]:
    """Corre el worker en ``directorio`` con el intérprete actual (que tiene NumPy, que Optimizada necesita)."""
    cmd = [sys.executable, str(TRABAJADOR), str(usuarios), str(repeticiones)]
    proc = subprocess.run(cmd, cwd=directorio, capture_output=True, text=True, check=False)  # noqa: S603
    if proc.returncode != 0:
        raise RuntimeError(f"{directorio.name} con {usuarios} usuarios falló:\n{proc.stderr[-800:]}")
    resultado: dict[str, Any] = json.loads(proc.stdout.strip().splitlines()[-1])
    return resultado


def entorno() -> dict[str, Any]:
    import os

    return {
        "python": platform.python_version(),
        "sistema": platform.platform(),
        "cpus": os.cpu_count(),
        "nota": "Los tiempos dependen de la máquina; comparar las versiones entre sí, no con otros equipos.",
    }


def metricas_de_codigo(directorio: Path) -> dict[str, Any]:
    """Complejidad ciclomática, índice de mantenibilidad y sentencias del núcleo de una versión (Radon)."""
    from radon.complexity import cc_visit
    from radon.metrics import mi_visit
    from radon.raw import analyze

    bloques: list[int] = []
    mi: dict[str, float] = {}
    sloc = 0
    for nombre in ("recommender_core.py", "analysis_utils.py"):
        codigo = (directorio / nombre).read_text(encoding="utf-8")
        bloques += [b.complexity for b in cc_visit(codigo)]
        mi[nombre] = round(mi_visit(codigo, multi=True), 2)
        sloc += analyze(codigo).sloc
    return {"cc_promedio": round(statistics.fmean(bloques), 2), "cc_maxima": max(bloques), "mi": mi, "sloc": sloc}


def medir() -> dict[str, Any]:
    versiones: dict[str, Any] = {}
    referencia: dict[int, list[str]] = {}
    for nombre, carpeta in VERSIONES.items():
        filas = []
        for n in TAMANOS:
            fila = lanzar(REPO / carpeta, n, repeticiones_para(nombre, n))
            recomendacion = fila.pop("recomendacion")
            if referencia.setdefault(n, recomendacion) != recomendacion:
                raise RuntimeError(f"{nombre} recomienda distinto con {n} usuarios: {recomendacion}")
            fila["total_ms"] = total_ms(fila["ms"])
            filas.append(fila)
            print(f"{nombre:11} {n:5} usuarios  total {fila['total_ms']:>10.1f} ms  pico {fila['pico_mb']} MB", flush=True)
        versiones[nombre] = {"mediciones": filas, "codigo": metricas_de_codigo(REPO / carpeta)}
    return {"entorno": entorno(), "dataset": {"peliculas": 500, "ratings_por_usuario": 30, "semilla": 42}, "versiones": versiones}


def calidad_de_tag(tag: str) -> dict[str, Any]:
    """Tests y cobertura de un tag, leídos de su metrics/<tag>.json (si ese tag lo tiene)."""
    proc = subprocess.run(
        ["git", "show", f"{tag}:Ver-Optimizada/metrics/{tag}.json"],  # noqa: S607
        cwd=REPO, capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        return {}
    datos = json.loads(proc.stdout)
    cob, cc = datos.get("cobertura", {}), datos.get("complejidad", {})
    return {"tests": cob.get("tests"), "cobertura": cob.get("total"), "cc_promedio": cc.get("cc_promedio"),
            "mi_core": next((v for k, v in cc.get("mi", {}).items() if k.startswith("recommender_core")), None)}


def historial() -> dict[str, Any]:
    """Mide Optimizada en cada tag de la Parcial 3 usando un worktree temporal por tag."""
    resultado: dict[str, Any] = {}
    with tempfile.TemporaryDirectory() as tmp:
        for tag in TAGS:
            destino = Path(tmp) / tag
            subprocess.run(["git", "worktree", "add", "--detach", str(destino), tag], cwd=REPO, check=True, capture_output=True)  # noqa: S607
            try:
                fila = lanzar(destino / "Ver-Optimizada", TAMANO_HISTORIAL, 5)
            except RuntimeError as error:
                print(f"{tag}: sin medición ({error})", flush=True)
                continue
            finally:
                subprocess.run(["git", "worktree", "remove", "--force", str(destino)], cwd=REPO, check=True, capture_output=True)  # noqa: S607
            fila.pop("recomendacion", None)
            fila["total_ms"] = total_ms(fila["ms"])
            fila["calidad"] = calidad_de_tag(tag)
            resultado[tag] = fila
            print(f"{tag}: total {fila['total_ms']:.1f} ms, pico {fila['pico_mb']} MB", flush=True)
    return resultado


def cargar() -> dict[str, Any]:
    return json.loads(SALIDA.read_text(encoding="utf-8")) if SALIDA.exists() else {}


def guardar(datos: dict[str, Any]) -> None:
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(datos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def cmd_medir() -> None:
    datos = cargar() | medir()
    guardar(datos)


def cmd_historial() -> None:
    datos = cargar()
    datos["historial"] = {"usuarios": TAMANO_HISTORIAL, "tags": historial()}
    datos.setdefault("entorno", entorno())
    guardar(datos)


def cmd_graficar() -> None:
    from graficos import dibujar_todo  # import local: matplotlib solo hace falta para graficar

    dibujar_todo(cargar(), IMAGENES)


def main() -> None:
    sys.path.insert(0, str(AQUI))
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("comando", choices=["medir", "historial", "graficar", "todo"])
    comando = parser.parse_args().comando
    if comando in ("medir", "todo"):
        cmd_medir()
    if comando in ("historial", "todo"):
        cmd_historial()
    if comando in ("graficar", "todo"):
        cmd_graficar()


if __name__ == "__main__":
    main()
