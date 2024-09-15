
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import logging
import requests
import pandas as pd
import json

page = 1
listOfAllMovies = []

def getMoviesFromTmdbApi():
    # Define la página y la lista de películas
    page = 1
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIyOTU1OGE0YmQxYmNlYWU5NTUwMmFlNjgzMDEwMzhlYiIsIm5iZiI6MTcxOTQzMDQxNS42NDc5NTIsInN1YiI6IjY2MjFhZTRjYmIxMDU3MDE4OWQyNGY4MiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.NlNxso6YVdLFXXOZXZK9ZzEDXYuDD2HUuTz0P67eKXY",
    }

    # Hace la solicitud a la API
    response = requests.get(f"https://api.themoviedb.org/3/movie/popular?language=en-US&page={page}", headers=headers)
    
    # Verifica si la solicitud fue exitosa
    if response.status_code == 200:
        # Obtén el JSON de la respuesta
        movies_data = response.json()

        # Guarda la respuesta en un archivo JSON
        with open('responseTMDB.json', 'w', encoding='utf-8') as json_file:
            json.dump(movies_data, json_file, ensure_ascii=False, indent=4)

        print("Datos guardados en movies.json")
    else:
        print(f"Error al obtener los datos: {response.status_code}")

# Llama a la función
getMoviesFromTmdbApi()

