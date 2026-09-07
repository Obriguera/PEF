# analysis_utils.py

def analyze_popularity(ratings_data, movies_data):
    """Calcula la popularidad iterando manualmente (Baseline)."""
    # Conteo manual usando un diccionario simple
    movie_counts = {}
    for r in ratings_data:
        m_id = r['movie_id']
        if m_id in movie_counts:
            movie_counts[m_id] += 1
        else:
            movie_counts[m_id] = 1
            
    popularity_list = []
    for m_id, count in movie_counts.items():
        title = ""
        # Búsqueda secuencial O(N) del título
        for m in movies_data:
            if m['movie_id'] == m_id:
                title = m['title']
                break
        popularity_list.append({'title': title, 'count': count})
        
    # Ordenamiento completo O(N log N)
    popularity_list.sort(key=lambda x: x['count'], reverse=True)
    
    # Obtener el Top 5 de forma ingenua
    top_5 = popularity_list[:5]
    
    return top_5