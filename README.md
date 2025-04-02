# chart-sayer

Chart Sayer is a lightweight service designed to analyze chart images and extract key trading information such as entry
and exit points based on user-defined rules. The service can be integrated with platforms like Discord and Telegram to
automate the process of chart analysis and position management.

## Features

- **Image Processing**: Analyze chart images to detect entry and exit points using machine vision and OCR.
- **Bot Integration**: Seamlessly integrate with Discord and Telegram to receive and process chart images.
- **Customizable Rules**: Define custom rules for interpreting chart features, such as color codes for entry and exit
  points.
- **Position Management**: Maintain a ledger of positions per user, allowing for easy querying and updates.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/lowhung/chart-sayer.git
   cd chart-sayer
   ```

2. Install the required dependencies:
   ```bash
   poetry install
   ```

## Environment Variables

Ensure you have the following environment variables set in your `.env` file:

- `TELEGRAM_TOKEN`: Your Telegram bot token.
- `DISCORD_TOKEN`: Your Discord bot token.
- `DISCORD_CLIENT_ID`: Your Discord client ID.
- `DISCORD_CLIENT_SECRET`: Your Discord client secret.
- `DISCORD_PUBLIC_KEY`: Your Discord public key.
- `OPENAI_API_KEY`: Your OpenAI API key.

## Usage

### Running the FastAPI Server

To run the FastAPI server, ensure you have set up your environment variables in a `.env` file based on the [
`.env.example`](.env.example). Then, execute the following command:

```bash
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

This will start the server, allowing you to interact with the API endpoints for Telegram and Discord bot integration.

### Command-Line Interface

Chart Sayer provides a convenient command-line interface for processing chart images without running the full server.
You can use Poetry to run the CLI tool:

```bash
poetry run analyze-chart <image_path> <config_path>
```

For example:

```bash
poetry run analyze-chart src/chart_images/aave_test_image.png src/config/chart_config.json
```

This will analyze the chart image and output the extracted information based on your configuration:

```
Analysis Result: Entry: 162.46, Stop Loss: 161.82, Take Profit: 243.01
```

Alternatively, you can run the Python script directly:

```bash
poetry run python src/cli.py <image_path> <config_path>
```

## Customization

Chart Sayer allows users to customize the analysis rules and output format through configuration files.

### Configuration File

You can use a configuration file to define your settings. A sample [`chart_config.json`](src/config/chart_config.json)
file is provided in the `src/config` directory:

```json
{
  "clients": [
    "discord",
    "telegram"
  ],
  "entry_color": "green",
  "stop_loss_color": "red",
  "take_profit_color": "blue",
  "output_format": "Entry: {entry}, Stop Loss: {stop_loss}, Take Profit: {take_profit}",
  "indicators": [
    "moving_average",
    "parabolic_sar"
  ],
  "image_processing": {
    "model": "gpt-4o",
    "max_tokens": 500
  }
}
```

### Configuration Options

The configuration file allows you to customize various aspects of the bot's behavior and image processing. Here are the
options you can set:

- `clients`: List of clients to integrate with, such as `discord` and `telegram`.
- `entry_color`: The color used to identify entry points on the chart.
- `stop_loss_color`: The color used to identify stop loss points.
- `take_profit_color`: The color used to identify take profit points.
- `output_format`: The format string for the output message, using placeholders like `{entry}`, `{stop_loss}`, and
  `{take_profit}`.
- `indicators`: List of indicators to use, such as `moving_average` and `parabolic_sar`.
- `telegram`: Configuration specific to the Telegram bot, including `webhook_mode` and `webhook_url`.
- `discord`: Configuration specific to the Discord bot, including `gateway_mode` and `webhook_mode`.
- `image_processing`: Settings for image processing, including the `model` and `max_tokens`.

These options allow you to tailor the bot's functionality to your specific needs.

## Contributing

We welcome contributions from the community. Please fork the repository and submit a pull request with your changes. For
major changes, please open an issue first to discuss what you would like to change.