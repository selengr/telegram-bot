"""
Funny Friends Bot — a silly Telegram bot to share with friends.
"""

from __future__ import annotations

import logging
import os
import random
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

JOKES = [
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
    "Why can't you give Elsa a balloon? Because she will let it go.",
    "I would tell you a UDP joke, but you might not get it.",
    "There are 10 types of people: those who understand binary and those who don't.",
    "My Wi-Fi went down for 5 minutes… so I had to talk to my family. They seem nice.",
    "Why did the developer go broke? Because he used up all his cache.",
]

ROASTS = [
    "{name}, your Wi-Fi password is stronger than your life decisions.",
    "{name}, if laziness was an Olympic sport, you'd still show up late.",
    "{name}, your phone battery has more energy than you before noon.",
    "{name}, even Autocorrect gives up halfway through your messages.",
    "{name}, you bring so much joy… whenever you leave the group chat.",
    "{name}, your jokes are so dry the desert asked for tips.",
    "{name}, if confidence was based on facts, you'd be whispering.",
    "{name}, you're not late — you're just on 'main character delay' mode.",
    "{name}, ChatGPT works harder than you do on group projects.",
    "{name}, your bed misspelled your name as 'permanent resident'.",
]

COMPLIMENTS = [
    "{name}, you're the human version of finding money in old jeans.",
    "{name}, your vibe could charge phones wirelessly.",
    "{name}, if kindness had a leaderboard, you'd be suspiciously high.",
    "{name}, you make group chats 47% funnier just by existing.",
    "{name}, you're proof that main character energy is contagious.",
    "{name}, even your typos have personality.",
    "{name}, you'd survive a zombie apocalypse with snacks and good playlists.",
    "{name}, you're the reason 'reply all' isn't always a disaster.",
    "{name}, sunshine called — it wants its energy back, but you're keeping it.",
    "{name}, you're rare… like a charging cable that still works.",
]

FORTUNES = [
    "Today you will find free Wi-Fi… and lose your charger.",
    "A mysterious snack will appear. Claim it before your roommate does.",
    "Someone will text you 'lol' and mean it this time.",
    "Your next idea is either genius or chaos. Do it anyway.",
    "Beware of Monday. It knows what you did this weekend.",
    "Lucky number: 7. Unlucky number: your unread messages.",
    "You will win an argument… silently, in the shower.",
    "A plot twist is coming. Bring snacks.",
    "Your future holds great things — and also laundry.",
    "The stars say: hydrate, stretch, and don't trust group projects.",
]

PICKUP_LINES = [
    "Are you Wi-Fi? Because I'm feeling a connection.",
    "Do you have a map? I keep getting lost in this group chat.",
    "Are you a password? Because you're hard to forget.",
    "If you were a vegetable, you'd be a cute-cumber.",
    "Are you made of copper and tellurium? Because you look CuTe.",
    "Is your name Google? Because you have everything I've been searching for.",
    "Are you a campfire? Because you're hot and I want s'more.",
    "Do you believe in love at first sight — or should I send another sticker?",
]

MAGIC_8 = [
    "Absolutely yes ✨",
    "Nope. Not today.",
    "Ask again after snacks.",
    "The universe says maybe…",
    "100%. Trust the chaos.",
    "I'd rather not say 👀",
    "Signs point to hilarious outcomes.",
    "Denied by the vibe council.",
    "Yes, but make it dramatic.",
    "Unclear. Flip a coin instead.",
]

DARES = [
    "Send a voice message singing the last song you heard.",
    "Change your Telegram name to something ridiculous for 10 minutes.",
    "Text the group your most embarrassing autocorrect fail.",
    "Do 10 jumping jacks and report back with proof (or lies).",
    "Compliment the next 3 people who message you.",
    "Speak only in movie quotes for the next 5 minutes.",
    "Send a selfie with your funniest face.",
    "Admit your most cursed food combo.",
    "Type with your eyes closed for one whole message.",
    "Start a rumor that you're secretly a raccoon in a hoodie.",
]

FACTS = [
    "Octopuses have three hearts. Still somehow less dramatic than your group chat.",
    "Bananas are berries. Strawberries aren't. Science is trolling us.",
    "A group of flamingos is called a flamboyance. Peak branding.",
    "Honey never spoils. Your leftover pizza does. Choose wisely.",
    "Wombat poop is cube-shaped. Nature has jokes too.",
    "Your stomach gets a new lining every few days. Relatable regeneration arc.",
    "Cows have best friends and get stressed when separated. Soft.",
    "The inventor of the Pringles can is buried in one. Commitment.",
]


def display_name(update: Update) -> str:
    user = update.effective_user
    if not user:
        return "friend"
    return user.first_name or user.username or "friend"


