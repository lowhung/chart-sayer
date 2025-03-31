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
   pip install -r requirements.txt
   ```

## Usage
To process a chart image, run the following command:
```bash
python3 image_processing/process_image.py
```
This will analyze the image and output the extracted information.

## Customization
Chart Sayer allows users to customize the analysis rules and output format through command-line arguments and configuration files.

### Command-Line Arguments
You can specify customization options directly from the command line. For example:
```bash
python3 image_processing/process_image.py --green-lower 35 100 100 --green-upper 85 255 255
```
This command sets the HSV thresholds for detecting green colors.

### Configuration File
Alternatively, you can use a configuration file to define your settings. A sample `config.json` file is provided in the `config` directory:
```json
{
    "green_lower": [35, 100, 100],
    "green_upper": [85, 255, 255],
    "red_lower1": [0, 100, 100],
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
