"""Tests for CAMPUS_SURVIVE Module 2. Run from project root:
python -m unittest discover -s tests -v
"""

import unittest
import questions


class QuestionsModuleTests(unittest.TestCase):
    def setUp(self):
        self.player = {
            "student_id": "MCA001", "name": "Mannu", "current_day": 1,
            "completed": False, "happiness": 80, "attendance": 100,
            "grades": 70, "energy": 100, "stress": 10, "money": 5000,
            "score": 0, "answers": [], "achievements": [], "question_order": [],
            "settings": {"music": True, "sound_effects": True, "volume": 50},
        }

    def test_all_15_days_and_question_shape(self):
        self.assertEqual(len(questions.QUESTIONS), 15)
        for question in questions.QUESTIONS:
            self.assertEqual(set(question), {"id", "day", "title", "scenario", "choices"})
            self.assertGreaterEqual(len(question["choices"]), 3)
            self.assertLessEqual(len(question["choices"]), 4)
            for choice in question["choices"]:
                self.assertEqual(set(choice), {"text", "effects", "feedback"})
                self.assertEqual(set(choice["effects"]), set(questions.STAT_KEYS))

    def test_get_question_valid_and_invalid_day(self):
        self.assertIsNotNone(questions.get_question(1, "MCA001"))
        self.assertIsNone(questions.get_question(0, "MCA001"))
        self.assertIsNone(questions.get_question(16, "MCA001"))
        self.assertIsNone(questions.get_question(1, ""))

    def test_get_question_by_id(self):
        question = questions.get_question_by_id("D1Q1")
        self.assertEqual(question["title"], "Assignment Deadline")
        self.assertIsNone(questions.get_question_by_id("NOPE"))
        question["title"] = "changed copy"
        self.assertEqual(questions.get_question_by_id("D1Q1")["title"], "Assignment Deadline")

    def test_question_bank_includes_internship_decisions(self):
        internship_questions = [
            question for question in questions.QUESTIONS
            if "internship" in (question["title"] + " " + question["scenario"]).lower()
        ]
        self.assertGreaterEqual(len(internship_questions), 2)
        for question in internship_questions:
            self.assertGreaterEqual(len(question["choices"]), 3)
            self.assertTrue(all(choice["feedback"] for choice in question["choices"]))

    def test_order_has_15_unique_ids_and_is_stable_per_student(self):
        first = questions.generate_question_order("MCA001")
        second = questions.generate_question_order("MCA001")
        other = questions.generate_question_order("MCA002")
        self.assertEqual(len(first), 15)
        self.assertEqual(len(set(first)), 15)
        self.assertEqual(first, second)
        self.assertNotEqual(first, other)

    def test_get_question_uses_student_order(self):
        order = questions.generate_question_order("MCA001")
        self.assertEqual(questions.get_question(1, "MCA001")["id"], order[0])

    def test_apply_choice_updates_stats_and_returns_feedback(self):
        question = questions.get_question_by_id("D1Q1")
        player, feedback = questions.apply_choice(self.player, question, 0)
        self.assertEqual(player["grades"], 80)
        self.assertEqual(player["energy"], 90)
        self.assertEqual(player["stress"], 5)
        self.assertIn("assignment", feedback.lower())
        self.assertEqual(player["current_day"], 1)  # no automatic day advance

    def test_stats_are_clamped_and_money_never_negative(self):
        self.player.update({
            "happiness": 98, "attendance": 98, "grades": 98,
            "energy": 3, "stress": 98, "money": 20
        })
        question = {
            "id": "TEST", "day": 1, "title": "Bounds", "scenario": "Test",
            "choices": [{
                "text": "Extreme", "effects": {
                    "happiness": 20, "attendance": 20, "grades": 20,
                    "energy": -50, "stress": 20, "money": -1000
                }, "feedback": "Bounds checked."
            }]
        }
        player, _ = questions.apply_choice(self.player, question, 0)
        for stat in questions.CLAMPED_STATS:
            self.assertGreaterEqual(player[stat], 0)
            self.assertLessEqual(player[stat], 100)
        self.assertEqual(player["energy"], 0)
        self.assertEqual(player["money"], 0)

    def test_invalid_choice_raises_without_mutation(self):
        question = questions.get_question_by_id("D1Q1")
        before = self.player.copy()
        with self.assertRaises(ValueError):
            questions.apply_choice(self.player, question, 99)
        self.assertEqual(self.player, before)

    def test_feedback_invalid_choice_raises(self):
        question = questions.get_question_by_id("D1Q1")
        with self.assertRaises(ValueError):
            questions.get_choice_feedback(question, -1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
