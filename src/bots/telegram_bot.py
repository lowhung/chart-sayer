import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

from src.image_processing.openai_integration import process_chart_with_gpt4o

logger = logging.getLogger(__name__)
load_dotenv()
telegram_token = os.getenv('TELEGRAM_TOKEN')


class TelegramBotManager:
    def __init__(self):
        self.application = None
        self.is_running = False
        self.bot = None
        self.ready_event = asyncio.Event()

    async def start_bot(self, token, polling=True, webhook_url=None):
        """Start the Telegram bot."""
        if self.is_running:
            logger.warning("Telegram bot is already running")
            return self.application

        self.bot = Bot(token)
        self.application = ApplicationBuilder().token(token).build()

        self.application.add_handler(CommandHandler('start', self._start))
        self.application.add_handler(CommandHandler('help', self._help_command))
        self.application.add_handler(CommandHandler('analyze', self._analyze_command))

        self.application.add_handler(MessageHandler(filters.PHOTO, self._handle_photo))

        self.application.add_error_handler(self._error_handler)

        if polling:

            self.application.run_polling(close_loop=False, stop_signals=None)
            logger.info("Telegram bot started successfully in polling mode")
        else:

            await self.application.initialize()
            await self._setup_webhook(webhook_url, token)
            logger.info(f"Telegram bot initialized in webhook mode with URL: {webhook_url}")

        self.is_running = True
        self.ready_event.set()
        return self.application

    async def _setup_webhook(self, url, token):
        """Set up the webhook for Telegram."""
        webhook_url = f"{url}/telegram/webhook"

        await self.bot.delete_webhook()

        await self.bot.set_webhook(url=webhook_url)
        logger.info(f"Telegram webhook set to: {webhook_url}")

    async def shutdown(self):
        """Shut down the Telegram bot."""
        if not self.is_running or not self.application:
            logger.warning("No Telegram bot is running")
            return

        logger.info("Shutting down Telegram bot...")
        try:

            if hasattr(self.application, 'updater') and self.application.updater:
                logger.info("Stopping Telegram updater...")
                await self.application.updater.stop()

            await self.application.stop()
            await self.application.shutdown()

            self.is_running = False
            self.ready_event.clear()
            logger.info("Telegram bot shutdown complete")
        except Exception as e:
            logger.error(f"Error shutting down Telegram bot: {e}")

    async def process_update(self, update_data):
        """Process an update from a webhook."""
        if not self.is_running or not self.application:
            logger.error("Cannot process update: Telegram bot is not running")
            return False

        update = Update.de_json(data=update_data, bot=self.bot)
        await self.application.process_update(update)
        return True

    async def _start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a welcome message when the command /start is issued."""
        await update.message.reply_text('Hello! I am your Chart Sayer bot.')

    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a help message when the command /help is issued."""
        await update.message.reply_text(
            'I can analyze chart images for you!\n\n'
            'Simply send me an image of a chart, or use the /analyze command and attach an image.'
        )

    async def _analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /analyze command with an attached image."""
        if update.message.photo:
            await self._process_image(update, context)
        else:
            await update.message.reply_text(
                'Please attach an image to analyze. You can:\n'
                '1. Send me an image directly\n'
                '2. Use the /analyze command with an attached image'
            )

    async def _handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle photos sent to the bot without a command."""
        await self._process_image(update, context)

    async def _process_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Process the chart image and return analysis."""
        processing_message = await update.message.reply_text('Processing your chart image...')

        try:
            photo = update.message.photo[-1]
            photo_file = await context.bot.get_file(photo.file_id)

            os.makedirs('/tmp', exist_ok=True)

            image_path = f"/tmp/telegram_image_{photo.file_id}.jpg"

            await photo_file.download_to_drive(image_path)

            config_path = "src/config/chart_config.json"
            result = process_chart_with_gpt4o(image_path, config_path)

            await update.message.reply_text(f"Analysis Result: {result}")

            try:
                os.remove(image_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file {image_path}: {e}")

        except Exception as e:
            logger.error(f"Error processing image: {e}")
            await update.message.reply_text(
                "Sorry, I encountered an error analyzing your chart. Please try again."
            )
        finally:
            await processing_message.delete()

    async def _error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors in the dispatcher."""
        logger.error(f"Update {update} caused error {context.error}")

        if update and isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "Sorry, something went wrong processing your request."
            )


bot_manager = TelegramBotManager()
