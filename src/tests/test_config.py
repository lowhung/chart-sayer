import json
import unittest
from unittest.mock import patch

from src.image_processing.process_image import parse_arguments, load_config


class TestConfig(unittest.TestCase):
    def setUp(self):
        # Sample configuration data
        self.sample_config = {
            "green_lower": [35, 100, 100],
            "green_upper": [85, 255, 255],
            "red_lower1": [0, 100, 100],
            "red_upper1": [10, 255, 255],
            "red_lower2": [160, 100, 100],
            "red_upper2": [180, 255, 255]
        }

    def test_load_config(self):
        # Test loading configuration from a file
        with patch('builtins.open', unittest.mock.mock_open(read_data=json.dumps(self.sample_config))):
            config = load_config('config.json')
            self.assertEqual(config, self.sample_config)

    def test_parse_arguments(self):
        # Test parsing command-line arguments
        test_args = [
            "process_image.py",
            "--green-lower", "30", "90", "90",
            "--green-upper", "80", "250", "250"
        ]
        with patch("sys.argv", test_args):
            args = parse_arguments()
            self.assertEqual(args.green_lower, [30, 90, 90])
            self.assertEqual(args.green_upper, [80, 250, 250])


if __name__ == "__main__":
    unittest.main()
