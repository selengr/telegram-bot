"""
Funny Friends Bot — bilingual pro fun bot (Persian + English).
"""

from __future__ import annotations

import logging
import os
import random
import re
import time
from datetime import datetime, time as dt_time

from dotenv import load_dotenv
from telegram import (
    BotCommand,
    BotCommandScopeDefault,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.constants import ChatAction, ParseMode
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    InlineQueryHandler,
    MessageHandler,
    filters,
)

import db
import hangman as hangman_game


load_dotenv()

VERSION = "1.0.0"
BOT_SHORT_FA = "ربات خنده با جوک، بازی، XP و دوستان"
BOT_SHORT_EN = "Funny bot with jokes, games, XP & friends"
BOT_DESC_FA = (
    "ربات سرگرمی دوستانه‌ست.\n"
    "جوک، تیکه، فال روزانه، کوییز، حدس کلمه، جدول امتیاز و دعوت دوستان.\n"
    "فارسی و انگلیسی. بزن /start"
)
BOT_DESC_EN = (
    "A friendly fun bot for your group.\n"
    "Jokes, roasts, daily luck, quiz, hangman, leaderboard and invites.\n"
    "Persian & English. Tap /start"
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

PERSIAN_RE = re.compile(r"[\u0600-\u06FF]")

# --- Content (kept sharp & funny) ---

JOKES = {
    "fa": [
        "می‌دونی چرا برنامه‌نویس‌ها عینک می‌زنن؟ چون نمی‌تونن C رو ببینن 😄",
        "رفتم دکتر گفتم حافظه‌م ضعیف شده. گفت: از کی؟ گفتم: از کی چی؟",
        "به رفیقم گفتم رمز وای‌فایت چیه؟ گفت: قوی باش. حالا نیم ساعته دارم سعی می‌کنم قوی باشم 😂",
        "استادم گفت تکالیفت کجاست؟ گفتم تو کلود هست. گفت کدوم کلود؟ گفتم همون ابری که رد شد رفت!",
        "چی میشه اگه وای‌فای قطع بشه؟ مجبوری با خانواده حرف بزنی… ترسناکه!",
        "به باتری گوشیم گفتم چرا زود تموم می‌شی؟ گفت تو خودت از من کم‌طاقت‌تری!",
        "دوستام می‌گن زیاد جوک می‌گم. منم می‌گم زندگی کمدیِ من فقط ساب‌تایتل نداره.",
        "گفتم امروز مود پروداکتیو دارم. لپ‌تاپم خندید و کرش کرد.",
        "تو جلسه گفتن ایده‌هات خارج از جعبه‌ست. گفتم چون جعبه هنوز تو گمرکه.",
        "می‌خواستم ورزش کنم؛ کشش کردم… کشش تا یخچال.",
    ],
    "en": [
        "Why do programmers wear glasses? Because they can't C#.",
        "Wi-Fi went down for 5 minutes… had to talk to my family. They seem nice.",
        "I told my computer I needed a break. It said: 'No problem, I'll go to sleep.'",
        "Why did the developer go broke? Used up all his cache.",
        "I would tell a UDP joke, but you might not get it.",
        "There are 10 types of people: those who get binary and those who don't.",
        "My code works… I have no idea why. My code breaks… I have no idea why.",
        "I don't always test my code, but when I do, I do it in production.",
        "Dark mode: because light attracts bugs.",
        "I changed my password to 'incorrect' so whenever I forget, it says 'your password is incorrect'.",
    ],
}

ROASTS = {
    "fa": [
        "{name}، رمز وای‌فایت از تصمیمات زندگیت قوی‌تره 🔥",
        "{name}، اگه تنبلی المپیک داشت تو به افتتاحیه هم دیر می‌رسیدی.",
        "{name}، باتری گوشیت صبح‌ها از خودت پرانرژی‌تره.",
        "{name}، جوکات انقدر خشکه که کویر ازت مشاوره می‌گیره.",
        "{name}، تختت اسمتو تو لیست ساکنین دائمی نوشته.",
        "{name}، تو دیر نمی‌کنی؛ روی حالت «شخصیت اصلی با تأخیر» هستی.",
        "{name}، اعلان‌هات بیشتر از خودت جواب می‌دن.",
    ],
    "en": [
        "{name}, your Wi-Fi password is stronger than your life decisions.",
        "{name}, if laziness was Olympic, you'd still show up late.",
        "{name}, your phone battery has more energy than you before noon.",
        "{name}, your jokes are so dry the desert asked for tips.",
        "{name}, your bed listed you as a permanent resident.",
        "{name}, you're not late — you're on main-character delay mode.",
        "{name}, ChatGPT works harder than you on group projects.",
    ],
}

COMPLIMENTS = {
    "fa": [
        "{name}، تو مثل پیدا کردن پول تو جیب شلوار قدیمی‌ای 💖",
        "{name}، انرژیت می‌تونه گوشی رو وایرلس شارژ کنه.",
        "{name}، فقط با بودنت گپ گروهی چند برابر باحال‌تر می‌شه.",
        "{name}، مثل کابل شارژری که هنوز کار می‌کنه — کمیاب!",
        "{name}، با تو بودن مثل پیدا کردن جای پارک خالیه.",
        "{name}، حتی غلط املایی‌هات هم کاراکتر دارن.",
    ],
    "en": [
        "{name}, you're like finding money in old jeans.",
        "{name}, your vibe could charge phones wirelessly.",
        "{name}, you make group chats instantly better.",
        "{name}, rare like a charging cable that still works.",
        "{name}, even your typos have personality.",
        "{name}, main-character energy detected.",
    ],
}

FORTUNES = {
    "fa": [
        "امروز وای‌فای رایگان پیدا می‌کنی… شارژر رو گم می‌کنی 🔮",
        "یه خوراکی اسرارآمیز ظاهر می‌شه. قبل از بقیه بردارش!",
        "ایده بعدی‌ت یا نبوغه یا آشوب. در هر صورت انجامش بده.",
        "عدد شانس: ۷ — عدد بدشانسی: پیام‌های خونده‌نشده.",
        "ستاره‌ها: آب بخور، پروژه‌های گروهی مشکوک‌ان.",
        "امروز یه تعریف واقعی می‌گیری. سعی کن باور کنی.",
        "پیچش داستانی در راهه. پاپ‌کورن آماده کن.",
    ],
    "en": [
        "You'll find free Wi-Fi… and lose your charger.",
        "A mysterious snack appears. Claim it fast.",
        "Next idea: genius or chaos. Do it anyway.",
        "Lucky number: 7. Unlucky: unread messages.",
        "Plot twist incoming. Bring snacks.",
        "Someone will laugh at your joke for real today.",
        "Hydrate. Stretch. Don't trust group projects.",
    ],
}

DARES = {
    "fa": [
        "آخرین آهنگ رو ویس کن و نیمه‌کاره بخون 🎤",
        "۱۰ دقیقه اسم تلگرامت رو یه چیز مسخره بذار.",
        "خجالت‌آورترین اتوکرکت رو بفرست تو گپ.",
        "با خنده‌دارترین قیافه سلفی بفرست.",
        "عجیب‌ترین ترکیب غذایی‌ت رو اعتراف کن.",
        "یه پیام کامل با چشم بسته تایپ کن.",
    ],
    "en": [
        "Voice-note the last song you heard — badly.",
        "Rename yourself something ridiculous for 10 minutes.",
        "Send your worst autocorrect fail to the chat.",
        "Selfie with your funniest face.",
        "Confess your cursed food combo.",
        "Type one full message with eyes closed.",
    ],
}

TRUTHS = {
    "fa": [
        "آخرین چیزی که سرچ کردی چی بود؟ (راستش رو بگو)",
        "تو گپ‌ها بیشتر لورک می‌کنی یا اسپم؟",
        "کدوم عادت بدت رو همه می‌دونن ولی تو انکار می‌کنی؟",
        "آخرین بار کی خجالت کشیدی تو چت؟",
        "اگه گوشیت الان به همه پیام‌ها فوروارد بشه، وحشت می‌کنی از کدوم چت؟",
    ],
    "en": [
        "What's the last thing you googled? Be honest.",
        "Are you a lurker or a spammer in chats?",
        "Which bad habit do friends already know about?",
        "When was your last chat cringe moment?",
        "Which chat would terrify you if it auto-forwarded?",
    ],
}

WYR = {
    "fa": [
        ("فقط با استیکر حرف بزنی", "فقط با ویس حرف بزنی"),
        ("اینترنت ضعیف همیشگی", "باتری ۱۵٪ همیشگی"),
        ("همه پیام‌هات با فونت Comic Sans", "همه نوتیف‌هات صدای اردک"),
        ("یه هفته بدون میم", "یه هفته بدون قهوه/چای"),
        ("اسم واقعی‌ت رو همه بدونن", "تاریخ سرچ‌هات رو یکی ببینه"),
    ],
    "en": [
        ("Only stickers forever", "Only voice notes forever"),
        ("Forever slow internet", "Forever 15% battery"),
        ("All messages in Comic Sans", "All notifications are duck sounds"),
        ("One week without memes", "One week without coffee/tea"),
        ("Everyone knows your real name", "Someone sees your search history"),
    ],
}

QUIZ = {
    "fa": [
        {
            "q": "پایتون اسمش از چی اومده؟",
            "options": ["مار پایتون", "گروه کمدی Monty Python", "جزیره پایتون", "برند لپ‌تاپ"],
            "answer": 1,
        },
        {
            "q": "تو تلگرام به ربات‌ها معمولاً چی می‌گن ته اسمشون؟",
            "options": ["_app", "bot", "ai", "tg"],
            "answer": 1,
        },
        {
            "q": "کدوم سریع‌تره؟",
            "options": ["نور", "پیام «اوکی» تو گپ گروهی", "دانلود با اینترنت ایران", "آپدیت ویندوز"],
            "answer": 0,
        },
        {
            "q": "HTTP کد ۲۰۰ یعنی؟",
            "options": ["ارور مرگ", "اوکیه", "برگرد فردا", "رمز اشتباهه"],
            "answer": 1,
        },
        {
            "q": "معمولاً برای ذخیره داده سبک ربات چی خوبه؟",
            "options": ["کاغذ", "SQLite", "فکس", "رادیو"],
            "answer": 1,
        },
        {
            "q": "اگه ربات جواب نده، اول چی چک می‌کنی؟",
            "options": ["آب‌وهوا", "اجرا بودن ربات", "ساعت برج", "رنگ گوشی"],
            "answer": 1,
        },
        {
            "q": "کدوم زبان این ربات رو راه انداخته؟",
            "options": ["HTML", "Python", "Excel", "Photoshop"],
            "answer": 1,
        },
    ],
    "en": [
        {
            "q": "Python is named after…",
            "options": ["The snake", "Monty Python", "A coffee brand", "NASA lab"],
            "answer": 1,
        },
        {
            "q": "Telegram bots usually end with…",
            "options": ["_app", "bot", "ai", "tg"],
            "answer": 1,
        },
        {
            "q": "Which is fastest?",
            "options": ["Light", "Group chat 'ok'", "Windows update", "Printer setup"],
            "answer": 0,
        },
        {
            "q": "HTTP 200 means…",
            "options": ["Fatal error", "OK", "Come back tomorrow", "Wrong password"],
            "answer": 1,
        },
        {
            "q": "Best lightweight DB for a small bot?",
            "options": ["Paper", "SQLite", "Fax machine", "Radio"],
            "answer": 1,
        },
        {
            "q": "Bot silent? Check first…",
            "options": ["Weather", "Is the bot running", "Tower clock", "Phone color"],
            "answer": 1,
        },
        {
            "q": "This bot is powered by…",
            "options": ["HTML", "Python", "Excel", "Photoshop"],
            "answer": 1,
        },
    ],
}

STORY_BITS = {
    "fa": {
        "heroes": ["یه گربه‌ی هکری", "کارمند خستهٔ شرکت", "دانشجوی نصفه‌شب", "راکون با هودی", "ادمین گروه"],
        "places": ["کافی‌شاپ وای‌فای‌دزد", "مترو شلوغ", "سرور اتاق خواب", "گپ فامیلی", "کلاس آنلاین خاموش"],
        "twists": [
            "ناگهان باتری ۱٪ شد",
            "ناگهان مامان اومد تو اتاق",
            "ناگهان همه دیدن آنلاین شدی",
            "ناگهان کپشن اشتباه پست شد",
            "ناگهان وای‌فای قطع شد وسط حرف مهم",
        ],
        "endings": [
            "و همه گفتن: اسطوره.",
            "و هیچ‌کس چیزی نفهمید، ولی خندیدن.",
            "و این شد دلیل تراپی این ماه.",
            "و گروه تا صبح ترکید از خنده.",
        ],
    },
    "en": {
        "heroes": ["a hacker cat", "a tired office human", "a midnight student", "a raccoon in a hoodie", "a group admin"],
        "places": ["a Wi-Fi thieving cafe", "a packed metro", "a bedroom server farm", "a family group chat", "a muted online class"],
        "twists": [
            "suddenly battery hit 1%",
            "suddenly mom entered the room",
            "suddenly everyone saw them online",
            "suddenly the wrong caption posted",
            "suddenly Wi-Fi died mid-confession",
        ],
        "endings": [
            "and everyone whispered: legend.",
            "and nobody understood, but everyone laughed.",
            "and that became this month's therapy topic.",
            "and the group chat exploded till sunrise.",
        ],
    },
}

UI = {
    "fa": {
        "friend": "رفیق",
        "start": (
            "سلام *{name}*! 👋\n\n"
            "به ربات خنده‌دار حرفه‌ای خوش اومدی.\n"
            "منو پایین صفحه یا `/` رو باز کن.\n\n"
            "🇮🇷 فارسی فعال — با /en انگلیسی کن"
        ),
        "help": (
            "*منوی حرفه‌ای ربات*\n\n"
            "🎭 سرگرمی: جوک، تیکه، تعریف، فال روزانه\n"
            "🎮 بازی: جرات/حقیقت، کدوم‌و، کوییز، داستان\n"
            "🏆 پیشرفت: آمار، بج‌ها، جدول امتیاز، XP\n"
            "📣 رشد: دعوت دوستان، یادآور روزانه\n"
            "🔤 بازی جدید: حدس کلمه (/hangman)\n"
            "👥 گروه: خوش‌آمدگویی خودکار به اعضای جدید\n"
            "⚙️ زبان: /fa /en\n\n"
            "توی هر چتی بنویس `@{bot}` تا اینلاین جوک بفرستی!"
        ),
        "menu_title": "🎛️ *منوی اصلی*\nیکی رو انتخاب کن:",
        "lang_set": "✅ زبان: فارسی",
        "typing_joke": "دارم جوک می‌سازم…",
        "daily_used": "فال امروزت قبلاً گرفته شده 🔮\nاستریک: *{streak}* روز\n\n{fortune}",
        "daily_new": "🔮 *فال امروز*\n{fortune}\n\n🔥 استریک: *{streak}* روز",
        "stats": (
            "📊 *پروفایل خنده*\n"
            "نام: {name}\n"
            "لقب: {title}\n"
            "لول: *{level}* | XP: *{xp}*\n"
            "`[{bar}]` {into}/100\n"
            "جوک‌ها: {jokes}\n"
            "بازی‌ها: {games}\n"
            "امتیاز کوییز: {quiz}\n"
            "فال روزانه: {daily}\n"
            "استریک: {streak} 🔥\n"
            "دعوت‌ها: {invites}"
        ),
        "top": "🏆 *جدول خنده‌دارها*\n\n{rows}",
        "top_empty": "هنوز کسی امتیاز نداره. اولین نفر باش!",
        "top_row": "{rank}. {name} — L{level} | {xp} XP",
        "badges": "🎖️ *بج‌های تو*\n\n{rows}",
        "badges_empty": "هنوز بج نداری. جوک بگو، بازی کن، فال روزانه بگیر!",
        "badge_new": "🎉 بج جدید باز شد: *{name}*",
        "level_up": "🚀 لول آپ! حالا لول *{level}* هستی\nلقب جدید: *{title}*",
        "welcome": "خوش اومدی {name}! 🎉\nاینجا بخش خنده‌ست — بزن /menu",
        "invite": (
            "📣 *لینک دعوت تو*\n"
            "`{link}`\n\n"
            "هر دوست با این لینک بیاد، تو *۵۰ XP* می‌گیری!\n"
            "دعوت‌های موفق: *{invites}*"
        ),
        "invite_ok": "🎁 با دعوت دوست اومدی! *۲۵ XP* هدیه گرفتی.",
        "remind_on": "⏰ یادآور روزانه روشن شد (حدود ساعت ۹ صبح).",
        "remind_off": "⏰ یادآور روزانه خاموش شد.",
        "remind_push": "🌞 جوک صبحگاهی:\n😂 {joke}\n\n/daily رو هم فراموش نکن!",
        "hang_guess_hint": "یه حرف بفرست یا از دکمه‌ها استفاده کن.",
        "hang_win": "🎉 بردی! کلمه: *{word}*\n+۳۰ XP",
        "hang_lose": "💀 باختی! کلمه: *{word}*",
        "hang_repeat": "این حرف رو قبلاً زدی.",
        "rate_limit": "آروم‌تر رفیق 😅 یه لحظه صبر کن.",
        "about": (
            "🤖 *Funny Friends Bot* `v{version}`\n\n"
            "یه ربات سرگرمی برای تو و دوستات.\n"
            "جوک · بازی · XP · بج · دعوت · گروه\n\n"
            "لینک: https://t.me/{bot}\n"
            "شروع سریع: /menu"
        ),
        "share": "این ربات رو بفرست برای دوستات 👇",
        "share_text": "بیا این ربات خنده‌دار رو امتحان کن 😄",
        "story": "📖 {hero} رفت به {place}… {twist}… {ending}",
        "tod_title": "🎲 حقیقت یا جرات؟",
        "truth": "🗣️ حقیقت:\n{text}",
        "dare": "🎯 جرات:\n{text}",
        "wyr_title": "🤯 کدوم رو انتخاب می‌کنی؟",
        "quiz_title": "🧠 کوییز\n\n*{q}*",
        "quiz_ok": "✅ درست! امتیازت: {score}",
        "quiz_bad": "❌ اشتباه! جواب درست: *{ans}*\nامتیازت: {score}",
        "coin": "🪙 سکه: *{side}*",
        "coin_sides": ("شیر", "خط"),
        "rate": "📊 *{target}* → *{score}/100* — {vibe}",
        "vibes": ("آشوبِ بامزه", "متوسطِ جذاب", "خفن", "افسانه"),
        "ship_usage": "مثال: `/ship علی سارا`",
        "ship": "{heart} *{a}* ✖️ *{b}*\nسازگاری: *{score}%*",
        "bored": "حوصله‌ت سر رفته؟ منو آماده‌ست 👇",
        "hello": "سلام {name}! منو رو بزن بریم 🎛️",
        "kb": {
            "menu": "🎛️ منو",
            "joke": "😂 جوک",
            "games": "🎮 بازی",
            "daily": "🔮 فال امروز",
            "stats": "📊 آمار",
            "lang": "🌐 زبان",
        },
        "btn": {
            "joke": "😂 جوک",
            "roast": "🔥 تیکه",
            "comp": "💖 تعریف",
            "daily": "🔮 فال امروز",
            "tod": "🎲 حقیقت/جرات",
            "wyr": "🤯 کدوم‌و",
            "quiz": "🧠 کوییز",
            "story": "📖 داستان",
            "coin": "🪙 سکه",
            "ship": "💕 شیپ",
            "stats": "📊 آمار",
            "share": "📤 اشتراک",
            "top": "🏆 جدول",
            "badges": "🎖️ بج‌ها",
            "hang": "🔤 حدس کلمه",
            "invite": "📣 دعوت",
            "remind": "⏰ یادآور",
            "help": "❓ راهنما",
            "back": "↩️ بازگشت",
            "again": "🔁 دوباره",
            "truth": "🗣️ حقیقت",
            "dare": "🎯 جرات",
            "fa": "🇮🇷 فارسی",
            "en": "🇬🇧 English",
        },
        "cmds": [
            ("start", "شروع ربات"),
            ("menu", "منوی اصلی"),
            ("joke", "جوک تصادفی"),
            ("roast", "تیکه دوستانه"),
            ("compliment", "تعریف"),
            ("daily", "فال روزانه"),
            ("tod", "حقیقت یا جرات"),
            ("wyr", "کدوم‌و انتخاب کنی"),
            ("quiz", "کوییز سریع"),
            ("hangman", "حدس کلمه"),
            ("story", "داستان آشوبی"),
            ("stats", "پروفایل و XP"),
            ("top", "جدول امتیاز"),
            ("badges", "بج‌های من"),
            ("invite", "لینک دعوت"),
            ("remind", "یادآور روزانه"),
            ("share", "اشتراک‌گذاری"),
            ("about", "درباره ربات"),
            ("fa", "فارسی"),
            ("en", "English"),
            ("help", "راهنما"),
        ],
    },
    "en": {
        "friend": "friend",
        "start": (
            "Hey *{name}*! 👋\n\n"
            "Welcome to a pro funny bot for friends.\n"
            "Use the menu below or tap `/`.\n\n"
            "🇬🇧 English on — /fa for فارسی"
        ),
        "help": (
            "*Pro bot menu*\n\n"
            "🎭 Fun: joke, roast, compliment, daily luck\n"
            "🎮 Games: truth/dare, would-you-rather, quiz, story\n"
            "🏆 Progress: stats, badges, leaderboard, XP\n"
            "📣 Growth: invites, daily reminder\n"
            "🔤 New game: hangman (/hangman)\n"
            "👥 Groups: auto-welcome for new members\n"
            "⚙️ Language: /fa /en\n\n"
            "Type `@{bot}` in any chat for inline jokes!"
        ),
        "menu_title": "🎛️ *Main menu*\nPick one:",
        "lang_set": "✅ Language: English",
        "typing_joke": "Cooking a joke…",
        "daily_used": "You already opened today's luck 🔮\nStreak: *{streak}* days\n\n{fortune}",
        "daily_new": "🔮 *Daily luck*\n{fortune}\n\n🔥 Streak: *{streak}* days",
        "stats": (
            "📊 *Fun profile*\n"
            "Name: {name}\n"
            "Title: {title}\n"
            "Level: *{level}* | XP: *{xp}*\n"
            "`[{bar}]` {into}/100\n"
            "Jokes: {jokes}\n"
            "Games: {games}\n"
            "Quiz score: {quiz}\n"
            "Daily luck: {daily}\n"
            "Streak: {streak} 🔥\n"
            "Invites: {invites}"
        ),
        "top": "🏆 *Leaderboard*\n\n{rows}",
        "top_empty": "Nobody scored yet. Be first!",
        "top_row": "{rank}. {name} — L{level} | {xp} XP",
        "badges": "🎖️ *Your badges*\n\n{rows}",
        "badges_empty": "No badges yet. Joke, play, claim daily luck!",
        "badge_new": "🎉 New badge unlocked: *{name}*",
        "level_up": "🚀 Level up! You are now level *{level}*\nNew title: *{title}*",
        "welcome": "Welcome {name}! 🎉\nThis chat is for laughs — tap /menu",
        "invite": (
            "📣 *Your invite link*\n"
            "`{link}`\n\n"
            "Friends joining with it give you *50 XP*!\n"
            "Successful invites: *{invites}*"
        ),
        "invite_ok": "🎁 You joined via invite! *+25 XP* gift.",
        "remind_on": "⏰ Daily reminder ON (around 9 AM).",
        "remind_off": "⏰ Daily reminder OFF.",
        "remind_push": "🌞 Morning joke:\n😂 {joke}\n\nDon't forget /daily !",
        "hang_guess_hint": "Send a letter or use the buttons.",
        "hang_win": "🎉 You won! Word: *{word}*\n+30 XP",
        "hang_lose": "💀 You lost! Word: *{word}*",
        "hang_repeat": "You already tried that.",
        "rate_limit": "Slow down a sec 😅",
        "about": (
            "🤖 *Funny Friends Bot* `v{version}`\n\n"
            "A fun bot for you and your friends.\n"
            "Jokes · games · XP · badges · invites · groups\n\n"
            "Link: https://t.me/{bot}\n"
            "Quick start: /menu"
        ),
        "share": "Share this bot with friends 👇",
        "share_text": "Try this funny Telegram bot 😄",
        "story": "📖 {hero} went to {place}… {twist}… {ending}",
        "tod_title": "🎲 Truth or Dare?",
        "truth": "🗣️ Truth:\n{text}",
        "dare": "🎯 Dare:\n{text}",
        "wyr_title": "🤯 Would you rather…",
        "quiz_title": "🧠 Quiz\n\n*{q}*",
        "quiz_ok": "✅ Correct! Score: {score}",
        "quiz_bad": "❌ Nope! Answer: *{ans}*\nScore: {score}",
        "coin": "🪙 Coin: *{side}*",
        "coin_sides": ("Heads", "Tails"),
        "rate": "📊 *{target}* → *{score}/100* — {vibe}",
        "vibes": ("chaotically fun", "solid mid", "elite", "legendary"),
        "ship_usage": "Example: `/ship Alice Bob`",
        "ship": "{heart} *{a}* ✖️ *{b}*\nMatch: *{score}%*",
        "bored": "Bored? Menu is ready 👇",
        "hello": "Hey {name}! Hit the menu 🎛️",
        "kb": {
            "menu": "🎛️ Menu",
            "joke": "😂 Joke",
            "games": "🎮 Games",
            "daily": "🔮 Daily",
            "stats": "📊 Stats",
            "lang": "🌐 Lang",
        },
        "btn": {
            "joke": "😂 Joke",
            "roast": "🔥 Roast",
            "comp": "💖 Compliment",
            "daily": "🔮 Daily luck",
            "tod": "🎲 Truth/Dare",
            "wyr": "🤯 Would you rather",
            "quiz": "🧠 Quiz",
            "story": "📖 Story",
            "coin": "🪙 Coin",
            "ship": "💕 Ship",
            "stats": "📊 Stats",
            "share": "📤 Share",
            "top": "🏆 Top",
            "badges": "🎖️ Badges",
            "hang": "🔤 Hangman",
            "invite": "📣 Invite",
            "remind": "⏰ Remind",
            "help": "❓ Help",
            "back": "↩️ Back",
            "again": "🔁 Again",
            "truth": "🗣️ Truth",
            "dare": "🎯 Dare",
            "fa": "🇮🇷 فارسی",
            "en": "🇬🇧 English",
        },
        "cmds": [
            ("start", "Start the bot"),
            ("menu", "Main menu"),
            ("joke", "Random joke"),
            ("roast", "Friendly roast"),
            ("compliment", "Compliment"),
            ("daily", "Daily luck"),
            ("tod", "Truth or dare"),
            ("wyr", "Would you rather"),
            ("quiz", "Quick quiz"),
            ("hangman", "Hangman word game"),
            ("story", "Chaos story"),
            ("stats", "Profile & XP"),
            ("top", "Leaderboard"),
            ("badges", "My badges"),
            ("invite", "Invite link"),
            ("remind", "Daily reminder"),
            ("share", "Share bot"),
            ("about", "About this bot"),
            ("fa", "فارسی"),
            ("en", "English"),
            ("help", "Help"),
        ],
    },
}


def lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    value = context.user_data.get("lang")
    return value if value in ("fa", "en") else "fa"


def set_lang(context: ContextTypes.DEFAULT_TYPE, value: str, user_id: int | None = None) -> None:
    context.user_data["lang"] = value
    if user_id:
        db.set_user_lang(user_id, value)


def t(context: ContextTypes.DEFAULT_TYPE) -> dict:
    return UI[lang(context)]


def name_of(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    user = update.effective_user
    if not user:
        return t(context)["friend"]
    return user.first_name or user.username or t(context)["friend"]


def sync_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    user = update.effective_user
    if not user:
        return None
    saved = db.ensure_user(user.id, name_of(update, context), lang(context))
    if "lang" not in context.user_data and saved.get("lang") in ("fa", "en"):
        context.user_data["lang"] = saved["lang"]
    return user.id


def bump(update: Update, context: ContextTypes.DEFAULT_TYPE, key: str, amount: int = 1) -> int:
    user_id = sync_user(update, context)
    if not user_id:
        return 0
    value = db.bump_stat(user_id, key, amount)
    stats = context.user_data.setdefault("stats", {})
    stats[key] = value
    return value


async def grant_pending_xp(update: Update, context: ContextTypes.DEFAULT_TYPE, message=None) -> None:
    user_id = sync_user(update, context)
    amount = int(context.user_data.pop("_pending_xp", 0) or 0)
    if not user_id or amount <= 0:
        return
    new_xp, new_level, leveled = db.add_xp(user_id, amount)
    if leveled:
        target = message or update.effective_message
        await target.reply_text(
            t(context)["level_up"].format(
                level=new_level,
                title=db.title_for(new_xp, lang(context)),
            ),
            parse_mode=ParseMode.MARKDOWN,
        )


def rate_ok(context: ContextTypes.DEFAULT_TYPE, cooldown: float = 0.7) -> bool:
    now = time.monotonic()
    last = float(context.user_data.get("_rl", 0))
    if now - last < cooldown:
        return False
    context.user_data["_rl"] = now
    return True


async def maybe_announce_badges(update: Update, context: ContextTypes.DEFAULT_TYPE, message=None) -> None:
    await grant_pending_xp(update, context, message=message)
    user_id = sync_user(update, context)
    if not user_id:
        return
    newly = db.unlock_badges(user_id)
    if not newly:
        return
    ui = t(context)
    target = message or update.effective_message
    for badge_id in newly:
        label = db.BADGE_DEFS[badge_id][lang(context)]
        await target.reply_text(ui["badge_new"].format(name=label), parse_mode=ParseMode.MARKDOWN)


def reply_kb(context: ContextTypes.DEFAULT_TYPE) -> ReplyKeyboardMarkup:
    kb = t(context)["kb"]
    return ReplyKeyboardMarkup(
        [
            [kb["menu"], kb["joke"]],
            [kb["games"], kb["daily"]],
            [kb["stats"], kb["lang"]],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def main_inline(context: ContextTypes.DEFAULT_TYPE) -> InlineKeyboardMarkup:
    b = t(context)["btn"]
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(b["joke"], callback_data="act:joke"), InlineKeyboardButton(b["roast"], callback_data="act:roast")],
            [InlineKeyboardButton(b["comp"], callback_data="act:comp"), InlineKeyboardButton(b["daily"], callback_data="act:daily")],
            [InlineKeyboardButton(b["hang"], callback_data="act:hang"), InlineKeyboardButton(b["quiz"], callback_data="act:quiz")],
            [InlineKeyboardButton(b["stats"], callback_data="act:stats"), InlineKeyboardButton(b["top"], callback_data="act:top")],
            [InlineKeyboardButton(b["invite"], callback_data="act:invite"), InlineKeyboardButton(b["remind"], callback_data="act:remind")],
            [InlineKeyboardButton(b["fa"], callback_data="lang:fa"), InlineKeyboardButton(b["en"], callback_data="lang:en")],
        ]
    )


def games_inline(context: ContextTypes.DEFAULT_TYPE) -> InlineKeyboardMarkup:
    b = t(context)["btn"]
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(b["tod"], callback_data="act:tod"), InlineKeyboardButton(b["wyr"], callback_data="act:wyr")],
            [InlineKeyboardButton(b["quiz"], callback_data="act:quiz"), InlineKeyboardButton(b["hang"], callback_data="act:hang")],
            [InlineKeyboardButton(b["story"], callback_data="act:story"), InlineKeyboardButton(b["coin"], callback_data="act:coin")],
            [InlineKeyboardButton(b["back"], callback_data="menu:main")],
        ]
    )


