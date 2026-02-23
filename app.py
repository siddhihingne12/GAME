from flask import Flask, jsonify, request, session, redirect, url_for, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key")
CORS(app)

# Database Configuration
# You can switch between SQLite, MySQL, or PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///memory_master.db")
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable static file caching in dev

db = SQLAlchemy(app)

# Prevent browser caching during development
@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    coins = db.Column(db.Integer, default=0)
    stars = db.Column(db.Integer, default=0)
    
    progress = db.relationship('GameProgress', backref='user', lazy=True)

class GameProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    game_type = db.Column(db.String(50), nullable=False) # 'memory', 'f1', 'schulte', 'confusion'
    score = db.Column(db.Float, default=0.0)
    level = db.Column(db.Integer, default=1)
    extra_data = db.Column(db.Text, nullable=True) # JSON strings for things like max_combo, avg_rt

# Routes
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    username = data.get('username', 'Master Player')
    google_id = data.get('google_id')
    
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, username=username, google_id=google_id)
        db.session.add(user)
        db.session.commit()
    
    return jsonify({
        "status": "success",
        "user": {
            "id": user.id,
            "username": user.username,
            "coins": user.coins,
            "stars": user.stars
        }
    })

@app.route('/api/save-progress', methods=['POST'])
def save_progress():
    data = request.json
    user_id = data.get('user_id')
    game_type = data.get('game_type')
    score = data.get('score', 0.0)
    level = data.get('level', 1)
    coins_gained = data.get('coins_gained', 0)
    stars_gained = data.get('stars_gained', 0)
    extra_data = data.get('extra_data', {})

    user = User.query.get(user_id)
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    # Update user stats
    user.coins += coins_gained
    user.stars += stars_gained

    # Update or create game progress
    progress = GameProgress.query.filter_by(user_id=user_id, game_type=game_type).first()
    if not progress:
        progress = GameProgress(user_id=user_id, game_type=game_type)
        db.session.add(progress)

    # For memory game, update level if higher
    if game_type == 'memory':
        if level > progress.level:
            progress.level = level
        if score > progress.score:
            progress.score = score
    
    # For reaction games, update score if better (lower is better for time)
    elif game_type in ['f1', 'schulte']:
        if progress.score == 0 or score < progress.score:
            progress.score = score
            
    # For Color Confusion, update high score
    elif game_type == 'confusion':
        if score > progress.score:
            progress.score = score

    progress.extra_data = json.dumps(extra_data)
    db.session.commit()

    return jsonify({"status": "success", "coins": user.coins, "stars": user.stars})

@app.route('/api/leaderboard/<game_type>', methods=['GET'])
def get_leaderboard(game_type):
    # Get top 10 players for the given game type
    if game_type in ['f1', 'schulte']:
        # Lower score (time) is better
        results = GameProgress.query.filter_by(game_type=game_type).order_by(GameProgress.score.asc()).limit(10).all()
    else:
        # Higher score is better
        results = GameProgress.query.filter_by(game_type=game_type).order_by(GameProgress.score.desc()).limit(10).all()

    leaderboard = []
    for res in results:
        leaderboard.append({
            "username": res.user.username,
            "score": res.score,
            "level": res.level,
            "extra_data": json.loads(res.extra_data) if res.extra_data else {}
        })

    return jsonify(leaderboard)

# Serve static frontend files (CSS, JS, images, etc.)
@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Port is set to 5000 by default or via env
    port = int(os.getenv("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
