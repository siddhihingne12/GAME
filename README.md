# Memory Master 🧠

A premium gaming platform designed to sharpen your memory and reflexes.

## Features

- **Room Observer (Memory Game)**: 300 levels of increasing difficulty. Observe objects and recall their colors.
- **F1 Reaction**: Test your reflexes against the world's fastest drivers with an interactive 5-light sequence.
- **Schulte Table**: A classic cognitive test. Find numbers in order as fast as possible.
- **Rewards System**: Earn coins and stars to track your progress.
- **Social Login**: Google authentication simulation.
- **Premium Design**: Dark mode, glassmorphism, and smooth GSAP animations.

## Tech Stack

- **Frontend**: HTML5, Vanilla CSS, Vanilla JavaScript
- **Animations**: GSAP (GreenSock Animation Platform)
- **Backend (Optional/API)**: Flask (Python), SQLAlchemy
- **Database**: SQLite (default), supports MySQL/PostgreSQL

## Setup

### Prerequisites
- Python 3.8+

### Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the platform:
   ```bash
   python run.py
   ```

## Project Structure

```text
├── app.py              # Flask API and Models
├── index.html          # Main entry point
├── style.css           # Core design system
├── app.js              # SPA Logic & Games
├── run.py              # Automation script
├── requirements.txt    # Python dependencies
└── README.md           # Documentation
```


# 🧠 Master Mind — Game Logic & File Explanation

Master Mind is a **multi-game brain training platform** designed to test and improve cognitive skills like memory, reflexes, observation, and focus. It features **four mini-games**, each targeting a different mental ability.

---

## 📁 Project File Structure & Purpose

### Core Application Files

| File | Language | Purpose |
|------|----------|---------|
| `index.html` | HTML | Frontend entry point |
| `app.js` | JavaScript | All game logic & UI rendering |
| `style.css` | CSS | Visual styling & animations |
| `app.py` | Python | Backend API server |
| `run.py` | Python | One-click game launcher |
| `confusion_engine.py` | Python | Color Confusion game engine |
| `requirements.txt` | Text | Python package dependencies |
| `database.sql` | SQL | Database schema reference |
| `README.md` | Markdown | Project overview |

### Supporting Files

| File | Purpose |
|------|---------|
| `ConfusionEngine.cs` | C# port of the Color Confusion engine (cross-platform) |
| `ConfusionEngine.java` | Java port of the Color Confusion engine (cross-platform) |
| `confusion_engine.cpp` | C++ port of the Color Confusion engine (cross-platform) |
| `ranker.cpp` | C++ utility for leaderboard ranking calculations |
| `memory_master.db` | SQLite database file storing user accounts & scores |

---

## 📄 Detailed File Explanations

### 🏠 `index.html` — The Game's Front Door

**Why it exists:** Every web application needs an HTML file as its entry point. This is the **skeleton** of the entire game — the structure that the browser reads first.

**What it does:**
- Defines the **loading screen** with a progress bar (the first thing players see)
- Sets up the **navigation bar** with tabs: Games, Leaderboard, About, Help
- Contains the **four game mode cards** (Room Observer, F1 Reflex, Schulte Grid, Color Confusion) on the home screen
- Provides the **login modal** popup for user authentication
- Loads Google Fonts (Poppins & Quicksand) for premium typography
- Loads the GSAP animation library for smooth transitions
- Links to `style.css` for visuals and `app.js` for all interactivity

**Why it's needed:** Without this file, there is no game. It's the HTML document that the browser renders, and every other file (CSS, JS) is connected through it.

---

### ⚡ `app.js` — The Brain of the Game (2000+ lines)

**Why it exists:** This is the **heart and soul** of Master Mind. All game logic, user interaction, sound effects, animations, and UI rendering happen here.

**What it does:**

#### 1. Persistent Storage (`DB` object)
- Saves/loads all game progress to `localStorage` so data survives browser refreshes
- Tracks: coins, stars, and per-game stats (levels, best times, high scores)

#### 2. State Management (`state` object)
- Central data store holding the current user, active view, active game, and all saved progress
- Acts as a single source of truth for the entire application

#### 3. Sound Engine (`SoundEngine`)
- Uses the **Web Audio API** to generate all game sounds synthetically (no audio files needed!)
- Includes: click, correct, wrong, tick, heartbeat, fanfare, light beep, false start
- Has a full **background music system** with two modes:
  - *Lobby mode*: Soothing guitar-pluck arpeggios (C→G→Am→F chord progression)
  - *Suspense mode*: Slow sine-wave drones for tense gameplay
