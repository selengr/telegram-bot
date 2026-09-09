"""
Funny Friends Bot — bilingual (Persian + English) fun bot for friends.
"""

from __future__ import annotations

import logging
import os
import random
import re
from datetime import datetime

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
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

# --- English content ---

JOKES_EN = [
    "Why don't scientists trust atoms? Because they make up everything.",
    "I told my computer I needed a break… and it said 'No problem, I'll go to sleep.'",
    "Why did the scarecrow win an award? He was outstanding in his field.",
    "I'm on a seafood diet. I see food and I eat it.",
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "I asked my dog what's two minus two. He said nothing.",
    "Parallel lines have so much in common… it's a shame they'll never meet.",
    "Why did the coffee file a police report? It got mugged.",
    "I used to hate facial hair… then it grew on me.",
    "What's a computer's favorite snack? Microchips.",
    "My Wi-Fi went down for 5 minutes… so I had to talk to my family. They seem nice.",
    "Why did the developer go broke? Because he used up all his cache.",
]

ROASTS_EN = [
    "{name}, your Wi-Fi password is stronger than your life decisions.",
    "{name}, if laziness was an Olympic sport, you'd still show up late.",
    "{name}, your phone battery has more energy than you before noon.",
    "{name}, even Autocorrect gives up halfway through your messages.",
    "{name}, you bring so much joy… whenever you leave the group chat.",
    "{name}, your jokes are so dry the desert asked for tips.",
    "{name}, you're not late — you're just on 'main character delay' mode.",
    "{name}, ChatGPT works harder than you do on group projects.",
    "{name}, your bed misspelled your name as 'permanent resident'.",
]

COMPLIMENTS_EN = [
    "{name}, you're the human version of finding money in old jeans.",
    "{name}, your vibe could charge phones wirelessly.",
    "{name}, if kindness had a leaderboard, you'd be suspiciously high.",
    "{name}, you make group chats 47% funnier just by existing.",
    "{name}, even your typos have personality.",
    "{name}, you're rare… like a charging cable that still works.",
]

FORTUNES_EN = [
    "Today you will find free Wi-Fi… and lose your charger.",
    "A mysterious snack will appear. Claim it before your roommate does.",
    "Someone will text you 'lol' and mean it this time.",
    "Your next idea is either genius or chaos. Do it anyway.",
    "Lucky number: 7. Unlucky number: your unread messages.",
    "A plot twist is coming. Bring snacks.",
    "The stars say: hydrate, stretch, and don't trust group projects.",
]

PICKUP_EN = [
    "Are you Wi-Fi? Because I'm feeling a connection.",
    "Do you have a map? I keep getting lost in this group chat.",
    "Are you a password? Because you're hard to forget.",
    "If you were a vegetable, you'd be a cute-cumber.",
    "Do you believe in love at first sight — or should I send another sticker?",
]

MAGIC8_EN = [
    "Absolutely yes ✨",
    "Nope. Not today.",
    "Ask again after snacks.",
    "The universe says maybe…",
    "100%. Trust the chaos.",
    "I'd rather not say 👀",
    "Signs point to hilarious outcomes.",
    "Yes, but make it dramatic.",
    "Unclear. Flip a coin instead.",
]

DARES_EN = [
    "Send a voice message singing the last song you heard.",
    "Change your Telegram name to something ridiculous for 10 minutes.",
    "Text the group your most embarrassing autocorrect fail.",
    "Compliment the next 3 people who message you.",
    "Send a selfie with your funniest face.",
    "Admit your most cursed food combo.",
    "Type with your eyes closed for one whole message.",
]

FACTS_EN = [
    "Octopuses have three hearts. Still somehow less dramatic than your group chat.",
    "Bananas are berries. Strawberries aren't. Science is trolling us.",
    "A group of flamingos is called a flamboyance. Peak branding.",
    "Honey never spoils. Your leftover pizza does. Choose wisely.",
    "Cows have best friends and get stressed when separated. Soft.",
]

# --- Persian content ---