def again_kb(context: ContextTypes.DEFAULT_TYPE, action: str) -> InlineKeyboardMarkup:
    b = t(context)["btn"]
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(b["again"], callback_data=f"act:{action}"), InlineKeyboardButton(b["back"], callback_data="menu:main")],
        ]
    )


async def typing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat:
        await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)


async def setup_commands(app: Application) -> None:
    db.init_db()
    fa_cmds = [BotCommand(c, d) for c, d in UI["fa"]["cmds"]]
    en_cmds = [BotCommand(c, d) for c, d in UI["en"]["cmds"]]
    await app.bot.set_my_commands(fa_cmds, scope=BotCommandScopeDefault(), language_code="fa")
    await app.bot.set_my_commands(en_cmds, scope=BotCommandScopeDefault(), language_code="en")
    await app.bot.set_my_commands(fa_cmds, scope=BotCommandScopeDefault())

    # Public profile text (helps when people open the bot page)
    try:
        await app.bot.set_my_short_description(BOT_SHORT_FA, language_code="fa")
        await app.bot.set_my_short_description(BOT_SHORT_EN, language_code="en")
        await app.bot.set_my_short_description(BOT_SHORT_FA)
        await app.bot.set_my_description(BOT_DESC_FA, language_code="fa")
        await app.bot.set_my_description(BOT_DESC_EN, language_code="en")
        await app.bot.set_my_description(BOT_DESC_FA)
    except Exception:
        logger.exception("Could not set bot profile description")

    me = await app.bot.get_me()
    app.bot_data["username"] = me.username or ""
    if app.job_queue:
        app.job_queue.run_daily(send_morning_reminders, time=dt_time(hour=9, minute=0))
        logger.info("Daily reminder job scheduled at 09:00")
    logger.info("Funny Friends Bot v%s ready @%s", VERSION, me.username)