- Supports muting and auto-cleanup of all audio resources

#### 4. Four Complete Mini-Games:

**🏠 Room Observer (Spatial Memory)**
- Player observes 5–12 colored objects for 10+ seconds
- Objects disappear, then player answers "What color was the [object]?"
- Difficulty increases every 5 levels (+1 object, +2 seconds)
- Features a shop with boosters (Extra Time, Shield, Hint) purchasable with coins
- Level 300 is the "Grand Level" — ultimate challenge

**🏎️ F1 Reflex (Reaction Speed)**
- Simulates a Formula 1 race start with 5 red lights
- Lights turn on one by one, then go out after a random delay
- Player must react as fast as possible when lights go out
- Reaction time is ranked against famous F1 drivers (Senna, Verstappen, Hamilton, etc.)
- Supports keyboard (Spacebar) and mouse input
- Detects false starts (pressing too early)

**🔢 Schulte Grid (Visual Perception)**
- Grid of shuffled numbers (3×3, 4×4, 5×5, or 6×6)
- Player taps numbers 1→N² in ascending order as fast as possible
- Timer tracks completion speed; best times saved per grid size
- Incorrect taps show a brief error flash

**🎨 Color Confusion (Stroop Effect)**
- Words are shown in mismatched colors (e.g., "YELLOW" written in red)
- Player must identify the **font color**, ignoring the word text
- Three modes: Endless (3 lives), Survival (60s timer), Speed (race to 50)
- Combo system: consecutive correct answers multiply points
- Speed bonus: faster answers earn extra points

#### 5. Navigation & UI System
- **View Router**: Switches between Home, About, Help, Leaderboard
- **Game Toolbar**: Back button + mute toggle on every game screen
- **Result Cards**: Fullscreen overlays showing scores, stars, and replay options
- **Toast Notifications**: Brief popup messages for events (login, shield usage, etc.)
- **GSAP Animations**: Smooth fade-ins, slide-ups, and staggered entrances

#### 6. Authentication & Backend Sync
- Login via Google/Gmail (connects to Flask backend)
- Offline fallback: game works without a server using localStorage
- Score syncing: sends results to backend for server-side leaderboards

**Why it's needed:** This single file replaces what would normally be dozens of component files in a framework like React. It handles everything the player sees and interacts with.

---

### 🎨 `style.css` — The Visual Identity

**Why it exists:** Controls every visual aspect of the game — colors, layouts, animations, responsiveness.

**What it does:**
- Defines the **purple-gradient glassmorphism** design system
- Implements the game card layouts, navbar, modals, and game-specific UIs
- Contains all CSS animations (loading bar, card hover effects, light pulses)
- Handles responsive design for different screen sizes
- Styles the result cards, toast notifications, and Schulte Grid cells

**Why it's needed:** Without CSS, the game would be unstyled plain text. The premium visual design is what makes the game feel polished and engaging.

---

### 🐍 `app.py` — The Backend Server

**Why it exists:** Handles **server-side** operations that can't be done in the browser: user accounts, persistent database storage, and cross-device leaderboards.

**What it does:**
- **Flask web server** that serves both the game frontend and the API
- **User model**: Stores player accounts (username, email, Google ID, coins, stars)
- **GameProgress model**: Stores per-game statistics (score, level, extra data)
- **API endpoints**:
  - `POST /api/login` — Creates or finds a user account
  - `POST /api/save-progress` — Saves game results and awards coins/stars
  - `GET /api/leaderboard/<game>` — Returns top 10 players for a game
  - `POST /api/confusion/generate` — Generates Stroop questions server-side
  - `POST /api/confusion/validate` — Validates answers server-side
- Serves static files (HTML, CSS, JS) so the game works from one URL

**Why it's needed:** While the game works offline with localStorage, the backend enables:
- User accounts that persist across devices
- Global leaderboards where players compete against each other
- Server-side game logic for Color Confusion (prevents cheating)

---

### 🚀 `run.py` — One-Click Launcher

**Why it exists:** Makes starting the game extremely easy — just run one file and everything works.

**What it does:**
1. Installs all Python dependencies from `requirements.txt`
2. Starts the Flask server (`app.py`) as a background process
3. Waits 2 seconds for the server to initialize
4. Automatically opens the game in the default web browser
5. Keeps running until the user presses Ctrl+C
6. Gracefully shuts down the server on exit

