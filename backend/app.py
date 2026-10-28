from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import Dict, List, Optional, Tuple

import joblib
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DB_PATH = BASE_DIR / "smartfit.db"

sys.path.insert(0, str(PROJECT_ROOT))
from analysis import run_analysis

FEATURE_COLUMNS = ["Calories", "ActivityScore", "Sedentary"]
CLUSTER_FEATURE_COLUMNS = ["Steps", "Calories", "ActivityScore", "Sedentary"]
PROFILE_KEYS = ["age", "height", "weight"]
ACTIVITY_KEYS = ["steps", "calories", "activity"]

BMI_CLUSTER_TYPE = {
    0: "Underactive",
    1: "Moderate",
    2: "Sedentary",
}


class SmartFitService:
    def __init__(self, model_dir: Path) -> None:
        self.rf_model = joblib.load(model_dir / "rf_model.pkl")
        self.kmeans = joblib.load(model_dir / "kmeans.pkl")
        self.scaler = joblib.load(model_dir / "scaler.pkl")
        self.cluster_scaler = joblib.load(model_dir / "cluster_scaler.pkl")
        self.cluster_mapping = joblib.load(model_dir / "cluster_mapping.pkl")

    def analyze_activity(
        self,
        steps: float,
        calories: float,
        activity: float,
        sedentary: Optional[float] = None,
    ) -> Dict[str, object]:
        sedentary_value = max(0.0, 1440.0 - activity) if sedentary is None else sedentary

        input_frame = pd.DataFrame(
            [{"Calories": calories, "ActivityScore": activity, "Sedentary": sedentary_value}],
            columns=FEATURE_COLUMNS,
        )
        cluster_frame = pd.DataFrame(
            [{"Steps": steps, "Calories": calories, "ActivityScore": activity, "Sedentary": sedentary_value}],
            columns=CLUSTER_FEATURE_COLUMNS,
        )

        scaled_values = self.scaler.transform(input_frame)
        fitness_level = str(self.rf_model.predict(scaled_values)[0])
        cluster_scaled_values = self.cluster_scaler.transform(cluster_frame)
        cluster = int(self.kmeans.predict(cluster_scaled_values)[0])
        cluster_type = self.cluster_mapping.get(cluster, "Unknown")

        return {
            "mode": "activity",
            "fitness_level": fitness_level,
            "cluster": cluster,
            "cluster_type": cluster_type,
            "bmi": None,
            "insights": self._activity_insights(steps=steps, activity=activity, fitness_level=fitness_level, cluster=cluster),
            "inputs": {
                "steps": steps,
                "calories": calories,
                "activity": activity,
                "sedentary": sedentary_value,
            },
        }

    def analyze_profile(self, age: float, height: float, weight: float) -> Dict[str, object]:
        height_m = height / 100.0 if height > 3 else height
        bmi = round(weight / (height_m**2), 1)

        if bmi < 18.5:
            cluster = 0
            insights = [
                "Your BMI is on the lower side, so building strength and regular meals can help improve energy.",
                "Try adding light daily movement and gradual resistance training for a sustainable start.",
            ]
        elif bmi <= 24.9:
            cluster = 1
            insights = [
                "Your BMI is in a healthy range, which is a strong baseline for long-term fitness.",
                "Staying consistent with walking and active minutes will help you maintain this momentum.",
            ]
        else:
            cluster = 2
            insights = [
                "Your BMI suggests you may benefit from improving your fitness routine.",
                "Increasing daily movement slightly can significantly improve your health over time.",
                "Focus on small, consistent habits rather than drastic changes.",
            ]

        return {
            "mode": "profile",
            "bmi": bmi,
            "cluster": cluster,
            "cluster_type": BMI_CLUSTER_TYPE[cluster],
            "fitness_level": None,
            "insights": insights[:3],
            "profile": {
                "age": age,
                "height_m": round(height_m, 2),
                "weight": weight,
            },
        }

    def _activity_insights(self, steps: float, activity: float, fitness_level: str, cluster: int) -> List[str]:
        insights: List[str] = []

        if cluster == 2:
            insights.append("You are currently leading a sedentary lifestyle compared to similar users.")
        elif cluster == 1:
            insights.append("You are maintaining a good level of activity compared to similar users.")
        else:
            insights.append("Your activity pattern is moderate and has room for steady improvement.")

        if fitness_level == "Low":
            insights.append("A small increase in daily movement can quickly improve your fitness trend.")
        elif fitness_level == "High":
            insights.append("Focus on consistency and recovery to sustain your performance.")
        else:
            insights.append("You are on the right path; consistency will move you toward a stronger fitness level.")

        if steps < 6000:
            insights.append("Try adding one short walk each day to build momentum without feeling overwhelmed.")
        elif activity < 150:
            insights.append("Your active minutes are a bit low, so even a brief workout can make a real difference.")
        else:
            insights.append("Your current routine is working; keep your weekly schedule consistent.")

        return insights[:3]


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                user_id INTEGER PRIMARY KEY,
                age REAL NOT NULL,
                height REAL NOT NULL,
                weight REAL NOT NULL,
                bmi REAL NOT NULL,
                cluster INTEGER NOT NULL,
                cluster_type TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                steps REAL NOT NULL,
                calories REAL NOT NULL,
                activity REAL NOT NULL,
                sedentary REAL NOT NULL,
                fitness_level TEXT,
                cluster INTEGER,
                cluster_type TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE (user_id, date),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )


