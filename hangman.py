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


def normalize(word: str) -> str:
    return word.strip()


def start_game(lang: str) -> dict:
    word = random.choice(WORDS["fa" if lang == "fa" else "en"])
    return {
        "word": word,
        "guessed": [],
        "wrong": 0,
        "max_wrong": 6,
    }


def mask(word: str, guessed: list[str]) -> str:
    out = []
    for ch in word:
        if ch == " ":
            out.append(" ")
        elif ch in guessed:
            out.append(ch)
        else:
            out.append("＿" if re.search(r"[\u0600-\u06FF]", word) else "_")
    return " ".join(out)


def render(game: dict, lang: str = "fa") -> str:
    pic = HANGMAN_PICS[min(game["wrong"], len(HANGMAN_PICS) - 1)]
    board = mask(game["word"], game["guessed"])
    guessed = " ".join(game["guessed"]) or ("—" if lang == "fa" else "—")
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


def guess(game: dict, letter: str) -> str:
    """Apply guess. Returns status: ok|repeat|wrong|win|lose."""
    letter = letter.strip()
    if not letter:
        return "repeat"
    # allow full word guess
    if len(letter) > 1:
        if letter == game["word"]:
            game["guessed"] = list(dict.fromkeys(list(game["word"]) + game["guessed"]))
            return "win"
        game["wrong"] += 1
        if game["wrong"] >= game["max_wrong"]:
            return "lose"
        return "wrong"

    if letter in game["guessed"]:
        return "repeat"
    game["guessed"].append(letter)
    if letter not in game["word"]:
        game["wrong"] += 1
        if game["wrong"] >= game["max_wrong"]:
            return "lose"
        return "wrong"
    if all(ch == " " or ch in game["guessed"] for ch in game["word"]):
        return "win"
    return "ok"


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
