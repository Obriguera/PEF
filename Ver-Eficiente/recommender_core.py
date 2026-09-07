import math
import heapq

def prepare_data(ratings_data):
    """Matriz de utilidad."""
    utility_matrix = {}
    for r in ratings_data:
        u = r['user_id']
        m = r['movie_id']
        rating = r['rating']
        if u not in utility_matrix:
            utility_matrix[u] = {}
        utility_matrix[u][m] = rating
    return utility_matrix

def _cosine_similarity(dict1, dict2):
    """Cálculo optimizado usando Sets para la intersección."""
    # OPTIMIZACIÓN: Usar Sets en lugar de iterar listas reduce la complejidad 
    # y evita la búsqueda secuencial O(N).
    intersection = set(dict1.keys()) & set(dict2.keys())
    
    if not intersection:
        return 0.0
        
    dot_product = sum(dict1[m] * dict2[m] for m in intersection)
    norm_a = math.sqrt(sum(v**2 for v in dict1.values()))
    norm_b = math.sqrt(sum(v**2 for v in dict2.values()))
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)

def calculate_similarity(utility_matrix):
    """Cálculo de similitudes."""
    similarities = {}
    users = list(utility_matrix.keys())
    for u1 in users:
        similarities[u1] = {}
        for u2 in users:
            if u1 == u2:
                similarities[u1][u2] = 0.0
            else:
                similarities[u1][u2] = _cosine_similarity(utility_matrix[u1], utility_matrix[u2])
    return similarities

def recommend_movies(user_id, utility_matrix, user_similarities, movies_data, top_n=5):
    target_ratings = utility_matrix.get(user_id, {})
    
    # OPTIMIZACIÓN: HashMap (diccionario) para búsqueda rápida O(1) de películas.
    movie_dict = {m['movie_id']: m['title'] for m in movies_data}
    
    # OPTIMIZACIÓN: Set para encontrar películas no vistas
    unwatched_movies = set(movie_dict.keys()) - set(target_ratings.keys())
            
    predictions = []
    
    for movie in unwatched_movies:
        numerator = 0.0
        denominator = 0.0
        
        for other_user, ratings in utility_matrix.items():
            if other_user != user_id and movie in ratings:
                sim = user_similarities[user_id].get(other_user, 0.0)
                if sim > 0:
                    numerator += sim * ratings[movie]
                    denominator += sim
                    
        if denominator > 0:
            predicted_rating = numerator / denominator
            # Guardamos como tupla (rating, id) para que el heap sepa cómo ordenar
            predictions.append((predicted_rating, movie))
    
    # OPTIMIZACIÓN: Uso de Heap para mantener el Top N.
    # Evitamos ordenar toda la lista O(N log N) y pasamos a O(N log K)
    top_predictions = heapq.nlargest(top_n, predictions)
    
    # Mapeo rápido O(1) gracias al diccionario
    final_recommendations = [movie_dict[p[1]] for p in top_predictions]
                
    return final_recommendations