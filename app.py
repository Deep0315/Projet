from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import requests
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin

# Configuration de l'application Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# Configuration de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Vue pour rediriger si non authentifié

# Clé API pour TMDB
TMDB_API_KEY = '4163e84b912dcfb237a0df9026441baa'


# ==============================================
# Modèles de base de données
# ==============================================

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    preferences = db.Column(db.String(255))


class MovieHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())


# ==============================================
# Fonctions utilitaires
# ==============================================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def get_user_info(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return {
            'username': user.username,
            'email': user.email,
            'preferences': user.preferences.split(',') if user.preferences else []
        }
    return None


def check_credentials(username, password):
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        return user
    return None


# ==============================================
# Routes liées à l'authentification
# ==============================================

@app.route('/connexion-account', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = check_credentials(username, password)
        if user:
            login_user(user)
            return redirect(url_for('profil'))
        flash('Nom d\'utilisateur ou mot de passe incorrect.', 'danger')
    return render_template('connexion.html')


@app.route('/create-account', methods=['POST'])
def create_account():
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']

    if User.query.filter_by(username=username).first():
        flash("Le nom d'utilisateur existe déjà.", 'error')
        return redirect(url_for('login'))

    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password_hash=hashed_password, email=email)
    db.session.add(new_user)
    db.session.commit()

    login_user(new_user)
    return redirect(url_for('profil'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# ==============================================
# Routes liées à l'utilisateur
# ==============================================

@app.route('/profile')
@login_required
def profil():
    user_info = get_user_info(current_user.username)
    page = request.args.get('page', 1, type=int)
    per_page = 5

    history_query = MovieHistory.query.filter_by(user_id=current_user.id).order_by(MovieHistory.timestamp.desc())
    paginated_history = history_query.paginate(page=page, per_page=per_page)

    return render_template(
        'profil.html',
        user_info=user_info,
        history=paginated_history.items,
        pagination=paginated_history,
        logged_in=current_user.is_authenticated,
        active_page='profile'
    )


@app.route('/update_user_info', methods=['GET', 'POST'])
@login_required
def update_user_info():
    if request.method == 'POST':
        if request.form['nom']:
            current_user.username = request.form['nom']
        if request.form['email']:
            current_user.email = request.form['email']

        new_password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if new_password or confirm_password:
            if new_password == confirm_password:
                current_user.password_hash = generate_password_hash(new_password)
            else:
                flash("Les mots de passe ne correspondent pas.", "error")
                return redirect(url_for('update_user_info'))

        db.session.commit()
        flash("Les informations ont été mises à jour avec succès!", "success")
        return redirect(url_for('profil'))

    return render_template('gestion_compte.html', user=current_user)


# ==============================================
# Routes liées aux films
# ==============================================

@app.route('/')
def index():
    trending_url = f"https://api.themoviedb.org/3/trending/movie/week?api_key={TMDB_API_KEY}&language=fr-FR"
    trending_movies = requests.get(trending_url).json().get('results', [])
    return render_template('index.html', trending_movies=trending_movies, active_page='home',
                           logged_in=current_user.is_authenticated)


@app.route('/movie/<int:movie_id>')
def movie_details(movie_id):
    movie_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=fr-FR"
    movie = requests.get(movie_url).json()

    if current_user.is_authenticated:
        if not MovieHistory.query.filter_by(user_id=current_user.id, movie_id=movie_id).first():
            new_history = MovieHistory(user_id=current_user.id, movie_id=movie_id, title=movie.get('title', ''))
            db.session.add(new_history)
            db.session.commit()

    return render_template('movie_details.html', movie=movie, logged_in=current_user.is_authenticated)


@app.route('/search')
def search():
    return render_template('search_results.html', logged_in=current_user.is_authenticated, active_page='search')


@app.route('/search_movies')
def search_movies():
    query = request.args.get('query', '')
    if query:
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&language=fr-FR&query={query}"
        movies = requests.get(search_url).json().get('results', [])
        return jsonify(movies)
    return jsonify({'error': 'No query provided'})


@app.route('/Creation')
def create():
    return render_template('Inscription.html')


# ==============================================
# Initialisation de la base de données
# ==============================================

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