async def send_morning_reminders(context: ContextTypes.DEFAULT_TYPE) -> None:
    for user in db.reminder_users():
        joke = random.choice(JOKES[user.get("lang") if user.get("lang") in ("fa", "en") else "fa"])
        text = UI[user.get("lang") if user.get("lang") in ("fa", "en") else "fa"]["remind_push"].format(joke=joke)
        try:
            await context.bot.send_message(chat_id=user["user_id"], text=text)
        except Exception:
            logger.exception("Reminder failed for %s", user.get("user_id"))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    was_new = False
    if user:
        was_new = not db.get_stats(user.id)
    sync_user(update, context)
    if "lang" not in context.user_data:
        set_lang(context, "fa", user.id if user else None)

    if was_new and context.args and user:
        payload = context.args[0]
        if payload.startswith("ref_"):
            try:
                ref_id = int(payload.replace("ref_", "", 1))
            except ValueError:
                ref_id = 0
            if db.apply_referral(user.id, ref_id):
                await update.message.reply_text(t(context)["invite_ok"], parse_mode=ParseMode.MARKDOWN)
                await maybe_announce_badges(update, context)

    await typing(update, context)
    text = t(context)["start"].format(name=name_of(update, context))
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_kb(context),
    )
    await update.message.reply_text(
        t(context)["menu_title"],
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_inline(context),
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sync_user(update, context)
    bot = context.application.bot_data.get("username", "bot")
    await update.message.reply_text(
        t(context)["help"].format(bot=bot),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_inline(context),
    )


async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sync_user(update, context)
    await update.message.reply_text(
        t(context)["menu_title"],
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_inline(context),
    )


async def set_fa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = sync_user(update, context)
    set_lang(context, "fa", uid)
    await update.message.reply_text(UI["fa"]["lang_set"], reply_markup=reply_kb(context))
    await menu_cmd(update, context)


async def set_en(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    uid = sync_user(update, context)
    set_lang(context, "en", uid)
    await update.message.reply_text(UI["en"]["lang_set"], reply_markup=reply_kb(context))
    await menu_cmd(update, context)


def award_xp(context: ContextTypes.DEFAULT_TYPE, amount: int) -> None:
    if amount > 0:
        context.user_data["_pending_xp"] = int(context.user_data.get("_pending_xp", 0) or 0) + amount


def joke_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bump(update, context, "jokes")
    award_xp(context, 5)
    return f"😂 {random.choice(JOKES[lang(context)])}"


def roast_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    award_xp(context, 3)
    return f"🔥 {random.choice(ROASTS[lang(context)]).format(name=name_of(update, context))}"


def comp_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    award_xp(context, 3)
    return f"💖 {random.choice(COMPLIMENTS[lang(context)]).format(name=name_of(update, context))}"


def story_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bump(update, context, "games")
    award_xp(context, 8)
    bits = STORY_BITS[lang(context)]
    return t(context)["story"].format(
        hero=random.choice(bits["heroes"]),
        place=random.choice(bits["places"]),
        twist=random.choice(bits["twists"]),
        ending=random.choice(bits["endings"]),
    )


def daily_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    sync_user(update, context)
    user = update.effective_user
    fortune_pool = random.choice(FORTUNES[lang(context)])
    if not user:
        return t(context)["daily_new"].format(fortune=fortune_pool, streak=1)
    is_new, fortune, streak = db.claim_daily(user.id, fortune_pool)
    if is_new:
        award_xp(context, 20)
    key = "daily_new" if is_new else "daily_used"
    return t(context)[key].format(fortune=fortune, streak=streak)


def stats_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    user_id = sync_user(update, context)
    s = db.get_stats(user_id) if user_id else {}
    xp = int(s.get("xp", 0) or 0)
    return t(context)["stats"].format(
        name=name_of(update, context),
        title=db.title_for(xp, lang(context)),
        level=db.level_from_xp(xp),
        xp=xp,
        bar=db.xp_bar(xp),
        into=xp % 100,
        jokes=s.get("jokes", 0),
        games=s.get("games", 0),
        quiz=s.get("quiz", 0),
        daily=s.get("daily", 0),
        streak=s.get("streak", 0),
        invites=s.get("invites", 0),
    )


def top_text(context: ContextTypes.DEFAULT_TYPE) -> str:
    rows = db.leaderboard(10)
    ui = t(context)
    if not rows:
        return ui["top"].format(rows=ui["top_empty"])
    lines = []
    for i, row in enumerate(rows, start=1):
        name = row.get("name") or ui["friend"]
        xp = int(row.get("xp", 0) or 0)
        lines.append(
            ui["top_row"].format(
                rank=i,
                name=name,
                level=db.level_from_xp(xp),
                xp=xp,
            )
        )
    return ui["top"].format(rows="\n".join(lines))


def badges_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    user_id = sync_user(update, context)
    ui = t(context)
    if not user_id:
        return ui["badges"].format(rows=ui["badges_empty"])
    user = db.get_stats(user_id)
    owned = db.badge_list(user.get("badges", ""))
    if not owned:
        return ui["badges"].format(rows=ui["badges_empty"])
    lines = [f"• {db.BADGE_DEFS[b][lang(context)]}" for b in owned if b in db.BADGE_DEFS]
    return ui["badges"].format(rows="\n".join(lines) or ui["badges_empty"])


async def send_share(update: Update, context: ContextTypes.DEFAULT_TYPE, message=None) -> None:
    bot = context.application.bot_data.get("username", "")
    ui = t(context)
    link = f"https://t.me/{bot}" if bot else "https://t.me/"
    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🚀 Open", url=link)], [InlineKeyboardButton(ui["btn"]["back"], callback_data="menu:main")]]
    )
    target = message or update.effective_message
    await target.reply_text(f"{ui['share']}\n{link}\n\n{ui['share_text']}", reply_markup=kb)


async def joke_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await typing(update, context)
    await update.message.reply_text(joke_text(update, context), reply_markup=again_kb(context, "joke"))
    await maybe_announce_badges(update, context)


async def roast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(roast_text(update, context), reply_markup=again_kb(context, "roast"))
    await maybe_announce_badges(update, context)


async def compliment_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(comp_text(update, context), reply_markup=again_kb(context, "comp"))
    await maybe_announce_badges(update, context)


async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        daily_text(update, context),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=again_kb(context, "daily"),
    )
    await maybe_announce_badges(update, context)


