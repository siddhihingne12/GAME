
import random
import time
import subprocess
import sys
import webbrowser
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
from flask import Flask, jsonify, request, session, redirect, url_for, send_from_directory
# Imports Flask framework and its utilities

from flask_cors import CORS
# Imports CORS (Cross-Origin Resource Sharing)


import os
import json

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key")


# Supabase initialization would go here for backend DB access
db_firestore = None 

CORS(app, supports_credentials=True)
# supports_credentials=True allows cookies/sessions to be sent cross-origin

# Helper functions for Firestore replacement of User/GameProgress models
def get_user(user_id):
    if not db_firestore: return None
    user_ref = db_firestore.collection('users').document(str(user_id))
    doc = user_ref.get()
    if doc.exists:
        return doc.to_dict()
    return None

def update_user(user_id, data):
    if not db_firestore: return
    user_ref = db_firestore.collection('users').document(str(user_id))
    user_ref.set(data, merge=True)

# Routes
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Supabase and session auth routes removed

# ── Legacy login (kept as fallback for offline mode) ──────
@app.route('/api/login', methods=['POST'])
def login():
    # Kept for compatibility but should use firebase_callback
    data = request.json
    uid = data.get('uid')
    if not uid: return jsonify({"status": "error"}), 400
    
    user_data = get_user(uid)
    if not user_data:
        user_data = {
            "id": uid,
            "email": data.get('email'),
            "username": data.get('username', 'Master Player'),
            "coins": 0,
            "stars": 0
        }
        update_user(uid, user_data)
    
    session['user_id'] = uid
    return jsonify({"status": "success", "user": user_data})

@app.route('/api/save-progress', methods=['POST'])
def save_progress():
    if not db_firestore:
        return jsonify({"status": "error", "message": "Firebase not initialized"}), 500

    data = request.json
    user_id = data.get('user_id')
    game_type = data.get('game_type')
    score = data.get('score', 0.0)
    level = data.get('level', 1)
    coins_gained = data.get('coins_gained', 0)
    stars_gained = data.get('stars_gained', 0)
    extra_data = data.get('extra_data', {})

    user_ref = db_firestore.collection('users').document(str(user_id))
    user_doc = user_ref.get()

    if not user_doc.exists:
        return jsonify({"status": "error", "message": "User not found"}), 404

    user_data = user_doc.to_dict()
    user_data['coins'] = user_data.get('coins', 0) + coins_gained
    user_data['stars'] = user_data.get('stars', 0) + stars_gained
    user_ref.set(user_data, merge=True)

    # Progress collection
    progress_ref = db_firestore.collection('progress').document(f"{user_id}_{game_type}")
    progress_doc = progress_ref.get()
    
    progress = progress_doc.to_dict() if progress_doc.exists else {
        "user_id": user_id,
        "username": user_data.get('username'),
        "game_type": game_type,
        "score": 0.0,
        "level": 1
    }

    if game_type == 'memory':
        if level > progress.get('level', 1): progress['level'] = level
        if score > progress.get('score', 0.0): progress['score'] = score
    elif game_type in ['f1', 'schulte']:
        if progress['score'] == 0 or score < progress['score']: progress['score'] = score
    elif game_type == 'confusion':
        if score > progress['score']: progress['score'] = score

    progress['extra_data'] = extra_data
    progress_ref.set(progress)

    return jsonify({"status": "success", "coins": user_data['coins'], "stars": user_data['stars']})
    # Returns a success response with the user's updated coin and star totals

@app.route('/api/leaderboard/<game_type>', methods=['GET'])
def get_leaderboard(game_type):
    if not db_firestore:
        return jsonify({"status": "error", "message": "Firebase not initialized"}), 500

    query = db_firestore.collection('progress').where('game_type', '==', game_type)
    
    if game_type in ['f1', 'schulte']:
        # Lower score (time) is better
        results = query.order_by('score', direction=firestore.Query.ASCENDING).limit(10).stream()
    else:
        # Higher score is better
        results = query.order_by('score', direction=firestore.Query.DESCENDING).limit(10).stream()

    leaderboard = []
    for doc in results:
        res = doc.to_dict()
        leaderboard.append({
            "username": res.get('username', 'Anonymous'),
            "score": res.get('score'),
            "level": res.get('level'),
            "extra_data": res.get('extra_data', {})
        })

    return jsonify(leaderboard)
    # Returns the leaderboard as a JSON array to the frontend