def validate_numeric_payload(payload: Dict[str, object], required_keys: List[str]) -> Tuple[bool, str]:
    for key in required_keys:
        if key not in payload:
            return False, f"Missing required field: {key}"

    for key in required_keys:
        try:
            value = float(payload[key])
            if value < 0:
                return False, f"{key} must be non-negative"
        except (TypeError, ValueError):
            return False, f"{key} must be a valid number"

    if "height" in required_keys and float(payload["height"]) == 0:
        return False, "height must be greater than 0"

    return True, ""


def parse_iso_date(value: object) -> Tuple[bool, str]:
    if value is None:
        return False, "Missing required field: date"
    if not isinstance(value, str):
        return False, "date must be in YYYY-MM-DD format"
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False, "date must be in YYYY-MM-DD format"
    return True, ""


def get_user_by_id(user_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        row = conn.execute("SELECT id, username FROM users WHERE id = ?", (user_id,)).fetchone()
    return row


def get_profile_row(user_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT user_id, age, height, weight, bmi, cluster, cluster_type, updated_at
            FROM profiles
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
    return row


def upsert_profile(user_id: int, age: float, height: float, weight: float, service: SmartFitService) -> Dict[str, object]:
    profile_analysis = service.analyze_profile(age=age, height=height, weight=weight)
    now = datetime.utcnow().isoformat()

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO profiles (user_id, age, height, weight, bmi, cluster, cluster_type, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                age = excluded.age,
                height = excluded.height,
                weight = excluded.weight,
                bmi = excluded.bmi,
                cluster = excluded.cluster,
                cluster_type = excluded.cluster_type,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                age,
                height,
                weight,
                float(profile_analysis["bmi"]),
                int(profile_analysis["cluster"]),
                str(profile_analysis["cluster_type"]),
                now,
            ),
        )

    return profile_analysis


def upsert_entry(
    user_id: int,
    date: str,
    steps: float,
    calories: float,
    activity: float,
    sedentary: float,
    analysis: Dict[str, object],
) -> None:
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO entries (
                user_id, date, steps, calories, activity, sedentary,
                fitness_level, cluster, cluster_type, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, date) DO UPDATE SET
                steps = excluded.steps,
                calories = excluded.calories,
                activity = excluded.activity,
                sedentary = excluded.sedentary,
                fitness_level = excluded.fitness_level,
                cluster = excluded.cluster,
                cluster_type = excluded.cluster_type,
                updated_at = excluded.updated_at
            """,
            (
                user_id,
                date,
                steps,
                calories,
                activity,
                sedentary,
                str(analysis.get("fitness_level", "")),
                int(analysis.get("cluster", 0)),
                str(analysis.get("cluster_type", "Unknown")),
                now,
                now,
            ),
        )


def fetch_history(user_id: int, window: str) -> List[Dict[str, object]]:
    days = 7 if window == "7d" else 30
    start_date = (datetime.now().date() - timedelta(days=days - 1)).isoformat()

    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT date, steps, calories, activity
            FROM entries
            WHERE user_id = ? AND date >= ?
            ORDER BY date ASC
            """,
            (user_id, start_date),
        ).fetchall()

    return [
        {
            "date": str(row["date"]),
            "steps": float(row["steps"]),
            "calories": float(row["calories"]),
            "activity": float(row["activity"]),
        }
        for row in rows
    ]


app = Flask(__name__)
CORS(app)
service = SmartFitService(PROJECT_ROOT)
init_db()
_analytics_cache: Optional[Dict[str, object]] = None


@app.get("/health")
def health_check():
    return jsonify({"status": "ok"})


@app.get("/analytics")
def analytics():
    global _analytics_cache
    try:
        if _analytics_cache is None:
            _analytics_cache = run_analysis()
        return jsonify(_analytics_cache)
    except (FileNotFoundError, ValueError, ImportError) as error:
        app.logger.exception("Analytics pipeline could not run")
        return jsonify({"error": str(error)}), 500


