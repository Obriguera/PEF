# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from data_models import USERS_DATA, MOVIES_DATA, RATINGS_DATA
from recommender_core import prepare_data, calculate_similarity, recommend_movies
from analysis_utils import analyze_popularity
from pydantic import BaseModel
from analysis_utils import invalidar_cache_popularidad

app = FastAPI()

# Para permitir que tu web consulte esta API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carga en memoria (igual que hacías en Tkinter)
utility_matrix = prepare_data(RATINGS_DATA)
user_similarities = calculate_similarity(utility_matrix)

@app.get("/api/users")
def get_users():
    """Devuelve la lista de usuarios para armar el selector en la web."""
    return {"users": USERS_DATA}

@app.get("/api/recommend/{user_id}")
def get_recommendations(user_id: int):
    """Devuelve las recomendaciones en formato JSON."""
    recomendaciones = recommend_movies(user_id, utility_matrix, user_similarities, MOVIES_DATA, top_n=5)
    return {"user_id": user_id, "recommendations": recomendaciones}

@app.get("/api/popularity")
def get_popularity():
    """Devuelve los datos crudos para armar el gráfico en la web."""
    top_5 = analyze_popularity(RATINGS_DATA, MOVIES_DATA)
    # Suponiendo que modificaste analyze_popularity para que no abra plt.show()
    return {"popular_movies": top_5}

class NewRating(BaseModel):
    user_id: int
    movie_id: int
    rating: float

@app.post("/api/rate")
def add_new_rating(rating_data: NewRating):
    """Simula agregar una nueva valoración e invalida el caché."""
    # 1. Agregamos el dato a la lista cruda
    RATINGS_DATA.append({
        'user_id': rating_data.user_id,
        'movie_id': rating_data.movie_id,
        'rating': rating_data.rating
    })
    
    # 2. ESTRATEGIA DE INVALIDACIÓN: Como hay un dato nuevo, la popularidad cambió.
    invalidar_cache_popularidad()
    
    return {"mensaje": "Valoración agregada exitosamente. Caché de popularidad invalidado."}

# Con este código, podés mostrar en vivo cómo pedir la popularidad es instantáneo, 
# pero si mandás un POST simulando un nuevo voto, la próxima vez que pidas la popularidad 
# el programa va a tener que recalcular todo desde cero y guardarlo de nuevo.