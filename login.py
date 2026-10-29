"""Student login and profile management for CAMPUS_SURVIVE.

The public function names, parameters, and return values in this module are
intended to remain stable for integration with the other game modules.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

DATA_FILE = Path(__file__).resolve().parent / "data" / "players.json"

# Canonical keys and defaults for the shared player dictionary.
DEFAULT_PLAYER = {
    "student_id": "",
    "name": "",
    "current_day": 1,
    "completed": False,
    "happiness": 80,
    "attendance": 100,
    "grades": 70,
    "energy": 100,
    "stress": 10,
    "money": 5000,
    "score": 0,
    "answers": [],
    "achievements": [],
    "question_order": [],
    "settings": {
        "music": True,
        "sound_effects": True,
        "volume": 50,
    },
}


def _read_players() -> Dict[str, Dict[str, Any]]:
    """Read all profiles; safely treat a missing or malformed file as empty."""
    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError, OSError, UnicodeDecodeError):
        return {}

    if not isinstance(data, dict):
        return {}

    # Keep only entries whose IDs and profile values have expected basic types.
    players: Dict[str, Dict[str, Any]] = {}
    for student_id, profile in data.items():
        if isinstance(student_id, str) and isinstance(profile, dict):
            players[student_id] = profile
    return players


def _write_players(players: Dict[str, Dict[str, Any]]) -> bool:
    """Atomically write all profiles to reduce the risk of a partial JSON file."""
    try:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(
            prefix="players_", suffix=".tmp", dir=str(DATA_FILE.parent)
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as file:
                json.dump(players, file, indent=4, ensure_ascii=False)
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())
            os.replace(temp_name, DATA_FILE)
        finally:
            if os.path.exists(temp_name):
                os.remove(temp_name)
        return True
    except (OSError, TypeError, ValueError):
        return False


def _normalise_profile(student_id: str, profile: Dict[str, Any]) -> Dict[str, Any]:
    """Fill absent fields from defaults while preserving saved progress."""
    player = {
        key: (value.copy() if isinstance(value, (dict, list)) else value)
        for key, value in DEFAULT_PLAYER.items()
    }
    player.update(profile)
    player["student_id"] = student_id

    # Ensure settings contain all expected keys, without discarding saved values.
    saved_settings = player.get("settings")
    settings = DEFAULT_PLAYER["settings"].copy()
    if isinstance(saved_settings, dict):
        settings.update(saved_settings)
    player["settings"] = settings

    for key in ("answers", "achievements", "question_order"):
        if not isinstance(player.get(key), list):
            player[key] = []

    return player


def create_profile(student_id, name):
    """Create and persist a new profile. Return the profile, or None if unavailable."""
    if not isinstance(student_id, str) or not student_id.strip():
        return None
    if not isinstance(name, str) or not name.strip():
        return None

    student_id = student_id.strip()
    name = name.strip()
    players = _read_players()

    if student_id in players:
        return None

    player = _normalise_profile(
        student_id,
        {
            **DEFAULT_PLAYER,
            "student_id": student_id,
            "name": name,
            "settings": DEFAULT_PLAYER["settings"].copy(),
            "answers": [],
            "achievements": [],
            "question_order": [],
        },
    )
    players[student_id] = player

    if not _write_players(players):
        return None
    return player


def validate_login(student_id):
    """Return True if the Student ID is registered, otherwise False."""
    if not isinstance(student_id, str) or not student_id.strip():
        return False
    return student_id.strip() in _read_players()


def load_player(student_id):
    """Load a complete saved profile; return None if the Student ID is absent."""
    if not isinstance(student_id, str) or not student_id.strip():
        return None

    student_id = student_id.strip()
    players = _read_players()
    profile = players.get(student_id)
    if not isinstance(profile, dict):
        return None

    player = _normalise_profile(student_id, profile)
    # Persist any newly-added default fields for forward compatibility.
    players[student_id] = player
    _write_players(players)
    return player


def save_player(player):
    """Save a player's latest state without overwriting any other student's data."""
    if not isinstance(player, dict):
        return False

    student_id = player.get("student_id")
    if not isinstance(student_id, str) or not student_id.strip():
        return False

    student_id = student_id.strip()
    players = _read_players()

    # Do not accidentally create a registered profile from an arbitrary dict.
    if student_id not in players:
        return False

    normalised = _normalise_profile(student_id, player)
    players[student_id] = normalised
    return _write_players(players)


def is_student_id_available(student_id):
    """Return True when a non-empty Student ID is not already registered."""
    if not isinstance(student_id, str) or not student_id.strip():
        return False
    return student_id.strip() not in _read_players()