**Why it's needed:** Without this, users would need to manually install dependencies, start the server, and navigate to the URL. This script automates the entire process.

---

### 🎨 `confusion_engine.py` — Stroop Effect Game Engine

**Why it exists:** The Color Confusion game has complex scoring logic (combos, speed bonuses, difficulty scaling, multiple modes) that benefits from a dedicated, well-structured module.

**What it does:**
- **StroopQuestion class**: Generates questions where the displayed word and font color are deliberately different (the Stroop Effect)
- **ConfusionEngine class**: Core logic for question generation and answer validation
  - Generates 4 answer options (1 correct + 3 distractors)
  - Calculates points with speed bonuses and combo multipliers
  - Auto-scales difficulty based on score (more colors at higher levels)
  - Assigns performance ratings (Trainee → Grandmaster)
- **GameSession class**: Manages a complete game playthrough
  - **Endless mode**: 3 lives, play until game over
  - **Survival mode**: 60-second timer, +3s for correct / −3s for wrong
  - **Speed mode**: Race to 50 correct answers

**Why it's needed:** Separating the engine from `app.py` keeps the code organized and testable. It can be run standalone for testing (`python confusion_engine.py`), and it keeps the Flask file clean.

---

### 📦 `requirements.txt` — Dependency List

**Why it exists:** Lists all Python packages the backend needs to run.

**Contents:**
- `flask` — Web server framework
- `flask-cors` — Cross-origin request support
- `flask-sqlalchemy` — Database ORM
- `python-dotenv` — Environment variable management

**Why it's needed:** Allows `pip install -r requirements.txt` to install everything automatically. Without it, users would need to manually figure out and install each dependency.

---

### 🗄️ `database.sql` — Database Schema Reference

**Why it exists:** Documents the database table structure in SQL format.

**What it defines:**
- `user` table: id, google_id, username, email, coins, stars
- `game_progress` table: id, user_id, game_type, score, level, extra_data

**Why it's needed:** Serves as a reference for anyone who wants to understand the database structure, set up a MySQL/PostgreSQL database instead of SQLite, or write custom queries.

---

### 🔄 Cross-Platform Engine Ports

#### `ConfusionEngine.cs` (C#), `ConfusionEngine.java` (Java), `confusion_engine.cpp` (C++)

**Why they exist:** These are ports of the Python `confusion_engine.py` to other programming languages.

**Why they're needed:** If the game were to be ported to:
- **Unity** (C#) for a desktop/mobile game
- **Android** (Java) for a native Android app
- **Unreal Engine or embedded** (C++) for high-performance applications

These ready-made ports would provide the same Stroop Effect logic in the target language.

---

## 🎮 How the Game Works (Flow)

```
Player opens browser
        │
        ▼
   index.html loads
        │
        ▼
   app.js runs on DOMContentLoaded
        │
        ├── Loads saved data from localStorage
        ├── Shows loading screen with progress bar
        ├── Fades to main app with GSAP animations
        └── Starts lobby background music
              │
              ▼
    Player selects a game mode card
              │
    ┌─────────┼─────────┬──────────┐
    ▼         ▼         ▼          ▼
 Room      F1       Schulte    Color
Observer  Reflex     Grid    Confusion
    │         │         │          │
    ▼         ▼         ▼          ▼
  Lobby    Race UI   Size       Mode
  Screen   Appears   Select    Select
    │         │         │          │
    ▼         ▼         ▼          ▼
  Play →   Lights →  Find     Answer
  Observe  React!    Numbers   Colors
    │         │         │          │
    ▼         ▼         ▼          ▼
  Answer   Result    Result    Result
  Questions Card     Card      Card
    │         │         │          │
    └─────────┴─────────┴──────────┘
              │
              ▼
    Score saved to localStorage + backend
    Coins & Stars updated in navbar
```

---

## 💡 Key Design Decisions

1. **Single-page app without a framework** — All views are rendered by swapping `innerHTML`, avoiding the complexity of React/Vue while keeping the game fast.

2. **Synthesized audio** — Instead of loading MP3 files, all sounds are generated live using the Web Audio API, making the game lightweight with zero audio assets.

3. **Offline-first architecture** — The game works fully offline using `localStorage`. The Flask backend is optional and adds multi-device sync and leaderboards.

4. **Progressive difficulty** — Each game gets harder as the player improves, keeping engagement high without overwhelming beginners.

5. **Combo & reward systems** — Coins, stars, combos, and speed bonuses create a satisfying feedback loop that motivates continued play.
