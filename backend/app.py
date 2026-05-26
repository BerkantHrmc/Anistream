from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Profile, SurveyAnswer, LikedAnime, WatchedAnime
from config import Config
from recommender import Recommender
from flasgger import Swagger
import os
import csv

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
app.config.from_object(Config)
swagger = Swagger(app)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Initialize Recommender pointing to the models folder
recommender = Recommender(models_dir=os.path.join(os.path.dirname(__file__), '../models'))

@app.context_processor
def inject_notification():
    """Inject a single anime recommendation as a notification for authenticated users."""
    from flask import session
    from flask_login import current_user
    from models import Rating, Anime
    
    notification_anime = None
    if current_user.is_authenticated:
        # Check session for cached notification
        if 'notification_anime' in session:
            notification_anime = session['notification_anime']
        else:
            # Only show notification if user has rated at least 1 anime
            rating_count = Rating.query.filter_by(user_id=current_user.id).count()
            if rating_count > 0:
                recs = recommender.get_recommendations(user_id=current_user.id, num_recs=5)
                if recs:
                    import random
                    pick = random.choice(recs[:5])
                    # Store minimal data in session
                    notification_anime = pick
                    session['notification_anime'] = pick
                    
    return dict(notification_anime=notification_anime)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Kullanıcı Kayıt Endpoint'i
    ---
    tags:
      - Auth
    parameters:
      - name: username
        in: formData
        type: string
        required: true
      - name: email
        in: formData
        type: string
        required: true
      - name: password
        in: formData
        type: string
        required: true
    responses:
      200:
        description: Kayıt sayfası veya başarılı kayıt sonrası yönlendirme
    """
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash('Username or Email already exists.')
            return redirect(url_for('register'))
            
        if len(password) < 6:
            flash('Password must be at least 6 characters long.')
            return redirect(url_for('register'))
            
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        # Create empty profile
        profile = Profile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('survey'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Kullanıcı Giriş Endpoint'i
    ---
    tags:
      - Auth
    parameters:
      - name: username
        in: formData
        type: string
        required: true
      - name: password
        in: formData
        type: string
        required: true
    responses:
      200:
        description: Giriş sayfası veya başarılı giriş sonrası yönlendirme
    """
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            if not user.survey:
                return redirect(url_for('survey'))
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password.')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    from flask import session
    session.pop('notification_anime', None)
    logout_user()
    return redirect(url_for('login'))

@app.route('/survey', methods=['GET', 'POST'])
@login_required
def survey():
    if request.method == 'POST':
        genres = request.form.getlist('genres')
        min_score = request.form.get('min_score')
        max_episodes = request.form.get('max_episodes')
        preferred_year = request.form.get('preferred_year')
        
        genres_str = ",".join(genres) if genres else ""
        
        survey_ans = SurveyAnswer.query.filter_by(user_id=current_user.id).first()
        if not survey_ans:
            survey_ans = SurveyAnswer(user_id=current_user.id)
            db.session.add(survey_ans)
            
        survey_ans.genres = genres_str
        survey_ans.min_score = float(min_score) if min_score else None
        survey_ans.max_episodes = int(max_episodes) if max_episodes else None
        survey_ans.preferred_year = int(preferred_year) if preferred_year else None
        
        db.session.commit()
        flash('Survey saved! Welcome to your personalized dashboard.')
        return redirect(url_for('home'))
        
    return render_template('survey.html')

