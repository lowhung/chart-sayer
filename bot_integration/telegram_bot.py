from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Hello! I am your Chart Sayer bot.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Send me a chart image to analyze.')

async def main() -> None:
    # Replace 'YOUR_TOKEN' with your bot's token
    application = ApplicationBuilder().token('YOUR_TOKEN').build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))

    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())