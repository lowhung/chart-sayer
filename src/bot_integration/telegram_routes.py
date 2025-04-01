import json
import logging

from fastapi import APIRouter, Request, Response, HTTPException, status
from telegram import Update

from src.bot_integration.telegram_bot import bot, telegram_app

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/webhook")
async def telegram_webhook(request: Request):
    """Handle incoming webhook updates from Telegram."""
    try:

        data = await request.body()

        if data:
            update_data = json.loads(data)

            logger.debug(f"Received Telegram update: {update_data}")

            update = Update.de_json(data=update_data, bot=bot)

            if telegram_app:
                await telegram_app.process_update(update)
                return {"status": "success"}
            else:
                logger.error("Telegram application not initialized")
                return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning("Received empty webhook request")
            return {"status": "empty request"}

    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook request")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
