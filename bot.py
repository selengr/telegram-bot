"""
Funny Friends Bot — bilingual pro fun bot (Persian + English).
"""

from __future__ import annotations

import logging
import os
import random
import re
from datetime import date, datetime

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

load_dotenv()

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
            "📊 حساب: آمار من، اشتراک‌گذاری\n"
            "⚙️ زبان: /fa /en\n\n"
            "توی هر چتی بنویس `@{bot}` تا اینلاین جوک بفرستی!"
        ),
        "menu_title": "🎛️ *منوی اصلی*\nیکی رو انتخاب کن:",
        "lang_set": "✅ زبان: فارسی",
        "typing_joke": "دارم جوک می‌سازم…",
        "daily_used": "فال امروزت قبلاً گرفته شده 🔮\nفردا دوباره بیا!\n\n{fortune}",
        "daily_new": "🔮 *فال امروز*\n{fortune}",
        "stats": (
            "📊 *پروفایل خنده*\n"
            "نام: {name}\n"
            "جوک‌ها: {jokes}\n"
            "بازی‌ها: {games}\n"
            "امتیاز کوییز: {quiz}\n"
            "فال روزانه: {daily}"
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
            ("story", "داستان آشوبی"),
            ("stats", "آمار من"),
            ("share", "اشتراک‌گذاری"),
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
            "📊 Account: stats, share\n"
            "⚙️ Language: /fa /en\n\n"
            "Type `@{bot}` in any chat for inline jokes!"
        ),
        "menu_title": "🎛️ *Main menu*\nPick one:",
        "lang_set": "✅ Language: English",
        "typing_joke": "Cooking a joke…",
        "daily_used": "You already opened today's luck 🔮\nCome back tomorrow!\n\n{fortune}",
        "daily_new": "🔮 *Daily luck*\n{fortune}",
        "stats": (
            "📊 *Fun profile*\n"
            "Name: {name}\n"
            "Jokes: {jokes}\n"
            "Games: {games}\n"
            "Quiz score: {quiz}\n"
            "Daily luck: {daily}"
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
            ("story", "Chaos story"),
            ("stats", "My stats"),
            ("share", "Share bot"),
            ("fa", "فارسی"),
            ("en", "English"),
            ("help", "Help"),
        ],
    },
}


def lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    value = context.user_data.get("lang")
    return value if value in ("fa", "en") else "fa"


def set_lang(context: ContextTypes.DEFAULT_TYPE, value: str) -> None:
    context.user_data["lang"] = value


def t(context: ContextTypes.DEFAULT_TYPE) -> dict:
    return UI[lang(context)]


def name_of(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    user = update.effective_user
    if not user:
        return t(context)["friend"]
    return user.first_name or user.username or t(context)["friend"]


def bump(context: ContextTypes.DEFAULT_TYPE, key: str, amount: int = 1) -> int:
    stats = context.user_data.setdefault("stats", {"jokes": 0, "games": 0, "quiz": 0, "daily": 0})
    stats[key] = int(stats.get(key, 0)) + amount
    return stats[key]


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
            [InlineKeyboardButton(b["tod"], callback_data="menu:games"), InlineKeyboardButton(b["quiz"], callback_data="act:quiz")],
            [InlineKeyboardButton(b["stats"], callback_data="act:stats"), InlineKeyboardButton(b["share"], callback_data="act:share")],
            [InlineKeyboardButton(b["fa"], callback_data="lang:fa"), InlineKeyboardButton(b["en"], callback_data="lang:en")],
        ]
    )


def games_inline(context: ContextTypes.DEFAULT_TYPE) -> InlineKeyboardMarkup:
    b = t(context)["btn"]
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(b["tod"], callback_data="act:tod"), InlineKeyboardButton(b["wyr"], callback_data="act:wyr")],
            [InlineKeyboardButton(b["quiz"], callback_data="act:quiz"), InlineKeyboardButton(b["story"], callback_data="act:story")],
            [InlineKeyboardButton(b["coin"], callback_data="act:coin")],
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
    fa_cmds = [BotCommand(c, d) for c, d in UI["fa"]["cmds"]]
    en_cmds = [BotCommand(c, d) for c, d in UI["en"]["cmds"]]
    await app.bot.set_my_commands(fa_cmds, scope=BotCommandScopeDefault(), language_code="fa")
    await app.bot.set_my_commands(en_cmds, scope=BotCommandScopeDefault(), language_code="en")
    await app.bot.set_my_commands(fa_cmds, scope=BotCommandScopeDefault())
    me = await app.bot.get_me()
    app.bot_data["username"] = me.username or ""
    logger.info("Commands menu set. Bot @%s", me.username)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if "lang" not in context.user_data:
        set_lang(context, "fa")
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
    bot = context.application.bot_data.get("username", "bot")
    await update.message.reply_text(
        t(context)["help"].format(bot=bot),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_inline(context),
    )


async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        t(context)["menu_title"],
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_inline(context),
    )


async def set_fa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    set_lang(context, "fa")
    await update.message.reply_text(UI["fa"]["lang_set"], reply_markup=reply_kb(context))
    await menu_cmd(update, context)


