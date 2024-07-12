from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import logging
import requests

# Configuración básica de logging
logging.basicConfig(level=logging.INFO) 

POPULAR_MOVIES_API = "https://api.themoviedb.org/3/discover/movie?include_adult=false&sort_by=popularity.desc"

app = FastAPI()
listOfAllMovies = []
page = 1

class MovieOnDB(BaseModel):
  idTmdb: int
  rate: int

def getMoviesFromTmdbApi():
  global page
  global listOfAllMovies
  headers = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIyOTU1OGE0YmQxYmNlYWU5NTUwMmFlNjgzMDEwMzhlYiIsIm5iZiI6MTcxOTMyODAxMi43NTk2OTYsInN1YiI6IjY2MjFhZTRjYmIxMDU3MDE4OWQyNGY4MiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.B-Ad3TSiycU0-qSZsE8w4p9x2dpWZ0BP9WZaf5y0Xfw",
    "with_genres": "10751",
    "language": "en-US",
    "page": str(page)
  }
  response = requests.get(POPULAR_MOVIES_API, headers=headers)
  if response.status_code == 200:
    if page < 190:
      listOfAllMovies.append(response.json())
      page = page+1
      return getMoviesFromTmdbApi()
    else:
      page = 1
      return True
  else:
    print("Rejected connection")
    return False


@app.post("/test")
def index(movies: List[MovieOnDB]):
  recommends = []
  """
  for movie in movies:
    logging.info(f"Received movie with idTmdb: {movie.idTmdb} and rate: {movie.rate}")
    recommend = {
        "id": str(movie.idTmdb),
        "txt": f"Este es el texto de la película con id {movie.idTmdb}. Le diste un rate de {movie.rate}."
    }
    recommends.append(recommend)

  """
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