JOKES_FA = [
    "می‌دونی چرا برنامه‌نویس‌ها عینک می‌زنن؟ چون نمی‌تونن C رو ببینن 😄",
    "رفتم دکتر گفتم حافظه‌م ضعیف شده. گفت: از کی؟ گفتم: از کی چی؟",
    "چرا گربه‌ها لپ‌تاپ دوست دارن؟ چون موس داره!",
    "به رفیقم گفتم رمز وای‌فایت چیه؟ گفت: قوی باش. حالا نیم ساعته دارم سعی می‌کنم قوی باشم 😂",
    "می‌دونی فرق آدم موفق با بقیه چیه؟ اونا زودتر از بقیه ناامید می‌شن… نه صبر کن اشتباه گفتم 😅",
    "استادم گفت تکالیفت کجاست؟ گفتم تو کلود هست. گفت کدوم کلود؟ گفتم همون ابری که رد شد رفت!",
    "چرا ساعت‌ها همیشه مضطربن؟ چون عقربه‌هاشون همیشه می‌دوه!",
    "رفتم مغازه گفتم نیم‌کیلو خوشحالی می‌خوام. گفت تموم شد، فقط قسط و قبض مونده 🥲",
    "چی میشه اگه وای‌فای قطع بشه؟ مجبوری با خانواده حرف بزنی… ترسناکه!",
    "به باتری گوشیم گفتم چرا اینقدر زود تموم می‌شی؟ گفت تو خودت از من کم‌طاقت‌تری!",
    "می‌دونی چرا نون سنگک نمی‌تونه دروغ بگه؟ چون روشنه و معلومه 🥖",
    "دوستام می‌گن زیاد جوک می‌گم. منم می‌گم خب زندگی کمدیِ من فقط ساب‌تایتل نداره.",
]

ROASTS_FA = [
    "{name}، رمز وای‌فایت از تصمیمات زندگیت قوی‌تره 🔥",
    "{name}، اگه تنبلی المپیک داشت تو حتی به افتتاحیه هم دیر می‌رسیدی.",
    "{name}، باتری گوشیت صبح‌ها از خودت پرانرژی‌تره.",
    "{name}، حتی کیبورد هم وقتی برات تایپ می‌کنه اشتباه می‌کنه از خستگی.",
    "{name}، جوکات انقدر خشکه که کویر ازت مشاوره می‌گیره.",
    "{name}، تو دیر نمی‌کنی؛ تو فقط روی حالت «شخصیت اصلی با تأخیر» هستی.",
    "{name}، تختت اسمتو تو لیست ساکنین دائمی نوشته.",
    "{name}، اگه خواب المپیک داشت، طلا مال تو بود (با چشم بسته).",
    "{name}، چت‌جی‌پی‌تی تو پروژه‌های گروهی از تو بیشتر کار می‌کنه.",
]

COMPLIMENTS_FA = [
    "{name}، تو نسخه انسانی پیدا کردن پول تو جیب شلوار قدیمی هستی 💖",
    "{name}، انرژیت می‌تونه گوشی رو وایرلس شارژ کنه.",
    "{name}، اگه مهربونی جدول رده‌بندی داشت، اسمت مشکوکانه بالاست.",
    "{name}، فقط با بودنت گپ گروهی ۴۷٪ باحال‌تر می‌شه.",
    "{name}، حتی غلط املایی‌هات هم شخصیت دارن.",
    "{name}، تو مثل کابل شارژری هستی که هنوز کار می‌کنه — کمیاب!",
    "{name}، خورشید زنگ زد انرژی‌شو پس می‌خواد، ولی تو نگهش دار.",
    "{name}، با تو بودن مثل پیدا کردن جای پارک خالیه — حس برد!",
]

FORTUNES_FA = [
    "امروز وای‌فای رایگان پیدا می‌کنی… شارژر رو گم می‌کنی 🔮",
    "یه خوراکی اسرارآمیز ظاهر می‌شه. قبل از روم‌میت بردارش!",
    "کسی برات «lol» می‌فرسته و این بار واقعاً می‌خنده.",
    "ایده بعدی‌ت یا نبوغه یا آشوب. در هر صورت انجامش بده.",
    "عدد شانس: ۷. عدد بدشانسی: پیام‌های خونده‌نشده‌ت.",
    "یه پیچش داستانی در راهه. خوراکی بردار.",
    "ستاره‌ها می‌گن: آب بخور، کش بیار، به پروژه‌های گروهی اعتماد نکن.",
    "امروز کسی ازت تعریف می‌کنه. سعی کن باور کنی.",
    "یه پیام مهم می‌اد… احتمالاً از بانک. ولی خب هیجان‌انگیزه!",
]

