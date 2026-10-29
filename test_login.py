"""Working integration tests for login.py.

Run from the project directory:
    python -m unittest discover -s tests -v

Tests use a temporary JSON file and do not alter data/players.json.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import login


class LoginModuleTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temp_dir.name) / "players.json"
        self.patch_file = patch.object(login, "DATA_FILE", self.data_file)
        self.patch_file.start()

    def tearDown(self):
        self.patch_file.stop()
        self.temp_dir.cleanup()

    def test_create_profile_uses_exact_default_schema(self):
        player = login.create_profile("MCA001", "Mannu")
        self.assertIsNotNone(player)
        self.assertEqual(
            set(player.keys()),
            {
                "student_id", "name", "current_day", "completed", "happiness",
                "attendance", "grades", "energy", "stress", "money", "score",
                "answers", "achievements", "question_order", "settings",
            },
        )
        self.assertEqual(player["student_id"], "MCA001")
        self.assertEqual(player["settings"], {
            "music": True, "sound_effects": True, "volume": 50
        })

    def test_duplicate_student_id_is_rejected(self):
        self.assertIsNotNone(login.create_profile("MCA001", "Mannu"))
        self.assertIsNone(login.create_profile("MCA001", "Someone Else"))

    def test_login_and_availability(self):
        self.assertFalse(login.validate_login("MCA001"))
        self.assertTrue(login.is_student_id_available("MCA001"))
        login.create_profile("MCA001", "Mannu")
        self.assertTrue(login.validate_login("MCA001"))
        self.assertFalse(login.is_student_id_available("MCA001"))

    def test_save_load_progress_and_preserve_other_students(self):
        first = login.create_profile("MCA001", "Mannu")
        second = login.create_profile("MCA002", "Aarav")
        first["current_day"] = 4
        first["score"] = 350
        first["answers"].append("Q1:B")
        self.assertTrue(login.save_player(first))

        loaded = login.load_player("MCA001")
        self.assertEqual(loaded["current_day"], 4)
        self.assertEqual(loaded["score"], 350)
        self.assertEqual(loaded["answers"], ["Q1:B"])

        saved = json.loads(self.data_file.read_text(encoding="utf-8"))
        self.assertIn("MCA001", saved)
        self.assertIn("MCA002", saved)
        self.assertEqual(saved["MCA002"]["name"], second["name"])

    def test_missing_profile_returns_none(self):
        self.assertIsNone(login.load_player("UNKNOWN"))

    def test_missing_file_is_safe(self):
        self.assertFalse(login.validate_login("MCA001"))
        self.assertIsNone(login.load_player("MCA001"))
        self.assertTrue(login.is_student_id_available("MCA001"))

    def test_invalid_json_is_safe(self):
        self.data_file.write_text("{invalid json", encoding="utf-8")
        self.assertFalse(login.validate_login("MCA001"))
        self.assertIsNone(login.load_player("MCA001"))
        self.assertTrue(login.is_student_id_available("MCA001"))

    def test_save_rejects_unregistered_player(self):
        self.assertFalse(login.save_player({"student_id": "UNKNOWN", "name": "X"}))


if __name__ == "__main__":
    unittest.main(verbosity=2)
