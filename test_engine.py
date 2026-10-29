"""Integration tests for Module 5; no graphical display is required."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import login
from game.engine import GameEngine, clamp_stats
import game.save_system as save_system


class FakeGUI:
    def __init__(self):
        self.calls = []
    def __getattr__(self, name):
        def record(*args):
            self.calls.append((name, args))
            return None
        return record


class EngineIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data_file = Path(self.tmp.name) / "players.json"
        self.login_patch = patch.object(login, "DATA_FILE", self.data_file)
        self.login_patch.start()
        self.save_patch = patch.object(save_system, "DATA_FILE", self.data_file)
        self.save_patch.start()
        # save_system functions import login functions, which read login.DATA_FILE.
        self.gui = FakeGUI()
        self.engine = GameEngine(self.gui)

    def tearDown(self):
        self.save_patch.stop()
        self.login_patch.stop()
        self.tmp.cleanup()

    def create(self):
        player = login.create_profile("MCA001", "Mannu")
        self.assertIsNotNone(player)
        return player

    def test_start_and_submit_choice_persists_progress(self):
        self.create()
        player = self.engine.start_game("MCA001")
        self.assertEqual(player["current_day"], 1)
        self.assertIsNotNone(self.engine.current_question)
        self.assertTrue(self.engine.submit_choice(0))
        loaded = login.load_player("MCA001")
        self.assertEqual(loaded["current_day"], 2)
        self.assertEqual(len(loaded["answers"]), 1)
        self.assertEqual(self.gui.calls[-1][0], "show_game_screen")

    def test_restart_preserves_identity_resets_stats_and_day(self):
        self.create()
        self.engine.start_game("MCA001")
        self.engine.player["grades"] = 20
        self.engine.player["current_day"] = 7
        self.engine.restart_game()
        self.assertEqual(self.engine.player["student_id"], "MCA001")
        self.assertEqual(self.engine.player["name"], "Mannu")
        self.assertEqual(self.engine.player["grades"], 70)
        self.assertEqual(self.engine.player["current_day"], 1)

    def test_return_to_menu_saves_progress(self):
        self.create()
        self.engine.start_game("MCA001")
        self.engine.player["current_day"] = 5
        self.engine.return_to_menu()
        self.assertEqual(login.load_player("MCA001")["current_day"], 5)

    def test_finish_game_sets_completed_and_shows_results(self):
        self.create()
        self.engine.start_game("MCA001")
        self.engine.player["current_day"] = 15
        report = self.engine.finish_game()
        self.assertTrue(self.engine.player["completed"])
        self.assertIsNotNone(report)
        self.assertEqual(self.gui.calls[-1][0], "show_results")


    def test_module_level_save_game_api(self):
        from game.engine import save_game
        player = self.create()
        self.assertTrue(save_game(player))

    def test_clamp_stats(self):
        player = {"happiness": 150, "attendance": -1, "grades": 50,
                  "energy": 101, "stress": -10, "money": -900}
        clamp_stats(player)
        self.assertEqual(
            [player[k] for k in ("happiness", "attendance", "grades", "energy", "stress", "money")],
            [100, 0, 50, 100, 0, 0],
        )

    def test_separate_student_profiles_are_preserved(self):
        self.create()
        login.create_profile("MCA002", "Aarav")
        self.engine.start_game("MCA001")
        self.engine.player["score"] = 321
        self.engine.save_game()
        data = json.loads(self.data_file.read_text(encoding="utf-8"))
        self.assertIn("MCA001", data)
        self.assertIn("MCA002", data)
        self.assertEqual(data["MCA002"]["name"], "Aarav")


if __name__ == "__main__":
    unittest.main(verbosity=2)
