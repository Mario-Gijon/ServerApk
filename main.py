from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import logging
import requests
import pandas as pd
import ast

logging.basicConfig(level=logging.INFO) 
app = FastAPI()

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


def getMoviesFromTmdbApi():
  global page
  global listOfAllMovies
  headers = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIyOTU1OGE0YmQxYmNlYWU5NTUwMmFlNjgzMDEwMzhlYiIsIm5iZiI6MTcxOTMyODAxMi43NTk2OTYsInN1YiI6IjY2MjFhZTRjYmIxMDU3MDE4OWQyNGY4MiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.B-Ad3TSiycU0-qSZsE8w4p9x2dpWZ0BP9WZaf5y0Xfw",
    "with_genres": "10751",
    "language": "en-US",
  }
  
  response = requests.get(f"https://api.themoviedb.org/3/discover/movie?with_genres=10751&page={page}&sort_by=popularity.desc",headers=headers)
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
    #keywords = next((item['keywords'] for item in listOfKeywords if item['id'] == movieId), [])
    #reviews = next((item['results'] for item in listOfReviews if item['id'] == movieId), [])
    movieData = {
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
    
    dataset.append(movieData)
    
  dfMovies = pd.DataFrame(dataset)
  dfMovies.to_csv('movies_dataset.csv', index=False)


def getUserProfile(moviesRated):
  global dfMovies
  rows = []

  movieIds = [movie.idTmdb for movie in moviesRated]
  ratings = {movie.idTmdb: movie.rate for movie in moviesRated}

  filteredMovies = dfMovies[dfMovies['id'].isin(movieIds)]

  for _, row in filteredMovies.iterrows():
    for genre_id in row['genre_id']:
      rows.append({'genre_id': genre_id, 'rating': ratings[row['id']]})

  dfRatings = pd.DataFrame(rows)
  genderCounts = dfRatings.groupby('genre_id')['rating'].sum().to_dict()

  return genderCounts


def getScores(userProfile):
  global dfMovies
  res = {}
  
  for index, row in dfMovies.iterrows():
    movieId = row['id']
    score = 0
    
    for genreId in row['genre_id']:
      if genreId in userProfile:
        score += userProfile[genreId]
        
    res[movieId] = score
    
  return res


@app.post("/recommender")
def index(moviesRated: List[MovieOnDB]):
  recommends = []
  
  userProfile = getUserProfile(moviesRated)
  scores = getScores(userProfile)
  
  sortedMovies = sorted(scores.items(), key=lambda x: x[1], reverse=True)
  filteredMovies = [(movieId, score) for movieId, score in sortedMovies if not any(movieId == rated.idTmdb for rated in moviesRated)]

  for id, score in filteredMovies:
    #print(str(id) + " - " + str(score))
    recommend = {
      "id": str(id),
      "txt": f"Este es el texto de la película con id {id}, con un score de {score}."
    }  
    recommends.append(recommend)
  
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
  """
  recommends = []
  moviesRated: List[MovieOnDB] = [MovieOnDB(idTmdb=502356, rate=4), MovieOnDB(idTmdb=1022789, rate=5)]
  
  userProfile = getUserProfile(moviesRated)
  scores = getScores(userProfile)
  
  sortedMovies = sorted(scores.items(), key=lambda x: x[1], reverse=True)
  for id, score in sortedMovies:
    print(str(id) + " - " + str(score))
    recommend = {
      "id": str(id),
      "txt": f"Este es el texto de la película con id {id} y con un score de {score}."
    }
    recommends.append(recommend)

  print(recommends)
  """
  
else:
  print("Error getting films from TMDB API")
