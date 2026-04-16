from flask import Flask, render_template, request, redirect, url_for
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)

DATA_FILE = "habits.json"


def load_habits():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_habits(habits):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(habits, f, ensure_ascii=False, indent=2)


def get_today():
    return datetime.now().strftime("%Y-%m-%d")


def calculate_streak(completed_dates):
    if not completed_dates:
        return 0
    sorted_dates = sorted(completed_dates, reverse=True)
    streak = 0
    current = datetime.now().date()

    for date_str in sorted_dates:
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            if date == current:
                streak += 1
                current -= timedelta(days=1)
            elif date > current:
                continue
            else:
                break
        except ValueError:
            continue
    return streak


@app.route("/")
def index():
    habits = load_habits()
    today = get_today()

    for habit in habits:
        habit["streak"] = calculate_streak(habit.get("completed_dates", []))
        habit["done_today"] = today in habit.get("completed_dates", [])

    total = len(habits)
    today_done = sum(1 for h in habits if h.get("done_today"))
    # fmt: off
    avg_streak = sum(h.get("streak", 0) for h in habits) // total if total > 0 else 0
    # fmt: on

    return render_template(
        "index.html",
        habits=habits,
        total=total,
        today_done=today_done,
        avg_streak=avg_streak,
    )


@app.route("/add", methods=["POST"])
def add_habit():
    name = request.form.get("name", "").strip()
    if name:
        habits = load_habits()
        habits.insert(0, {"name": name, "completed_dates": []})
        save_habits(habits)
    return redirect(url_for("index"))


@app.route("/mark/<int:index>")
def mark_done(index):
    habits = load_habits()
    today = get_today()
    if 0 <= index < len(habits):
        if today not in habits[index].get("completed_dates", []):
            habits[index].setdefault("completed_dates", []).append(today)
            save_habits(habits)
    return redirect(url_for("index"))


@app.route("/delete/<int:index>")
def delete_habit(index):
    habits = load_habits()
    if 0 <= index < len(habits):
        del habits[index]
        save_habits(habits)
    return redirect(url_for("index"))


# Тестовый маршрут для проверки статусов стрика
@app.route("/test_set_streak/<int:index>/<int:value>")
def test_set_streak(index, value):
    habits = load_habits()
    if 0 <= index < len(habits):
        habits[index]["completed_dates"] = []
        current = datetime.now().date()
        for _ in range(value):
            habits[index].setdefault("completed_dates", []).append(
                current.strftime("%Y-%m-%d")
            )
            current -= timedelta(days=1)
        save_habits(habits)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
