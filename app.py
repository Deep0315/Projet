from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import requests
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker

TMDB_API_KEY = '4163e84b912dcfb237a0df9026441baa'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    preferences = db.Column(db.String(255))

# Modify the get_user_info function to retrieve the user's information from the database
def get_user_info(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return {
            'username': user.username,
            'email': user.email,
            'preferences': user.preferences.split(',') if user.preferences else []
        }
    else:
        return None

def check_credentials(username, password):
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        return True
    else:
        return False

@app.route('/')
def index():
    trending_url = f"https://api.themoviedb.org/3/trending/movie/week?api_key={TMDB_API_KEY}&language=fr-FR"
    trending_response = requests.get(trending_url)

    if trending_response.status_code == 200:
        trending_movies = trending_response.json()['results']
    else:
        trending_movies = []

    return render_template('index.html', trending_movies=trending_movies, active_page='home')

@app.route('/profile')
def profile():
    if 'username' in session:
        # Récupérer les informations de profil de l'utilisateur à partir de la base de données ou d'un autre système de stockage sécurisé
        user_info = get_user_info(session['username'])
        return render_template('profile.html', user_info=user_info)
    else:
        flash('Vous devez être connecté pour accéder à cette page. Merci de vous connecter ou vous inscrire!')
        return redirect(url_for('index'))

@app.route('/connexion-account', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Récupérer les informations d'identification de l'utilisateur à partir du formulaire
        username = request.form['username']
        password = request.form['password']

        # Vérifier les informations d'identification de l'utilisateur en les comparant aux informations stockées dans la base de données ou dans un autre système de stockage sécurisé
        if check_credentials(username, request.form['password']):
            # Stocker le nom d'utilisateur dans la session de l'utilisateur
            session['username'] = username

            # Rediriger l'utilisateur vers la page de profil
            return redirect(url_for('profile'))
        else:
            # Afficher un message d'erreur sur la page de connexion
            error = 'Nom d\'utilisateur ou mot de passe incorrect.'
            return render_template('connexion.html', error=error)
    else:
        return render_template('connexion.html')


@app.route('/create-account', methods=['POST'])
def create_account():
    # Récupérer les données du formulaire
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']

    # Vérifier si l'utilisateur existe déjà dans la base de données
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        # L'utilisateur existe déjà, gérer l'erreur ici
        return "Username already exists"

    # Hasher le mot de passe
    hashed_password = generate_password_hash(password)

    # Créer un nouvel utilisateur
    new_user = User(username=username, password_hash=hashed_password, email=email)

    # Ajouter l'utilisateur à la base de données
    db.session.add(new_user)
    db.session.commit()

    # Stocker le nom d'utilisateur dans la session de l'utilisateur
    session['username'] = username

    # Rediriger l'utilisateur vers la page de profil
    return redirect(url_for('profile'))

@app.route('/search')
def search_page():
    return render_template('search_results.html', active_page='search')

@app.route('/logout')
def logout():
    # Supprimer les données de session de l'utilisateur
    session.pop('username', None)

    # Rediriger l'utilisateur vers la page d'accueil
    return redirect(url_for('index'))

@app.route('/search_movies')
def search_movies():
    query = request.args.get('query', '')
    if query:
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&language=fr-FR&query={query}"
        response = requests.get(search_url)
        if response.status_code == 200:
            movies = response.json().get('results', [])
            return jsonify(movies)
    return jsonify({'error': 'No query provided'})

@app.route('/Creation')
def create():
    return render_template('Creation.html')

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
        if collection_response.status_code == 200:
            collection = collection_response.json()
        else:
            collection = None

    return render_template('movie_details.html', movie=movie, videos=videos, recommendations=recommendations,
                           collection=collection)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)