def fun_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("😂 Joke", callback_data="joke"),
                InlineKeyboardButton("🔥 Roast", callback_data="roast"),
            ],
            [
                InlineKeyboardButton("💖 Compliment", callback_data="compliment"),
                InlineKeyboardButton("🔮 Fortune", callback_data="fortune"),
            ],
            [
                InlineKeyboardButton("🪙 Flip coin", callback_data="coin"),
                InlineKeyboardButton("🎲 Dare", callback_data="dare"),
            ],
        ]
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    name = display_name(update)
    text = (
        f"Hey {name}! 👋\n\n"
        "I'm your chaos gremlin bot — built for laughs with friends.\n\n"
        "Try a button below, or type:\n"
        "/joke /roast /compliment /fortune\n"
        "/flip /dare /8ball /fact /pickup /rate\n"
        "/help for the full menu"
    )
    await update.message.reply_text(text, reply_markup=fun_keyboard())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "🎪 *Funny Friends Bot menu*\n\n"
        "/start — wake me up\n"
        "/joke — random joke\n"
        "/roast — gentle roast (friendly fire)\n"
        "/compliment — ego boost\n"
        "/fortune — questionable prophecy\n"
        "/flip — coin flip\n"
        "/dare — silly dare\n"
        "/8ball <question> — magic answers\n"
        "/fact — weird fun fact\n"
        "/pickup — cursed pickup line\n"
        "/rate — rate something 0–100\n"
        "/ship @a @b — ship two people\n"
        "/menu — show quick buttons\n\n"
        "Or just send me any message and I'll bounce chaos back."
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=fun_keyboard())


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Pick your chaos:", reply_markup=fun_keyboard())


async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"😂 {random.choice(JOKES)}")


async def roast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    name = display_name(update)
    await update.message.reply_text(f"🔥 {random.choice(ROASTS).format(name=name)}")


async def compliment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    name = display_name(update)
    await update.message.reply_text(f"💖 {random.choice(COMPLIMENTS).format(name=name)}")


async def fortune(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"🔮 {random.choice(FORTUNES)}")


async def flip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    side = random.choice(["Heads", "Tails"])
    await update.message.reply_text(f"🪙 The coin says… *{side}!*", parse_mode="Markdown")


async def dare(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"🎲 Dare accepted:\n{random.choice(DARES)}")


async def eight_ball(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    question = " ".join(context.args).strip() if context.args else ""
    if not question:
        await update.message.reply_text("Ask me something!\nExample: `/8ball will we order pizza?`", parse_mode="Markdown")
        return
    await update.message.reply_text(
        f"🎱 *Question:* {question}\n*Answer:* {random.choice(MAGIC_8)}",
        parse_mode="Markdown",
    )


async def fact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"🧠 {random.choice(FACTS)}")


async def pickup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"💘 {random.choice(PICKUP_LINES)}")


async def rate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    target = " ".join(context.args).strip() if context.args else display_name(update)
    score = random.randint(0, 100)
    if score >= 90:
        vibe = "legendary"
    elif score >= 70:
        vibe = "elite"
    elif score >= 40:
        vibe = "mid-but-charming"
    else:
        vibe = "chaotically valid"
    await update.message.reply_text(f"📊 I rate *{target}* a solid *{score}/100* — {vibe}.", parse_mode="Markdown")


async def ship(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Usage: `/ship Alice Bob` or `/ship @a @b`", parse_mode="Markdown")
        return
    a, b = context.args[0], context.args[1]
    score = random.randint(1, 100)
    heart = "💕" if score >= 70 else "🙂" if score >= 40 else "💀"
    await update.message.reply_text(
        f"{heart} Ship-o-meter\n*{a}* ✖️ *{b}*\nCompatibility: *{score}%*",
        parse_mode="Markdown",
    )


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Playful replies when friends just chat with the bot."""
    text = (update.message.text or "").lower()
    name = display_name(update)

    if any(word in text for word in ("bored", "boring")):
        await update.message.reply_text("Boredom detected. Deploying nonsense…", reply_markup=fun_keyboard())
        return
    if any(word in text for word in ("hello", "hi", "hey", "salam", "سلام")):
        await update.message.reply_text(f"Hey {name}! Ready to cause mild chaos?", reply_markup=fun_keyboard())
        return
    if "love" in text:
        await update.message.reply_text("Love is stored in the hugs folder. Also snacks.")
        return
    if "?" in text:
        await update.message.reply_text(f"🎱 {random.choice(MAGIC_8)}")
        return

    reactions = [
        f"{name}, that message has main-character energy.",
        "Noted in the chaos archives.",
        "Bold of you to say that in 2026.",
        "I laughed. Internally. Very loudly.",
        "Plot twist: that was actually profound.",
        "Sending virtual confetti. 🎉",
        f"Ok {name}, but have you tried /dare?",
    ]
    await update.message.reply_text(random.choice(reactions))


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    name = query.from_user.first_name if query.from_user else "friend"
    data = query.data

    responses = {
        "joke": f"😂 {random.choice(JOKES)}",
        "roast": f"🔥 {random.choice(ROASTS).format(name=name)}",
        "compliment": f"💖 {random.choice(COMPLIMENTS).format(name=name)}",
        "fortune": f"🔮 {random.choice(FORTUNES)}",
        "coin": f"🪙 The coin says… {random.choice(['Heads', 'Tails'])}!",
        "dare": f"🎲 Dare accepted:\n{random.choice(DARES)}",
    }
    await query.message.reply_text(responses.get(data, "Unknown button magic."), reply_markup=fun_keyboard())


def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise SystemExit("Missing BOT_TOKEN. Put it in a .env file.")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("menu", menu))
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
