from flask import Flask, render_template, redirect, url_for, request, session, flash, make_response, jsonify
from datetime import datetime, timedelta
from colorama import Fore, Style
import csv
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import io
from dotenv import load_dotenv
import os
from groq import Groq
import requests
import random

load_dotenv()



app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")

app.permanent_session_lifetime = timedelta(days=5)
database_url = os.getenv("DATABASE_URL", "sqlite:///users.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key= True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


tips = [
    "High temperatures can lower insulin sensitivity — monitor your glucose more closely in summer.",
    "Stress hormones like cortisol can raise blood sugar even without eating.",
    "Exercise can lower blood glucose for up to 24 hours after activity.",
    "Skipping meals can cause unpredictable blood sugar swings.",
    "Staying hydrated helps your kidneys flush out excess glucose.",
    "Poor sleep raises cortisol and can spike morning blood sugar levels.",
    "Caffeine can raise blood glucose in some people with type 1 diabetes.",
    "Cold weather can make blood glucose harder to control.",
    "Always log your readings at consistent times for more accurate trend data.",
    "High-fiber foods slow glucose absorption and help prevent spikes.",
    "Illness and infections can cause significant blood sugar rises.",
    "Rotating injection sites prevents insulin absorption issues.",
    "Alcohol can cause delayed hypoglycemia hours after drinking.",
    "Morning glucose is often higher due to the dawn phenomenon.",
    "Even a 10-minute walk after meals can significantly reduce glucose spikes.",
    "Dehydration makes blood glucose readings appear higher than they are.",
    "Anxiety and panic can trigger adrenaline which raises blood sugar.",
    "Consistency in meal timing helps stabilize glucose patterns over time.",
]

@app.route('/login', methods=["GET", "POST"])
def login():
    tip = random.choice(tips)
    if request.method == "POST":
        username = request.form["nm"]
        password = request.form["pw"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session.permanent = True
            session["user"] = username
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Invalid username or password", tip=tip)
    else:
        if "user" in session:
            return redirect(url_for("index"))
        return render_template("login.html", tip=tip)


class GlucoseLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.String(50), nullable=False)
    insulin_type = db.Column(db.String(50))
    insulin_units = db.Column(db.Float)
    food = db.Column(db.String(200))
    glucose = db.Column(db.Float, nullable = False)


with app.app_context():
    db.create_all()

from groq import Groq

@app.route('/ai_analysis')
def ai_analysis():
    if "user" not in session:
        return redirect(url_for("login"))

    user = User.query.filter_by(username=session["user"]).first()
    readings = GlucoseLog.query.filter_by(user_id=user.id)\
                .order_by(GlucoseLog.id.desc()).limit(7).all()

    if not readings:
        flash("No readings to analyze yet.")
        return redirect(url_for('index'))

    readings_text = "\n".join([
        f"- {r.timestamp}: glucose={r.glucose} mg/dL, insulin={r.insulin_type} {r.insulin_units} units, food={r.food}"
        for r in readings
    ])

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful diabetes management assistant. Analyze the user's recent glucose readings and give practical, friendly advice. Keep it concise — 3 to 4 short paragraphs. Never replace medical advice, always remind them to consult their doctor."
            },
            {
                "role": "user",
                "content": f"Here are my last 7 glucose readings:\n{readings_text}\n\nPlease analyze my glucose control and give me practical suggestions for improvement."
            }
        ]
    )

    analysis = response.choices[0].message.content
    return render_template("ai_analysis.html", analysis=analysis)


@app.route('/delete_reading/<int:reading_id>', methods=['POST'])

def delete_reading(reading_id):
    if "user" not in session:
        return redirect(url_for("login"))

    reading = GlucoseLog.query.get(reading_id)
    if reading:
        db.session.delete(reading)
        db.session.commit()
        flash("Reading Deleted.")
    return redirect(url_for('index'))


@app.route('/last_readings', methods=['GET', 'POST'])
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    user = User.query.filter_by(username=session["user"]).first()

    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    query = GlucoseLog.query.filter_by(user_id=user.id)

    if start_date and end_date:
        query = query.filter(
            GlucoseLog.timestamp >= start_date + ' 00:00:00',
            GlucoseLog.timestamp <= end_date + ' 23:59:59'

        )

        readings = query.order_by(GlucoseLog.id.desc()).all()

    else:
        readings = query.order_by(GlucoseLog.id.desc()).limit(7).all()

    return render_template("last_readings.html", readings=readings, start_date=start_date, end_date=end_date)



@app.route('/weather')
def weather():
    if "user" not in session:
        return redirect(url_for("login"))

    lat = request.args.get('lat')
    lon = request.args.get('lon')
    api_key = os.getenv("OPENWEATHER_API_KEY")

    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    response = requests.get(url)
    data = response.json()

    print("WEATHER API RESPONSE:", data)  # temporary debug line

    if 'main' not in data:
        return jsonify({"error": data.get("message", "API error")}), 500

    temp = data['main']['temp']
    description = data['weather'][0]['description']
    city = data['name']

    if temp > 35:
        advice = "extreme heat may lower your insulin sensitivity"
    elif temp > 28:
        advice = "hot weather may affect your glucose levels"
    elif temp < 10:
        advice = "cold weather may raise your blood sugar"
    else:
        advice = "weather conditions are moderate"

    return jsonify({
        "temp": round(temp, 1),
        "description": description,
        "city": city,
        "advice": advice
    })





@app.route('/export_csv', methods=['POST'])
def export_csv():
    if "user" not in session:
        return redirect(url_for("login"))

    user = User.query.filter_by(username=session["user"]).first()
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    query = GlucoseLog.query.filter_by(user_id=user.id)
    if start_date and end_date:
        query = query.filter(
            GlucoseLog.timestamp >= start_date + ' 00:00:00',
            GlucoseLog.timestamp <= end_date + ' 23:59:59'
        )
    readings = query.order_by(GlucoseLog.id.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Timestamp', 'Glucose (mg/dL)', 'Insulin Type', 'Insulin Units', 'Food'])
    for r in readings:
        writer.writerow([r.timestamp, r.glucose, r.insulin_type, r.insulin_units, r.food])

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=glucose_report.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response

@app.route('/home')
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("home.html")


@app.route('/log', methods=['POST'])
def log():
    if "user" not in session:
        return redirect(url_for("login"))
    glucose = request.form['glucose']
    insulin_type = request.form['insulin_type']
    insulin_units = request.form['insulin_units']
    insulin_units = float(insulin_units) if insulin_units else None
    food = request.form.get('food') or None
    user_test_time = request.form.get('test_time')

    if user_test_time:

        dt = datetime.strptime(user_test_time, '%Y-%m-%dT%H:%M')

        timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')

    else:

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    user = User.query.filter_by(username=session["user"]).first()
    entry = GlucoseLog(
        user_id = user.id,
        timestamp = timestamp,
        insulin_type = insulin_type,
        insulin_units = insulin_units,
        food = food,
        glucose = glucose
        )
    db.session.add(entry)
    db.session.commit()
    flash("Reading logged!")
    return redirect(url_for('home'))

@app.route('/register', methods=["GET", "POST"])
def register():
    tip = random.choice(tips)
    if request.method == "POST":
        username = request.form["nm"]
        password = request.form["pw"]

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:

            return render_template("register.html", error="Username already taken")

        new_user = User(username=username, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html", tip=tip)



@app.route("/user")
def user():
    if "user" in session:
        user = session["user"]
        return f"<h1>{user}</h1>"
    else:
        return redirect(url_for("login"))



@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))




if __name__ == '__main__':
    app.run(debug=True)
