import hashlib
import json
import os
import sqlite3
from pathlib import Path

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


@app.post("/api/login")
def login(body: LoginBody):
    if body.password != APP_PASSWORD:
        raise HTTPException(status_code=401, detail="Неверный пароль")
    return {"token": expected_token()}


@app.get("/api/workouts")
def list_workouts(authorization: str | None = Header(default=None)):
    check_auth(authorization)
    conn = get_db()
    rows = conn.execute("SELECT id, date, entries FROM workouts ORDER BY id DESC").fetchall()
    conn.close()
    return [{"id": r[0], "date": r[1], "entries": json.loads(r[2])} for r in rows]


@app.post("/api/workouts")
def create_workout(body: WorkoutBody, authorization: str | None = Header(default=None)):
    check_auth(authorization)
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO workouts (date, entries) VALUES (?, ?)",
        (body.date, json.dumps(body.entries, ensure_ascii=False)),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {"id": new_id, "date": body.date, "entries": body.entries}


@app.delete("/api/workouts/{workout_id}")
def delete_workout(workout_id: int, authorization: str | None = Header(default=None)):
    check_auth(authorization)
    conn = get_db()
    conn.execute("DELETE FROM workouts WHERE id = ?", (workout_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


# serve frontend
app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")
