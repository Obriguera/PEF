# analysis_utils.py
from collections.abc import Iterable

from data_models import Movie, PopularMovie, Rating

# Variable global para almacenar el resultado en memoria RAM
_cache_popularidad: list[PopularMovie] | None = None


def analyze_popularity(ratings_data: Iterable[Rating], movies_data: Iterable[Movie]) -> list[PopularMovie]:
    """Calcula la popularidad implementando Caching Inteligente."""
    global _cache_popularidad

    # ESTRATEGIA DE CACHING: Si ya tenemos el cálculo, lo devolvemos en O(1)
    if _cache_popularidad is not None:
        return _cache_popularidad

    movie_counts: dict[int, int] = {}
    for r in ratings_data:
        m_id = r["movie_id"]
        movie_counts[m_id] = movie_counts.get(m_id, 0) + 1

    popularity_list: list[PopularMovie] = []
    # Usamos un dict para mapear títulos rápido O(1) en vez de iterar listas
    movie_dict = {m["movie_id"]: m["title"] for m in movies_data}

    for m_id, count in movie_counts.items():
        title = movie_dict.get(m_id, "Desconocida")
        popularity_list.append({"title": title, "count": count})

    popularity_list.sort(key=lambda x: x["count"], reverse=True)
    top_5 = popularity_list[:5]

    # GUARDAR EN CACHÉ: Almacenamos el resultado final antes de devolverlo
    _cache_popularidad = top_5
    return top_5


def invalidar_cache_popularidad() -> None:
    """Estrategia de invalidación: Se llama cuando cambia el historial de preferencias."""
    global _cache_popularidad
    _cache_popularidad = None


# Se almacena el Top 5 ya
# procesado en una variable en memoria
# porque es un dato de acceso frecuente y lectura intensiva.
#  Se reutiliza en cada petición a la ruta /api/popularity y se invalida
# (borrando la variable) únicamente si ingresa un nuevo rating a la base de datos.