@app.post("/auth/register")
def register():
    payload = request.get_json(silent=True) or {}

    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", "")).strip()
    if not username:
        return jsonify({"error": "Missing required field: username"}), 400
    if len(password) < 4:
        return jsonify({"error": "password must be at least 4 characters"}), 400

    is_valid, error = validate_numeric_payload(payload, PROFILE_KEYS)
    if not is_valid:
        return jsonify({"error": error}), 400

    now = datetime.utcnow().isoformat()
    try:
        with get_conn() as conn:
            cursor = conn.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), now),
            )
            user_id = int(cursor.lastrowid)
    except sqlite3.IntegrityError:
        return jsonify({"error": "username already exists"}), 409

    profile_analysis = upsert_profile(
        user_id=user_id,
        age=float(payload["age"]),
        height=float(payload["height"]),
        weight=float(payload["weight"]),
        service=service,
    )

    return jsonify(
        {
            "user": {"id": user_id, "username": username},
            "profile": profile_analysis,
        }
    )


@app.post("/auth/login")
def login():
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", "")).strip()

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()

    if row is None or not check_password_hash(str(row["password_hash"]), password):
        return jsonify({"error": "invalid username or password"}), 401

    return jsonify({"user": {"id": int(row["id"]), "username": str(row["username"])}})


@app.get("/profile")
def get_profile():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"error": "Query param 'user_id' is required"}), 400

    user = get_user_by_id(user_id)
    if user is None:
        return jsonify({"error": "user not found"}), 404

    row = get_profile_row(user_id)
    if row is None:
        return jsonify({"error": "profile not found"}), 404

    return jsonify(
        {
            "user": {"id": int(user["id"]), "username": str(user["username"])},
            "profile": {
                "age": float(row["age"]),
                "height": float(row["height"]),
                "weight": float(row["weight"]),
                "bmi": float(row["bmi"]),
                "cluster": int(row["cluster"]),
                "cluster_type": str(row["cluster_type"]),
                "fitness_level": None,
                "insights": service.analyze_profile(
                    age=float(row["age"]),
                    height=float(row["height"]),
                    weight=float(row["weight"]),
                )["insights"],
            },
        }
    )


@app.put("/profile")
def update_profile():
    payload = request.get_json(silent=True) or {}

    user_id = payload.get("user_id")
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return jsonify({"error": "user_id must be a valid integer"}), 400

    if get_user_by_id(user_id) is None:
        return jsonify({"error": "user not found"}), 404

    is_valid, error = validate_numeric_payload(payload, PROFILE_KEYS)
    if not is_valid:
        return jsonify({"error": error}), 400

    profile_analysis = upsert_profile(
        user_id=user_id,
        age=float(payload["age"]),
        height=float(payload["height"]),
        weight=float(payload["weight"]),
        service=service,
    )

    return jsonify({"profile": profile_analysis})


@app.post("/daily-entry")
def daily_entry():
    payload = request.get_json(silent=True) or {}

    user_id = payload.get("user_id")
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return jsonify({"error": "user_id must be a valid integer"}), 400

    if get_user_by_id(user_id) is None:
        return jsonify({"error": "user not found"}), 404

    is_valid_date, date_error = parse_iso_date(payload.get("date"))
    if not is_valid_date:
        return jsonify({"error": date_error}), 400

    is_valid, error = validate_numeric_payload(payload, ACTIVITY_KEYS)
    if not is_valid:
        return jsonify({"error": error}), 400

    activity_minutes = float(payload["activity"])
    sedentary_value = float(payload.get("sedentary", max(0.0, 1440.0 - activity_minutes)))

    analysis = service.analyze_activity(
        steps=float(payload["steps"]),
        calories=float(payload["calories"]),
        activity=activity_minutes,
        sedentary=sedentary_value,
    )

    upsert_entry(
        user_id=user_id,
        date=str(payload["date"]),
        steps=float(payload["steps"]),
        calories=float(payload["calories"]),
        activity=activity_minutes,
        sedentary=sedentary_value,
        analysis=analysis,
    )

    result = dict(analysis)
    result["saved_date"] = str(payload["date"])
    return jsonify(result)


@app.get("/activity-history")
def activity_history():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"error": "Query param 'user_id' is required"}), 400

    if get_user_by_id(user_id) is None:
        return jsonify({"error": "user not found"}), 404

    window = str(request.args.get("window", "7d")).strip().lower()
    if window not in {"7d", "30d"}:
        return jsonify({"error": "window must be either '7d' or '30d'"}), 400

    history = fetch_history(user_id=user_id, window=window)
    return jsonify({"user_id": user_id, "window": window, "history": history})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
