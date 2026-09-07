MOVIES_DATA = [
    {'movie_id': 1, 'title': "Joker 2", 'genre': "Musical", 'duration': 120},
    {'movie_id': 2, 'title': 'Interstellar', 'genre': 'Science Fiction', 'duration': 169},
    {'movie_id': 3, 'title': 'The Godfather', 'genre': 'Crime|Drama', 'duration': 175},
    {'movie_id': 4, 'title': 'Toy Story', 'genre': 'Animation|Family', 'duration': 81},
    {'movie_id': 5, 'title': 'Avatar', 'genre': 'Science Fiction|Adventure', 'duration': 162},
    {'movie_id': 6, 'title': 'Inception', 'genre': 'Science Fiction|Thriller', 'duration': 148},
    {'movie_id': 7, 'title': 'The Dark Knight', 'genre': 'Action|Crime|Drama', 'duration': 152},
    {'movie_id': 8, 'title': 'Pulp Fiction', 'genre': 'Crime|Drama', 'duration': 154},
    {'movie_id': 9, 'title': 'Forrest Gump', 'genre': 'Drama|Romance', 'duration': 142},
    {'movie_id': 10, 'title': 'The Matrix', 'genre': 'Science Fiction|Action', 'duration': 136},
    {'movie_id': 11, 'title': 'The Shawshank Redemption', 'genre': 'Drama', 'duration': 142},
    {'movie_id': 12, 'title': 'Fight Club', 'genre': 'Drama|Thriller', 'duration': 139},
    {'movie_id': 13, 'title': 'Finding Nemo', 'genre': 'Animation|Family|Adventure', 'duration': 100},
    {'movie_id': 14, 'title': 'The Lion King', 'genre': 'Animation|Family|Drama', 'duration': 88},
    {'movie_id': 15, 'title': 'Frozen', 'genre': 'Animation|Family|Musical', 'duration': 102},
    {'movie_id': 16, 'title': 'Blade Runner 2049', 'genre': 'Science Fiction|Thriller', 'duration': 164},
    {'movie_id': 17, 'title': 'Parasite', 'genre': 'Drama|Thriller', 'duration': 132},
    {'movie_id': 18, 'title': 'The Avengers', 'genre': 'Action|Adventure|Science Fiction', 'duration': 143},
    {'movie_id': 19, 'title': 'Joker', 'genre': 'Crime|Drama|Thriller', 'duration': 122},
    {'movie_id': 20, 'title': 'La La Land', 'genre': 'Musical|Romance|Drama', 'duration': 128}
]

USERS_DATA = [
    {'user_id': 101, 'name': 'Ana'},
    {'user_id': 102, 'name': 'Beto'},
    {'user_id': 103, 'name': 'Carlos'},
    {'user_id': 104, 'name': 'Diana'},
    {'user_id': 105, 'name': 'Emma'},
    {'user_id': 106, 'name': 'Frank'},
    {'user_id': 107, 'name': 'Grace'},
    {'user_id': 108, 'name': 'Henry'},
    {'user_id': 109, 'name': 'Isabel'},
    {'user_id': 110, 'name': 'Jack'}
]

