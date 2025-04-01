import base64
import os

import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


import json


def load_chart_config(config_path):
    with open(config_path, 'r') as file:
        return json.load(file)


def process_chart_with_gpt4o(image_path, config_path):
    config = load_chart_config(config_path)

    prompt = f"Analyze this chart image. Entry color: {config['entry_color']}, Stop Loss color: {config['stop_loss_color']}, Take Profit color: {config['take_profit_color']}. "
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


if __name__ == "__main__":
    image_path = "/workspace/chart-sayer/test_chart_image.png"
    config_path = "/workspace/chart-sayer/config/chart_config.json"
    result = process_chart_with_gpt4o(image_path, config_path)
    print("Analysis Result:", result)
