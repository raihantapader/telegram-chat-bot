import os
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

from db import (
    ensure_indexes,
    test_exists,
    upsert_participant,
    get_participant_test_id,
    insert_message,
    get_last_messages,
)
from llm import generate_customer_reply
from customer_personas import personas

load_dotenv()

ALL_PERSONAS = personas()

PLEASE_START = "Please start this bot using the test link from the starter bot (it includes the Test ID)."

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_id: str):
    chat_id = update.effective_chat.id

    if not context.args:
        await update.message.reply_text(PLEASE_START)
        return

    test_id = context.args[0].strip().upper()
    if not await test_exists(test_id):
        await update.message.reply_text("Invalid Test ID. Please create a new test using the starter bot.")
        return

    await upsert_participant(chat_id=chat_id, bot_id=bot_id, test_id=test_id)

    persona = ALL_PERSONAS[bot_id]

    # Salesperson greeting stored as first message for context consistency
    salesperson_greeting = "Hello sir I'm sales person Raihan, How can i help you today?"
    await insert_message(test_id, bot_id, "salesperson", salesperson_greeting, chat_id)

    # Customer first message generated (NOT scripted)
    history = await get_last_messages(test_id, bot_id, limit=10)
    customer_msg = await generate_customer_reply(
        system_prompt=persona.system_prompt,
        few_shot=persona.few_shot,
        history_docs=history,
        salesperson_message=salesperson_greeting,
    )

    await insert_message(test_id, bot_id, "customer", customer_msg, chat_id)

    await update.message.reply_text(f"Test ID: {test_id}")
    await update.message.reply_text(customer_msg)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE, bot_id: str):
    chat_id = update.effective_chat.id
    salesperson_text = (update.message.text or "").strip()
    if not salesperson_text:
        return

    test_id = await get_participant_test_id(chat_id=chat_id, bot_id=bot_id)
    if not test_id:
        await update.message.reply_text(PLEASE_START)
        return

    await insert_message(test_id, bot_id, "salesperson", salesperson_text, chat_id)

    persona = ALL_PERSONAS[bot_id]
    history = await get_last_messages(test_id, bot_id, limit=10)

    customer_reply = await generate_customer_reply(
        system_prompt=persona.system_prompt,
        few_shot=persona.few_shot,
        history_docs=history,
        salesperson_message=salesperson_text,
    )

    await insert_message(test_id, bot_id, "customer", customer_reply, chat_id)
    await update.message.reply_text(customer_reply)


def run_customer_bot(token: str, bot_id: str):
    if bot_id not in ALL_PERSONAS:
        raise ValueError(f"Unknown bot_id: {bot_id}")

    app = ApplicationBuilder().token(token).build()

    # bind bot_id into handlers
    async def _start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await start_cmd(update, context, bot_id)

    async def _handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await handle_text(update, context, bot_id)

    app.add_handler(CommandHandler("start", _start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _handle))

    app.post_init = lambda _: ensure_indexes()
    app.run_polling(drop_pending_updates=True)
