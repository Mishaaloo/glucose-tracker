# GlucoTracker
*A Flask web app for tracking blood glucose readings, built for people living with T1D.*

This app was essentially made for people with T1D (like myself). Over the years of living with this chronic condition, I learned that it was very helpful to 
note down your readings to see the necessary improvements you need to make in the future for better treatement. 
so I thought maybe we can turn this idea from an idea to functional application. First I made a personal CLI based program then I decided to decvelop the whole idea into a deployable full-stack web-app that people can access to. 

## The web-app URL:
https://glucose-tracker-zw2f.onrender.com/login
Note: it may take 30 seconds to load since the app sleeps on inactivity on the free trial.

## Features:
you can log in or register if you have no account.
each user has their own data - no body else can see it.
there's an AI analysis option to get feedback on your last readings.
there's a real-time weather integration that warns you how temperature may affect your BG.
there's a small "did you know?" box which tells you common diabetes knowledge.
there's a chart based on your last readings data.
you can also filter readings data and display it or convert it into a csv file to show your doctor.
session based authentication with timeout.

## Tech Stack:
Backend: Python, Flask
Database: PostgreSQL (production), SQLite (local development) via SQLAlchemy
Frontend: HTML, Bootstrap 4, custom CSS
Data Visualization: Chart.js
AI Integration: Groq API (Llama 3.3 70B)
Weather Data: OpenWeatherMap API
Authentication: Werkzeug password hashing
Deployment: Render (web service + managed PostgreSQL)

Screenshots:
<img width="1918" height="962" alt="Screenshot 2026-06-21 123109" src="https://github.com/user-attachments/assets/baeb59a1-d536-4bb0-9acb-dc34b124cc90" />
<img width="1918" height="965" alt="image" src="https://github.com/user-attachments/assets/2d076b92-6b6f-4c1b-83e9-c6c20618ded7" />

## How to run locally:
## How to Run Locally

1. Clone the repository
```bash
   git clone https://github.com/Mishaaloo/glucose-tracker.git
   cd glucose-tracker
```

2. Create and activate a virtual environment
```bash
   python -m venv env
   source env/bin/activate   # On Windows: env\Scripts\activate
```

3. Install dependencies
```bash
   pip install -r requirements.txt
```

4. Create a `.env` file in the project root with the following:
   (DATABASE_URL is optional locally — it defaults to SQLite if not set)
SECRET_KEY=your_secret_key
GROQ_API_KEY=your_groq_api_key
OPENWEATHER_API_KEY=your_openweather_api_key

5. Run the app
```bash
   python app.py
```

6. Visit `http://127.0.0.1:5000` in your browser

## Known limitations:
Since the app is on render's free-tier PostgreSQL database which is going to expire in 90 days so a new database needs to be provisioned.

## Possible future improvements:
Make the app fully responsive so the UI/UX holds up well on mobile devices, not just desktop
Add reminder notifications for missed logging streaks, similar to Duolingo's engagement system
