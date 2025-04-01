from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Welcome to Chart Sayer API!"}

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Initialize Telegram bot
telegram_token = os.getenv('TELEGRAM_TOKEN')
telegram_app = ApplicationBuilder().token(telegram_token).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hello! I am your Chart Sayer bot.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Send me a chart image to analyze.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Logic to process incoming messages and images
    await update.message.reply_text('Processing your request...')

telegram_app.add_handler(CommandHandler('start', start))
telegram_app.add_handler(CommandHandler('help', help_command))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.post("/telegram")
async def telegram_webhook(update: Update):
    await telegram_app.update_queue.put(update)
    return {"status": "Telegram webhook received"}

import discord

# Initialize Discord bot
class DiscordBot(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith('!start'):
            await message.channel.send('Hello! I am your Chart Sayer bot.')

        if message.content.startswith('!help'):
            await message.channel.send('Send me a chart image to analyze.')

# Create Discord client
intents = discord.Intents.default()
intents.message_content = True

discord_token = os.getenv('DISCORD_TOKEN')
discord_client = DiscordBot(intents=intents)

discord_client.run(discord_token)

@app.post("/discord")
async def discord_webhook():
    # Logic for handling Discord webhook
    return {"status": "Discord webhook received"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)