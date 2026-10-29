# Campus Survival

A decision-making game about balancing academics, campus life, personal well-being, and career opportunities throughout a college semester.

## Requirements
- Python 3.10+ recommended
- Tkinter (usually bundled with Python; on some Linux distributions install `python3-tk`)
- No third-party packages required

## Run the game
From this folder:
```bash
python main.py
```

## Run tests
```bash
python -m unittest discover -s tests -v
```

## Project map
- `main.py`: entry point and login-to-home integration.
- `login.py`: student profiles and `data/players.json` persistence.
- `questions.py`: 15 college-life scenarios covering assignments, exams, internships, finances, teamwork, and well-being, with student-specific question order, choice outcomes, and feedback.
- `achievements.py`: score formula, badges, final report and leaderboard.
- `gui.py`: Tkinter screens and callbacks.
- `game/engine.py`: game flow, choice submission, day progression, restart, pause/resume and completion.
- `game/save_system.py`: adapters for saving/loading individual profiles and loading leaderboard data.
- `tests/`: module and integration tests.

## Game flow
1. Enter a Student ID and name. New IDs create profiles; registered IDs load existing profiles.
2. Continue Game resumes the saved day. New Game resets run stats but keeps the student's ID, name and settings.
3. Select one choice per day. Each scenario presents realistic trade-offs; the selected choice affects the student's academic, financial, and well-being stats. Answers are recorded and progress is saved.
4. After Day 15, the engine marks the player completed, calculates the score/badges, and displays the report and leaderboard.
5. Main Menu saves progress. Settings update `player["settings"]`.

## Score formula
- Grades 30%, attendance 20%, happiness 15%, energy 10%, low stress 15%, money 10% (money points cap at ₹5,000).
- Ratings: 80–100 Excellent; 60–79 Good; 40–59 Average; 0–39 Needs Improvement.
- Equal leaderboard scores share a rank; ties sort by Student ID then name.

## Integration notes
- The GUI does not implement scoring, question selection, or persistence.
- `show_login` calls the callback for both Login/Continue and Create Profile; `main.py` checks registration and creates only unknown IDs.
- The first GUI release intentionally has no music playback, so it has no dependency on optional `pygame` or missing audio files. Music/sound settings are stored and ready for an audio layer.
- Player runtime callbacks are private `_on_*` keys and are removed before saving.
