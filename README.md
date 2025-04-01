# chart-sayer
Chart Sayer is a lightweight service designed to analyze chart images and extract key trading information such as entry and exit points based on user-defined rules. The service can be integrated with platforms like Discord and Telegram to automate the process of chart analysis and position management.

## Features
- **Image Processing**: Analyze chart images to detect entry and exit points using machine vision and OCR.
- **Bot Integration**: Seamlessly integrate with Discord and Telegram to receive and process chart images.
- **Customizable Rules**: Define custom rules for interpreting chart features, such as color codes for entry and exit points.
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
To run the FastAPI server, ensure you have set up your environment variables in a `.env` file based on the [`.env.example`](.env.example). Then, execute the following command:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```
This will start the server, allowing you to interact with the API endpoints for Telegram and Discord bot integration.

### Processing a Chart Image
To process a chart image directly, run the following command:
```bash
python3 image_processing/process_image.py
```
This will analyze the image and output the extracted information.

### Command-Line Interface
You can also process a chart image using the command-line interface. Run the following command:
```bash
python3 src/cli.py <image_path> <config_path>
```
Replace `<image_path>` with the path to your chart image file and `<config_path>` with the path to your configuration JSON file.

This will analyze the image and output the extracted information based on the provided configuration.

## Customization
Chart Sayer allows users to customize the analysis rules and output format through command-line arguments and configuration files.

### Command-Line Arguments
You can specify customization options directly from the command line. For example:
```bash
python3 image_processing/process_image.py --green-lower 35 100 100 --green-upper 85 255 255
```
This command sets the HSV thresholds for detecting green colors.

### Configuration File
Alternatively, you can use a configuration file to define your settings. A sample [`config.json`](config/config.json) file is provided in the `config` directory:
```json
{
    "green_lower": [35, 100, 100],
    "green_upper": [85, 255, 255],
    "red_lower1": [0, 100, 100],
### Configuration Options
The `config.json` file allows you to customize various aspects of the bot's behavior and image processing. Here are the options you can set:

- `clients`: List of clients to integrate with, such as `discord` and `telegram`.
- `entry_color`: The color used to identify entry points on the chart.
- `stop_loss_color`: The color used to identify stop loss points.
- `take_profit_color`: The color used to identify take profit points.
- `output_format`: The format string for the output message, using placeholders like `{entry}`, `{stop_loss}`, and `{take_profit}`.
- `indicators`: List of indicators to use, such as `moving_average` and `parabolic_sar`.
- `telegram`: Configuration specific to the Telegram bot, including `webhook_mode` and `webhook_url`.
- `discord`: Configuration specific to the Discord bot, including `gateway_mode` and `webhook_mode`.
- `image_processing`: Settings for image processing, including the `model` and `max_tokens`.

These options allow you to tailor the bot's functionality to your specific needs.
    "red_upper1": [10, 255, 255],
    "red_lower2": [160, 100, 100],
    "red_upper2": [180, 255, 255]
}
```
To use the configuration file, run:
```bash
python3 image_processing/process_image.py --config config/config.json
```

Command-line arguments will override settings in the configuration file if both are provided.

## Contributing
We welcome contributions from the community. Please fork the repository and submit a pull request with your changes. For major changes, please open an issue first to discuss what you would like to change.
