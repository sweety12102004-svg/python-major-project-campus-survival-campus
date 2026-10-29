"""Tests for CAMPUS_SURVIVE Module 3.

Run from this directory:
    python -m unittest discover -s tests -v
"""

import unittest
from achievements import (
    calculate_score,
    get_achievements,
    generate_final_report,
    get_leaderboard,
    get_performance_rating,
)


def make_player(student_id="MCA001", name="Mannu", **overrides):
    player = {
        "student_id": student_id,
        "name": name,
        "current_day": 15,
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
        "settings": {"music": True, "sound_effects": True, "volume": 50},
    }
    player.update(overrides)
    return player


class AchievementsModuleTests(unittest.TestCase):
    def test_score_formula_and_player_update(self):
        player = make_player(
            grades=100, attendance=100, happiness=100,
            energy=100, stress=0, money=5000
        )
        self.assertEqual(calculate_score(player), 100)
        self.assertEqual(player["score"], 100)

    def test_score_is_bounded_for_out_of_range_stats(self):
        player = make_player(
            grades=200, attendance=-10, happiness=1000,
            energy=100, stress=-50, money=100000
        )
        score = calculate_score(player)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_earned_badges_are_added_once(self):
        player = make_player(
            grades=95, attendance=95, happiness=95, energy=95,
            stress=10, money=6000, achievements=["Topper"]
        )
        badges = get_achievements(player)
        self.assertEqual(len(badges), len(set(badges)))
        self.assertEqual(badges.count("Topper"), 1)
        for badge in (
            "Topper", "Attendance Hero", "Happy Soul",
            "Energy Master", "Money Saver", "Stress Survivor"
        ):
            self.assertIn(badge, badges)
        self.assertEqual(get_achievements(player), badges)

    def test_performance_rating_thresholds(self):
        cases = [
            (100, "Excellent"), (80, "Excellent"),
            (79, "Good"), (60, "Good"),
            (59, "Average"), (40, "Average"),
            (39, "Needs Improvement"), (0, "Needs Improvement"),
        ]
        for score, expected in cases:
            with self.subTest(score=score):
                self.assertEqual(
                    get_performance_rating(make_player(score=score)), expected
                )

    def test_report_not_generated_until_completed(self):
        player = make_player()
        self.assertIsNone(generate_final_report(player))
        player["completed"] = True
        report = generate_final_report(player)
        self.assertIsInstance(report, dict)
        self.assertTrue(report["completed"])
        self.assertEqual(report["student_id"], "MCA001")
        self.assertEqual(report["name"], "Mannu")
        self.assertIn("final_score", report)
        self.assertIn("stats", report)
        self.assertIn("achievements", report)
        self.assertIn("summary", report)
        self.assertEqual(player["score"], report["final_score"])

    def test_leaderboard_descending_and_tie_handling(self):
        players = [
            make_player("MCA003", "Zoya", score=80),
            make_player("MCA002", "Aarav", score=90),
            make_player("MCA001", "Mannu", score=90),
            make_player("MCA004", "Dev", score=70),
        ]
        board = get_leaderboard(players)
        self.assertEqual(
            [(entry["rank"], entry["student_id"], entry["score"]) for entry in board],
            [
                (1, "MCA001", 90),
                (1, "MCA002", 90),
                (3, "MCA003", 80),
                (4, "MCA004", 70),
            ],
        )
        self.assertEqual(set(board[0]), {"rank", "student_id", "name", "score"})

    def test_leaderboard_does_not_mutate_players(self):
        players = [make_player(score=45), make_player("MCA002", "Aarav", score=88)]
        original = [player.copy() for player in players]
        get_leaderboard(players)
        self.assertEqual(players, original)

    def test_empty_leaderboard(self):
        self.assertEqual(get_leaderboard([]), [])

    def test_incomplete_or_invalid_achievements_list_is_repaired(self):
        player = make_player(grades=95, achievements=None)
        self.assertIn("Topper", get_achievements(player))
        self.assertIsInstance(player["achievements"], list)


if __name__ == "__main__":
    unittest.main(verbosity=2)
