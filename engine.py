"""CAMPUS_SURVIVE game engine and integration coordinator."""

from copy import deepcopy

from login import DEFAULT_PLAYER, create_profile, validate_login
from questions import (
    apply_choice,
    generate_question_order,
    get_question,
)
from achievements import (
    calculate_score,
    generate_final_report,
    get_achievements,
    get_leaderboard,
)
from game.save_system import save_game as persist_player_game, load_game as load_saved_game, load_all_players


class GameEngine:
    """Coordinates game flow while keeping GUI and game logic separate."""

    def __init__(self, gui_module=None):
        self.gui = gui_module
        self.player = None
        self.current_question = None
        self.paused = False
        self.last_feedback = ""

    def _show(self, function_name, *args):
        if self.gui is not None:
            return getattr(self.gui, function_name)(*args)
        return None

    def _attach_gui_hooks(self):
        if not isinstance(self.player, dict):
            return
        # Private runtime hooks are not persisted to JSON by save_player because
        # JSON serializes only serializable values; these are callables and are
        # removed from the dictionary before persistence in save_game().
        self.player["_on_resume"] = self.resume_game
        self.player["_on_pause"] = self.pause_game
        self.player["_on_main_menu"] = self.return_to_menu
        self.player["_on_restart"] = self.restart_game
        self.player["_on_quit"] = self.quit_game
        self.player["_on_play_again"] = self.play_again
        self.player["_on_settings"] = self.open_settings

    def _clean_for_save(self, player):
        return {key: value for key, value in player.items() if not key.startswith("_on_")}

    def save_game(self, player=None):
        target = player if player is not None else self.player
        if not isinstance(target, dict):
            return False
        return persist_player_game(self._clean_for_save(target))

    def load_game(self, student_id):
        return load_saved_game(student_id)

    def _prepare_question(self):
        if not isinstance(self.player, dict):
            return None
        day = self.player.get("current_day", 1)
        if not self.player.get("question_order"):
            self.player["question_order"] = generate_question_order(self.player["student_id"])
        question = get_question(day, self.player["student_id"])
        if question is None:
            return None
        # The question data's original day is part of the source scenario ID.
        # Display/progression day is the player's current position in the run.
        question["day"] = day
        self.current_question = question
        self._attach_gui_hooks()
        return question

    def start_game(self, student_id):
        """Load a registered profile, create a missing one only if identity known elsewhere."""
        player = self.load_game(student_id)
        if player is None:
            return None
        self.player = player
        self.paused = False
        if player.get("completed"):
            # Completed run remains available as results; caller may start a fresh run.
            self.finish_game()
            return player
        if not player.get("question_order"):
            player["question_order"] = generate_question_order(student_id)
            self.save_game(player)
        question = self._prepare_question()
        if question is None:
            self.finish_game()
        else:
            self._show("show_game_screen", self.player, question, self.submit_choice)
        return player

    def next_day(self):
        """Load the next question or finish after the fifteenth completed day."""
        if not isinstance(self.player, dict):
            return None
        if self.player.get("current_day", 1) >= 15:
            self.finish_game()
            return None
        self.player["current_day"] += 1
        self.paused = False
        question = self._prepare_question()
        self.save_game()
        if question is None:
            self.finish_game()
        else:
            self._show("show_game_screen", self.player, question, self.submit_choice)
        return question

    def submit_choice(self, choice_index):
        """Apply a decision, record history, save, then advance to next day."""
        if not isinstance(self.player, dict) or not isinstance(self.current_question, dict):
            return False
        try:
            question = self.current_question
            player, feedback = apply_choice(self.player, question, choice_index)
        except (ValueError, TypeError, IndexError) as exc:
            self._show("show_message", str(exc), "error")
            return False

        choice = question["choices"][choice_index]
        player.setdefault("answers", []).append({
            "day": player.get("current_day", 1),
            "question_id": question.get("id"),
            "choice_index": choice_index,
            "choice_text": choice.get("text", ""),
            "feedback": feedback,
        })
        self.last_feedback = feedback
        if not self.save_game(player):
            self._show("show_message", "Progress could not be saved. Check data/players.json permissions.", "error")
        else:
            self._show("show_message", feedback, "success")

        # If the GUI has been shown from a choice callback, continue after feedback.
        self.next_day()
        return True

    def restart_game(self):
        """Reset run progress/stats while preserving student identity and settings."""
        if not isinstance(self.player, dict):
            return False
        student_id = self.player["student_id"]
        name = self.player["name"]
        settings = deepcopy(self.player.get("settings", DEFAULT_PLAYER["settings"]))
        fresh = deepcopy(DEFAULT_PLAYER)
        fresh["student_id"] = student_id
        fresh["name"] = name
        fresh["settings"] = settings
        fresh["question_order"] = generate_question_order(student_id)
        self.player = fresh
        self.paused = False
        self.save_game()
        self._prepare_question()
        self._show("show_game_screen", self.player, self.current_question, self.submit_choice)
        return True

    def return_to_menu(self):
        """Save without deleting progress and display home menu."""
        if isinstance(self.player, dict):
            self.save_game()
            self._attach_gui_hooks()
            self._show("show_home", self.player, self.handle_home_action)
        return True

    def pause_game(self):
        if not isinstance(self.player, dict):
            return False
        self.paused = True
        self.save_game()
        self._attach_gui_hooks()
        self._show(
            "show_pause_menu", self.resume_game, self.return_to_menu,
            self.restart_game, self.quit_game
        )
        return True

    def resume_game(self):
        if not isinstance(self.player, dict):
            return False
        self.paused = False
        question = self._prepare_question()
        if question:
            self._show("show_game_screen", self.player, question, self.submit_choice)
            return True
        self.finish_game()
        return False

    def finish_game(self):
        if not isinstance(self.player, dict):
            return None
        self.player["completed"] = True
        calculate_score(self.player)
        get_achievements(self.player)
        report = generate_final_report(self.player)
        # Store completed state before generating the leaderboard.
        self.save_game()
        players = load_all_players()
        # Use the in-memory current profile, including the freshly calculated score.
        replaced = False
        for index, candidate in enumerate(players):
            if candidate.get("student_id") == self.player.get("student_id"):
                players[index] = self._clean_for_save(self.player)
                replaced = True
                break
        if not replaced:
            players.append(self._clean_for_save(self.player))
        leaderboard = get_leaderboard(players)
        self._attach_gui_hooks()
        self._show("show_results", self.player, report, leaderboard)
        return report

    def open_settings(self):
        if not isinstance(self.player, dict):
            return False
        self._attach_gui_hooks()
        self._show(
            "show_settings", self.player, self.resume_game, self.return_to_menu,
            self.restart_game, self.quit_game
        )
        return True

    def handle_home_action(self, action):
        if action == "continue":
            if isinstance(self.player, dict) and self.player.get("completed") is True:
                return self.finish_game()
            return self.resume_game()
        if action == "new_game":
            if self.gui:
                confirmed = self._show("show_message", "Start a fresh run? Current run progress will be reset.", "confirmation")
                if not confirmed:
                    return False
            return self.restart_game()
        if action == "settings":
            return self.open_settings()
        if action == "quit":
            return self.quit_game()
        return None

    def quit_game(self):
        if isinstance(self.player, dict):
            self.save_game()
        if self.gui is not None:
            root = getattr(self.gui, "_root", None)
            if root is not None and root.winfo_exists():
                root.destroy()
        return True

    def play_again(self):
        if self.gui:
            confirmed = self._show("show_message", "Start a new semester? This resets this run's stats.", "confirmation")
            if not confirmed:
                return False
        return self.restart_game()


