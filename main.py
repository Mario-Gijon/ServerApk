from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import logging
import requests
import pandas as pd
import ast

# Configuración básica de logging
logging.basicConfig(level=logging.INFO) 
class MovieOnDB(BaseModel):
  idTmdb: int
  rate: int



app = FastAPI()
listOfAllMovies = []
moviesRated: List[MovieOnDB] = [MovieOnDB(idTmdb=502356, rate=4), MovieOnDB(idTmdb=1022789, rate=5)]
dfMovies = None
page = 1
# Lista de géneros con sus id y nombres
genres_list = [
  {"id": 28, "name": "Action"},
  {"id": 12, "name": "Adventure"},
  {"id": 16, "name": "Animation"},
  {"id": 35, "name": "Comedy"},
  {"id": 80, "name": "Crime"},
  {"id": 99, "name": "Documentary"},
  {"id": 18, "name": "Drama"},
  {"id": 10751, "name": "Family"},
  {"id": 14, "name": "Fantasy"},
  {"id": 36, "name": "History"},
  {"id": 27, "name": "Horror"},
  {"id": 10402, "name": "Music"},
  {"id": 9648, "name": "Mystery"},
  {"id": 10749, "name": "Romance"},
  {"id": 878, "name": "Science Fiction"},
  {"id": 10770, "name": "TV Movie"},
  {"id": 53, "name": "Thriller"},
  {"id": 10752, "name": "War"},
  {"id": 37, "name": "Western"}
]
genres_dict = {genre['id']: genre['name'] for genre in genres_list}





def getMoviesFromTmdbApi():
  global page
  global listOfAllMovies
  headers = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIyOTU1OGE0YmQxYmNlYWU5NTUwMmFlNjgzMDEwMzhlYiIsIm5iZiI6MTcxOTMyODAxMi43NTk2OTYsInN1YiI6IjY2MjFhZTRjYmIxMDU3MDE4OWQyNGY4MiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.B-Ad3TSiycU0-qSZsE8w4p9x2dpWZ0BP9WZaf5y0Xfw",
    "with_genres": "10751",
    "language": "en-US",
  }
  response = requests.get(
    f"https://api.themoviedb.org/3/discover/movie?with_genres=10751&page={page}&sort_by=popularity.desc",
    headers=headers
  )
  if response.status_code == 200:
    if page < 3:
      listOfAllMovies.extend(response.json()['results'])
      print(f"Page {page} success")
      page += 1
      return getMoviesFromTmdbApi()
    else:
      page = 1
      getCsv()
      return True
  else:
    print("Rejected connection")
    return False

def getCsv():
  dataset = []
  global listOfAllMovies
  for movie in listOfAllMovies:
    #keywords = next((item['keywords'] for item in listOfKeywords if item['id'] == movie_id), [])
    #reviews = next((item['results'] for item in listOfReviews if item['id'] == movie_id), [])
    
    
    movie_data = {
      'id': movie['id'],
      'title': movie['title'],
      #'overview': movie['overview'],
      #'release_date': movie['release_date'],
      'genre_id': movie['genre_ids'],
      'genre_name': [genres_dict[genre_id] for genre_id in movie['genre_ids']],
      #'vote_average': movie['vote_average'],
      #'vote_count': movie['vote_count'],
      #'keywords': [keyword['name'] for keyword in keywords],
      #'reviews': [{'author': review['author'], 'content': review['content'], 'rating': review['author_details'].get('rating')} for review in reviews]
    }
    dataset.append(movie_data)
  df = pd.DataFrame(dataset)
  df.to_csv('movies_dataset.csv', index=False)

def getUserProfile(moviesRated):
  global dfMovies
  # Leer el archivo CSV
  dfMovies = pd.read_csv('movies_dataset.csv')
  dfMovies['genre_id'] = dfMovies['genre_id'].apply(ast.literal_eval)
  # Extraer los IDs y las puntuaciones de las películas de la lista de objetos MovieOnDB
  movie_ids = [movie.idTmdb for movie in moviesRated]
  ratings = {movie.idTmdb: movie.rate for movie in moviesRated}
  # Filtrar el DataFrame para obtener solo las películas en movie_ids
  filteredMovies = dfMovies[dfMovies['id'].isin(movie_ids)]
  # Crear una lista de filas para cada película y su rating
  rows = []
  for _, row in filteredMovies.iterrows():
      for genre_id in row['genre_id']:
          rows.append({'genre_id': genre_id, 'rating': ratings[row['id']]})
  # Convertir las filas a un DataFrame
  dfRatings = pd.DataFrame(rows)
  # Agrupar por genre_id y sumar las puntuaciones
  gender_counts = dfRatings.groupby('genre_id')['rating'].sum().to_dict()
  # Imprimir el diccionario de puntuaciones por género
  return gender_counts

def getScores(userProfile):
  global dfMovies
  res = {}
  for index, row in dfMovies.iterrows():
      movie_id = row['id']
      score = 0
      for genre_id in row['genre_id']:
          if genre_id in userProfile:
              score += userProfile[genre_id]
      res[movie_id] = score
  return res


@app.post("/recommender")
def index(movies: List[MovieOnDB]):
  recommends = []
  
  userProfile = getUserProfile(moviesRated)
  scores = getScores(userProfile)
  # Imprimir los resultados para cada película
  sorted_movies = sorted(scores.items(), key=lambda x: x[1], reverse=True)
  for id, score in sorted_movies:
    print(str(id) + " - " + str(score))
    #logging.info(f"Received movie with idTmdb: {movie.idTmdb} and rate: {movie.rate}")
    recommend = {
      "id": str(id),
      "txt": f"Este es el texto de la película con id {id} y con un score de {score}."
    }
    recommends.append(recommend)
  
  #for movie in movies:
  #  logging.info(f"Received movie with idTmdb: {movie.idTmdb} and rate: {movie.rate}")
  #  recommend = {
  #      "id": str(movie.idTmdb),
  #      "txt": f"Este es el texto de la película con id {movie.idTmdb}. Le diste un rate de {movie.rate}."
  #  }
  #  recommends.append(recommend)

  
  return {"Recommends": recommends}

@app.get("/testAllMovies")
def allMovies():
  global listOfAllMovies
  return {
    "Recommends": listOfAllMovies
  }


if getMoviesFromTmdbApi():
  print("Conection to TMDB -> success")
  #moviesRated: List[MovieOnDB] = [MovieOnDB(idTmdb=502356, rate=4), MovieOnDB(idTmdb=1022789, rate=5)]
  #userProfile = userProfile(moviesRated)
  #scores = getScores(userProfile)
  # Imprimir los resultados para cada película
  #sorted_movies = sorted(scores.items(), key=lambda x: x[1], reverse=True)
  #for id, score in sorted_movies:
  #  print(str(id) + " - " + str(score))
    #title = dfMovies[dfMovies['id'] == movie_id]['title'].iloc[0]
    #print(f"Score for movie '{title}' (ID: {movie_id}): {score}")
  
else:
  print("Error getting films from TMDB API")
