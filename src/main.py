import asyncio
import json
import logging
import signal
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from src.bot_integration.discord_bot import setup_bot, shutdown_bot, start_bot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Load chart configuration
config_path = "src/config/chart_config.json"
with open(config_path, 'r') as file:
    config = json.load(file)

# Import Telegram and Discord routes conditionally
if "telegram" in config["clients"]:
    from src.bot_integration.telegram_routes import router as telegram_router

    app.include_router(telegram_router)

logger.info('Starting Discord bot')

# Create a shutdown event
shutdown_event = asyncio.Event()


# Signal handler
def signal_handler():
    logging.info("Shutdown signal received!")
    shutdown_event.set()


# Signal handler that works with asyncio
def handle_shutdown_signal():
    logger.info("Shutdown signal received!")
    # Set the shutdown event and schedule the shutdown
    shutdown_event.set()

    # Give the app a chance to shut down gracefully, then force exit if needed
    def force_exit():
        logger.warning("Forcing exit after 10 seconds")
        sys.exit(1)

    # Schedule a forced exit in 10 seconds
    asyncio.get_event_loop().call_later(10, force_exit)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Set up signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_shutdown_signal)

    if "discord" in config["clients"]:
        # Set up the bot cogs
        await setup_bot()

        # Start the bot and command sync in tracked tasks
        logger.info("Starting Discord bot...")
        bot_task, sync_task = await start_bot()

    try:
        yield
    finally:
        logger.info("Application shutdown initiated...")

        if "discord" in config["clients"]:
            # Properly shut down the Discord bot
            await shutdown_bot()

        logger.info("Application shutdown complete")


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def read_root():
    return {"message": "Welcome to Chart Sayer API!"}


# In-memory storage for positions
positions = {}


@app.get("/get_positions/{user_id}")
async def get_positions(user_id: str):
    user_positions = positions.get(user_id, [])
    return {"user_id": user_id, "positions": user_positions}


@app.post("/close_position/{position_id}")
async def close_position(position_id: str):
    # Logic to close the position and notify users
    return {"status": "Position closed", "position_id": position_id}


@app.post("/update_position/{position_id}")
async def update_position(position_id: str):
    # Logic to update the position and notify users
    return {"status": "Position updated", "position_id": position_id}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
