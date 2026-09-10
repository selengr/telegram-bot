# Funny Friends Bot

A fun Telegram bot for you and your friends.  
Works in **Persian** and **English**.

Bot link: https://t.me/r_helper_fun_bot

---

## What it can do

- Jokes, roasts, compliments
- Daily luck + streak
- Games: truth/dare, would-you-rather, quiz, hangman, chaos story
- XP, levels, badges, leaderboard
- Invite friends and earn XP
- Morning reminder
- Welcome message in groups
- Inline jokes (`@r_helper_fun_bot` in any chat)

---

## Quick start (Mac / Linux)

1. Get a token from [@BotFather](https://t.me/BotFather)
2. In this folder:

```bash
cp .env.example .env
```

3. Open `.env` and paste your token:

```
BOT_TOKEN=123456:ABC...
```

4. Run:

```bash
chmod +x run.sh
./run.sh
```

Or manually:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python bot.py
```

Keep the terminal open. If you close it, the bot goes offline.

---

## Share with friends

Send them:

https://t.me/r_helper_fun_bot

Or use `/invite` inside the bot for your personal invite link.

---

## Useful commands

| Command | Meaning |
|---------|---------|
| `/start` | Start |
| `/menu` | Main menu |
| `/joke` | Joke |
| `/daily` | Daily luck |
| `/hangman` | Word game |
| `/quiz` | Quiz |
| `/stats` | Your XP profile |
| `/top` | Leaderboard |
| `/badges` | Badges |
| `/invite` | Invite link |
| `/remind` | Morning joke on/off |
| `/share` | Share bot |
| `/fa` `/en` | Language |
| `/about` | About |
| `/help` | Help |

---

## Project files

- `bot.py` — main bot
- `db.py` — save users, XP, badges
- `hangman.py` — hangman game
- `.env` — your secret token (not uploaded to GitHub)
- `data/` — local database (created automatically)

---

## Publish checklist

1. Token stays only in `.env` (never commit it)
2. Push code to GitHub
3. Run the bot on your computer (or a small server / VPS later)
4. Share the bot link with friends
5. Optional: in BotFather set a profile photo and about text

---

## Version

`v1.0.1` — ready to share with friends.

## Notes

- Keep the bot process running (your Mac or a server). Morning reminders need it up around **09:00 local time**.
- Your token stays in `.env` and is never pushed to GitHub.
- Optional in BotFather: add a profile photo (description is set by the bot automatically).

Made for fun. Enjoy.