# Module-level API requested in the assignment, backed by a default engine.
_default_engine = None


def configure(gui_module=None):
    global _default_engine
    _default_engine = GameEngine(gui_module=gui_module)
    return _default_engine


def _engine():
    global _default_engine
    if _default_engine is None:
        _default_engine = GameEngine()
    return _default_engine


def start_game(student_id):
    return _engine().start_game(student_id)


def next_day():
    return _engine().next_day()


def submit_choice(choice_index):
    return _engine().submit_choice(choice_index)


def restart_game():
    return _engine().restart_game()


def return_to_menu():
    return _engine().return_to_menu()


def pause_game():
    return _engine().pause_game()


def resume_game():
    return _engine().resume_game()


def finish_game():
    return _engine().finish_game()


def clamp_stats(player):
    """Clamp five 0..100 stats and ensure money never goes below zero."""
    for key in ("happiness", "attendance", "grades", "energy", "stress"):
        value = player.get(key, 0)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            player[key] = max(0, min(100, value))
        else:
            player[key] = 0
    money = player.get("money", 0)
    player["money"] = max(0, money) if isinstance(money, (int, float)) and not isinstance(money, bool) else 0
    return player


def save_game(player):
    return _engine().save_game(player)


def load_game(student_id):
    return _engine().load_game(student_id)
