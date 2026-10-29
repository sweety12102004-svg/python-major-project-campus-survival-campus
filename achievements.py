"""CAMPUS_SURVIVE Module 3: Score, Achievements & Leaderboard.

No GUI imports and no file persistence. The caller (game engine/login module)
is responsible for saving player data and deciding when the game is complete.

Score formula (maximum 100 points):
    1. Grades:      30% weight (grades / 100 * 30)
    2. Attendance:  20% weight (attendance / 100 * 20)
    3. Happiness:   15% weight (happiness / 100 * 15)
    4. Energy:      10% weight (energy / 100 * 10)
    5. Stress:      15% weight ((100 - stress) / 100 * 15)
    6. Money:       10% weight (min(money, 5000) / 5000 * 10)

Each input is bounded to its expected range before scoring. Money score caps at
₹5,000 so saving more money cannot push the total above 100. The final score is
rounded to the nearest whole number and stored in player["score"].

Rating thresholds are percentages of the 100-point score:
    80-100: Excellent
    60-79:  Good
    40-59:  Average
    0-39:   Needs Improvement

Leaderboard tie handling: players are sorted by score descending; equal scores
are ordered by Student ID ascending (case-insensitive), then name ascending.
Ranks use competition ranking (1, 1, 3): tied players share the same rank and
the next rank skips accordingly.
"""

from copy import deepcopy

MAX_SCORE = 100
MONEY_SCORE_CAP = 5000

SCORE_WEIGHTS = {
    "grades": 30,
    "attendance": 20,
    "happiness": 15,
    "energy": 10,
    "stress": 15,  # uses inverse stress: lower stress is better
    "money": 10,
}

BADGE_RULES = (
    ("Topper", lambda player: _number(player, "grades") >= 90),
    ("Attendance Hero", lambda player: _number(player, "attendance") >= 90),
    ("Happy Soul", lambda player: _number(player, "happiness") >= 90),
    ("Energy Master", lambda player: _number(player, "energy") >= 90),
    ("Money Saver", lambda player: _number(player, "money") >= 5000),
    ("Stress Survivor", lambda player: _number(player, "stress") <= 20),
)


def _number(player, key, default=0):
    """Read a numeric player stat safely; invalid/missing values use default."""
    value = player.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return default
    return value


def _clamp(value, low=0, high=100):
    return max(low, min(high, value))


def calculate_score(player):
    """Calculate a consistent 0..100 score and update player['score']."""
    if not isinstance(player, dict):
        raise TypeError("player must be a dictionary")

    grades = _clamp(_number(player, "grades"))
    attendance = _clamp(_number(player, "attendance"))
    happiness = _clamp(_number(player, "happiness"))
    energy = _clamp(_number(player, "energy"))
    stress = _clamp(_number(player, "stress"))
    money = max(0, _number(player, "money"))

    score = (
        grades / 100 * SCORE_WEIGHTS["grades"]
        + attendance / 100 * SCORE_WEIGHTS["attendance"]
        + happiness / 100 * SCORE_WEIGHTS["happiness"]
        + energy / 100 * SCORE_WEIGHTS["energy"]
        + (100 - stress) / 100 * SCORE_WEIGHTS["stress"]
        + min(money, MONEY_SCORE_CAP) / MONEY_SCORE_CAP * SCORE_WEIGHTS["money"]
    )
    final_score = max(0, min(MAX_SCORE, round(score)))
    player["score"] = final_score
    return final_score


def get_achievements(player):
    """Award earned badges without duplicates; return a copy of the badge list."""
    if not isinstance(player, dict):
        raise TypeError("player must be a dictionary")

    existing = player.get("achievements")
    if not isinstance(existing, list):
        existing = []
        player["achievements"] = existing

    for badge_name, condition in BADGE_RULES:
        if condition(player) and badge_name not in existing:
            existing.append(badge_name)

    return list(existing)


def get_performance_rating(player):
    """Return the rating label based on player['score'] (0..100)."""
    if not isinstance(player, dict):
        raise TypeError("player must be a dictionary")

    score = _clamp(_number(player, "score"))
    if score >= 80:
        return "Excellent"
    if score >= 60:
        return "Good"
    if score >= 40:
        return "Average"
    return "Needs Improvement"


def generate_final_report(player):
    """Return a report dictionary, only if player['completed'] is True.

    The game engine should call this after setting completed=True. Otherwise,
    None is returned so an unfinished run is not presented as a final report.
    """
    if not isinstance(player, dict):
        raise TypeError("player must be a dictionary")
    if player.get("completed") is not True:
        return None

    final_score = calculate_score(player)
    badges = get_achievements(player)
    rating = get_performance_rating(player)

    stats = {
        "happiness": _clamp(_number(player, "happiness")),
        "attendance": _clamp(_number(player, "attendance")),
        "grades": _clamp(_number(player, "grades")),
        "energy": _clamp(_number(player, "energy")),
        "stress": _clamp(_number(player, "stress")),
        "money": max(0, _number(player, "money")),
    }

    if final_score >= 80:
        summary = "Strong overall semester performance with a healthy balance of progress and wellbeing."
    elif final_score >= 60:
        summary = "Good progress overall. Review the weaker stats to make the next semester more balanced."
    elif final_score >= 40:
        summary = "A mixed semester. A few focused changes to study habits, attendance, or wellbeing can help."
    else:
        summary = "This semester was challenging. Start with small, realistic goals and build consistency."

    return {
        "student_id": player.get("student_id", ""),
        "name": player.get("name", ""),
        "completed": True,
        "final_score": final_score,
        "performance_rating": rating,
        "stats": stats,
        "achievements": badges,
        "summary": summary,
    }


def get_leaderboard(players):
    """Return sorted leaderboard entries with competition ranks.

    Expected input: list of player dictionaries. Missing/invalid scores are
    treated as zero. Equal scores share a rank; ties are ordered deterministically
    by Student ID and name.
    """
    if not isinstance(players, (list, tuple)):
        raise TypeError("players must be a list or tuple of player dictionaries")

    valid_players = [player for player in players if isinstance(player, dict)]
    ordered = sorted(
        valid_players,
        key=lambda player: (
            -_clamp(_number(player, "score")),
            str(player.get("student_id", "")).casefold(),
            str(player.get("name", "")).casefold(),
        ),
    )

    leaderboard = []
    previous_score = None
    current_rank = 0

    for position, player in enumerate(ordered, start=1):
        score = _clamp(_number(player, "score"))
        if previous_score is None or score != previous_score:
            current_rank = position
        leaderboard.append({
            "rank": current_rank,
            "student_id": player.get("student_id", ""),
            "name": player.get("name", ""),
            "score": score,
        })
        previous_score = score

    return leaderboard