@app.route('/home')
@login_required
def home():
    # Fetch survey and liked items
    survey_ans = current_user.survey
    liked_anime_ids = [la.anime_id for la in current_user.liked_anime]
    
    recommendations = recommender.get_recommendations(
        user_id=current_user.id,
        num_recs=12,
        survey_data=survey_ans,
        liked_anime_ids=liked_anime_ids
    )
    
    unrated_recommendations = recommender.get_unrated_recommendations(
        user_id=current_user.id,
        num_recs=12,
        survey_data=survey_ans,
        liked_anime_ids=liked_anime_ids
    )
    
    hero_anime = recommendations[0] if recommendations else None
    slider_anime = recommendations[1:] if len(recommendations) > 1 else recommendations
    
    from models import Anime, Rating
    top_animes = Anime.query.filter(Anime.score != None, Anime.scored_by >= 1000).order_by(Anime.score.desc()).limit(10).all()
    
    # "If you liked this, you might also like these" - Similar recommendations from top 2 recent high-rated anime
    because_you_liked = []
    latest_high_rated_list = Rating.query.filter(
        Rating.user_id == current_user.id,
        Rating.rating >= 7
    ).order_by(Rating.timestamp.desc()).limit(2).all()
    
    for rating_item in latest_high_rated_list:
        source_anime = Anime.query.filter_by(mal_id=rating_item.anime_id).first()
        if source_anime:
            sim_data = recommender.get_similar_items(mal_id=rating_item.anime_id, num_recs=12)
            similar = sim_data.get("similar", []) if isinstance(sim_data, dict) else sim_data
            if similar:
                because_you_liked.append({
                    "source_title": source_anime.english_name if source_anime.english_name and source_anime.english_name != 'Unknown' else source_anime.title,
                    "source_id": rating_item.anime_id,
                    "anime_list": similar
                })
    
    # Notification count: if there are new similar recommendations
    notification_count = len(because_you_liked)
    
    return render_template('index.html', hero_anime=hero_anime, recommendations=slider_anime,
                           unrated_recommendations=unrated_recommendations,
                           top_animes=top_animes, because_you_liked=because_you_liked,
                           notification_count=notification_count)

@app.route('/anime/<int:mal_id>')
@login_required
def anime_detail(mal_id):
    from models import Anime
    # Fetch anime details from database
    anime = Anime.query.filter_by(mal_id=mal_id).first()
    if not anime:
        flash('Anime not found in database.')
        return redirect(url_for('home'))
        
    similar_data = recommender.get_similar_items(mal_id=mal_id, num_recs=10)
    franchise_animes = similar_data.get("franchise", []) if isinstance(similar_data, dict) else []
    similar_animes = similar_data.get("similar", similar_data) if isinstance(similar_data, dict) else similar_data
    
    # Check if user already rated this anime
    from models import Rating
    user_rating_obj = Rating.query.filter_by(user_id=current_user.id, anime_id=mal_id).first()
    user_rating = user_rating_obj.rating if user_rating_obj else 0
    
    return render_template('detail.html', anime=anime, franchise_animes=franchise_animes, similar_animes=similar_animes, user_rating=user_rating)

