from flask import Flask, render_template, request
import requests

# Remplace par ta clé API TMDB
TMDB_API_KEY = '4163e84b912dcfb237a0df9026441baa'


def get_popular_movies():
    url = f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&language=fr-FR&page=1"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json().get('results', [])
    else:
        return []


app = Flask(__name__)


@app.route('/')
def index():
    # Récupérer les films en tendance
    trending_url = f"https://api.themoviedb.org/3/trending/movie/week?api_key={TMDB_API_KEY}&language=fr-FR"
    trending_response = requests.get(trending_url)

    if trending_response.status_code == 200:
        trending_movies = trending_response.json()['results']
    else:
        trending_movies = []

    return render_template('index.html', trending_movies=trending_movies)


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        query = request.form['query']  # Récupère la requête utilisateur depuis le formulaire
        url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&language=fr-FR&query={query}"
        response = requests.get(url)

        if response.status_code == 200:
            movies = response.json().get('results', [])
            return render_template('search_results.html', movies=movies, query=query)
        else:
            return f"Erreur dans la recherche : {response.status_code}"

    return render_template('search.html')


# Route pour les détails d'un film
@app.route('/movie/<int:movie_id>')
def movie_details(movie_id):
    # Récupérer les détails du film
    movie_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=fr-FR"
    movie_response = requests.get(movie_url)
    movie = movie_response.json()

    # Récupérer les vidéos (bandes-annonces)
    videos_url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={TMDB_API_KEY}&language=fr-FR"
    videos_response = requests.get(videos_url)
    videos = videos_response.json().get('results', [])

    # Retourner toutes les vidéos trouvées
    return render_template('movie_details.html', movie=movie, videos=videos)


if __name__ == '__main__':
    app.run(debug=True)
