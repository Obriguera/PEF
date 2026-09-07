import math

def prepare_data(ratings_data):
    """Línea base: Matriz de utilidad usando diccionarios anidados."""
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
    """Cálculo ingenuo de similitud coseno iterando listas."""
    # Búsqueda secuencial ineficiente para encontrar intersección
    intersection = []
    for m in dict1:
        if m in dict2:
            intersection.append(m)
    
    if not intersection:
        return 0.0
        
    dot_product = sum(dict1[m] * dict2[m] for m in intersection)
    norm_a = math.sqrt(sum(v**2 for v in dict1.values()))
    norm_b = math.sqrt(sum(v**2 for v in dict2.values()))
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)

def calculate_similarity(utility_matrix):
    """Compara todos contra todos en O(N^2)."""
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
    
    # Búsqueda ingenua de películas no vistas
    all_movies = [m['movie_id'] for m in movies_data]
    unwatched_movies = []
    for m in all_movies:
        if m not in target_ratings:
            unwatched_movies.append(m)
            
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
            predictions.append({'movie_id': movie, 'pred_rating': predicted_rating})
    
    # Ineficiencia a propósito: Ordenamiento total O(N log N) para sacar solo el Top N
    predictions.sort(key=lambda x: x['pred_rating'], reverse=True)
    top_predictions = predictions[:top_n]
    
    # Ineficiencia a propósito: Búsqueda secuencial O(N) para mapear ID a Título
    final_recommendations = []
    for p in top_predictions:
        for m in movies_data:
            if m['movie_id'] == p['movie_id']:
                final_recommendations.append(m['title'])
                break
                
    return final_recommendations