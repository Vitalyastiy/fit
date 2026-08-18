import hashlib
import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

APP_PASSWORD = os.environ.get("APP_PASSWORD", "melok")
DB_PATH = os.environ.get("DB_PATH", "./melok.db")

app = FastAPI()

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"


# ---------- storage ----------
def _add_column_if_missing(conn, table, column, coltype):
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")
    except sqlite3.OperationalError:
        pass  # column already exists — безопасная повторная миграция, no-op


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            entries TEXT NOT NULL
        )
        """
    )
    # Этап 1 — расширение модели данных без потери старых тренировок.
    # Старые строки просто получают NULL в новых колонках — читаются как раньше.
    _add_column_if_missing(conn, "workouts", "duration", "REAL")
    _add_column_if_missing(conn, "workouts", "notes", "TEXT")
    _add_column_if_missing(conn, "workouts", "workout_type", "TEXT")
    _add_column_if_missing(conn, "workouts", "created_at", "TEXT")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            workout_type TEXT,
            exercises TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return conn


# ---------- auth ----------
def expected_token() -> str:
    return hashlib.sha256((APP_PASSWORD + "::melok_salt").encode()).hexdigest()


def check_auth(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Не авторизован")
    token = authorization.removeprefix("Bearer ").strip()
    if token != expected_token():
        raise HTTPException(status_code=401, detail="Неверный токен")


class LoginBody(BaseModel):
    password: str


class WorkoutBody(BaseModel):
    date: str
    entries: list
    duration: Optional[float] = None
    notes: Optional[str] = None
    workout_type: Optional[str] = None


class TemplateBody(BaseModel):
    name: str
    workout_type: Optional[str] = None
    exercises: list


def _row_to_workout(r) -> dict[str, Any]:
    return {
        "id": r[0],
        "date": r[1],
        "entries": json.loads(r[2]),
        "duration": r[3],
        "notes": r[4],
        "workout_type": r[5],
    }


@app.post("/api/login")
def login(body: LoginBody):
    if body.password != APP_PASSWORD:
        raise HTTPException(status_code=401, detail="Неверный пароль")
    return {"token": expected_token()}


@app.get("/api/workouts")
def list_workouts(authorization: str | None = Header(default=None)):
    check_auth(authorization)
    conn = get_db()
    rows = conn.execute(
        "SELECT id, date, entries, duration, notes, workout_type FROM workouts ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [_row_to_workout(r) for r in rows]


@app.post("/api/workouts")
def create_workout(body: WorkoutBody, authorization: str | None = Header(default=None)):
    check_auth(authorization)
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO workouts (date, entries, duration, notes, workout_type, created_at) "
        "VALUES (?, ?, ?, ?, ?, datetime('now'))",
        (
            body.date,
            json.dumps(body.entries, ensure_ascii=False),
            body.duration,
            body.notes,
            body.workout_type,
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {
        "id": new_id,
        "date": body.date,
        "entries": body.entries,
        "duration": body.duration,
        "notes": body.notes,
        "workout_type": body.workout_type,
    }


@app.delete("/api/workouts/{workout_id}")
def delete_workout(workout_id: int, authorization: str | None = Header(default=None)):
    check_auth(authorization)
    conn = get_db()
    conn.execute("DELETE FROM workouts WHERE id = ?", (workout_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


# ---------- templates (Этап 5 — шаблоны тренировок) ----------
@app.get("/api/templates")
def list_templates(authorization: str | None = Header(default=None)):
    check_auth(authorization)
    conn = get_db()
    rows = conn.execute(
        "SELECT id, name, workout_type, exercises FROM templates ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [
        {"id": r[0], "name": r[1], "workout_type": r[2], "exercises": json.loads(r[3])}
        for r in rows
    ]


@app.post("/api/templates")
def create_template(body: TemplateBody, authorization: str | None = Header(default=None)):
    check_auth(authorization)
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO templates (name, workout_type, exercises) VALUES (?, ?, ?)",
        (body.name, body.workout_type, json.dumps(body.exercises, ensure_ascii=False)),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {
        "id": new_id,
        "name": body.name,
        "workout_type": body.workout_type,
        "exercises": body.exercises,
    }


@app.delete("/api/templates/{template_id}")
def delete_template(template_id: int, authorization: str | None = Header(default=None)):
    check_auth(authorization)
    conn = get_db()
    conn.execute("DELETE FROM templates WHERE id = ?", (template_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


# serve frontend
app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")