PICKUP_FA = [
    "وای‌فایی؟ چون حس می‌کنم بهت وصلم 💘",
    "نقشه داری؟ تو این گپ گروهی گم شدم.",
    "رمزی؟ چون فراموش‌نشدنی‌ای.",
    "اگه سبزی بودی، خیار‌بامزه‌ای بودی 🥒",
    "به عشق در نگاه اول اعتقاد داری… یا یه استیکر دیگه بفرستم؟",
    "اسمت گوگله؟ چون هرچی دنبالشم پیش تو پیدا می‌شه.",
    "قهوه‌ای؟ چون بدون تو روزم تلخه ☕",
]

MAGIC8_FA = [
    "قطعاً آره ✨",
    "نه. امروز نه.",
    "بعد از یه میان‌وعده دوباره بپرس.",
    "جهان می‌گه شاید…",
    "صددرصد. به آشوب اعتماد کن.",
    "ترجیح می‌دم نگم 👀",
    "نشانه‌ها می‌گن نتیجه خنده‌داره.",
    "آره، ولی نمایشی‌ش کن.",
    "معلوم نیست. سکه بنداز.",
    "شورای حس‌وحال رد کرد.",
]

DARES_FA = [
    "آخرین آهنگی که شنیدی رو ویس کن و بخون 🎤",
    "۱۰ دقیقه اسم تلگرامت رو یه چیز مسخره بذار.",
    "خجالت‌آورترین اتوکرکت رو تو گروه بفرست.",
    "به ۳ نفر بعدی که پیام می‌دن تعریف کن.",
    "با خنده‌دارترین قیافه‌ت سلفی بفرست.",
    "عجیب‌ترین ترکیب غذایی که دوست داری رو اعتراف کن.",
    "یه پیام کامل با چشم بسته تایپ کن.",
    "۵ دقیقه فقط با دیالوگ فیلم حرف بزن.",
    "تو گروه شایعه کن که مخفیانه یه راکون با هودی هستی 🦝",
]

FACTS_FA = [
    "اختاپوس سه تا قلب داره. باز هم از گپ گروهی شما درام کمتری داره 🧠",
    "موز جزء توت‌هاست، توت‌فرنگی نه. علم داره مسخره‌مون می‌کنه.",
    "به گروه فلامینگو می‌گن flamboyance. برندینگ درجه یک.",
    "عسل هیچ‌وقت خراب نمی‌شه. پیتزای مونده‌ت چرا. عاقلانه انتخاب کن.",
    "گاوها رفیق صمیمی دارن و جدا شدنشون استرس‌زاست. نرم!",
    "پوسته معده هر چند روز عوض می‌شه. ریدمپشن آرک واقعی.",
    "وومبت مدفوع مکعبی داره. طبیعت هم جوک بلده.",
]

CONTENT = {
    "en": {
        "jokes": JOKES_EN,
        "roasts": ROASTS_EN,
        "compliments": COMPLIMENTS_EN,
        "fortunes": FORTUNES_EN,
        "pickup": PICKUP_EN,
        "magic8": MAGIC8_EN,
        "dares": DARES_EN,
        "facts": FACTS_EN,
        "coin": ("Heads", "Tails"),
        "friend": "friend",
    },
    "fa": {
        "jokes": JOKES_FA,
        "roasts": ROASTS_FA,
        "compliments": COMPLIMENTS_FA,
        "fortunes": FORTUNES_FA,
        "pickup": PICKUP_FA,
        "magic8": MAGIC8_FA,
        "dares": DARES_FA,
        "facts": FACTS_FA,
        "coin": ("شیر", "خط"),
        "friend": "رفیق",
    },
}

