import os
import tempfile
import unittest

import app


class QuizApplicationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_db_path = app.DB_PATH
        app.DB_PATH = os.path.join(self.temp_dir.name, "test_quiz.sqlite3")
        app.init_db()
        app.app.config["TESTING"] = True
        self.client = app.app.test_client()
        self.categories = app.get_categories()

    def tearDown(self):
        app.DB_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_homepage_lists_categories_and_questions(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"General Knowledge", response.data)
        self.assertIn(b"16 questions ready", response.data)

    def test_category_quiz_scores_correct_answers(self):
        category = self.categories[0]
        questions = app.get_questions_for_category(category["id"])
        answers = {"category_id": str(category["id"])}
        for question in questions:
            answers[f"answer_{question['id']}"] = question["correct_option"]

        response = self.client.post("/submit_quiz", data=answers)

        self.assertEqual(response.status_code, 302)
        attempt_id = int(response.headers["Location"].rsplit("/", 1)[-1])
        attempt = app.get_attempt_by_id(attempt_id)
        self.assertEqual(attempt["score"], len(questions))
        self.assertEqual(attempt["unanswered"], 0)
        self.assertEqual(attempt["percentage"], 100)

    def test_unanswered_questions_are_saved_as_unanswered(self):
        category = self.categories[0]

        response = self.client.post(
            "/submit_quiz",
            data={"category_id": str(category["id"])},
        )

        self.assertEqual(response.status_code, 302)
        attempt_id = int(response.headers["Location"].rsplit("/", 1)[-1])
        attempt = app.get_attempt_by_id(attempt_id)
        self.assertEqual(attempt["score"], 0)
        self.assertEqual(attempt["unanswered"], attempt["total_questions"])

    def test_question_search_and_category_filter(self):
        category = next(item for item in self.categories if item["name"] == "General Knowledge")

        search_response = self.client.get("/questions?search=capital")
        filter_response = self.client.get(
            f"/questions?category_filter={category['id']}"
        )

        self.assertEqual(search_response.status_code, 200)
        self.assertIn(b"capital city of France", search_response.data)
        self.assertEqual(filter_response.status_code, 200)
        self.assertIn(b"General Knowledge", filter_response.data)

    def test_question_crud_and_invalid_inputs(self):
        category_id = self.categories[0]["id"]
        question_data = {
            "category_id": str(category_id),
            "question_text": "What is 2 + 2?",
            "option_a": "3",
            "option_b": "4",
            "option_c": "5",
            "option_d": "6",
            "correct_option": "B",
        }

        invalid_add = self.client.post(
            "/questions",
            data=dict(question_data, category_id="999999"),
        )
        self.assertEqual(invalid_add.status_code, 200)
        self.assertIn(b"available category", invalid_add.data)
        self.assertEqual(len(app.get_questions_for_management("What is 2 + 2?")), 0)

        add_response = self.client.post("/questions", data=question_data)
        self.assertEqual(add_response.status_code, 302)
        question = app.get_questions_for_management("What is 2 + 2?")[0]
        question_id = question["id"]

        invalid_edit = self.client.post(
            f"/question/{question_id}/edit",
            data=dict(question_data, correct_option="Z"),
        )
        self.assertEqual(invalid_edit.status_code, 200)
        self.assertIn(b"must be one of A, B, C, or D", invalid_edit.data)
        self.assertEqual(app.get_question_by_id(question_id)["correct_option"], "B")

        edit_response = self.client.post(
            f"/question/{question_id}/edit",
            data=dict(question_data, question_text="Updated question"),
        )
        self.assertEqual(edit_response.status_code, 302)
        self.assertEqual(
            app.get_question_by_id(question_id)["question_text"],
            "Updated question",
        )

        delete_response = self.client.post(f"/question/{question_id}/delete")
        self.assertEqual(delete_response.status_code, 302)
        self.assertIsNone(app.get_question_by_id(question_id))

    def test_history_displays_saved_attempt(self):
        category = self.categories[0]
        attempt_id = app.save_quiz_attempt(
            category["id"],
            score=2,
            total_questions=4,
            unanswered=1,
        )

        response = self.client.get("/history")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"2/4", response.data)
        self.assertIsNotNone(app.get_attempt_by_id(attempt_id))


if __name__ == "__main__":
    unittest.main()