async def story_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(story_text(update, context), reply_markup=again_kb(context, "story"))
    await maybe_announce_badges(update, context)


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        stats_text(update, context),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_inline(context),
    )


async def top_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sync_user(update, context)
    await update.message.reply_text(top_text(context), parse_mode=ParseMode.MARKDOWN, reply_markup=main_inline(context))


async def badges_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        badges_text(update, context),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_inline(context),
    )


def hangman_markup(context: ContextTypes.DEFAULT_TYPE, game: dict) -> InlineKeyboardMarkup:
    used = set(game.get("guessed", []))
    rows = []
    for row in hangman_game.letter_keyboard(lang(context)):
        buttons = []
        for ch in row:
            if ch in used:
                continue
            buttons.append(InlineKeyboardButton(ch, callback_data=f"hg:{ch}"))
            if len(buttons) == 7:
                rows.append(buttons)
                buttons = []
        if buttons:
            rows.append(buttons)
    rows.append([InlineKeyboardButton(t(context)["btn"]["back"], callback_data="menu:games")])
    return InlineKeyboardMarkup(rows)


async def begin_hangman(update: Update, context: ContextTypes.DEFAULT_TYPE, message) -> None:
    game = hangman_game.start_game(lang(context))
    context.user_data["hangman"] = game
    bump(update, context, "games")
    award_xp(context, 5)
    await message.reply_text(
        hangman_game.render(game, lang(context)),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=hangman_markup(context, game),
    )
    await maybe_announce_badges(update, context, message=message)