UI = {
    "en": {
        "start": (
            "Hey {name}! 👋\n\n"
            "I'm your chaos gremlin bot — built for laughs with friends.\n"
            "Now with Persian too! Use /fa or /en to switch language.\n\n"
            "Try the buttons, or:\n"
            "/joke /roast /compliment /fortune\n"
            "/flip /dare /8ball /fact /pickup /rate /ship\n"
            "/help for the full menu"
        ),
        "help": (
            "🎪 *Funny Friends Bot*\n\n"
            "/start — wake me up\n"
            "/fa — فارسی\n"
            "/en — English\n"
            "/joke — random joke\n"
            "/roast — friendly roast\n"
            "/compliment — ego boost\n"
            "/fortune — silly prophecy\n"
            "/flip — coin flip\n"
            "/dare — silly dare\n"
            "/8ball <q> — magic answers\n"
            "/fact — weird fact\n"
            "/pickup — cursed pickup line\n"
            "/rate — rate 0–100\n"
            "/ship A B — ship two people\n"
            "/menu — quick buttons"
        ),
        "menu": "Pick your chaos:",
        "lang_set": "Language set to English ✅",
        "ask_8ball": "Ask me something!\nExample: `/8ball will we order pizza?`",
        "q_label": "Question",
        "a_label": "Answer",
        "dare_label": "Dare accepted:",
        "coin_says": "The coin says… *{side}!*",
        "rate": "📊 I rate *{target}* a solid *{score}/100* — {vibe}.",
        "vibes": ("chaotically valid", "mid-but-charming", "elite", "legendary"),
        "ship_usage": "Usage: `/ship Alice Bob`",
        "ship": "{heart} Ship-o-meter\n*{a}* ✖️ *{b}*\nCompatibility: *{score}%*",
        "bored": "Boredom detected. Deploying nonsense…",
        "hello": "Hey {name}! Ready to cause mild chaos?",
        "love": "Love is stored in the hugs folder. Also snacks.",
        "unknown_btn": "Unknown button magic.",
        "btn_joke": "😂 Joke",
        "btn_roast": "🔥 Roast",
        "btn_comp": "💖 Compliment",
        "btn_fortune": "🔮 Fortune",
        "btn_coin": "🪙 Flip",
        "btn_dare": "🎲 Dare",
        "btn_fa": "🇮🇷 فارسی",
        "btn_en": "🇬🇧 English",
        "reactions": [
            "{name}, that message has main-character energy.",
            "Noted in the chaos archives.",
            "Bold of you to say that in 2026.",
            "I laughed. Internally. Very loudly.",
            "Sending virtual confetti. 🎉",
            "Ok {name}, but have you tried /dare?",
        ],
    },
    "fa": {
        "start": (
            "سلام {name}! 👋\n\n"
            "من ربات شوخ‌طبع دوستات هستم — برای خنده و دورهمی.\n"
            "با /fa یا /en می‌تونی زبان رو عوض کنی.\n\n"
            "از دکمه‌ها استفاده کن، یا بزن:\n"
            "/joke /roast /compliment /fortune\n"
            "/flip /dare /8ball /fact /pickup /rate /ship\n"
            "/help برای لیست کامل"
        ),
        "help": (
            "🎪 *ربات بامزه دوستان*\n\n"
            "/start — شروع\n"
            "/fa — فارسی\n"
            "/en — English\n"
            "/joke — جوک تصادفی\n"
            "/roast — تیکه دوستانه\n"
            "/compliment — تعریف و تمجید\n"
            "/fortune — فال الکی\n"
            "/flip — شیر یا خط\n"
            "/dare — جرات\n"
            "/8ball سوال — جواب جادویی\n"
            "/fact — فکت عجیب\n"
            "/pickup — لای خط خنده‌دار\n"
            "/rate — امتیاز ۰ تا ۱۰۰\n"
            "/ship آ ب — درصد سازگاری\n"
            "/menu — دکمه‌های سریع"
        ),
        "menu": "آشوشت رو انتخاب کن:",
        "lang_set": "زبان روی فارسی تنظیم شد ✅",
        "ask_8ball": "یه چیزی بپرس!\nمثلاً: `/8ball امشب پیتزا بخوریم؟`",
        "q_label": "سوال",
        "a_label": "جواب",
        "dare_label": "جراتت اینه:",
        "coin_says": "سکه می‌گه… *{side}!*",
        "rate": "📊 به *{target}* می‌دم *{score}/100* — {vibe}.",
        "vibes": ("آشوبِ دوست‌داشتنی", "متوسط ولی باحال", "خفن", "افسانه‌ای"),
        "ship_usage": "نحوه استفاده: `/ship علی سارا`",
        "ship": "{heart} درصد عشق\n*{a}* ✖️ *{b}*\nسازگاری: *{score}%*",
        "bored": "حوصله‌سررفتگی تشخیص داده شد. در حال ارسال چرندیات…",
        "hello": "سلام {name}! آماده‌ای یه کم آشوب راه بندازیم؟",
        "love": "عشق تو پوشه بغل ذخیره می‌شه. میان‌وعده هم فراموش نشه.",
        "unknown_btn": "دکمه ناشناس بود 😅",
        "btn_joke": "😂 جوک",
        "btn_roast": "🔥 تیکه",
        "btn_comp": "💖 تعریف",
        "btn_fortune": "🔮 فال",
        "btn_coin": "🪙 سکه",
        "btn_dare": "🎲 جرات",
        "btn_fa": "🇮🇷 فارسی",
        "btn_en": "🇬🇧 English",
        "reactions": [
            "{name}، این پیام انرژی شخصیت اصلی داره.",
            "تو آرشیو آشوب ثبت شد.",
            "جرئت کردی اینو تو ۲۰۲۶ بگی.",
            "خندیدم. داخلی. خیلی بلند.",
            "دارم مجازی کانفتی می‌فرستم 🎉",
            "باشه {name}، ولی /dare رو امتحان کردی؟",
        ],
    },
}


