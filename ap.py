
@app.route('/movie/<int:movie_id>')
def movie_details(movie_id):
    movie_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=fr-FR"
    movie_response = requests.get(movie_url)
    movie = movie_response.json()

    videos_url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={TMDB_API_KEY}&language=fr-FR"
    videos_response = requests.get(videos_url)
    videos = videos_response.json().get('results', [])

    recommendations_url = f"https://api.themoviedb.org/3/movie/{movie_id}/recommendations?api_key={TMDB_API_KEY}&language=fr-FR"
    recommendations_response = requests.get(recommendations_url)
    recommendations = recommendations_response.json().get('results', [])

    collection = None
    if 'belongs_to_collection' in movie and movie['belongs_to_collection']:
        collection_id = movie['belongs_to_collection']['id']
        collection_url = f"https://api.themoviedb.org/3/collection/{collection_id}?api_key={TMDB_API_KEY}&language=fr-FR"
        collection_response = requests.get(collection_url)
        collection = collection_response.json() if collection_response.status_code == 200 else None

    return render_template('movie_details.html', movie=movie, videos=videos, recommendations=recommendations,
                           collection=collection, logged_in=current_user.is_authenticated)

