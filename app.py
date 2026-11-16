import os
import sqlite3
from datetime import datetime

from flask import Flask, redirect, render_template, request, url_for

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "quiz_app.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = "quiz-application-secret-key"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def seed_data():
    conn = get_db_connection()
    categories = [
        ("General Knowledge", "A broad set of beginner-friendly questions."),
        ("Science", "Basic scientific facts and ideas."),
        ("History", "Key historical events and figures."),
        ("Technology", "Everyday tech and digital awareness."),
    ]

    for name, description in categories:
        conn.execute(
            "INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)",
            (name, description),
        )

    category_map = {
        row["name"]: row["id"]
        for row in conn.execute("SELECT id, name FROM categories").fetchall()
    }

    questions = [
        (category_map["General Knowledge"], "What is the capital city of France?", "Paris", "London", "Berlin", "Rome", "A"),
        (category_map["General Knowledge"], "Which planet is known as the Red Planet?", "Mars", "Venus", "Jupiter", "Mercury", "A"),
        (category_map["General Knowledge"], "Which language is primarily spoken in Brazil?", "Portuguese", "Spanish", "French", "English", "A"),
        (category_map["General Knowledge"], "How many days are there in a leap year?", "366", "365", "364", "360", "A"),
        (category_map["Science"], "What gas do plants absorb from the atmosphere?", "Carbon dioxide", "Oxygen", "Nitrogen", "Hydrogen", "A"),
        (category_map["Science"], "Which organ pumps blood through the body?", "Heart", "Lungs", "Brain", "Liver", "A"),
        (category_map["Science"], "What is the boiling point of water at sea level?", "100°C", "50°C", "150°C", "80°C", "A"),
        (category_map["Science"], "Which force keeps us on the ground?", "Gravity", "Magnetism", "Friction", "Electricity", "A"),
        (category_map["History"], "Who was the first President of the United States?", "George Washington", "Thomas Jefferson", "Abraham Lincoln", "John Adams", "A"),
        (category_map["History"], "The Great Wall of China was built primarily to protect against invasions from which direction?", "North", "South", "East", "West", "A"),
        (category_map["History"], "Which ancient civilization built Machu Picchu?", "Inca", "Roman", "Greek", "Mayan", "A"),
        (category_map["History"], "Which event began in 1939 and involved many countries across the world?", "World War II", "French Revolution", "Cold War", "Industrial Revolution", "A"),
        (category_map["Technology"], "What does CPU stand for?", "Central Processing Unit", "Computer Power Utility", "Central Program Unit", "Control Processing Utility", "A"),
        (category_map["Technology"], "Which device is used to type text into a computer?", "Keyboard", "Monitor", "Printer", "Speaker", "A"),
        (category_map["Technology"], "What does HTML stand for?", "HyperText Markup Language", "HighText Machine Language", "Hyper Transfer Markup Logic", "Home Tool Markup Language", "A"),
        (category_map["Technology"], "Which storage device is usually used to save files permanently?", "Hard drive", "RAM", "CPU", "Screen", "A"),
    ]

    conn.executemany(
        "INSERT OR IGNORE INTO questions (category_id, question_text, option_a, option_b, option_c, option_d, correct_option) VALUES (?, ?, ?, ?, ?, ?, ?)",
        questions,
    )
    conn.commit()
    conn.close()


def init_db():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_option TEXT NOT NULL CHECK(correct_option IN ('A','B','C','D')),
            FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE CASCADE
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS quiz_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            unanswered INTEGER NOT NULL DEFAULT 0,
            percentage REAL NOT NULL,
            attempted_at TEXT NOT NULL,
            FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()
    category_count = conn.execute("SELECT COUNT(*) AS total FROM categories").fetchone()["total"]
    if category_count == 0:
        seed_data()
    conn.close()


def get_categories():
    conn = get_db_connection()
    categories = conn.execute(
        "SELECT id, name, description FROM categories ORDER BY name ASC"
    ).fetchall()
    conn.close()
    return categories


def get_category_by_id(category_id):
    conn = get_db_connection()
    category = conn.execute(
        "SELECT id, name, description FROM categories WHERE id = ?",
        (category_id,),
    ).fetchone()
    conn.close()
    return category