# ── Color Confusion API Endpoints ─────────────────────────────
# Uses the Python confusion_engine for Stroop question generation and validation

"""
Color Confusion — Python Game Engine
Stroop Effect question generation, validation, and scoring logic.
Used by the Flask API to serve game data to the frontend.
"""
# Module docstring: This file implements the backend engine for the Color Confusion game, handling Stroop Effect question creation, answer checking, scoring, and session management

import random
# Imports the random module for shuffling colors and generating randomized Stroop questions

import time
# Imports the time module for tracking session duration and question timestamps

import json
# Imports json module for serializing the final game report (used in CLI test)

from dataclasses import dataclass, field, asdict
# Imports dataclass utilities: @dataclass auto-generates constructors/repr, field() sets default factories, asdict() converts dataclass to dict

from typing import List, Dict, Optional, Tuple
# Imports type hints for better code documentation and IDE support

# ── Color Palette ─────────────────────────────────────────────
COLORS = {
    'Red':      '#ef4444',
    'Blue':     '#3b82f6',
    'Green':    '#22c55e',
    'Yellow':   '#eab308',
    'Purple':   '#8b5cf6',
    'Orange':   '#f97316',
    'Pink':     '#ff29ff',
    'Cyan':     '#06b6d4',
    'Indigo':   '#6366f1',
    'Violet':   '#8b5cf6',
    'Black':    '#1a1a1a',
    'Brown':    '#78350f',
    'Lavender': '#a78bfa',
    'White':    '#ffffff',
    'Beige':    '#f5f5dc',
}
# Master dictionary mapping color names to their CSS hex codes — used for rendering text in the correct font color on the frontend

# Difficulty tiers — more colors = harder
DIFFICULTY_TIERS = {
    1: ['Red', 'Blue', 'Green', 'Yellow'],
    # Tier 1 (Easiest): Only 4 basic colors — easy to distinguish

    2: ['Red', 'Blue', 'Green', 'Yellow', 'Purple', 'Orange'],
    # Tier 2: Adds Purple and Orange — 6 colors to choose from

    3: ['Red', 'Blue', 'Green', 'Yellow', 'Purple', 'Orange', 'Pink', 'Cyan'],
    # Tier 3: Adds Pink and Cyan — 8 colors increase confusion

    4: ['Red', 'Blue', 'Green', 'Yellow', 'Purple', 'Orange', 'Pink', 'Cyan', 'Indigo', 'Violet'],
    # Tier 4: Adds Indigo and Violet — 10 colors; similar shades make it much harder

    5: list(COLORS.keys()),  # All colors
    # Tier 5 (Hardest): Uses every color in the palette — maximum cognitive challenge
}


@dataclass
class StroopQuestion:
    """A single Stroop effect question."""
    # Dataclass representing one Stroop Effect question shown to the player

    text_word: str          # The word displayed (e.g., "YELLOW")
    # The text written on screen — this is the DISTRACTOR that tries to trick the player

    font_color_name: str    # The actual font color name (e.g., "Red")
    # The name of the actual font color — this is what the player must identify (the CORRECT ANSWER)

    font_color_hex: str     # Hex for the font color
    # The CSS hex code of the font color — used by the frontend to render the word in this color

    options: List[str]      # 4 answer choices
    # List of 4 color name strings: 1 correct answer + 3 distractors

    difficulty: int         # Current difficulty level
    # The difficulty tier (1-5) at which this question was generated

    timestamp: float = field(default_factory=time.time)
    # Automatically records when this question was created (Unix timestamp)

    def to_dict(self) -> dict:
        # Converts this question object into a plain Python dictionary for JSON serialization
        return asdict(self)
        # Uses the dataclass asdict() helper to convert all fields to a dictionary


