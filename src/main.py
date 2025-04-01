from fastapi import FastAPI
from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Load environment variables from .env file
load_dotenv()

app = FastAPI()

import json

# Load chart configuration
config_path = "config/chart_config.json"
with open(config_path, 'r') as file:
    config = json.load(file)

# Import Telegram and Discord routes conditionally
if "telegram" in config["clients"]:
    from bot_integration.telegram_routes import router as telegram_router
    app.include_router(telegram_router)

from contextlib import asynccontextmanager
logger.info('Starting Discord bot')

from bot_integration.discord_bot import bot

@asynccontextmanager
async def lifespan(app: FastAPI):
    if "discord" in config["clients"]:
        await bot.start(os.getenv('DISCORD_TOKEN'))
        await bot.setup_bot()
    try:
        yield
    finally:
        await bot.close()

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
