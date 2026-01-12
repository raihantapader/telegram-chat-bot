import os
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from utils import generate_test_id
from db import create_test, ensure_indexes

load_dotenv()

STARTER_BOT_TOKEN = os.environ["STARTER_BOT_TOKEN"]

CUST_USERNAMES = [
    os.environ["CUST_1_USERNAME"],
    os.environ["CUST_2_USERNAME"],
    os.environ["CUST_3_USERNAME"],
    os.environ["CUST_4_USERNAME"],
    os.environ["CUST_5_USERNAME"],
]

async def newtest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    test_id = generate_test_id()

    await create_test(test_id, created_by_user_id=user_id)

    lines = []
    lines.append("✅ Reply Speed Test Created!")
    lines.append(f"🧪 Test ID: {test_id}")
    lines.append("")
    lines.append("Use this ID with the other bots so they all log the same session.")
    lines.append("")
    lines.append("Next steps:")
    lines.append("1️⃣ Open each bot:")

    for uname in CUST_USERNAMES:
        lines.append(f"• @{uname}")

    lines.append("")
    lines.append("2️⃣ In each bot, send this link (click):")
    for uname in CUST_USERNAMES:
        lines.append(f"https://t.me/{uname}?start={test_id}")

    lines.append("")
    lines.append("3️⃣ Then reply in each bot as the salesperson. Each bot will respond as a customer.")

    await update.message.reply_text("\n".join(lines))

def run_starter():
    app = ApplicationBuilder().token(STARTER_BOT_TOKEN).build()
    app.add_handler(CommandHandler("newtest", newtest))
    app.post_init = lambda _: ensure_indexes()
    app.run_polling(drop_pending_updates=True, poll_interval=1)
    

if __name__ == "__main__":
    run_starter()
