import os

from fastapi import APIRouter
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

router = APIRouter()

# Initialize Telegram bot
telegram_token = os.getenv('TELEGRAM_TOKEN')
telegram_app = ApplicationBuilder().token(telegram_token).build()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hello! I am your Chart Sayer bot.')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Send me a chart image to analyze.')


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Processing your request...')


telegram_app.add_handler(CommandHandler('start', start))
telegram_app.add_handler(CommandHandler('help', help_command))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


@router.post("/telegram")
async def telegram_webhook(update: Update):
    await telegram_app.update_queue.put(update)
    return {"status": "Telegram webhook received"}