@dataclass
class AnswerResult:
    """Result of a single answer validation."""
    # Dataclass holding the outcome of validating a player's answer

    correct: bool
    # Whether the player's answer was correct (True) or wrong (False)

    reaction_time_ms: int
    # How fast the player answered in milliseconds

    points_earned: int
    # Total points earned for this answer (base + speed bonus × combo multiplier)

    combo: int
    # Current combo streak count (resets to 0 on wrong answer)

    speed_bonus: int
    # Extra points earned for answering quickly (within 2 seconds)

    multiplier: float
    # Combo multiplier applied to points (increases with consecutive correct answers)


class ConfusionEngine:
    """
    Core Stroop Effect game engine.
    
    Handles question generation, answer validation,
    scoring with combo multipliers, and difficulty scaling.
    """
    # The main engine class that powers the Color Confusion game logic
    
    def __init__(self, difficulty: int = 1):
        # Constructor: initializes the engine with a starting difficulty level

        self.difficulty = max(1, min(5, difficulty))
        # Clamps the difficulty between 1 and 5 to prevent invalid values

        self._color_pool = self._get_color_pool()
        # Loads the available colors for the current difficulty tier
    
    def _get_color_pool(self) -> List[str]:
        """Get available colors based on difficulty."""
        # Returns the list of color names available at the current difficulty level

        tier = min(self.difficulty, max(DIFFICULTY_TIERS.keys()))
        # Ensures the tier doesn't exceed the maximum defined tier

        return DIFFICULTY_TIERS.get(tier, DIFFICULTY_TIERS[1])
        # Looks up the color list for this tier; falls back to tier 1 if not found
    
    def generate_question(self) -> StroopQuestion:
        """
        Generate a Stroop question where the displayed word
        and its font color are always different (the Stroop effect).
        """
        # Creates a new question where the word text and its font color are deliberately mismatched to create the Stroop Effect

        pool = self._color_pool
        # Gets the available colors for the current difficulty level
        
        # Pick the font color (this is the CORRECT answer)
        font_color_name = random.choice(pool)
        # Randomly selects which color the text will actually be rendered in — the player must identify THIS color
        
        # Pick a DIFFERENT word to display (creates the Stroop effect)
        available_words = [c for c in pool if c != font_color_name]
        # Filters out the font color to ensure the displayed word is always different from the actual color

        text_word = random.choice(available_words) if available_words else 'Black'
        # Picks a random different color name as the displayed word; uses 'Black' as fallback if pool is too small
        
        # Build 4 options: correct + 3 distractors
        distractors = [c for c in pool if c != font_color_name and c != text_word]
        # Creates a list of potential wrong answers by excluding both the correct answer and the displayed word

        random.shuffle(distractors)
        # Randomizes the distractor order so different ones are picked each time

        options = [font_color_name] + distractors[:3]
        # Builds the options list: the correct answer plus up to 3 random distractors
        
        # Ensure we have exactly 4 options
        while len(options) < 4:
            # If there aren't enough distractors (small color pool), adds more from the full color list

            filler = random.choice(list(COLORS.keys()))
            # Picks a random color from the entire palette as a filler

            if filler not in options:
                options.append(filler)
                # Adds the filler only if it's not already in the options to avoid duplicates
        
        random.shuffle(options)
        # Shuffles all 4 options so the correct answer isn't always in the same position
        
        return StroopQuestion(
            text_word=text_word.upper(),
            # The displayed word in uppercase (e.g., "YELLOW") — the visual distractor

            font_color_name=font_color_name,
            # The actual font color name — the correct answer

            font_color_hex=COLORS.get(font_color_name, '#888'),
            # The hex code for the font color; falls back to gray if color not found

            options=options,
            # The 4 shuffled answer choices

            difficulty=self.difficulty
            # Records the difficulty level at which this question was generated
        )
    
    def validate_answer(
        self,
        question: StroopQuestion,
        selected_color: str,
        reaction_time_ms: int,
        current_combo: int
    ) -> AnswerResult:
        """
        Validate a player's answer and calculate points.
        
        Scoring:
        - Base: 10 points per correct answer
        - Speed bonus: up to 20 extra points for fast reactions (<2s)
        - Combo multiplier: 1 + (combo * 0.1), e.g., 5-streak = 1.5x
        """
        # Checks if the player selected the correct font color and calculates their score

        correct = selected_color.lower() == question.font_color_name.lower()
        # Case-insensitive comparison between the player's selection and the correct answer
        
        if correct:
            # If the player answered correctly:

            combo = current_combo + 1
            # Increments the combo streak counter

            base_points = 10
            # Base points awarded for a correct answer

            speed_bonus = max(0, (2000 - reaction_time_ms) // 100)
            # Calculates speed bonus: faster answers (under 2 seconds) earn up to 20 extra points; 100ms per bonus point

            multiplier = 1.0 + (combo * 0.1)
            # Combo multiplier increases by 0.1 per consecutive correct answer (e.g., 5-streak = 1.5x)

            points = round((base_points + speed_bonus) * multiplier)
            # Total points = (base + speed bonus) × combo multiplier, rounded to nearest integer

        else:
            # If the player answered incorrectly:

            combo = 0
            # Resets the combo streak to 0

            base_points = 0
            # No base points for wrong answers

            speed_bonus = 0
            # No speed bonus for wrong answers

            multiplier = 1.0
            # Multiplier resets to 1.0 (no bonus)

            points = 0
            # Zero points earned for an incorrect answer
        
        return AnswerResult(
            correct=correct,
            # Whether the answer was right or wrong

            reaction_time_ms=reaction_time_ms,
            # The player's reaction time

            points_earned=points,
            # Total points earned this round

            combo=combo,
            # Updated combo streak count

            speed_bonus=speed_bonus,
            # Speed bonus points earned

            multiplier=multiplier
            # The combo multiplier that was applied
        )
    
    def scale_difficulty(self, score: int) -> None:
        """Auto-scale difficulty based on score milestones."""
        # Automatically increases the difficulty as the player scores more correct answers

        if score >= 40:
            self.difficulty = 5
            # 40+ correct: Maximum difficulty with all 15 colors

        elif score >= 30:
            self.difficulty = 4
            # 30+ correct: 10 colors including similar shades (Indigo, Violet)

        elif score >= 20:
            self.difficulty = 3
            # 20+ correct: 8 colors adding Pink and Cyan

        elif score >= 10:
            self.difficulty = 2
            # 10+ correct: 6 colors adding Purple and Orange

        else:
            self.difficulty = 1
            # Below 10: Easiest with only 4 basic colors

        self._color_pool = self._get_color_pool()
        # Refreshes the available color pool to match the new difficulty tier
    
    def get_performance_rating(
        self,
        avg_reaction_ms: float,
        total_score: int
    ) -> str:
        """Assign a performance rating based on reaction time and score."""
        # Evaluates the player's overall performance and assigns a rank title

        if avg_reaction_ms < 600 and total_score > 40:
            return "Grandmaster"
            # Lightning-fast reactions AND high score — the best possible rating

        elif avg_reaction_ms < 800 and total_score > 25:
            return "Expert"
            # Very fast reactions with a strong score

        elif avg_reaction_ms < 1000 and total_score > 15:
            return "Advanced"
            # Good reaction time with a solid score

        elif avg_reaction_ms < 1200 and total_score > 8:
            return "Intermediate"
            # Decent reaction time with a moderate score

        elif total_score > 3:
            return "Beginner"
            # Player got a few correct but needs more practice

        else:
            return "Trainee"
            # Very few correct answers — just starting out


# ── Session Manager ───────────────────────────────────────────

class GameSession:
    """
    Manages a complete Color Confusion game session.
    
    Modes:
    - endless:   3 lives, play until lives run out
    - survival:  60s timer, +3s correct / -3s wrong
    - speed:     race to 50 correct answers
    """
    # Session class that tracks an entire game playthrough including score, lives, timer, and combo streaks
    
    def __init__(self, mode: str = 'endless'):
        # Constructor: initializes a new game session with the specified mode

        self.mode = mode
        # Stores the game mode ('endless', 'survival', or 'speed')

        self.engine = ConfusionEngine(difficulty=1)
        # Creates a new ConfusionEngine starting at difficulty 1

        self.score = 0
        # Tracks the number of correct answers

        self.total_points = 0
        # Tracks the cumulative point score (includes speed bonuses and combo multipliers)

        self.combo = 0
        # Current consecutive correct answer streak

        self.max_combo = 0
        # Highest combo streak achieved during this session

        self.lives = 3 if mode == 'endless' else -1
        # Endless mode starts with 3 lives; other modes don't use lives (-1 means disabled)

        self.time_left = 60.0 if mode == 'survival' else -1
        # Survival mode starts with 60 seconds; other modes don't use a timer (-1 means disabled)

        self.target = 50 if mode == 'speed' else -1
        # Speed mode requires 50 correct answers to win; other modes don't have a target (-1 means disabled)

        self.reactions: List[int] = []
        # List storing every reaction time (in ms) for calculating the average at the end

        self.start_time = time.time()
        # Records when the session started (Unix timestamp) for calculating total elapsed time

        self.is_active = True
        # Flag indicating whether the session is still ongoing (False when game over)

        self.current_question: Optional[StroopQuestion] = None
        # Stores the current question being asked; None when no question is active
    
    def next_question(self) -> Optional[StroopQuestion]:
        """Generate the next question if session is still active."""
        # Creates and returns the next Stroop question, or None if the game has ended

        if not self.is_active:
            return None
            # Returns None if the session is over — no more questions to generate

        self.current_question = self.engine.generate_question()
        # Uses the engine to create a new randomized Stroop question

        return self.current_question
        # Returns the generated question to be sent to the frontend
    
    def submit_answer(self, selected_color: str, reaction_time_ms: int) -> dict:
        """Process an answer and return the result with updated session state."""
        # Handles a player's answer submission: validates it, updates score/lives/time, and returns the result

        if not self.is_active or not self.current_question:
            return {"error": "No active question"}
            # Returns an error if there's no active session or no question was asked

        result = self.engine.validate_answer(
            self.current_question, selected_color, reaction_time_ms, self.combo
        )
        # Validates the answer using the engine's scoring logic (checks correctness, calculates points and combo)
        
        self.reactions.append(reaction_time_ms)
        # Records this reaction time for the end-of-game average calculation
        
        if result.correct:
            # If the player answered correctly:

            self.score += 1
            # Increments the correct answer counter

            self.combo = result.combo
            # Updates the combo streak from the validation result

            self.max_combo = max(self.max_combo, self.combo)
            # Updates the max combo if the current streak is the longest so far

            self.total_points += result.points_earned
            # Adds the earned points (with bonuses) to the total score
            
            # Mode-specific rewards
            if self.mode == 'survival':
                self.time_left += 3
                # In Survival mode, correct answers reward +3 seconds to the timer
            
            # Difficulty scaling every 5 correct
            if self.score % 5 == 0:
                self.engine.scale_difficulty(self.score)
                # Every 5 correct answers, the engine increases the difficulty (more colors in the pool)

        else:
            # If the player answered incorrectly:

            self.combo = 0
            # Resets the combo streak to 0
            
            # Mode-specific penalties
            if self.mode == 'endless':
                self.lives -= 1
                # In Endless mode, wrong answers cost 1 life

                if self.lives <= 0:
                    self.is_active = False
                    # Game over when all lives are lost

            elif self.mode == 'survival':
                self.time_left = max(0, self.time_left - 3)
                # In Survival mode, wrong answers deduct 3 seconds from the timer

                if self.time_left <= 0:
                    self.is_active = False
                    # Game over when the timer reaches zero

            elif self.mode == 'speed':
                self.total_points = max(0, self.total_points - 5)
                # In Speed mode, wrong answers deduct 5 points as a penalty (can't go below 0)
        
        # Speed run win condition
        if self.mode == 'speed' and self.score >= self.target:
            self.is_active = False
            # In Speed mode, the game ends (as a WIN) when the player reaches the target of 50 correct answers
        
        return {
            "correct": result.correct,
            # Whether this answer was correct

            "points_earned": result.points_earned,
            # Points earned for this specific answer

            "total_points": self.total_points,
            # Running total of all points earned so far

            "score": self.score,
            # Total number of correct answers so far

            "combo": self.combo,
            # Current combo streak count

            "max_combo": self.max_combo,
            # Highest combo achieved in this session

            "lives": self.lives,
            # Remaining lives (Endless mode only; -1 for other modes)

            "time_left": round(self.time_left, 1) if self.time_left >= 0 else -1,
            # Remaining time in seconds (Survival mode only; -1 for other modes)

            "is_active": self.is_active,
            # Whether the game is still ongoing

            "speed_bonus": result.speed_bonus,
            # Speed bonus points earned for this answer

            "multiplier": result.multiplier,
            # Combo multiplier applied to this answer's points
        }
    
    def get_final_report(self) -> dict:
        """Generate the end-of-session report."""
        # Creates a comprehensive performance summary when the game session ends

        elapsed = round(time.time() - self.start_time, 2)
        # Calculates total time played in seconds (rounded to 2 decimal places)

        avg_rt = (
            round(sum(self.reactions) / len(self.reactions))
            if self.reactions else 0
        )
        # Calculates the average reaction time across all answers; returns 0 if no answers were given

        rating = self.engine.get_performance_rating(avg_rt, self.score)
        # Gets the player's performance rating title based on their average reaction time and total score
        
        return {
            "mode": self.mode,
            # Which game mode was played

            "total_points": self.total_points,
            # Final cumulative point score

            "score": self.score,
            # Total number of correct answers

            "max_combo": self.max_combo,
            # Longest consecutive correct answer streak

            "avg_reaction_ms": avg_rt,
            # Average reaction time in milliseconds

            "elapsed_seconds": elapsed,
            # Total time spent playing in seconds

            "rating": rating,
            # Performance rating title (Trainee → Grandmaster)

            "total_questions": len(self.reactions),
            # Total number of questions answered (correct + wrong)

            "accuracy": round(self.score / max(1, len(self.reactions)) * 100, 1),
            # Accuracy percentage: (correct / total) × 100, rounded to 1 decimal; max(1,...) prevents division by zero
        }



_confusion_available = True


# Active game sessions stored in memory (keyed by user_id or session token)
_active_sessions = {}
# Dictionary to hold active Color Confusion game sessions; maps session IDs to GameSession objects

@app.route('/api/confusion/generate', methods=['POST'])
# Defines the endpoint to generate a new Stroop effect question for Color Confusion
def confusion_generate():
    """Generate a Stroop effect question for the Color Confusion game."""
    # Docstring explaining this endpoint's purpose

    if not _confusion_available:
        return jsonify({"status": "error", "message": "Confusion engine not available"}), 500
        # Returns a 500 server error if the confusion_engine module couldn't be imported

    data = request.json or {}
    # Parses the request body; defaults to empty dict if no JSON is sent

    difficulty = data.get('difficulty', 1)
    # Gets the requested difficulty level (1-5); defaults to easiest

    mode = data.get('mode', 'endless')
    # Gets the game mode ('endless', 'survival', 'speed'); defaults to endless

    session_id = data.get('session_id', 'default')
    # Gets the unique session identifier; defaults to 'default'

    # Create or retrieve session
    if session_id not in _active_sessions or not _active_sessions[session_id].is_active:
        _active_sessions[session_id] = GameSession(mode)
        # Creates a new game session if one doesn't exist or the previous one ended

    session = _active_sessions[session_id]
    # Retrieves the active game session for this player

    question = session.next_question()
    # Generates the next Stroop effect question using the confusion engine

    if question is None:
        report = session.get_final_report()
        # If no more questions (session ended), generate the final performance report

        return jsonify({"status": "finished", "report": report})
        # Returns the final report indicating the game session is complete

    return jsonify({
        "status": "success",
        "question": {
            "text_word": question.text_word,
            # The word displayed on screen (e.g., "YELLOW") — this is the DISTRACTOR

            "font_color_name": question.font_color_name,
            # The actual font color name — this is the CORRECT ANSWER the player must identify

            "font_color_hex": question.font_color_hex,
            # The hex code of the font color for rendering in CSS

            "options": question.options,
            # Four answer choices (one correct + three distractors)

            "difficulty": question.difficulty
            # The current difficulty level affecting the color pool size
        }
    })
    # Returns the generated question data to the frontend for display

@app.route('/api/confusion/validate', methods=['POST'])
# Defines the endpoint to validate a player's answer in Color Confusion
def confusion_validate():
    """Validate a player's answer for the Color Confusion game."""
    # Docstring explaining this endpoint's purpose

    if not _confusion_available:
        return jsonify({"status": "error", "message": "Confusion engine not available"}), 500
        # Returns a 500 error if the engine module is unavailable

    data = request.json or {}
    # Parses the request body

    session_id = data.get('session_id', 'default')
    # Gets the session identifier to find the correct game session

    selected_color = data.get('selected_color', '')
    # Gets the color the player selected as their answer

    reaction_time_ms = data.get('reaction_time_ms', 2000)
    # Gets how fast the player answered in milliseconds; defaults to 2 seconds

    if session_id not in _active_sessions:
        return jsonify({"status": "error", "message": "No active session"}), 404
        # Returns a 404 error if the session doesn't exist (expired or never started)

    session = _active_sessions[session_id]
    # Retrieves the active game session

    result = session.submit_answer(selected_color, reaction_time_ms)
    # Processes the player's answer: checks correctness, updates score, combo, lives/time

    # If game is over, include the final report
    if not result.get('is_active', True):
        # Checks if the game session has ended (lives ran out, time expired, or target reached)
        result['report'] = session.get_final_report()
        # Attaches the final performance report to the response

        # Cleanup session
        del _active_sessions[session_id]
        # Removes the ended session from memory to free resources

    return jsonify({"status": "success", **result})
    # Returns the validation result (correct/wrong, points, combo, lives, etc.) to the frontend

# Serve static frontend files (CSS, JS, images, etc.)
@app.route('/<path:filename>')
# Catch-all route that serves any static file from the current directory (CSS, JS, images, etc.)
def serve_static(filename):
    # Handler function for serving static frontend assets
    return send_from_directory('.', filename)
    # Sends the requested file from the project root directory to the browser


def lint_js():
        try:
            with open('app.js', 'r', encoding='utf-8') as f:
                content = f.read()
            depth = 0
            lines = content.split('\n')
            for i, line in enumerate(lines):
                for char in line:
                    if char == '{':
                        depth += 1
                    elif char == '}':
                        depth -= 1
                    if depth < 0:
                        print(f'Negative depth at line {i+1}: {line.strip()}')
                        sys.exit(1)
            print(f'Final depth: {depth}')
        except Exception as e:
            print(f'Error: {e}')
            sys.exit(1)
        


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "lint":
        lint_js()
        sys.exit(0)

    port = int(os.getenv("PORT", 5000))
    print(f"Starting Flask server on port {port}...")
    
    # Run browser open in a timer thread
    import threading
    def open_browser():
        time.sleep(2)
        url = f"http://localhost:{port}"
        print(f"Opening Game UI: {url}")
        webbrowser.open(url)
        
    threading.Thread(target=open_browser, daemon=True).start()
    
    app.run(debug=True, host='0.0.0.0', port=port)

