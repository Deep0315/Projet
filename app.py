from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import requests
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin

TMDB_API_KEY = '4163e84b912dcfb237a0df9026441baa'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# Initialisation de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Vue de la page de connexion


# Define the User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    preferences = db.Column(db.String(255))


# Fonction de chargement de l'utilisateur pour Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Récupération des informations utilisateur
def get_user_info(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return {
            'username': user.username,
            'email': user.email,
            'preferences': user.preferences.split(',') if user.preferences else []
        }
    return None


# Vérification des identifiants de connexion
def check_credentials(username, password):
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        return user  # Retourne l'utilisateur si les identifiants sont corrects
    return None


@app.route('/')
def index():
    trending_url = f"https://api.themoviedb.org/3/trending/movie/week?api_key={TMDB_API_KEY}&language=fr-FR"
    trending_response = requests.get(trending_url)

    trending_movies = trending_response.json().get('results', []) if trending_response.status_code == 200 else []

    return render_template('index.html', trending_movies=trending_movies, active_page='home',
                           logged_in=current_user.is_authenticated)


@app.route('/profile')
@login_required
def profile():
    user_info = get_user_info(current_user.username)
    return render_template('profil.html', user_info=user_info)


@app.route('/connexion-account', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = check_credentials(username, password)

        if user:
            login_user(user)  # Utilise Flask-Login pour gérer la session
            return redirect(url_for('profile'))
        else:
            error = 'Nom d\'utilisateur ou mot de passe incorrect.'
            return render_template('connexion.html', error=error)
    return render_template('connexion.html')


@app.route('/create-account', methods=['POST'])
def create_account():
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']

    # Vérification de l'existence de l'utilisateur
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash("Le nom d'utilisateur existe déjà.", 'error')
        return redirect(url_for('login'))

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password_hash=hashed_password, email=email)

    db.session.add(new_user)
    db.session.commit()

    login_user(new_user)  # Connecte automatiquement l'utilisateur
    return redirect(url_for('profile'))


@app.route('/update_user_info', methods=['GET', 'POST'])
@login_required
def update_user_info():
    if request.method == 'POST':
        current_user.username = request.form['nom']
        current_user.email = request.form['email']
        new_password = request.form['password']
        confirm_password = request.form['confirm_password']

        if new_password:
            if new_password == confirm_password:
                current_user.password_hash = generate_password_hash(new_password)
            else:
                flash("Les mots de passe ne correspondent pas.", "error")
                return redirect(url_for('update_user_info'))

        db.session.commit()
        flash("Les informations ont été mises à jour avec succès!", "success")
        return redirect(url_for('profile'))

    return render_template('gestion_compte.html', user=current_user)


@app.route('/logout')
@login_required
def logout():
    logout_user()  # Utilise Flask-Login pour la déconnexion
    return redirect(url_for('index'))


@app.route('/search_movies')
def search_movies():
    query = request.args.get('query', '')
    if query:
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&language=fr-FR&query={query}"
        response = requests.get(search_url)
        movies = response.json().get('results', []) if response.status_code == 200 else []
        return jsonify(movies)
    return jsonify({'error': 'No query provided'})


@app.route('/Creation')
def create():
    return render_template('Inscription.html')


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


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)