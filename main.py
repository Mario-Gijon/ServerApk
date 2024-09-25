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
    {"id": 28, "name": "Acción"},
    {"id": 12, "name": "Aventura"},
    {"id": 16, "name": "Animación"},
    {"id": 35, "name": "Comedia"},
    {"id": 80, "name": "Crimen"},
    {"id": 99, "name": "Documental"},
    {"id": 18, "name": "Drama"},
    {"id": 10751, "name": "Familia"},
    {"id": 14, "name": "Fantasía"},
    {"id": 36, "name": "Historia"},
    {"id": 27, "name": "Terror"},
    {"id": 10402, "name": "Música"},
    {"id": 9648, "name": "Misterio"},
    {"id": 10749, "name": "Romance"},
    {"id": 878, "name": "Ciencia Ficción"},
    {"id": 10770, "name": "Película para TV"},
    {"id": 53, "name": "Suspenso"},
    {"id": 10752, "name": "Guerra"},
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
    movieData = {
      'id': movie['id'],
      'title': movie['title'],
      'genre_ids': movie['genre_ids'],
      'poster_path': IMG_PATH + movie['poster_path'] if movie['poster_path'] else 'No Image'
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
    filteredMovies = filteredMovies.explode('genre_ids')

    # Añadir las calificaciones correspondientes a cada fila de película
    filteredMovies['rating'] = filteredMovies['id'].map(ratings)

    # Agrupar por género y sumar las calificaciones para crear el perfil del usuario
    genderCounts = filteredMovies.groupby('genre_ids')['rating'].sum().to_dict()

    return genderCounts


def getScores(userProfile):
    global dfMovies

    # Crear una Serie de pandas a partir del userProfile para facilitar la operación de mapeo
    userProfileSeries = pd.Series(userProfile)

    # Expandir las filas por géneros
    dfExploded = dfMovies.explode('genre_ids')

    # Mapear los géneros al perfil de usuario y llenar con 0 donde no haya coincidencias
    dfExploded['genre_score'] = dfExploded['genre_ids'].map(userProfileSeries).fillna(0)

    # Agrupar por id de película, sumar los scores de los géneros y convertir en diccionario
    movieScores = dfExploded.groupby('id')['genre_score'].sum().astype(int).to_dict()

    return movieScores


def getExplanation(movie_id, userProfile, dfMovies):
    # Obtener los géneros de la película como una lista de enteros
    genres_ids = dfMovies.loc[dfMovies['id'] == movie_id, 'genre_ids'].values[0]
    
    # Si genres_ids es una cadena, convertimos a lista
    if isinstance(genres_ids, str):
        genres_ids = eval(genres_ids)

    # Obtener nombres de géneros y puntajes, usando comprensión de listas
    genre_names_scores = [
        (genres_dict.get(genre_id, "Desconocido"), userProfile.get(genre_id, 0))
        for genre_id in genres_ids
    ]

    # Filtrar géneros con puntajes positivos
    genre_names, score_details = zip(*[(name, score) for name, score in genre_names_scores if score > 0]) if genre_names_scores else ([], [])

    # Excluir el género "Familiar" (con id 10751)
    filtered_genres = [(name, score) for name, score in zip(genre_names, score_details) if name != "Familia"]

    # Generar la explicación
    if filtered_genres:
        # Tomar los dos primeros géneros más relevantes (excluyendo "Familia")
        top_genres = ' y '.join([name for name, score in filtered_genres[:2]])
        explanation = f"Porque está en las categorías de {top_genres}!"
    else:
        explanation = "Te recomendamos esta película debido a su popularidad."

    return explanation



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

    filtered_sorted_movies = filtered_sorted_movies[:10]

    # Crear la lista de recomendaciones con el formato {id, txt}
    recommends = [
        {
            "id": str(id),
            "txt": getExplanation(id, userProfile, dfMovies),
            "img": dfMovies.loc[dfMovies['id'] == id, 'poster_path'].values[0]
        }
        for id, score in filtered_sorted_movies
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
  
else:
  print("Error getting films from TMDB API")
