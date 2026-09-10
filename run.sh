#!/usr/bin/env bash
# Start the Funny Friends Telegram bot
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
else
  source .venv/bin/activate
fi

if [ ! -f ".env" ]; then
  echo "Missing .env file."
  echo "Copy .env.example to .env and put your BotFather token inside."
  exit 1
fi

echo "Starting Funny Friends Bot..."
python bot.py
