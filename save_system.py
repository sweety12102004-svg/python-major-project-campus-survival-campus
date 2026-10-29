"""Persistence adapters for CAMPUS_SURVIVE.

This module delegates single-profile reads/writes to login.py so the agreed
profile format and Student-ID keyed database stay consistent.
"""

import json
from pathlib import Path

from login import DATA_FILE, load_player, save_player


def save_game(player):
    """Persist current player state. Return True on success, False otherwise."""
    return save_player(player)


def load_game(student_id):
    """Load one registered player's saved state, or return None."""
    return load_player(student_id)


def load_all_players():
    """Load every profile for leaderboard generation; malformed files are safe."""
    try:
        with Path(DATA_FILE).open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return []
    if not isinstance(data, dict):
        return []
    return [profile for profile in data.values() if isinstance(profile, dict)]