RATINGS_DATA = [
    # Ana's ratings (likes musicals, sci-fi, and family movies)
    {'user_id': 101, 'movie_id': 1, 'rating': 5.0}, 
    {'user_id': 101, 'movie_id': 2, 'rating': 4.0}, 
    {'user_id': 101, 'movie_id': 4, 'rating': 3.5},
    {'user_id': 101, 'movie_id': 6, 'rating': 4.5},
    {'user_id': 101, 'movie_id': 13, 'rating': 4.0},
    {'user_id': 101, 'movie_id': 15, 'rating': 5.0},
    {'user_id': 101, 'movie_id': 20, 'rating': 5.0},
    
    # Beto's ratings (likes crime and drama)
    {'user_id': 102, 'movie_id': 1, 'rating': 4.5}, 
    {'user_id': 102, 'movie_id': 2, 'rating': 2.0},
    {'user_id': 102, 'movie_id': 3, 'rating': 5.0}, 
    {'user_id': 102, 'movie_id': 7, 'rating': 5.0},
    {'user_id': 102, 'movie_id': 8, 'rating': 4.5},
    {'user_id': 102, 'movie_id': 11, 'rating': 5.0},
    {'user_id': 102, 'movie_id': 12, 'rating': 4.0},
    {'user_id': 102, 'movie_id': 19, 'rating': 4.5},
    
    # Carlos's ratings (likes sci-fi and action)
    {'user_id': 103, 'movie_id': 2, 'rating': 4.5}, 
    {'user_id': 103, 'movie_id': 3, 'rating': 3.0}, 
    {'user_id': 103, 'movie_id': 5, 'rating': 5.0},
    {'user_id': 103, 'movie_id': 6, 'rating': 5.0},
    {'user_id': 103, 'movie_id': 7, 'rating': 4.5},
    {'user_id': 103, 'movie_id': 10, 'rating': 5.0},
    {'user_id': 103, 'movie_id': 16, 'rating': 4.0},
    {'user_id': 103, 'movie_id': 18, 'rating': 4.5},
    
    # Diana's ratings (likes animation and family)
    {'user_id': 104, 'movie_id': 1, 'rating': 4.5},
    {'user_id': 104, 'movie_id': 4, 'rating': 5.0}, 
    {'user_id': 104, 'movie_id': 5, 'rating': 4.0}, 
    {'user_id': 104, 'movie_id': 9, 'rating': 4.5},
    {'user_id': 104, 'movie_id': 13, 'rating': 5.0},
    {'user_id': 104, 'movie_id': 14, 'rating': 5.0},
    {'user_id': 104, 'movie_id': 15, 'rating': 4.5},
    {'user_id': 104, 'movie_id': 20, 'rating': 4.0},
    
    # Emma's ratings (likes drama and thrillers)
    {'user_id': 105, 'movie_id': 1, 'rating': 4.0},
    {'user_id': 105, 'movie_id': 3, 'rating': 5.0},
    {'user_id': 105, 'movie_id': 8, 'rating': 4.5},
    {'user_id': 105, 'movie_id': 9, 'rating': 5.0},
    {'user_id': 105, 'movie_id': 11, 'rating': 5.0},
    {'user_id': 105, 'movie_id': 12, 'rating': 4.0},
    {'user_id': 105, 'movie_id': 17, 'rating': 5.0},
    {'user_id': 105, 'movie_id': 19, 'rating': 4.5},
    
    # Frank's ratings (likes sci-fi and action)
    {'user_id': 106, 'movie_id': 1, 'rating': 4.5},
    {'user_id': 106, 'movie_id': 2, 'rating': 5.0},
    {'user_id': 106, 'movie_id': 5, 'rating': 4.5},
    {'user_id': 106, 'movie_id': 6, 'rating': 5.0},
    {'user_id': 106, 'movie_id': 7, 'rating': 4.0},
    {'user_id': 106, 'movie_id': 10, 'rating': 5.0},
    {'user_id': 106, 'movie_id': 16, 'rating': 4.5},
    {'user_id': 106, 'movie_id': 18, 'rating': 4.0},
    
    # Grace's ratings (likes animation and musicals)
    {'user_id': 107, 'movie_id': 1, 'rating': 5.0},
    {'user_id': 107, 'movie_id': 4, 'rating': 4.5},
    {'user_id': 107, 'movie_id': 13, 'rating': 5.0},
    {'user_id': 107, 'movie_id': 14, 'rating': 4.5},
    {'user_id': 107, 'movie_id': 15, 'rating': 5.0},
    {'user_id': 107, 'movie_id': 20, 'rating': 5.0},
    
    # Henry's ratings (likes crime and thrillers)
    {'user_id': 108, 'movie_id': 1, 'rating': 4.5},
    {'user_id': 108, 'movie_id': 3, 'rating': 4.5},
    {'user_id': 108, 'movie_id': 7, 'rating': 5.0},
    {'user_id': 108, 'movie_id': 8, 'rating': 5.0},
    {'user_id': 108, 'movie_id': 12, 'rating': 4.5},
    {'user_id': 108, 'movie_id': 17, 'rating': 4.0},
    {'user_id': 108, 'movie_id': 19, 'rating': 5.0},
    
    # Isabel's ratings (diverse taste)
    {'user_id': 109, 'movie_id': 1, 'rating': 5.0},
    {'user_id': 109, 'movie_id': 2, 'rating': 4.0},
    {'user_id': 109, 'movie_id': 6, 'rating': 4.5},
    {'user_id': 109, 'movie_id': 9, 'rating': 5.0},
    {'user_id': 109, 'movie_id': 11, 'rating': 4.5},
    {'user_id': 109, 'movie_id': 14, 'rating': 4.0},
    {'user_id': 109, 'movie_id': 17, 'rating': 5.0},
    {'user_id': 109, 'movie_id': 20, 'rating': 4.0},
    
    # Jack's ratings (likes action and adventure)
    {'user_id': 110, 'movie_id': 1, 'rating': 4.0},
    {'user_id': 110, 'movie_id': 5, 'rating': 5.0},
    {'user_id': 110, 'movie_id': 7, 'rating': 5.0},
    {'user_id': 110, 'movie_id': 10, 'rating': 4.5},
    {'user_id': 110, 'movie_id': 18, 'rating': 5.0},
    {'user_id': 110, 'movie_id': 6, 'rating': 4.0},
    {'user_id': 110, 'movie_id': 16, 'rating': 3.5}
]