def get_questions_for_category(category_id):
    conn = get_db_connection()
    questions = conn.execute(
        """
        SELECT q.id, q.question_text, q.option_a, q.option_b, q.option_c, q.option_d, q.correct_option
        FROM questions q
        WHERE q.category_id = ?
        ORDER BY q.id ASC
        """,
        (category_id,),
    ).fetchall()
    conn.close()
    return questions


def get_questions_for_management(search_query="", category_id=None):
    conn = get_db_connection()
    sql = """
        SELECT q.id, q.question_text, q.option_a, q.option_b, q.option_c, q.option_d, q.correct_option,
               c.name AS category_name, c.id AS category_id
        FROM questions q
        JOIN categories c ON c.id = q.category_id
        WHERE 1 = 1
    """
    parameters = []

    if search_query:
        sql += " AND (q.question_text LIKE ? OR c.name LIKE ?)"
        search_text = f"%{search_query}%"
        parameters.extend([search_text, search_text])

    if category_id:
        sql += " AND q.category_id = ?"
        parameters.append(category_id)

    sql += " ORDER BY c.name ASC, q.id ASC"

    rows = conn.execute(sql, tuple(parameters)).fetchall()
    conn.close()
    return rows


def get_question_by_id(question_id):
    conn = get_db_connection()
    question = conn.execute(
        """
        SELECT q.id, q.question_text, q.option_a, q.option_b, q.option_c, q.option_d, q.correct_option,
               q.category_id, c.name AS category_name
        FROM questions q
        JOIN categories c ON c.id = q.category_id
        WHERE q.id = ?
        """,
        (question_id,),
    ).fetchone()
    conn.close()
    return question


def save_quiz_attempt(category_id, score, total_questions, unanswered):
    conn = get_db_connection()
    percentage = 0.0 if total_questions == 0 else round((score / total_questions) * 100, 2)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.execute(
        """
        INSERT INTO quiz_history (category_id, score, total_questions, unanswered, percentage, attempted_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (category_id, score, total_questions, unanswered, percentage, timestamp),
    )
    conn.commit()
    attempt_id = cursor.lastrowid
    conn.close()
    return attempt_id


def get_recent_attempts(limit=10):
    conn = get_db_connection()
    attempts = conn.execute(
        """
        SELECT h.id, h.score, h.total_questions, h.unanswered, h.percentage, h.attempted_at,
               c.id AS category_id, c.name AS category_name
        FROM quiz_history h
        JOIN categories c ON c.id = h.category_id
        ORDER BY h.id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return attempts


def get_attempt_by_id(attempt_id):
    conn = get_db_connection()
    attempt = conn.execute(
        """
        SELECT h.id, h.category_id, h.score, h.total_questions, h.unanswered, h.percentage, h.attempted_at,
               c.name AS category_name
        FROM quiz_history h
        JOIN categories c ON c.id = h.category_id
        WHERE h.id = ?
        """,
        (attempt_id,),
    ).fetchone()
    conn.close()
    return attempt


@app.route("/")
def index():
    categories = get_categories()
    total_questions = 0
    conn = get_db_connection()
    total_questions = conn.execute("SELECT COUNT(*) AS total FROM questions").fetchone()["total"]
    conn.close()
    return render_template("index.html", categories=categories, total_questions=total_questions)


@app.route("/quiz")
def quiz_page():
    category_id = request.args.get("category", type=int)
    if category_id is None:
        categories = get_categories()
        if categories:
            return redirect(url_for("quiz_page", category=categories[0]["id"]))
        return render_template("quiz.html", category=None, questions=[], message="Add a category before starting a quiz.")

    category = get_category_by_id(category_id)
    if category is None:
        return redirect(url_for("index"))

    questions = get_questions_for_category(category_id)
    if not questions:
        return render_template(
            "quiz.html",
            category=category,
            questions=[],
            message="No questions are available for this category yet.",
        )

    return render_template("quiz.html", category=category, questions=questions, message="")


@app.route("/submit_quiz", methods=["POST"])
def submit_quiz():
    category_id = request.form.get("category_id", type=int)
    if category_id is None:
        return redirect(url_for("index"))

    questions = get_questions_for_category(category_id)
    if not questions:
        return redirect(url_for("quiz_page", category=category_id))

    score = 0
    unanswered = 0

    for question in questions:
        answer = request.form.get(f"answer_{question['id']}", "").strip().upper()
        if answer not in {"A", "B", "C", "D"}:
            unanswered += 1
        elif answer == question["correct_option"]:
            score += 1

    attempt_id = save_quiz_attempt(category_id, score, len(questions), unanswered)
    return redirect(url_for("result_page", attempt_id=attempt_id))


@app.route("/result/<int:attempt_id>")
def result_page(attempt_id):
    attempt = get_attempt_by_id(attempt_id)
    if attempt is None:
        return redirect(url_for("index"))
    return render_template("result.html", attempt=attempt)


@app.route("/history")
def history_page():
    attempts = get_recent_attempts(limit=20)
    return render_template("history.html", attempts=attempts)


@app.route("/questions", methods=["GET", "POST"])
def questions_page():
    categories = get_categories()
    search_query = request.args.get("search", "").strip()
    category_filter = request.args.get("category_filter", type=int)

    if request.method == "POST":
        category_id = request.form.get("category_id", type=int)
        question_text = request.form.get("question_text", "").strip()
        option_a = request.form.get("option_a", "").strip()
        option_b = request.form.get("option_b", "").strip()
        option_c = request.form.get("option_c", "").strip()
        option_d = request.form.get("option_d", "").strip()
        correct_option = request.form.get("correct_option", "").strip().upper()

        if not all([category_id, question_text, option_a, option_b, option_c, option_d, correct_option]):
            questions = get_questions_for_management(search_query, category_filter)
            return render_template(
                "questions.html",
                categories=categories,
                questions=questions,
                search_query=search_query,
                category_filter=category_filter,
                error="Please fill in every field and choose a valid correct answer.",
            )

        if category_id not in {category["id"] for category in categories}:
            questions = get_questions_for_management(search_query, category_filter)
            return render_template(
                "questions.html",
                categories=categories,
                questions=questions,
                search_query=search_query,
                category_filter=category_filter,
                error="Please choose an available category.",
            )

        if correct_option not in {"A", "B", "C", "D"}:
            questions = get_questions_for_management(search_query, category_filter)
            return render_template(
                "questions.html",
                categories=categories,
                questions=questions,
                search_query=search_query,
                category_filter=category_filter,
                error="Correct answer must be one of A, B, C, or D.",
            )

        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO questions (category_id, question_text, option_a, option_b, option_c, option_d, correct_option)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (category_id, question_text, option_a, option_b, option_c, option_d, correct_option),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("questions_page"))

    questions = get_questions_for_management(search_query, category_filter)
    return render_template(
        "questions.html",
        categories=categories,
        questions=questions,
        search_query=search_query,
        category_filter=category_filter,
        error="",
    )


