import argparse
from src.image_processing.openai_integration import process_chart_with_gpt4o


def main():
    parser = argparse.ArgumentParser(description='Process a chart image using GPT-4o.')
    parser.add_argument('image_path', type=str, help='Path to the chart image file')
    parser.add_argument('config_path', type=str, help='Path to the configuration JSON file')

    args = parser.parse_args()

    result = process_chart_with_gpt4o(args.image_path, args.config_path)
    print("Analysis Result:", result)


if __name__ == "__main__":
    main()
