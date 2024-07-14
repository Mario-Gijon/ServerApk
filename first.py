import requests
import json
import numpy as np



#url = "https://api.themoviedb.org/3/movie/1022789?language=es-ES"


preferred_movies={502356:4,1022789:5}

headers = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJiMzY3OTljM2E5YzZmYjEyZTQzODg0MDQ2ODc5MWRlMiIsIm5iZiI6MTcyMDYxMTM0Ni4wNDQwODUsInN1YiI6IjY2OGU2Yzk5NGYwZDMwYjljOGQ0ODkxNSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.4HxMklEmzub1uk9saHuIw312SCJ4PpwX6t7eIHF1JiY"
}



#response = requests.get(url, headers=headers)



#print(response.text)

#json_data = json.loads(response.text)

#print(json_data["genres"][0]["id"])
#print(" ")
#print(json_data["genres"][1]["id"])



url2 = "https://api.themoviedb.org/3/discover/movie?with_genres=10751&page=1&sort_by=popularity.desc"
response2 = requests.get(url2, headers=headers)
#print(response2.text)

json_data2 = json.loads(response2.text)
#print(json_data2)

id_list=[]
title_list={}

for movie in json_data2["results"]:
    id_list.append((movie["id"],movie["original_title"]))
    title_list[movie["id"]]=movie["original_title"]

#print(id_list)
#print("-------------")
#print(title_list)


#for movie in json_data2["results"]:
    #print(movie["original_title"]+"\n")
    #print(movie["genre_ids"])
    #print("\n\n")



gender_counts={}

for m in preferred_movies:
    rating=preferred_movies[m]
    url = "https://api.themoviedb.org/3/movie/"+str(m)+"?language=es-ES"
    response = requests.get(url, headers=headers)
    json_data = json.loads(response.text)
#    print(json_data["genres"])
    for g in json_data["genres"]:
        if g["id"] in gender_counts:
            gender_counts[g["id"]]=gender_counts[g["id"]]+rating
        else:
            gender_counts[g["id"]]=rating
#print(gender_counts)

res={}
for n,title in id_list:
    score=0
    url = "https://api.themoviedb.org/3/movie/"+str(n)+"?language=es-ES"
    response1 = requests.get(url, headers=headers)
    json_data1 = json.loads(response1.text)
    #print(json_data1["genres"])
    #print("\n")
    for g in json_data1["genres"]:
        if g["id"] in gender_counts:
    	    score=score+gender_counts[g["id"]]
    #print(score)
    #print("  "+title)
    res[n]=score
    #print("\n")


keys = list(res.keys())
values = list(res.values())
sorted_value_index = np.argsort(values)
sorted_value_index2=[]
for val in sorted_value_index:
    sorted_value_index2.insert(0,val)
sorted_res = {keys[i]: values[i] for i in sorted_value_index2}


print(sorted_res)
#{16: 9, 10751: 9, 12: 9, 14: 4, 35: 9, 18: 5}