@app.route("/question/<int:question_id>/edit", methods=["GET", "POST"])
def edit_question(question_id):
    categories = get_categories()
    question = get_question_by_id(question_id)
    if question is None:
        return redirect(url_for("questions_page"))

    if request.method == "POST":
        category_id = request.form.get("category_id", type=int)
        question_text = request.form.get("question_text", "").strip()
        option_a = request.form.get("option_a", "").strip()
        option_b = request.form.get("option_b", "").strip()
        option_c = request.form.get("option_c", "").strip()
        option_d = request.form.get("option_d", "").strip()
        correct_option = request.form.get("correct_option", "").strip().upper()

        if not all([category_id, question_text, option_a, option_b, option_c, option_d, correct_option]):
            return render_template(
                "edit_question.html",
                categories=categories,
                question=question,
                error="Please complete every field before saving changes.",
            )

        if category_id not in {category["id"] for category in categories}:
            return render_template(
                "edit_question.html",
                categories=categories,
                question=question,
                error="Please choose an available category.",
            )

        if correct_option not in {"A", "B", "C", "D"}:
            return render_template(
                "edit_question.html",
                categories=categories,
                question=question,
                error="Correct answer must be one of A, B, C, or D.",
            )

        conn = get_db_connection()
        conn.execute(
            """
            UPDATE questions
            SET category_id = ?, question_text = ?, option_a = ?, option_b = ?, option_c = ?, option_d = ?, correct_option = ?
            WHERE id = ?
            """,
            (category_id, question_text, option_a, option_b, option_c, option_d, correct_option, question_id),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("questions_page"))

    return render_template("edit_question.html", categories=categories, question=question, error="")


@app.route("/question/<int:question_id>/delete", methods=["POST"])
def delete_question(question_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM questions WHERE id = ?", (question_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("questions_page"))


init_db()


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
