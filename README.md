# Playline – Online Gaming Hub

A Python Flask mini project with a neon gaming dashboard and six browser games.

## Features
- User registration, login and logout (passwords are hashed).
- Neon dashboard with play statistics and recent activity.
- Six playable games: Tic Tac Toe, Neon Snake, 2048, Rock Paper Scissors, Memory Match and Number Guessing.
- Game search and category filtering.
- Favourite games, score history and leaderboard.
- SQLite database created automatically on first run.

## Requirements
- Python 3.9 or newer
- VS Code (recommended)

## Run in VS Code

### Windows (PowerShell)
```powershell
cd Playline
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py app.py
```

If PowerShell blocks activation, run this once in the current terminal:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

### Windows (Command Prompt)
```bat
cd Playline
py -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
py app.py
```

Open **http://127.0.0.1:5000** in your browser. Register an account to start playing.

## Database
`playline.db` is generated automatically beside `app.py`. It contains:
- `users` – account details and password hashes
- `scores` – saved game scores
- `favorites` – each user's favourite games

To reset all project data, stop Flask and delete `playline.db`. It will be recreated on the next run.

## Project structure
```text
Playline/
├── app.py
├── requirements.txt
├── README.md
├── playline.db          # generated on first run
├── static/
│   ├── css/style.css
│   └── js/games.js
└── templates/
    ├── base.html
    ├── landing.html
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── games.html
    ├── play.html
    ├── leaderboard.html
    └── profile.html
```

## Notes for submission
- This is a local academic demonstration project, not a production multiplayer service.
- Scores are stored when a game finishes. Some games use score/attempt-based scoring.
- For deployment, set a strong `PLAYLINE_SECRET` environment variable, disable Flask debug mode, and add CSRF protection and HTTPS.


## Shared game setup and local multiplayer
All six games include Easy, Medium and Hard difficulty, AI opponent mode, local same-device two-player mode, and Playline points. Friends mode is pass-and-play; it does not require internet or a second account. Snake and 2048 compare two consecutive runs. Tic Tac Toe, Rock Paper Scissors, Memory Match and Number Guessing use turn-based play. Difficulty changes game speed, AI behaviour, target score, pair count, number range or attempts depending on the game. The signed-in account's earned points are saved to the SQLite leaderboard.
