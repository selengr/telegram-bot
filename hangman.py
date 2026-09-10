"""Hangman word game helpers."""

from __future__ import annotations

import random
import re

WORDS = {
    "fa": [
        "خنده",
        "تلگرام",
        "پیتزا",
        "دوست",
        "کامپیوتر",
        "موسیقی",
        "قهوه",
        "استیکر",
        "گیم",
        "خورشید",
        "ماجرا",
        "کمدی",
        "اینترنت",
        "پروژه",
        "یخچال",
    ],
    "en": [
        "python",
        "telegram",
        "comedy",
        "banana",
        "rocket",
        "puzzle",
        "galaxy",
        "keyboard",
        "coffee",
        "friend",
        "sticker",
        "chaos",
        "wizard",
        "pirate",
        "meme",
    ],
}

HANGMAN_PICS = [
    "➕\n│\n│\n│",
    "➕\n│ 😮\n│\n│",
    "➕\n│ 😮\n│ /\n│",
    "➕\n│ 😮\n│ /|\n│",
    "➕\n│ 😮\n│ /|\\\n│",
    "➕\n│ 😮\n│ /|\\\n│ /",
    "➕\n│ 😵\n│ /|\\\n│ / \\",
]


def _is_persian(word: str) -> bool:
    return bool(re.search(r"[\u0600-\u06FF]", word))


def _norm_char(ch: str, persian: bool) -> str:
    return ch if persian else ch.lower()


def start_game(lang: str) -> dict:
    word = random.choice(WORDS["fa" if lang == "fa" else "en"])
    return {
        "word": word,
        "guessed": [],
        "wrong": 0,
        "max_wrong": 6,
    }


def mask(word: str, guessed: list[str]) -> str:
    persian = _is_persian(word)
    guessed_norm = {_norm_char(g, persian) for g in guessed}
    out = []
    for ch in word:
        if ch == " ":
            out.append(" ")
        elif _norm_char(ch, persian) in guessed_norm:
            out.append(ch)
        else:
            out.append("＿" if persian else "_")
    return " ".join(out)


def render(game: dict, lang: str = "fa") -> str:
    pic = HANGMAN_PICS[min(game["wrong"], len(HANGMAN_PICS) - 1)]
    board = mask(game["word"], game["guessed"])
    guessed = " ".join(game["guessed"]) or "—"
    if lang == "fa":
        return (
            f"*حدس کلمه*\n```\n{pic}\n```\n"
            f"کلمه: `{board}`\n"
            f"غلط: {game['wrong']}/{game['max_wrong']}\n"
            f"حدس‌زده: {guessed}"
        )
    return (
        f"*Hangman*\n```\n{pic}\n```\n"
        f"Word: `{board}`\n"
        f"Wrong: {game['wrong']}/{game['max_wrong']}\n"
        f"Guessed: {guessed}"
    )


def _won(game: dict) -> bool:
    word = game["word"]
    persian = _is_persian(word)
    guessed_norm = {_norm_char(g, persian) for g in game["guessed"]}
    return all(ch == " " or _norm_char(ch, persian) in guessed_norm for ch in word)


def guess(game: dict, letter: str) -> str:
    """Apply guess. Returns status: ok|repeat|wrong|win|lose."""
    letter = letter.strip()
    if not letter:
        return "repeat"

    word = game["word"]
    persian = _is_persian(word)
    if not persian:
        letter = letter.lower()

    # full word guess
    if len(letter) > 1:
        target = word if persian else word.lower()
        if letter == target:
            game["guessed"] = list(dict.fromkeys(list(word) + game["guessed"]))
            return "win"
        game["wrong"] += 1
        return "lose" if game["wrong"] >= game["max_wrong"] else "wrong"

    guessed_norm = {_norm_char(g, persian) for g in game["guessed"]}
    if _norm_char(letter, persian) in guessed_norm:
        return "repeat"

    game["guessed"].append(letter)
    word_chars = {_norm_char(ch, persian) for ch in word if ch != " "}
    if _norm_char(letter, persian) not in word_chars:
        game["wrong"] += 1
        return "lose" if game["wrong"] >= game["max_wrong"] else "wrong"

    return "win" if _won(game) else "ok"


def letter_keyboard(lang: str):
    """Return rows of common letters for inline keyboard."""
    if lang == "fa":
        letters = list("ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی")
    else:
        letters = list("abcdefghijklmnopqrstuvwxyz")
    rows = []
    row = []
    for i, ch in enumerate(letters, start=1):
        row.append(ch)
        if i % 7 == 0:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return rows
