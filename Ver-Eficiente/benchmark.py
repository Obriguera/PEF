# benchmark.py
import random
from recommender_core import prepare_data, calculate_similarity, recommend_movies
from analysis_utils import analyze_popularity

def generate_massive_data(num_users=2000, num_movies=500, ratings_per_user=30):
    """Genera un dataset sintético masivo en Python puro."""
    movies_data = [{'movie_id': i, 'title': f'Pelicula_{i}', 'genre': 'Action', 'duration': 120} for i in range(1, num_movies + 1)]
    
    ratings_data = []
    for user_id in range(1, num_users + 1):
        # Cada usuario califica un puñado de películas al azar
        watched = random.sample(range(1, num_movies + 1), ratings_per_user)
        for movie_id in watched:
            ratings_data.append({
                'user_id': user_id,
                'movie_id': movie_id,
                'rating': round(random.uniform(1.0, 5.0), 1)
            })
            
    return movies_data, ratings_data

def run_baseline_test():
    print("Generando dataset masivo... ⏳")
    MOVIES_DATA, RATINGS_DATA = generate_massive_data(num_users=2000, num_movies=500, ratings_per_user=30)
    
    print(f"Dataset listo: 2000 usuarios, 500 películas y {len(RATINGS_DATA)} ratings.")
    print("Corriendo el benchmark (esto va a transpirar un poco)... 💦")
    
    # 1. Preparar matrices
    utility_matrix = prepare_data(RATINGS_DATA)
    user_similarities = calculate_similarity(utility_matrix)
    
    # 2. Medir recomendación (elegimos el usuario 1)
    _ = recommend_movies(1, utility_matrix, user_similarities, MOVIES_DATA, top_n=5)
    
    # 3. Medir popularidad
    _ = analyze_popularity(RATINGS_DATA, MOVIES_DATA)
    
    print("¡Terminado! ✅")

if __name__ == "__main__":
    run_baseline_test()



# Se paralelizó el motor de recomendaciones (recommend_movies)
#  utilizando concurrent.futures.ThreadPoolExecutor. 
# Son independientes porque ninguna recomendación altera 
# la matriz principal compartida. Se eligió hilos en lugar 
# de multiprocesamiento (ProcessPoolExecutor) para evitar el 
# masivo overhead de memoria que implicaría clonar las estructuras
#  de datos (matrices de similitud) a múltiples procesos, asumiendo
#  ese trade-off arquitectónico.