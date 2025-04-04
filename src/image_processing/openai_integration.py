import base64
import json
import logging
import os

import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

logger = logging.getLogger(__name__)


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def load_chart_config(config_path):
    with open(config_path, "r") as file:
        return json.load(file)


def process_chart_with_gpt4o(image_path, config_path, user_config=None):
    """Process a chart image using GPT-4o."""
    logger.info(f"Processing chart image: {image_path}")
    config = load_chart_config(config_path)

    if user_config:
        for key in [
            "entry_color",
            "stop_loss_color",
            "take_profit_color",
            "output_format",
            "indicators",
        ]:
            if key in user_config:
                config[key] = user_config[key]

    prompt = (
        f"Look at this chart image. "
        f"Find the following data points."
        f"Symbol (BTC/ETH/USDT), "
        f"Entry (color={config['entry_color']}), "
        f"Stop Loss (color={config['stop_loss_color']}), "
        f"Take Profit (color={config['take_profit_color']}),"
        f"Position Type (long/short). It is long if the Take Profit > Entry, and short if Entry < Take Profit. "
    )
    prompt += f"Indicators: {', '.join(config['indicators'])}. "
    prompt += f"Output format: {config['output_format']}"

    base64_image = encode_image(image_path)

    response = openai.responses.create(
        model="gpt-4o",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{base64_image}",
                    },
                ],
            }
        ],
    )

    analysis_result = response.output_text

    return analysis_result
