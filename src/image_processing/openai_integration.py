import base64
import os

import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')


# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


import json


# Function to load chart configuration
def load_chart_config(config_path):
    with open(config_path, 'r') as file:
        return json.load(file)


# Function to process chart image using GPT-4o
def process_chart_with_gpt4o(image_path, config_path):
    # Load chart configuration
    config = load_chart_config(config_path)

    # Construct the prompt with user configuration
    prompt = f"Analyze this chart image. Entry color: {config['entry_color']}, Stop Loss color: {config['stop_loss_color']}, Take Profit color: {config['take_profit_color']}. "
    prompt += f"Indicators: {', '.join(config['indicators'])}. "
    prompt += f"Output format: {config['output_format']}"

    # Encode the image to Base64
    base64_image = encode_image(image_path)

    # Call OpenAI API
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

    # Process the response
    analysis_result = response.output_text

    return analysis_result


# Example usage
if __name__ == "__main__":
    image_path = "/workspace/chart-sayer/test_chart_image.png"
    config_path = "/workspace/chart-sayer/config/chart_config.json"
    result = process_chart_with_gpt4o(image_path, config_path)
    print("Analysis Result:", result)
