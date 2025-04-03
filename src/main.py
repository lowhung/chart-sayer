import asyncio
import json
import logging
import signal
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from src.bots.discord_bot import setup_bot as setup_discord_bot
from src.bots.discord_bot import shutdown_bot as shutdown_discord_bot
from src.bots.discord_bot import start_bot as start_discord_bot
from src.bots.telegram_bot import bot_manager, telegram_token
from src.storage.redis_client import RedisClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

config_path = "src/config/chart_config.json"
with open(config_path, 'r') as file:
    config = json.load(file)

shutdown_event = asyncio.Event()


def handle_shutdown_signal():
    logger.info("Shutdown signal received!")
    shutdown_event.set()

    def force_exit():
        logger.warning("Forcing exit after 10 seconds")
        sys.exit(1)

    asyncio.get_event_loop().call_later(10, force_exit)


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_shutdown_signal)

    discord_tasks = []

    try:

        if "discord" in config["clients"]:
            logger.info("Setting up Discord bot...")
            await setup_discord_bot()
            discord_tasks = await start_discord_bot()
            logger.info("Discord bot started")

        if "telegram" in config["clients"]:
            telegram_config = config.get("telegram", {})

            if telegram_config.get("webhook_mode", False):
                webhook_url = telegram_config.get("webhook_url")
                await bot_manager.start_bot(telegram_token, polling=False, webhook_url=webhook_url)
            else:
                await bot_manager.start_bot(telegram_token, polling=True)

        yield
    finally:
        logger.info("Application shutdown initiated...")

        shutdown_tasks = []

        if "discord" in config["clients"]:
            shutdown_tasks.append(shutdown_discord_bot())

        if "telegram" in config["clients"]:
            await bot_manager.shutdown()

        if shutdown_tasks:
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)

        logger.info("Application shutdown complete")


app = FastAPI(lifespan=lifespan)

# Initialize Redis client
redis_client = RedisClient()

if "telegram" in config["clients"] and config.get("telegram", {}).get("webhook_mode", False):
    from src.routes.telegram_routes import router as telegram_router
    app.include_router(telegram_router)

# Include positions router
from src.routes.positions.router import router as positions_router
app.include_router(positions_router)


@app.get("/")
async def read_root():
    return {"message": "Welcome to Chart Sayer API!"}




if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