def get_lang(context: ContextTypes.DEFAULT_TYPE) -> str:
    lang = context.user_data.get("lang")
    return lang if lang in ("fa", "en") else "fa"


def set_lang(context: ContextTypes.DEFAULT_TYPE, lang: str) -> None:
    context.user_data["lang"] = lang


def ui(context: ContextTypes.DEFAULT_TYPE) -> dict:
    return UI[get_lang(context)]


def pack(context: ContextTypes.DEFAULT_TYPE) -> dict:
    return CONTENT[get_lang(context)]


def display_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    user = update.effective_user
    if not user:
        return pack(context)["friend"]
    return user.first_name or user.username or pack(context)["friend"]


def fun_keyboard(context: ContextTypes.DEFAULT_TYPE) -> InlineKeyboardMarkup:
    t = ui(context)
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(t["btn_joke"], callback_data="joke"),
                InlineKeyboardButton(t["btn_roast"], callback_data="roast"),
            ],
            [
                InlineKeyboardButton(t["btn_comp"], callback_data="compliment"),
                InlineKeyboardButton(t["btn_fortune"], callback_data="fortune"),
            ],
            [
                InlineKeyboardButton(t["btn_coin"], callback_data="coin"),
                InlineKeyboardButton(t["btn_dare"], callback_data="dare"),
            ],
            [
                InlineKeyboardButton(t["btn_fa"], callback_data="lang_fa"),
                InlineKeyboardButton(t["btn_en"], callback_data="lang_en"),
            ],
        ]
    )