async def resolve_hangman(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    letter: str,
    message,
) -> None:
    game = context.user_data.get("hangman")
    ui = t(context)
    if not game:
        await begin_hangman(update, context, message)
        return
    status = hangman_game.guess(game, letter)
    if status == "repeat":
        await message.reply_text(ui["hang_repeat"])
        return
    if status == "win":
        context.user_data.pop("hangman", None)
        bump(update, context, "hangman_wins")
        award_xp(context, 30)
        await message.reply_text(
            ui["hang_win"].format(word=game["word"]),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=again_kb(context, "hang"),
        )
        await maybe_announce_badges(update, context, message=message)
        return
    if status == "lose":
        context.user_data.pop("hangman", None)
        await message.reply_text(
            ui["hang_lose"].format(word=game["word"]),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=again_kb(context, "hang"),
        )
        return
    await message.reply_text(
        hangman_game.render(game, lang(context)),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=hangman_markup(context, game),
    )


async def hangman_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await begin_hangman(update, context, update.message)


async def invite_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = sync_user(update, context)
    bot = context.application.bot_data.get("username", "")
    s = db.get_stats(user_id) if user_id else {}
    link = f"https://t.me/{bot}?start=ref_{user_id}" if bot and user_id else ""
    msg = update.effective_message
    await msg.reply_text(
        t(context)["invite"].format(link=link, invites=s.get("invites", 0)),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_inline(context),
    )


