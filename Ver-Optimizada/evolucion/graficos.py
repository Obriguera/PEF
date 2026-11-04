"""Gráficos de la Fase 6 (matplotlib, backend sin pantalla). Los lee de ``metrics/evolucion.json``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# Paleta apta para daltonismo (Okabe-Ito) + marcadores distintos: no depende solo del color.
ESTILO = {
    "Base": ("#D55E00", "o"),
    "Eficiente": ("#0072B2", "s"),
    "Optimizada": ("#009E73", "^"),
}
ETIQUETAS_ETAPA = {
    "prepare_data": "Preparar matriz",
    "calculate_similarity": "Similitud (todos contra todos)",
    "recommend_movies": "Recomendar a un usuario",
    "analyze_popularity": "Popularidad",
}


def _base(titulo: str, subtitulo: str) -> tuple[Any, Any]:
    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=150)
    ax.set_title(titulo, loc="left", fontsize=13, fontweight="bold")
    ax.text(0, 1.01, subtitulo, transform=ax.transAxes, fontsize=9, color="#555555", va="bottom")
    ax.grid(True, which="both", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    return fig, ax


def _guardar(fig: Any, destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(destino)
    plt.close(fig)


def _pie(datos: dict[str, Any]) -> str:
    e = datos.get("entorno", {})
    return f"{e.get('cpus', '?')} CPU · Python {e.get('python', '?')} · tiempos dependientes de la máquina"


def tiempo_total(datos: dict[str, Any], destino: Path) -> None:
    fig, ax = _base("Tiempo total según la cantidad de usuarios", "Suma de las cuatro etapas, escala logarítmica")
    for nombre, info in datos["versiones"].items():
        color, marca = ESTILO[nombre]
        xs = [m["usuarios"] for m in info["mediciones"]]
        ys = [m["total_ms"] for m in info["mediciones"]]
        ax.plot(xs, ys, marker=marca, color=color, label=nombre, linewidth=2)
        ax.annotate(f"{ys[-1] / 1000:.1f} s" if ys[-1] >= 1000 else f"{ys[-1]:.0f} ms", (xs[-1], ys[-1]),
                    textcoords="offset points", xytext=(6, 0), va="center", fontsize=8, color=color)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks([250, 500, 1000, 2000], ["250", "500", "1000", "2000"])
    ax.set_xlabel("Usuarios (30 calificaciones cada uno, 500 películas)")
    ax.set_ylabel("Milisegundos")
    ax.legend(frameon=False)
    fig.text(0.01, 0.005, _pie(datos), fontsize=7, color="#777777")
    _guardar(fig, destino)


def aceleracion(datos: dict[str, Any], destino: Path) -> None:
    mayor = max(m["usuarios"] for m in datos["versiones"]["Base"]["mediciones"])
    fig, ax = _base(f"Aceleración respecto de Base ({mayor} usuarios)", "Veces más rápido que Base, por etapa (escala logarítmica)")
    etapas = list(ETIQUETAS_ETAPA)
    ancho = 0.38
    base = next(m for m in datos["versiones"]["Base"]["mediciones"] if m["usuarios"] == mayor)
    for i, nombre in enumerate(("Eficiente", "Optimizada")):
        fila = next(m for m in datos["versiones"][nombre]["mediciones"] if m["usuarios"] == mayor)
        valores = [base["ms"][e] / fila["ms"][e] for e in etapas]
        pos = [j + (i - 0.5) * ancho for j in range(len(etapas))]
        barras = ax.bar(pos, valores, ancho, label=nombre, color=ESTILO[nombre][0])
        for b, v in zip(barras, valores, strict=True):
            ax.annotate(f"{v:.1f}×", (b.get_x() + b.get_width() / 2, v), ha="center", xytext=(0, 3), textcoords="offset points", fontsize=8)
    ax.axhline(1, color="#555555", linewidth=1, linestyle="--")
    ax.set_yscale("log")
    ax.set_xticks(range(len(etapas)), [ETIQUETAS_ETAPA[e] for e in etapas], fontsize=8)
    ax.set_ylabel("Veces más rápido que Base (1 = igual)")
    ax.legend(frameon=False)
    fig.text(0.01, 0.005, _pie(datos), fontsize=7, color="#777777")
    _guardar(fig, destino)


def memoria(datos: dict[str, Any], destino: Path) -> None:
    fig, ax = _base("Pico de memoria del proceso", "Incluye el intérprete y el dataset (iguales para todas las versiones)")
    for nombre, info in datos["versiones"].items():
        color, marca = ESTILO[nombre]
        ax.plot([m["usuarios"] for m in info["mediciones"]], [m["pico_mb"] for m in info["mediciones"]],
                marker=marca, color=color, label=nombre, linewidth=2)
    ax.set_xscale("log")
    ax.set_xticks([250, 500, 1000, 2000], ["250", "500", "1000", "2000"])
    ax.set_xlabel("Usuarios")
    ax.set_ylabel("MB (RSS máximo)")
    ax.legend(frameon=False)
    fig.text(0.01, 0.005, _pie(datos), fontsize=7, color="#777777")
    _guardar(fig, destino)


def historial(datos: dict[str, Any], destino: Path) -> None:
    tags = datos["historial"]["tags"]
    nombres = [t.replace("parcial3-", "") for t in tags]
    fig, ax = _base(f"Optimizada a lo largo de la Parcial 3 ({datos['historial']['usuarios']} usuarios)",
                    "Tiempo total por fase (barras) y cobertura de tests (línea)")
    ax.bar(nombres, [t["total_ms"] for t in tags.values()], color=ESTILO["Optimizada"][0])
    ax.set_ylabel("Tiempo total (ms)")
    cobertura = [t.get("calidad", {}).get("cobertura") for t in tags.values()]
    if all(c is not None for c in cobertura):
        ax2 = ax.twinx()
        ax2.plot(nombres, cobertura, color="#555555", marker="o", linestyle="--")
        ax2.set_ylabel("Cobertura (%)")
        ax2.set_ylim(0, 105)
        ax2.spines[["top"]].set_visible(False)
    fig.text(0.01, 0.005, _pie(datos), fontsize=7, color="#777777")
    _guardar(fig, destino)


def dibujar_todo(datos: dict[str, Any], carpeta: Path) -> None:
    if "versiones" in datos:
        tiempo_total(datos, carpeta / "evolucion-tiempo.png")
        aceleracion(datos, carpeta / "evolucion-aceleracion.png")
        memoria(datos, carpeta / "evolucion-memoria.png")
    if "historial" in datos:
        historial(datos, carpeta / "evolucion-historial.png")
