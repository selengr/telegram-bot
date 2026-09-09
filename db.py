"""SQLite storage for users, streaks, badges, and leaderboard."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent / "data" / "bot.db"

BADGE_DEFS = {
    "first_laugh": {"fa": "اولین خنده 😂", "en": "First laugh 😂", "check": lambda u: u["jokes"] >= 1},
    "comedy_club": {"fa": "باشگاه کمدی 🎭", "en": "Comedy club 🎭", "check": lambda u: u["jokes"] >= 25},
    "player": {"fa": "گیمر 🎮", "en": "Player 🎮", "check": lambda u: u["games"] >= 15},
    "quiz_brain": {"fa": "مغز کوییز 🧠", "en": "Quiz brain 🧠", "check": lambda u: u["quiz"] >= 50},
    "streak_3": {"fa": "استریک ۳ روزه 🔥", "en": "3-day streak 🔥", "check": lambda u: u["streak"] >= 3},
    "streak_7": {"fa": "استریک ۷ روزه 🏆", "en": "7-day streak 🏆", "check": lambda u: u["streak"] >= 7},
}


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL DEFAULT '',
                lang TEXT NOT NULL DEFAULT 'fa',
                jokes INTEGER NOT NULL DEFAULT 0,
                games INTEGER NOT NULL DEFAULT 0,
                quiz INTEGER NOT NULL DEFAULT 0,
                daily INTEGER NOT NULL DEFAULT 0,
                streak INTEGER NOT NULL DEFAULT 0,
                last_daily TEXT,
                daily_fortune TEXT,
                badges TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT ''
            )
            """
        )


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_user(user_id: int, name: str = "", lang: str = "fa") -> dict[str, Any]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if row:
            if name and name != row["name"]:
                conn.execute(
                    "UPDATE users SET name = ?, updated_at = ? WHERE user_id = ?",
                    (name, _now(), user_id),
                )
                row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return dict(row)
        conn.execute(
            "INSERT INTO users (user_id, name, lang, updated_at) VALUES (?, ?, ?, ?)",
            (user_id, name or "", lang, _now()),
        )
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row)


def set_user_lang(user_id: int, lang: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET lang = ?, updated_at = ? WHERE user_id = ?",
            (lang, _now(), user_id),
        )


def bump_stat(user_id: int, key: str, amount: int = 1) -> int:
    if key not in {"jokes", "games", "quiz", "daily"}:
        raise ValueError(key)
    with _connect() as conn:
        conn.execute(
            f"UPDATE users SET {key} = {key} + ?, updated_at = ? WHERE user_id = ?",
            (amount, _now(), user_id),
        )
        row = conn.execute(f"SELECT {key} FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return int(row[0]) if row else 0


def get_stats(user_id: int) -> dict[str, Any]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else {}


def claim_daily(user_id: int, fortune: str) -> tuple[bool, str, int]:
    """Return (is_new, fortune_text, streak)."""
    today = date.today()
    today_s = today.isoformat()
    with _connect() as conn:
        row = conn.execute(
            "SELECT last_daily, daily_fortune, streak, daily FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            return True, fortune, 1
        last = row["last_daily"]
        if last == today_s and row["daily_fortune"]:
            return False, row["daily_fortune"], int(row["streak"] or 0)

        streak = int(row["streak"] or 0)
        if last:
            try:
                prev = date.fromisoformat(last)
                streak = streak + 1 if prev == today - timedelta(days=1) else 1
            except ValueError:
                streak = 1
        else:
            streak = 1

        conn.execute(
            """
            UPDATE users
            SET last_daily = ?, daily_fortune = ?, streak = ?, daily = daily + 1, updated_at = ?
            WHERE user_id = ?
            """,
            (today_s, fortune, streak, _now(), user_id),
        )
        return True, fortune, streak


def badge_list(raw: str) -> list[str]:
    return [b for b in (raw or "").split(",") if b]


def unlock_badges(user_id: int) -> list[str]:
    """Check and unlock new badges. Returns newly unlocked ids."""
    user = get_stats(user_id)
    if not user:
        return []
    owned = set(badge_list(user.get("badges", "")))
    newly: list[str] = []
    for badge_id, meta in BADGE_DEFS.items():
        if badge_id in owned:
            continue
        if meta["check"](user):
            owned.add(badge_id)
            newly.append(badge_id)
    if newly:
        with _connect() as conn:
            conn.execute(
                "UPDATE users SET badges = ?, updated_at = ? WHERE user_id = ?",
                (",".join(sorted(owned)), _now(), user_id),
            )
    return newly


def leaderboard(limit: int = 10) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT user_id, name, jokes, games, quiz, streak,
                   (jokes + games + quiz + daily) AS score
            FROM users
            ORDER BY score DESC, quiz DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