async def remind_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = sync_user(update, context)
    if not user_id:
        return
    s = db.get_stats(user_id)
    enabled = not bool(s.get("remind"))
    db.set_remind(user_id, enabled)
    await update.effective_message.reply_text(t(context)["remind_on" if enabled else "remind_off"])


async def share_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_share(update, context)


async def about_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sync_user(update, context)
    bot = context.application.bot_data.get("username", "r_helper_fun_bot")
    await update.effective_message.reply_text(
        t(context)["about"].format(version=VERSION, bot=bot),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_inline(context),
    )


async def tod_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    b = t(context)["btn"]
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(b["truth"], callback_data="tod:truth"), InlineKeyboardButton(b["dare"], callback_data="tod:dare")],
            [InlineKeyboardButton(b["back"], callback_data="menu:games")],
        ]
    )
    await update.message.reply_text(t(context)["tod_title"], reply_markup=kb)


async def wyr_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    a, b_opt = random.choice(WYR[lang(context)])
    bump(update, context, "games")
    award_xp(context, 8)
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(f"🅰️ {a}", callback_data="wyr:pick")],
            [InlineKeyboardButton(f"🅱️ {b_opt}", callback_data="wyr:pick")],
            [InlineKeyboardButton(t(context)["btn"]["again"], callback_data="act:wyr")],
            [InlineKeyboardButton(t(context)["btn"]["back"], callback_data="menu:games")],
        ]
    )
    await update.message.reply_text(t(context)["wyr_title"], reply_markup=kb)
    await maybe_announce_badges(update, context)