def rate_vibe(score: int, vibes: tuple[str, str, str, str]) -> str:
    if score >= 90:
        return vibes[3]
    if score >= 70:
        return vibes[2]
    if score >= 40:
        return vibes[1]
    return vibes[0]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if "lang" not in context.user_data:
        set_lang(context, "fa")
    name = display_name(update, context)
    t = ui(context)
    await update.message.reply_text(
        t["start"].format(name=name),
        reply_markup=fun_keyboard(context),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    t = ui(context)
    await update.message.reply_text(
        t["help"],
        parse_mode="Markdown",
        reply_markup=fun_keyboard(context),
    )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(ui(context)["menu"], reply_markup=fun_keyboard(context))


async def set_fa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    set_lang(context, "fa")
    await update.message.reply_text(UI["fa"]["lang_set"], reply_markup=fun_keyboard(context))


async def set_en(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    set_lang(context, "en")
    await update.message.reply_text(UI["en"]["lang_set"], reply_markup=fun_keyboard(context))


async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"😂 {random.choice(pack(context)['jokes'])}")


async def roast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    name = display_name(update, context)
    await update.message.reply_text(
        f"🔥 {random.choice(pack(context)['roasts']).format(name=name)}"
    )


async def compliment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    name = display_name(update, context)
    await update.message.reply_text(
        f"💖 {random.choice(pack(context)['compliments']).format(name=name)}"
    )


async def fortune(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"🔮 {random.choice(pack(context)['fortunes'])}")


async def flip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    side = random.choice(pack(context)["coin"])
    text = ui(context)["coin_says"].format(side=side)
    await update.message.reply_text(f"🪙 {text}", parse_mode="Markdown")


async def dare(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    t = ui(context)
    await update.message.reply_text(
        f"🎲 {t['dare_label']}\n{random.choice(pack(context)['dares'])}"
    )


async def eight_ball(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    t = ui(context)
    question = " ".join(context.args).strip() if context.args else ""
    if not question:
        await update.message.reply_text(t["ask_8ball"], parse_mode="Markdown")
        return
    answer = random.choice(pack(context)["magic8"])
    await update.message.reply_text(
        f"🎱 *{t['q_label']}:* {question}\n*{t['a_label']}:* {answer}",
        parse_mode="Markdown",
    )


async def fact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"🧠 {random.choice(pack(context)['facts'])}")


async def pickup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"💘 {random.choice(pack(context)['pickup'])}")


async def rate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    t = ui(context)
    target = " ".join(context.args).strip() if context.args else display_name(update, context)
    score = random.randint(0, 100)
    vibe = rate_vibe(score, t["vibes"])
    await update.message.reply_text(
        t["rate"].format(target=target, score=score, vibe=vibe),
        parse_mode="Markdown",
    )


async def ship(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    t = ui(context)
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(t["ship_usage"], parse_mode="Markdown")
        return
    a, b = context.args[0], context.args[1]
    score = random.randint(1, 100)
    heart = "💕" if score >= 70 else "🙂" if score >= 40 else "💀"
    await update.message.reply_text(
        t["ship"].format(heart=heart, a=a, b=b, score=score),
        parse_mode="Markdown",
    )


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text_raw = update.message.text or ""
    text = text_raw.lower()
    name = display_name(update, context)
    t = ui(context)

    # Auto-switch toward Persian if user writes Persian and has no lang yet
    if "lang" not in context.user_data and PERSIAN_RE.search(text_raw):
        set_lang(context, "fa")
        t = ui(context)

    bored_words = ("bored", "boring", "حوصله", "کسل", "حوصلم")
    hello_words = ("hello", "hi", "hey", "salam", "سلام", "درود", "خوبی", "چطوری")
    love_words = ("love", "عاشق", "دوستت دارم", "عشق")

    if any(w in text or w in text_raw for w in bored_words):
        await update.message.reply_text(t["bored"], reply_markup=fun_keyboard(context))
        return
    if any(w in text or w in text_raw for w in hello_words):
        await update.message.reply_text(
            t["hello"].format(name=name),
            reply_markup=fun_keyboard(context),
        )
        return
    if any(w in text or w in text_raw for w in love_words):
        await update.message.reply_text(t["love"])
        return
    if "?" in text_raw or "؟" in text_raw:
        await update.message.reply_text(f"🎱 {random.choice(pack(context)['magic8'])}")
        return

    await update.message.reply_text(
        random.choice(t["reactions"]).format(name=name)
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data or ""

    if data == "lang_fa":
        set_lang(context, "fa")
        await query.message.reply_text(UI["fa"]["lang_set"], reply_markup=fun_keyboard(context))
        return
    if data == "lang_en":
        set_lang(context, "en")
        await query.message.reply_text(UI["en"]["lang_set"], reply_markup=fun_keyboard(context))
        return

    name = query.from_user.first_name if query.from_user else pack(context)["friend"]
    t = ui(context)
    p = pack(context)

    if data == "joke":
        text = f"😂 {random.choice(p['jokes'])}"
    elif data == "roast":
        text = f"🔥 {random.choice(p['roasts']).format(name=name)}"
    elif data == "compliment":
        text = f"💖 {random.choice(p['compliments']).format(name=name)}"
    elif data == "fortune":
        text = f"🔮 {random.choice(p['fortunes'])}"
    elif data == "coin":
        side = random.choice(p["coin"])
        text = f"🪙 {t['coin_says'].format(side=side)}".replace("*", "")
    elif data == "dare":
        text = f"🎲 {t['dare_label']}\n{random.choice(p['dares'])}"
    else:
        text = t["unknown_btn"]

    await query.message.reply_text(text, reply_markup=fun_keyboard(context))


def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise SystemExit("Missing BOT_TOKEN. Put it in a .env file.")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("fa", set_fa))
    app.add_handler(CommandHandler("en", set_en))
    app.add_handler(CommandHandler("lang", set_fa))  # default shortcut -> فارسی
    app.add_handler(CommandHandler("joke", joke))
    app.add_handler(CommandHandler("roast", roast))
    app.add_handler(CommandHandler("compliment", compliment))
    app.add_handler(CommandHandler("fortune", fortune))
    app.add_handler(CommandHandler("flip", flip))
    app.add_handler(CommandHandler("dare", dare))
    app.add_handler(CommandHandler("8ball", eight_ball))
    app.add_handler(CommandHandler("fact", fact))
    app.add_handler(CommandHandler("pickup", pickup))
    app.add_handler(CommandHandler("rate", rate))
    app.add_handler(CommandHandler("ship", ship))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    logger.info("Funny Friends Bot is online at %s", datetime.now().isoformat(timespec="seconds"))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
