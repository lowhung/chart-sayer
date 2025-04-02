import json
import logging

from fastapi import APIRouter, Request, Response, HTTPException, status

from src.bots.discord_bot import verify_discord_signature, process_discord_interaction

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/discord", tags=["discord"])


@router.post("/interactions")
async def discord_interactions(request: Request):
    """Handle incoming interactions from Discord."""
    try:
        # Get configuration
        from src.main import config
        discord_config = config.get("discord", {})
        public_key = discord_config.get("public_key")

        if not public_key:
            logger.error("Discord public key missing from configuration")
            return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Verify the request came from Discord
        is_valid = await verify_discord_signature(request, public_key)
        if not is_valid:
            logger.warning("Invalid Discord interaction signature")
            return Response(status_code=status.HTTP_401_UNAUTHORIZED)

        # Get the interaction data
        data = await request.json()
        logger.debug(f"Received Discord interaction: {data}")

        # Process the interaction
        response_data = await process_discord_interaction(data)

        return response_data

    except json.JSONDecodeError:
        logger.error("Invalid JSON in Discord interaction request")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error(f"Error processing Discord interaction: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