async def quiz_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_quiz(update, context, update.message)


async def coin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    side = random.choice(t(context)["coin_sides"])
    await update.message.reply_text(
        t(context)["coin"].format(side=side),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=again_kb(context, "coin"),
    )


async def ship_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ui = t(context)
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(ui["ship_usage"], parse_mode=ParseMode.MARKDOWN)
        return
    a, b = context.args[0], context.args[1]
    score = random.randint(1, 100)
    heart = "💕" if score >= 70 else "🙂" if score >= 40 else "💀"
    await update.message.reply_text(ui["ship"].format(heart=heart, a=a, b=b, score=score), parse_mode=ParseMode.MARKDOWN)


async def welcome_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.new_chat_members:
        return
    ui = t(context)
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        name = member.first_name or member.username or ui["friend"]
        await update.message.reply_text(ui["welcome"].format(name=name))


async def send_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE, message) -> None:
    item = random.choice(QUIZ[lang(context)])
    context.user_data["quiz"] = item
    bump(update, context, "games")
    award_xp(context, 5)
    buttons = [
        [InlineKeyboardButton(opt, callback_data=f"quiz:{i}")]
        for i, opt in enumerate(item["options"])
    ]
    buttons.append([InlineKeyboardButton(t(context)["btn"]["back"], callback_data="menu:games")])
    await message.reply_text(
        t(context)["quiz_title"].format(q=item["q"]),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    await maybe_announce_badges(update, context, message=message)


async def safe_edit(query, text: str, reply_markup=None, parse_mode=None) -> None:
    try:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except BadRequest:
        await query.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    sync_user(update, context)
    data = query.data or ""
    ui = t(context)
    uid = update.effective_user.id if update.effective_user else None

    if data.startswith("lang:"):
        set_lang(context, data.split(":", 1)[1], uid)
        await query.message.reply_text(t(context)["lang_set"], reply_markup=reply_kb(context))
        await safe_edit(query, t(context)["menu_title"], main_inline(context), ParseMode.MARKDOWN)
        return

    if data == "menu:main":
        await safe_edit(query, ui["menu_title"], main_inline(context), ParseMode.MARKDOWN)
        return
    if data == "menu:games":
        title = "🎮" if lang(context) == "en" else "🎮 بازی‌ها"
        await safe_edit(query, f"{title}\n{ui['menu_title']}", games_inline(context), ParseMode.MARKDOWN)
        return

    if data.startswith("tod:"):
        kind = data.split(":", 1)[1]
        bump(update, context, "games")
        award_xp(context, 8)
        if kind == "truth":
            text = ui["truth"].format(text=random.choice(TRUTHS[lang(context)]))
        else:
            text = ui["dare"].format(text=random.choice(DARES[lang(context)]))
        b = ui["btn"]
        kb = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(b["truth"], callback_data="tod:truth"), InlineKeyboardButton(b["dare"], callback_data="tod:dare")],
                [InlineKeyboardButton(b["back"], callback_data="menu:games")],
            ]
        )
        await query.message.reply_text(text, reply_markup=kb)
        await maybe_announce_badges(update, context, message=query.message)
        return

    if data == "wyr:pick":
        await query.answer("😏" if lang(context) == "en" else "انتخاب جالبی بود 😏", show_alert=False)
        return

    if data.startswith("quiz:"):
        item = context.user_data.get("quiz")
        if not item:
            await query.message.reply_text(ui["menu_title"], reply_markup=main_inline(context), parse_mode=ParseMode.MARKDOWN)
            return
        choice = int(data.split(":", 1)[1])
        if choice == item["answer"]:
            score = bump(update, context, "quiz", 10)
            award_xp(context, 15)
            msg = ui["quiz_ok"].format(score=score)
        else:
            user_id = sync_user(update, context)
            score = db.get_stats(user_id).get("quiz", 0) if user_id else 0
            msg = ui["quiz_bad"].format(ans=item["options"][item["answer"]], score=score)
        await query.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=again_kb(context, "quiz"))
        await maybe_announce_badges(update, context, message=query.message)
        return

    if data.startswith("hg:"):
        letter = data.split(":", 1)[1]
        await resolve_hangman(update, context, letter, query.message)
        return

    if data.startswith("act:"):
        action = data.split(":", 1)[1]
        await context.bot.send_chat_action(chat_id=query.message.chat_id, action=ChatAction.TYPING)

        if action == "joke":
            await query.message.reply_text(joke_text(update, context), reply_markup=again_kb(context, "joke"))
            await maybe_announce_badges(update, context, message=query.message)
        elif action == "roast":
            await query.message.reply_text(roast_text(update, context), reply_markup=again_kb(context, "roast"))
            await maybe_announce_badges(update, context, message=query.message)
        elif action == "comp":
            await query.message.reply_text(comp_text(update, context), reply_markup=again_kb(context, "comp"))
            await maybe_announce_badges(update, context, message=query.message)
        elif action == "daily":
            await query.message.reply_text(
                daily_text(update, context),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=again_kb(context, "daily"),
            )
            await maybe_announce_badges(update, context, message=query.message)
        elif action == "story":
            await query.message.reply_text(story_text(update, context), reply_markup=again_kb(context, "story"))
            await maybe_announce_badges(update, context, message=query.message)
        elif action == "stats":
            await query.message.reply_text(
                stats_text(update, context),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=main_inline(context),
            )
        elif action == "top":
            await query.message.reply_text(top_text(context), parse_mode=ParseMode.MARKDOWN, reply_markup=main_inline(context))
        elif action == "badges":
            await query.message.reply_text(
                badges_text(update, context),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=main_inline(context),
            )
        elif action == "invite":
            await invite_cmd(update, context)
        elif action == "remind":
            await remind_cmd(update, context)
        elif action == "hang":
            await begin_hangman(update, context, query.message)
        elif action == "share":
            await send_share(update, context, message=query.message)
        elif action == "coin":
            side = random.choice(ui["coin_sides"])
            await query.message.reply_text(
                ui["coin"].format(side=side),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=again_kb(context, "coin"),
            )
        elif action == "tod":
            b = ui["btn"]
            kb = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(b["truth"], callback_data="tod:truth"), InlineKeyboardButton(b["dare"], callback_data="tod:dare")],
                    [InlineKeyboardButton(b["back"], callback_data="menu:games")],
                ]
            )
            await query.message.reply_text(ui["tod_title"], reply_markup=kb)
        elif action == "wyr":
            a, b_opt = random.choice(WYR[lang(context)])
            bump(update, context, "games")
            award_xp(context, 8)
            kb = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(f"🅰️ {a}", callback_data="wyr:pick")],
                    [InlineKeyboardButton(f"🅱️ {b_opt}", callback_data="wyr:pick")],
                    [InlineKeyboardButton(ui["btn"]["again"], callback_data="act:wyr")],
                    [InlineKeyboardButton(ui["btn"]["back"], callback_data="menu:games")],
                ]
            )
            await query.message.reply_text(ui["wyr_title"], reply_markup=kb)
            await maybe_announce_badges(update, context, message=query.message)
        elif action == "quiz":
            await send_quiz(update, context, query.message)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text_raw = update.message.text or ""
    text = text_raw.strip()
    sync_user(update, context)
    if "lang" not in context.user_data and PERSIAN_RE.search(text_raw):
        uid = update.effective_user.id if update.effective_user else None
        set_lang(context, "fa", uid)

    if not rate_ok(context):
        await update.message.reply_text(t(context)["rate_limit"])
        return

    # Active hangman: treat short messages as guesses
    if context.user_data.get("hangman") and text and not text.startswith("/"):
        kb_labels = set(t(context)["kb"].values())
        if text not in kb_labels:
            await resolve_hangman(update, context, text, update.message)
            return

    kb = t(context)["kb"]
    mapping = {
        kb["menu"]: menu_cmd,
        kb["joke"]: joke_cmd,
        kb["games"]: lambda u, c: u.message.reply_text(
            ("🎮 Games\n" if lang(c) == "en" else "🎮 بازی‌ها\n") + t(c)["menu_title"],
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=games_inline(c),
        ),
        kb["daily"]: daily_cmd,
        kb["stats"]: stats_cmd,
        kb["lang"]: lambda u, c: u.message.reply_text(
            t(c)["lang_set"] + "\n/fa | /en",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(t(c)["btn"]["fa"], callback_data="lang:fa"), InlineKeyboardButton(t(c)["btn"]["en"], callback_data="lang:en")]]
            ),
        ),
    }
    # Also accept the other language keyboard labels
    for other in ("fa", "en"):
        if other == lang(context):
            continue
        okb = UI[other]["kb"]
        mapping.setdefault(okb["menu"], menu_cmd)
        mapping.setdefault(okb["joke"], joke_cmd)
        mapping.setdefault(okb["daily"], daily_cmd)
        mapping.setdefault(okb["stats"], stats_cmd)

    handler = mapping.get(text)
    if handler:
        result = handler(update, context)
        if hasattr(result, "__await__"):
            await result
        return

    low = text.lower()
    name = name_of(update, context)
    ui = t(context)
    if any(w in text or w in low for w in ("bored", "boring", "حوصله", "کسل", "حوصلم")):
        await update.message.reply_text(ui["bored"], reply_markup=main_inline(context))
        return
    if any(w in text or w in low for w in ("hello", "hi", "hey", "salam", "سلام", "درود")):
        await update.message.reply_text(ui["hello"].format(name=name), reply_markup=reply_kb(context))
        return
    if "?" in text or "؟" in text:
        answers = FORTUNES[lang(context)]
        await update.message.reply_text(f"🎱 {random.choice(answers)}")
        return
    await update.message.reply_text(ui["bored"], reply_markup=main_inline(context))


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.inline_query.query.strip() if update.inline_query else ""
    # Default Persian jokes for inline; mix a bit of English too
    pool = JOKES["fa"] + JOKES["en"]
    if query:
        filtered = [j for j in pool if query.lower() in j.lower()] or pool
    else:
        filtered = pool
    sample = random.sample(filtered, k=min(5, len(filtered)))
    results = [
        InlineQueryResultArticle(
            id=str(i),
            title=("😂 Joke" if not PERSIAN_RE.search(joke) else "😂 جوک"),
            description=joke[:80],
            input_message_content=InputTextMessageContent(joke),
        )
        for i, joke in enumerate(sample)
    ]
    await update.inline_query.answer(results, cache_time=5, is_personal=True)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Update error: %s", context.error)


