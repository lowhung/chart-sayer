from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Import Telegram and Discord routes
from bot_integration.telegram_routes import router as telegram_router
from bot_integration.discord_routes import router as discord_router

# Include routers
app.include_router(telegram_router)
app.include_router(discord_router)

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