async def set_en(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    set_lang(context, "en")
    await update.message.reply_text(UI["en"]["lang_set"], reply_markup=reply_kb(context))
    await menu_cmd(update, context)


def joke_text(context: ContextTypes.DEFAULT_TYPE) -> str:
    bump(context, "jokes")
    return f"😂 {random.choice(JOKES[lang(context)])}"


def roast_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    return f"🔥 {random.choice(ROASTS[lang(context)]).format(name=name_of(update, context))}"


def comp_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    return f"💖 {random.choice(COMPLIMENTS[lang(context)]).format(name=name_of(update, context))}"


def story_text(context: ContextTypes.DEFAULT_TYPE) -> str:
    bump(context, "games")
    bits = STORY_BITS[lang(context)]
    return t(context)["story"].format(
        hero=random.choice(bits["heroes"]),
        place=random.choice(bits["places"]),
        twist=random.choice(bits["twists"]),
        ending=random.choice(bits["endings"]),
    )


def daily_text(context: ContextTypes.DEFAULT_TYPE) -> str:
    today = date.today().isoformat()
    cached = context.user_data.get("daily_date")
    fortune = context.user_data.get("daily_fortune")
    if cached == today and fortune:
        return t(context)["daily_used"].format(fortune=fortune)
    fortune = random.choice(FORTUNES[lang(context)])
    context.user_data["daily_date"] = today
    context.user_data["daily_fortune"] = fortune
    bump(context, "daily")
    return t(context)["daily_new"].format(fortune=fortune)


def stats_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    s = context.user_data.setdefault("stats", {"jokes": 0, "games": 0, "quiz": 0, "daily": 0})
    return t(context)["stats"].format(
        name=name_of(update, context),
        jokes=s.get("jokes", 0),
        games=s.get("games", 0),
        quiz=s.get("quiz", 0),
        daily=s.get("daily", 0),
    )


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
    await update.message.reply_text(joke_text(context), reply_markup=again_kb(context, "joke"))


async def roast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(roast_text(update, context), reply_markup=again_kb(context, "roast"))


async def compliment_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(comp_text(update, context), reply_markup=again_kb(context, "comp"))


async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(daily_text(context), parse_mode=ParseMode.MARKDOWN, reply_markup=again_kb(context, "daily"))


async def story_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(story_text(context), reply_markup=again_kb(context, "story"))


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(stats_text(update, context), parse_mode=ParseMode.MARKDOWN, reply_markup=main_inline(context))


async def share_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_share(update, context)


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
    bump(context, "games")
    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(f"🅰️ {a}", callback_data="wyr:pick")],
            [InlineKeyboardButton(f"🅱️ {b_opt}", callback_data="wyr:pick")],
            [InlineKeyboardButton(t(context)["btn"]["again"], callback_data="act:wyr")],
            [InlineKeyboardButton(t(context)["btn"]["back"], callback_data="menu:games")],
        ]
    )
    await update.message.reply_text(t(context)["wyr_title"], reply_markup=kb)


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


async def send_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE, message) -> None:
    item = random.choice(QUIZ[lang(context)])
    context.user_data["quiz"] = item
    bump(context, "games")
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


async def safe_edit(query, text: str, reply_markup=None, parse_mode=None) -> None:
    try:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except BadRequest:
        await query.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    ui = t(context)

    if data.startswith("lang:"):
        set_lang(context, data.split(":", 1)[1])
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
        bump(context, "games")
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
            score = bump(context, "quiz", 10)
            msg = ui["quiz_ok"].format(score=score)
        else:
            score = context.user_data.get("stats", {}).get("quiz", 0)
            msg = ui["quiz_bad"].format(ans=item["options"][item["answer"]], score=score)
        await query.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=again_kb(context, "quiz"))
        return

    if data.startswith("act:"):
        action = data.split(":", 1)[1]
        await context.bot.send_chat_action(chat_id=query.message.chat_id, action=ChatAction.TYPING)

        if action == "joke":
            await query.message.reply_text(joke_text(context), reply_markup=again_kb(context, "joke"))
        elif action == "roast":
            await query.message.reply_text(roast_text(update, context), reply_markup=again_kb(context, "roast"))
        elif action == "comp":
            await query.message.reply_text(comp_text(update, context), reply_markup=again_kb(context, "comp"))
        elif action == "daily":
            await query.message.reply_text(daily_text(context), parse_mode=ParseMode.MARKDOWN, reply_markup=again_kb(context, "daily"))
        elif action == "story":
            await query.message.reply_text(story_text(context), reply_markup=again_kb(context, "story"))
        elif action == "stats":
            await query.message.reply_text(stats_text(update, context), parse_mode=ParseMode.MARKDOWN, reply_markup=main_inline(context))
        elif action == "share":
            await send_share(update, context, message=query.message)
        elif action == "coin":
            side = random.choice(ui["coin_sides"])
            await query.message.reply_text(ui["coin"].format(side=side), parse_mode=ParseMode.MARKDOWN, reply_markup=again_kb(context, "coin"))
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
            bump(context, "games")
            kb = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(f"🅰️ {a}", callback_data="wyr:pick")],
                    [InlineKeyboardButton(f"🅱️ {b_opt}", callback_data="wyr:pick")],
                    [InlineKeyboardButton(ui["btn"]["again"], callback_data="act:wyr")],
                    [InlineKeyboardButton(ui["btn"]["back"], callback_data="menu:games")],
                ]
            )
            await query.message.reply_text(ui["wyr_title"], reply_markup=kb)
        elif action == "quiz":
            await send_quiz(update, context, query.message)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text_raw = update.message.text or ""
    text = text_raw.strip()
    if "lang" not in context.user_data and PERSIAN_RE.search(text_raw):
        set_lang(context, "fa")

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
    app.add_handler(CommandHandler("story", story_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("share", share_cmd))
    app.add_handler(CommandHandler("flip", coin_cmd))
    app.add_handler(CommandHandler("coin", coin_cmd))
    app.add_handler(CommandHandler("ship", ship_cmd))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_error_handler(on_error)

    logger.info("Pro Funny Bot online at %s", datetime.now().isoformat(timespec="seconds"))
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