@app.route('/rate_anime', methods=['POST'])
@login_required
def rate_anime():
    """
    Anime Puanlama Endpoint'i
    ---
    tags:
      - Interaction
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            anime_id:
              type: integer
            rating:
              type: integer
    responses:
      200:
        description: Puan başarıyla kaydedildi
      400:
        description: Eksik veya hatalı veri
    """
    from flask import request, jsonify
    from models import db, Rating
    
    data = request.get_json()
    anime_id = data.get('anime_id')
    rating_val = data.get('rating')
    
    if not anime_id or not rating_val:
        return jsonify({"error": "Missing data"}), 400
        
    try:
        rating_val = int(rating_val)
        if rating_val < 1 or rating_val > 10:
            return jsonify({"error": "Rating must be between 1 and 10"}), 400
            
        existing_rating = Rating.query.filter_by(user_id=current_user.id, anime_id=anime_id).first()
        is_new = False
        if existing_rating:
            existing_rating.rating = rating_val
        else:
            new_rating = Rating(user_id=current_user.id, anime_id=anime_id, rating=rating_val)
            db.session.add(new_rating)
            is_new = True
            
        db.session.commit()
        
        # We intentionally DO NOT overwrite Anime.score with local ratings
        # to preserve the global MyAnimeList dataset score and prevent
        # locally-rated animes from jumping to the top of All Time Masterpieces.
        from models import Anime
        anime = Anime.query.filter_by(mal_id=anime_id).first()
        if anime and is_new:
            anime.scored_by = (anime.scored_by or 0) + 1
            db.session.commit()
                
        return jsonify({"success": True, "message": "Rating saved!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/discover')
@login_required
def discover():
    """
    Rastgele Anime Keşfetme Endpoint'i
    ---
    tags:
      - Exploration
    responses:
      200:
        description: Rastgele seçilmiş animeler listesi
    """
    from models import Anime
    from sqlalchemy.sql import func
    # Randomly select 18 animes for the discover page
    random_animes = Anime.query.filter(Anime.score != None).order_by(func.random()).limit(18).all()
    return render_template('category.html', title="Discover (Random Recommendations)", animes=random_animes)

@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    from models import Anime
    if not query:
        return redirect(url_for('home'))
    
    # Search by title, synopsis, or names (case-insensitive substring match)
    from sqlalchemy import or_
    search_results = Anime.query.filter(
        or_(
            Anime.title.ilike(f'%{query}%'),
            Anime.english_name.ilike(f'%{query}%'),
            Anime.japanese_name.ilike(f'%{query}%'),
            Anime.synopsis.ilike(f'%{query}%')
        )
    ).order_by(Anime.score.desc()).limit(30).all()
    title = f"Search results for '{query}'"
    return render_template('category.html', title=title, animes=search_results)

@app.route('/category/<genre>')
@login_required
def category(genre):
    from models import Anime
    # Find animes matching the genre (case-insensitive substring match)
    category_animes = Anime.query.filter(Anime.genres.ilike(f'%{genre}%'), Anime.score != None).order_by(Anime.score.desc()).limit(18).all()
    title = f"{genre} Animes"
    return render_template('category.html', title=title, animes=category_animes)

@app.route('/random_recommendation')
@login_required
def random_recommendation():
    import random
    # Get top 20 hybrid recommendations
    recommendations = recommender.get_recommendations(
        user_id=current_user.id,
        num_recs=20,
        survey_data=current_user.survey,
        liked_anime_ids=[la.anime_id for la in current_user.liked_anime]
    )
    
    if recommendations:
        # Pick one randomly from the top recommendations to make it feel fresh
        choice = random.choice(recommendations)
        return redirect(url_for('anime_detail', mal_id=choice['anime_id']))
    
    flash("Could not generate a surprise recommendation right now. Try again later!")
    return redirect(url_for('home'))

@app.route('/profile')
@login_required
def profile():
    from models import Rating, Anime
    # Get all ratings from the user and join with anime info
    user_ratings = Rating.query.filter_by(user_id=current_user.id).order_by(Rating.rating.desc()).all()
    rated_animes = []
    for r in user_ratings:
        anime = Anime.query.filter_by(mal_id=r.anime_id).first()
        rated_animes.append({
            "anime": anime,
            "anime_id": r.anime_id,
            "rating": r.rating,
            "timestamp": r.timestamp
        })
    return render_template('profile.html', user=current_user, rated_animes=rated_animes)

@app.route('/like/<int:anime_id>', methods=['POST'])
@login_required
def like_anime(anime_id):
    title = request.form.get('title', f"Anime {anime_id}")
    if not LikedAnime.query.filter_by(user_id=current_user.id, anime_id=anime_id).first():
        like = LikedAnime(user_id=current_user.id, anime_id=anime_id, title=title)
        db.session.add(like)
        db.session.commit()
    return redirect(url_for('home'))

@app.route('/watch/<int:anime_id>', methods=['POST'])
@login_required
def watch_anime(anime_id):
    title = request.form.get('title', f"Anime {anime_id}")
    if not WatchedAnime.query.filter_by(user_id=current_user.id, anime_id=anime_id).first():
        watch = WatchedAnime(user_id=current_user.id, anime_id=anime_id, title=title)
        db.session.add(watch)
        db.session.commit()
    return redirect(url_for('home'))

@app.route('/delete_rating/<int:anime_id>', methods=['POST'])
@login_required
def delete_rating(anime_id):
    from models import Rating
    rating = Rating.query.filter_by(user_id=current_user.id, anime_id=anime_id).first()
    if rating:
        db.session.delete(rating)
        db.session.commit()
        flash('Rating removed successfully.')
    return redirect(url_for('profile'))

@app.route('/delete_like/<int:anime_id>', methods=['POST'])
@login_required
def delete_like(anime_id):
    like = LikedAnime.query.filter_by(user_id=current_user.id, anime_id=anime_id).first()
    if like:
        db.session.delete(like)
        db.session.commit()
        flash('Removed from Liked list.')
    return redirect(url_for('profile'))

@app.route('/delete_watch/<int:anime_id>', methods=['POST'])
@login_required
def delete_watch(anime_id):
    watch = WatchedAnime.query.filter_by(user_id=current_user.id, anime_id=anime_id).first()
    if watch:
        db.session.delete(watch)
        db.session.commit()
        flash('Removed from Watched list.')
    return redirect(url_for('profile'))

@app.route('/api/users', methods=['GET'])
def get_users():
    """
    Kayıtlı Tüm Kullanıcıları Listeler
    ---
    tags:
      - Admin/Debug
    responses:
      200:
        description: Kullanıcı listesi
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              username:
                type: string
    """
    users = User.query.all()
    user_list = [{"id": u.id, "username": u.username} for u in users]
    return jsonify(user_list)

@app.route('/api/user/<int:user_id>/survey', methods=['GET'])
def get_user_survey(user_id):
    """
    Kullanıcının Anket (Tercih) Verilerini Getirir
    ---
    tags:
      - Admin/Debug
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: Kullanıcı ID'si
    responses:
      200:
        description: Kullanıcı tercih verileri (Türler vb.)
      404:
        description: Kullanıcı veya anket bulunamadı
    """
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    survey = user.survey
    if not survey:
        return jsonify({"error": "Survey not found for this user"}), 404
    
    return jsonify({
        "user_id": user.id,
        "username": user.username,
        "genres": survey.genres,
        "min_score": survey.min_score,
        "max_episodes": survey.max_episodes,
        "preferred_year": survey.preferred_year
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Auto-populate DB from CSV if Anime table is empty or missing names
        from models import Anime
        if not Anime.query.first() or not Anime.query.filter(Anime.english_name != None).first():
            # Clear existing data
            Anime.query.delete()
            db.session.commit()
            
            anime_csv = os.path.join(os.path.dirname(__file__), '../data/anime.csv')
            synopsis_csv = os.path.join(os.path.dirname(__file__), '../data/anime_with_synopsis.csv')
            
            if os.path.exists(anime_csv):
                print("Populating Anime table... This may take a moment.")
                
                # Load synopses into memory for fast lookup
                synopses = {}
                if os.path.exists(synopsis_csv):
                    with open(synopsis_csv, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            synopses[row['MAL_ID']] = row.get('sypnopsis')
                
                with open(anime_csv, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    count = 0
                    for row in reader:
                        try:
                            score = float(row['Score']) if row['Score'] and row['Score'] != 'Unknown' else None
                            
                            scored_by = 0
                            for i in range(1, 11):
                                score_col = f'Score-{i}'
                                val = row.get(score_col, 'Unknown')
                                if val != 'Unknown':
                                    try:
                                        scored_by += int(float(val))
                                    except ValueError:
                                        pass

                            anime = Anime(
                                mal_id=int(row['MAL_ID']),
                                title=row['Name'],
                                english_name=row.get('English name'),
                                japanese_name=row.get('Japanese name'),
                                score=score,
                                genres=row['Genres'],
                                synopsis=synopses.get(row['MAL_ID']),
                                scored_by=scored_by
                            )
                            db.session.add(anime)
                            count += 1
                            if count % 1000 == 0:
                                db.session.commit()
                        except Exception:
                            pass
                    db.session.commit()
                print("Done populating!")
    app.run(debug=True, port=8080)
