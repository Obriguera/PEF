import pytest
from starlette.testclient import TestClient

from analysis_utils import invalidar_cache_popularidad
from data_models import RATINGS_DATA
from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def restaurar_estado_global():
    """POST /api/rate modifica RATINGS_DATA y el caché de popularidad, que son globales.

    Se restauran después de cada test para no contaminar al resto de la suite.
    """
    ratings_originales = list(RATINGS_DATA)
    yield
    RATINGS_DATA[:] = ratings_originales
    invalidar_cache_popularidad()


def test_api_get_users():
    response = client.get("/api/users")
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert len(data["users"]) > 0


def test_api_get_recommendations():
    response = client.get("/api/recommend/101")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == 101
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)


def test_api_get_popularity():
    response = client.get("/api/popularity")
    assert response.status_code == 200
    data = response.json()
    assert "popular_movies" in data
    assert len(data["popular_movies"]) <= 5


def test_api_add_rating():
    payload = {"user_id": 101, "movie_id": 99, "rating": 5.0}
    response = client.post("/api/rate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Valoración agregada" in data["mensaje"]


def test_api_procesa_archivo_grande(tmp_path, monkeypatch):
    # El endpoint escribe en el directorio actual: se aísla en tmp_path
    monkeypatch.chdir(tmp_path)
    response = client.get("/api/large-files/process", params={"records": 1000})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["records_processed"] == 1000
    assert 0 < data["movies_aggregated"] <= 1000
    assert (tmp_path / data["source_file"]).exists()
    assert (tmp_path / data["output_file"]).exists()

    # Segunda llamada: reutiliza el archivo existente en lugar de generarlo de nuevo
    generado = (tmp_path / data["source_file"]).stat().st_mtime_ns
    assert client.get("/api/large-files/process", params={"records": 1000}).status_code == 200
    assert (tmp_path / data["source_file"]).stat().st_mtime_ns == generado


def test_api_informa_los_registros_realmente_procesados(tmp_path, monkeypatch):
    # Si el CSV ya existe, el endpoint lo reutiliza y no genera uno nuevo con el tamaño pedido:
    # records_processed debe reflejar lo que se procesó, no el parámetro recibido.
    monkeypatch.chdir(tmp_path)
    assert client.get("/api/large-files/process", params={"records": 1000}).json()["records_processed"] == 1000
    data = client.get("/api/large-files/process", params={"records": 5000}).json()
    assert data["records_processed"] == 1000


def test_api_recomendacion_de_usuario_inexistente_es_404():
    response = client.get("/api/recommend/999999")
    assert response.status_code == 404


@pytest.mark.parametrize("rating", [0.0, 0.99, 5.01, -3.0, 1e308])
def test_api_rate_rechaza_ratings_fuera_de_rango(rating):
    cantidad = len(RATINGS_DATA)
    response = client.post("/api/rate", json={"user_id": 101, "movie_id": 1, "rating": rating})
    assert response.status_code == 422
    assert len(RATINGS_DATA) == cantidad  # no se agregó nada


@pytest.mark.parametrize("rating", [1.0, 3.5, 5.0])
def test_api_rate_acepta_los_extremos_del_rango(rating):
    response = client.post("/api/rate", json={"user_id": 101, "movie_id": 1, "rating": rating})
    assert response.status_code == 200


@pytest.mark.parametrize("records", [0, -5, 1_000_001])
def test_api_large_files_rechaza_cantidades_fuera_de_rango(tmp_path, monkeypatch, records):
    monkeypatch.chdir(tmp_path)
    response = client.get("/api/large-files/process", params={"records": records})
    assert response.status_code == 422
    assert list(tmp_path.iterdir()) == []  # no se generó ningún archivo
