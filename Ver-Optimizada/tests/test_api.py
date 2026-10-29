from starlette.testclient import TestClient

from main import app

client = TestClient(app)


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