def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise SystemExit("Missing BOT_TOKEN. Put it in a .env file.")

    app = (
        Application.builder()
        .token(token)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .pool_timeout(30.0)
        .get_updates_connect_timeout(30.0)
        .get_updates_read_timeout(30.0)
        .post_init(setup_commands)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CommandHandler("fa", set_fa))
    app.add_handler(CommandHandler("en", set_en))
    app.add_handler(CommandHandler("joke", joke_cmd))
    app.add_handler(CommandHandler("roast", roast_cmd))
    app.add_handler(CommandHandler("compliment", compliment_cmd))
    app.add_handler(CommandHandler("daily", daily_cmd))
    app.add_handler(CommandHandler("tod", tod_cmd))
    app.add_handler(CommandHandler("wyr", wyr_cmd))
    app.add_handler(CommandHandler("quiz", quiz_cmd))
    app.add_handler(CommandHandler("hangman", hangman_cmd))
    app.add_handler(CommandHandler("story", story_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("top", top_cmd))
    app.add_handler(CommandHandler("badges", badges_cmd))
    app.add_handler(CommandHandler("invite", invite_cmd))
    app.add_handler(CommandHandler("remind", remind_cmd))
    app.add_handler(CommandHandler("share", share_cmd))
    app.add_handler(CommandHandler("about", about_cmd))
    app.add_handler(CommandHandler("flip", coin_cmd))
    app.add_handler(CommandHandler("coin", coin_cmd))
    app.add_handler(CommandHandler("ship", ship_cmd))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_members))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_error_handler(on_error)

    logger.info("Pro Funny Bot online at %s", datetime.now().isoformat(timespec="seconds"))
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
