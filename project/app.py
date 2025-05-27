from flask import Flask, request, jsonify
import pickle
import requests
from flask_cors import CORS
import pandas as pd
import difflib

app = Flask(__name__)
CORS(app)

# Load movie data
movies = pickle.load(open(r"C:\Users\hp\Desktop\project\movie_list.pkl", 'rb'))
similarity = pickle.load(open(r"C:\Users\hp\Desktop\project\similarity.pkl", 'rb'))

# Fetch movie details (poster and overview) using TMDb API
def fetch_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US"
    data = requests.get(url).json()
    poster_path = data.get('poster_path')
    overview = data.get('overview', "")
    genres = data.get('genres', "")
    vote_average = data.get('vote_average',"")
    poster_url = f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else ""
    return poster_url, overview, genres,vote_average

# Recommend movies with fuzzy title matching
def recommend(movie):
    # Find the closest match from the title list
    close_matches = difflib.get_close_matches(movie, movies['title'].tolist(), n=1, cutoff=0.5)

    if not close_matches:
        return {
            'error': 'Movie not found. Please check the spelling or try a different title.'
        }

    matched_title = close_matches[0]
    index = movies[movies['title'] == matched_title].index[0]
    movie_id = movies.iloc[index].movie_id

    poster, overview, genres, vote_average = fetch_movie_details(movie_id)

    searched_movie = {
        'title': matched_title,
        'poster': poster,
        'overview': overview,
        'genres': genres,
        'vote_average' : vote_average
    }

    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended = []

    for i in distances[1:13]:  # top 6 excluding itself
        rec_movie_id = movies.iloc[i[0]].movie_id
        rec_poster, rec_overview,_,rec_vote_average = fetch_movie_details(rec_movie_id)
        recommended.append({
            'title': movies.iloc[i[0]].title,
            'poster': rec_poster,
            'overview': rec_overview,
            'vote_average': rec_vote_average
        })

    return {
        'searched': searched_movie,
        'recommended': recommended
    }

# API route
@app.route("/recommend", methods=["POST"])
def recommend_movies():
    data = request.get_json()
    movie_name = data.get('movie')
    result = recommend(movie_name)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
