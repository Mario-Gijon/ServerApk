from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import logging
import requests
import pandas as pd
import ast
from fastapi.middleware.cors import CORSMiddleware
from typing import List

logging.basicConfig(level=logging.INFO) 
app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes (puedes especificar dominios específicos si lo prefieres)
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permitir todos los encabezados
)

class MovieOnDB(BaseModel):
  idTmdb: int
  rate: int

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
listOfAllMovies = []
dfMovies = None
page = 1
IMG_PATH = "https://image.tmdb.org/t/p/original"


def getMoviesFromTmdbApi():
  global page
  global listOfAllMovies
  headers = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIyOTU1OGE0YmQxYmNlYWU5NTUwMmFlNjgzMDEwMzhlYiIsIm5iZiI6MTcxOTMyODAxMi43NTk2OTYsInN1YiI6IjY2MjFhZTRjYmIxMDU3MDE4OWQyNGY4MiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.B-Ad3TSiycU0-qSZsE8w4p9x2dpWZ0BP9WZaf5y0Xfw",
  }
  response = requests.get(f"https://api.themoviedb.org/3/discover/movie?with_genres=10751&language=es-ES&page={page}&sort_by=popularity.desc",headers=headers)
  
  if response.status_code == 200:
    
    if page < 90:
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
  global dfMovies
  
  for movie in listOfAllMovies:
    if movie['poster_path'] is None:
      continue
    #keywords = next((item['keywords'] for item in listOfKeywords if item['id'] == movieId), [])
    #reviews = next((item['results'] for item in listOfReviews if item['id'] == movieId), [])
    movieData = {
      'id': movie['id'],
      'title': movie['title'],
      #'overview': movie['overview'],
      #'release_date': movie['release_date'],
      'genre_id': movie['genre_ids'],
      'genre_name': [genres_dict[genre_id] for genre_id in movie['genre_ids']],
      'poster_path': IMG_PATH + movie['poster_path'] if movie['poster_path'] else 'No Image'
      #'vote_average': movie['vote_average'],
      #'vote_count': movie['vote_count'],
      #'keywords': [keyword['name'] for keyword in keywords],
      #'reviews': [{'author': review['author'], 'content': review['content'], 'rating': review['author_details'].get('rating')} for review in reviews]
    }
    
    dataset.append(movieData)
    
  dfMovies = pd.DataFrame(dataset)
  dfMovies.to_csv('movies_dataset.csv', index=False)


def getUserProfile(moviesRated):
  global dfMovies

  # Extraer los ids de las películas valoradas y sus ratings
  movieIds = [movie.idTmdb for movie in moviesRated]
  ratings = {movie.idTmdb: movie.rate for movie in moviesRated}

  # Filtrar el DataFrame de películas para incluir solo las películas valoradas por el usuario
  filteredMovies = dfMovies[dfMovies['id'].isin(movieIds)].copy()

  # Expandir las listas de géneros en filas separadas
  filteredMovies = filteredMovies.explode('genre_id')

  # Añadir las calificaciones correspondientes a cada fila de película
  filteredMovies['rating'] = filteredMovies['id'].map(ratings)

  # Agrupar por género y sumar las calificaciones para crear el perfil del usuario
  genderCounts = filteredMovies.groupby('genre_id')['rating'].sum().to_dict()

  return genderCounts


def getScores(userProfile):
  global dfMovies

  # Crear una Serie de pandas a partir del userProfile para facilitar la operación de mapeo
  userProfileSeries = pd.Series(userProfile)

  # Expandir las filas por géneros
  dfExploded = dfMovies.explode('genre_id')

  # Mapear los géneros al perfil de usuario y llenar con 0 donde no haya coincidencias
  dfExploded['genre_score'] = dfExploded['genre_id'].map(userProfileSeries).fillna(0)

  # Agrupar por id de película, sumar los scores de los géneros y convertir en diccionario
  movieScores = dfExploded.groupby('id')['genre_score'].sum().astype(int).to_dict()

  return movieScores


@app.post("/recommender")
def index(moviesRated: List[MovieOnDB]):
  # Obtener el perfil del usuario basado en las películas calificadas
  userProfile = getUserProfile(moviesRated)
  # Obtener los puntajes de recomendación para todas las películas basándonos en el perfil del usuario
  scores = getScores(userProfile)
  
  # Convertir la lista de IDs de películas calificadas a un conjunto para un acceso más rápido
  ratedMoviesIds = {movie.idTmdb for movie in moviesRated}
  
  # Ordenar y filtrar las películas en una sola pasada
  filtered_sorted_movies = [
    (movieId, score) for movieId, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)
    if movieId not in ratedMoviesIds
  ]

  # Crear la lista de recomendaciones con el formato {id, txt}
  recommends = [
    {
      "id": str(id),
      "txt": f"Este es el texto de la película con id {id}, con un score de {score}.",
      "img": dfMovies.loc[dfMovies['id'] == id, 'poster_path'].values[0]
      }
    for id, score in filtered_sorted_movies[:10]
  ]
  
  # Devolver la lista de recomendaciones como JSON
  return {"Recommends": recommends}


@app.get("/testAllMovies")
def allMovies():
  global listOfAllMovies
  return {
    "Recommends": listOfAllMovies
  }


if getMoviesFromTmdbApi():
  print("Conection to TMDB -> success")
  
  #Esto es para poder hacer las comprobaciones usando directamente la terminal y no el servidor
  
  recommends = []
  moviesRated: List[MovieOnDB] = [
    MovieOnDB(idTmdb=502356, rate=4),
    MovieOnDB(idTmdb=1022789, rate=5),
    MovieOnDB(idTmdb=350650, rate=2),
    MovieOnDB(idTmdb=10957, rate=1),
    MovieOnDB(idTmdb=25741, rate=5),
    MovieOnDB(idTmdb=326215, rate=5),
    MovieOnDB(idTmdb=422803, rate=2),
    MovieOnDB(idTmdb=587562, rate=4),
    MovieOnDB(idTmdb=10837, rate=3),
    MovieOnDB(idTmdb=12903, rate=3),
    ]
  
  userProfile = getUserProfile(moviesRated)
  scores = getScores(userProfile)
  
  sortedMovies = sorted(scores.items(), key=lambda x: x[1], reverse=True)
  
  for id, score in sortedMovies[:10]:
    #print(str(id) + " - " + str(score))
    recommend = {
      "id": str(id),
      "txt": f"Este es el texto de la película con id {id} y con un score de {score}.",
      "img": dfMovies.loc[dfMovies['id'] == id, 'poster_path'].values[0]
    }
    recommends.append(recommend)
    
  print(recommends)
 
  
else:
  print("Error getting films from TMDB API")
