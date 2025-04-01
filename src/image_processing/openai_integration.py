import base64
import os
import json
import base64
import logging
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def encode_image(img_path):
    try:
        with open(img_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
            logger.info(f"Image at {img_path} successfully encoded.")
            return encoded_image
    except Exception as e:
        logger.error(f"Failed to encode image at {img_path}: {e}")
        raise


def load_chart_config(cfg_path):
    try:
        with open(cfg_path, 'r') as file:
            config = json.load(file)
            logger.info(f"Configuration loaded from {cfg_path}.")
            return config
    except Exception as e:
        logger.error(f"Failed to load configuration from {cfg_path}: {e}")
        raise


def process_chart_with_gpt4o(img_path, cfg_path):
    config = load_chart_config(cfg_path)

    prompt = (f"Analyze this chart image. Entry color: {config['entry_color']}, "
              f"Stop Loss color: {config['stop_loss_color']}, Take Profit color: {config['take_profit_color']}. "
              f"Indicators: {', '.join(config['indicators'])}. "
              f"Output format: {config['output_format']}")

    base64_image = encode_image(img_path)

    try:
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
        logger.info("Chart analysis completed successfully.")
        return analysis_result
    except Exception as e:
        logger.error(f"Failed to process chart with GPT-4o: {e}")
        raise


if __name__ == "__main__":
    test_image_path = "/workspace/chart-sayer/src/test_images/test_chart_image.png"
    test_config_path = "/workspace/chart-sayer/src/config/chart_config.json"
    try:
        result = process_chart_with_gpt4o(test_image_path, test_config_path)
        print("Analysis Result:", result)
    except Exception as e:
        logger.error(f"Error during chart analysis: {e}")
