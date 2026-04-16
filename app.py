from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)

DATA_FILE = 'habits.json'

def load_habits():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_habits(habits):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(habits, f, ensure_ascii=False, indent=2)

def get_today():
    return datetime.now().strftime("%Y-%m-%d")

@app.route('/')
def index():
    habits = load_habits()
    today = get_today()
    
    for habit in habits:
        habit['streak'] = calculate_streak(habit['completed_dates'])
        habit['done_today'] = today in habit['completed_dates']
    
    total = len(habits)
    today_done = sum(1 for h in habits if h['done_today'])
    avg_streak = sum(h['streak'] for h in habits) // total if total > 0 else 0
    
    return render_template('index.html', 
                         habits=habits, 
                         total=total, 
                         today_done=today_done, 
                         avg_streak=avg_streak)

def calculate_streak(completed_dates):
    if not completed_dates:
        return 0

    parsed_dates = set()
    for date_str in completed_dates:
        try:
            parsed_dates.add(datetime.strptime(date_str, "%Y-%m-%d").date())
        except (TypeError, ValueError):
            continue

    if not parsed_dates:
        return 0

    streak = 0
    current = datetime.now().date()

    while current in parsed_dates:
        streak += 1
        current -= timedelta(days=1)

    return streak

@app.route('/add', methods=['POST'])
def add_habit():
    name = request.form.get('name', '').strip()
    if name:
        habits = load_habits()
        habits.insert(0, {"name": name, "completed_dates": []})
        save_habits(habits)
    return redirect(url_for('index'))

@app.route('/mark/<int:index>')
def mark_done(index):
    habits = load_habits()
    today = get_today()
    if 0 <= index < len(habits):
        if today not in habits[index]['completed_dates']:
            habits[index]['completed_dates'].append(today)
            save_habits(habits)
    return redirect(url_for('index'))

@app.route('/delete/<int:index>')
def delete_habit(index):
    habits = load_habits()
    if 0 <= index < len(habits):
        del habits[index]
        save_habits(habits)
    return redirect(url_for('index'))

@app.route('/api/stats')
def api_stats():
    habits = load_habits()
    today = get_today()
    total = len(habits)
    today_done = sum(1 for h in habits if today in h.get('completed_dates', []))
    avg_streak = sum(calculate_streak(h.get('completed_dates', [])) for h in habits) // total if total > 0 else 0
    return jsonify({"total": total, "today_done": today_done, "avg_streak": avg_streak})

if __name__ == '__main__':
    app.run(debug=True)
