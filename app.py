from flask import Flask, render_template, request, jsonify
import requests

TMDB_API_KEY = '4163e84b912dcfb237a0df9026441baa'

app = Flask(__name__)


# Route pour la page d'accueil
@app.route('/')
def index():
    trending_url = f"https://api.themoviedb.org/3/trending/movie/week?api_key={TMDB_API_KEY}&language=fr-FR"
    trending_response = requests.get(trending_url)

    if trending_response.status_code == 200:
        trending_movies = trending_response.json()['results']
    else:
        trending_movies = []

    return render_template('index.html', trending_movies=trending_movies, active_page='home')


# Route pour la recherche
@app.route('/search')
def search_page():
    return render_template('search_results.html', active_page='search')


# Recherche des films via l'API TMDB en temps réel
@app.route('/search_movies')
def search_movies():
    query = request.args.get('query', '')
    if query:
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&language=fr-FR&query={query}"
        response = requests.get(search_url)
        if response.status_code == 200:
            movies = response.json().get('results', [])
            return jsonify(movies)
    return jsonify([])


# Route pour les détails d'un film
@app.route('/movie/<int:movie_id>')
def movie_details(movie_id):
    movie_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=fr-FR"
    movie_response = requests.get(movie_url)
    movie = movie_response.json()

    videos_url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={TMDB_API_KEY}&language=fr-FR"
    videos_response = requests.get(videos_url)
    videos = videos_response.json().get('results', [])

    return render_template('movie_details.html', movie=movie, videos=videos)


if __name__ == '__main__':
    app.run(debug=True)
