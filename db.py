"""SQLite storage for users, XP, invites, streaks, badges, reminders."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent / "data" / "bot.db"

LEVEL_TITLES = {
    "fa": [
        (1, "تازه‌وارد 🌱"),
        (3, "جوک‌آموز 😄"),
        (5, "کمدین محلی 🎭"),
        (8, "سلطان گپ 👑"),
        (12, "افسانه خنده 🏆"),
        (20, "خدای میم 🌌"),
    ],
    "en": [
        (1, "Newbie 🌱"),
        (3, "Joke trainee 😄"),
        (5, "Local comic 🎭"),
        (8, "Chat royalty 👑"),
        (12, "Laugh legend 🏆"),
        (20, "Meme deity 🌌"),
    ],
}

BADGE_DEFS = {
    "first_laugh": {"fa": "اولین خنده 😂", "en": "First laugh 😂", "check": lambda u: u["jokes"] >= 1},
    "comedy_club": {"fa": "باشگاه کمدی 🎭", "en": "Comedy club 🎭", "check": lambda u: u["jokes"] >= 25},
    "player": {"fa": "گیمر 🎮", "en": "Player 🎮", "check": lambda u: u["games"] >= 15},
    "quiz_brain": {"fa": "مغز کوییز 🧠", "en": "Quiz brain 🧠", "check": lambda u: u["quiz"] >= 50},
    "streak_3": {"fa": "استریک ۳ روزه 🔥", "en": "3-day streak 🔥", "check": lambda u: u["streak"] >= 3},
    "streak_7": {"fa": "استریک ۷ روزه 🏆", "en": "7-day streak 🏆", "check": lambda u: u["streak"] >= 7},
    "social": {"fa": "دعوت‌کننده 📣", "en": "Inviter 📣", "check": lambda u: u.get("invites", 0) >= 3},
    "xp_hero": {"fa": "قهرمان XP ⚡", "en": "XP hero ⚡", "check": lambda u: u.get("xp", 0) >= 500},
    "hangman": {"fa": "شکارچی کلمات 🔤", "en": "Word hunter 🔤", "check": lambda u: u.get("hangman_wins", 0) >= 5},
}


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _migrate(conn: sqlite3.Connection) -> None:
    cols = {r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
    for col, typedef in {
        "xp": "INTEGER NOT NULL DEFAULT 0",
        "invites": "INTEGER NOT NULL DEFAULT 0",
        "referred_by": "INTEGER",
        "remind": "INTEGER NOT NULL DEFAULT 0",
        "hangman_wins": "INTEGER NOT NULL DEFAULT 0",
    }.items():
        if col not in cols:
            conn.execute(f"ALTER TABLE users ADD COLUMN {col} {typedef}")


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
                xp INTEGER NOT NULL DEFAULT 0,
                invites INTEGER NOT NULL DEFAULT 0,
                referred_by INTEGER,
                remind INTEGER NOT NULL DEFAULT 0,
                hangman_wins INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT ''
            )
            """
        )
        _migrate(conn)


def level_from_xp(xp: int) -> int:
    return max(1, int(xp) // 100 + 1)


def title_for(xp: int, lang: str = "fa") -> str:
    level = level_from_xp(xp)
    titles = LEVEL_TITLES["fa" if lang == "fa" else "en"]
    current = titles[0][1]
    for need, title in titles:
        if level >= need:
            current = title
    return current


def xp_bar(xp: int, width: int = 10) -> str:
    into = int(xp) % 100
    filled = min(width, into * width // 100)
    return "█" * filled + "░" * (width - filled)


def ensure_user(user_id: int, name: str = "", lang: str = "fa") -> dict[str, Any]:
    with _connect() as conn:
        _migrate(conn)
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


def apply_referral(new_user_id: int, referrer_id: int) -> bool:
    """Link referral once. Returns True if applied."""
    if not referrer_id or referrer_id == new_user_id:
        return False
    with _connect() as conn:
        _migrate(conn)
        me = conn.execute("SELECT referred_by FROM users WHERE user_id = ?", (new_user_id,)).fetchone()
        if not me or me["referred_by"]:
            return False
        ref = conn.execute("SELECT user_id FROM users WHERE user_id = ?", (referrer_id,)).fetchone()
        if not ref:
            return False
        conn.execute(
            "UPDATE users SET referred_by = ?, updated_at = ? WHERE user_id = ?",
            (referrer_id, _now(), new_user_id),
        )
        conn.execute(
            "UPDATE users SET invites = invites + 1, xp = xp + 50, updated_at = ? WHERE user_id = ?",
            (_now(), referrer_id),
        )
        conn.execute(
            "UPDATE users SET xp = xp + 25, updated_at = ? WHERE user_id = ?",
            (_now(), new_user_id),
        )
        return True


def set_user_lang(user_id: int, lang: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET lang = ?, updated_at = ? WHERE user_id = ?",
            (lang, _now(), user_id),
        )


def bump_stat(user_id: int, key: str, amount: int = 1) -> int:
    if key not in {"jokes", "games", "quiz", "daily", "hangman_wins"}:
        raise ValueError(key)
    with _connect() as conn:
        _migrate(conn)
        conn.execute(
            f"UPDATE users SET {key} = {key} + ?, updated_at = ? WHERE user_id = ?",
            (amount, _now(), user_id),
        )
        row = conn.execute(f"SELECT {key} FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return int(row[0]) if row else 0


def add_xp(user_id: int, amount: int) -> tuple[int, int, bool]:
    """Add XP. Returns (xp, level, leveled_up)."""
    with _connect() as conn:
        _migrate(conn)
        row = conn.execute("SELECT xp FROM users WHERE user_id = ?", (user_id,)).fetchone()
        old_xp = int(row["xp"] if row else 0)
        old_level = level_from_xp(old_xp)
        new_xp = old_xp + amount
        conn.execute(
            "UPDATE users SET xp = ?, updated_at = ? WHERE user_id = ?",
            (new_xp, _now(), user_id),
        )
        new_level = level_from_xp(new_xp)
        return new_xp, new_level, new_level > old_level


def get_stats(user_id: int) -> dict[str, Any]:
    with _connect() as conn:
        _migrate(conn)
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else {}


def set_remind(user_id: int, enabled: bool) -> None:
    with _connect() as conn:
        _migrate(conn)
        conn.execute(
            "UPDATE users SET remind = ?, updated_at = ? WHERE user_id = ?",
            (1 if enabled else 0, _now(), user_id),
        )


def reminder_users() -> list[dict[str, Any]]:
    with _connect() as conn:
        _migrate(conn)
        rows = conn.execute(
            "SELECT user_id, name, lang FROM users WHERE remind = 1"
        ).fetchall()
        return [dict(r) for r in rows]


def claim_daily(user_id: int, fortune: str) -> tuple[bool, str, int]:
    """Return (is_new, fortune_text, streak)."""
    today = date.today()
    today_s = today.isoformat()
    with _connect() as conn:
        _migrate(conn)
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
        _migrate(conn)
        rows = conn.execute(
            """
            SELECT user_id, name, jokes, games, quiz, streak, xp, invites,
                   (jokes + games + quiz + daily + xp / 10) AS score
            FROM users
            ORDER BY xp DESC, score DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
