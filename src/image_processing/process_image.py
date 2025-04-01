import argparse
import json

import cv2
import numpy as np
import pytesseract


def load_config(config_path):
    with open(config_path, 'r') as file:
        return json.load(file)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Process chart images with customizable settings.')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--green-lower', type=int, nargs=3, metavar=('H', 'S', 'V'),
                        help='Lower HSV threshold for green color')
    parser.add_argument('--green-upper', type=int, nargs=3, metavar=('H', 'S', 'V'),
                        help='Upper HSV threshold for green color')
    parser.add_argument('--red-lower1', type=int, nargs=3, metavar=('H', 'S', 'V'),
                        help='Lower HSV threshold for red color (range 1)')
    parser.add_argument('--red-upper1', type=int, nargs=3, metavar=('H', 'S', 'V'),
                        help='Upper HSV threshold for red color (range 1)')
    parser.add_argument('--red-lower2', type=int, nargs=3, metavar=('H', 'S', 'V'),
                        help='Lower HSV threshold for red color (range 2)')
    parser.add_argument('--red-upper2', type=int, nargs=3, metavar=('H', 'S', 'V'),
                        help='Upper HSV threshold for red color (range 2)')
    return parser.parse_args()


def process_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Image not found at path: {image_path}")

    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    green_lower = np.array([35, 100, 100])
    green_upper = np.array([85, 255, 255])
    red_lower1 = np.array([0, 100, 100])
    red_upper1 = np.array([10, 255, 255])
    red_lower2 = np.array([160, 100, 100])
    red_upper2 = np.array([180, 255, 255])

    green_mask = cv2.inRange(hsv_image, green_lower, green_upper)
    red_mask1 = cv2.inRange(hsv_image, red_lower1, red_upper1)
    red_mask2 = cv2.inRange(hsv_image, red_lower2, red_upper2)
    red_mask = cv2.add(red_mask1, red_mask2)

    image[green_mask > 0] = [0, 255, 0]
    image[red_mask > 0] = [0, 0, 255]

    edges = cv2.Canny(gray_image, 50, 150, apertureSize=3)

    lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

    horizontal_red_lines = []

    if lines is not None:
        for rho, theta in lines[:, 0]:
            if abs(theta) < np.pi / 36 or abs(theta - np.pi) < np.pi / 36:
                a = np.cos(theta)
                b = np.sin(theta)
                x0 = a * rho
                y0 = b * rho
                x1 = int(x0 + 1000 * (-b))
                y1 = int(y0 + 1000 * (a))
                x2 = int(x0 - 1000 * (-b))
                y2 = int(y0 - 1000 * (a))
                x1 = max(0, min(x1, image.shape[1] - 1))
                y1 = max(0, min(y1, image.shape[0] - 1))
                x2 = max(0, min(x2, image.shape[1] - 1))
                y2 = max(0, min(y2, image.shape[0] - 1))

                if red_mask[y1, x1] > 0 and red_mask[y2, x2] > 0:
                    cv2.line(image, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    horizontal_red_lines.append(((x1, y1), (x2, y2)))

    text = pytesseract.image_to_string(gray_image)

    import time
    timestamp = int(time.time())
    output_filename = f"/workspace/chart-sayer/detected_colors_{timestamp}.png"
    cv2.imwrite(output_filename, image)
    print(f"Processed image saved as: {output_filename}")

    return {
        "extracted_text": text,
        "horizontal_red_lines": horizontal_red_lines,
        "output_filename": output_filename
    }


if __name__ == "__main__":
    image_paths = [
        "/workspace/chart-sayer/test_chart_image.png",
        "/workspace/chart-sayer/aave_test_image.png",
        "/workspace/chart-sayer/near_test_image.png"
    ]

    for image_path in image_paths:
        print(f"\nProcessing image: {image_path}")
        try:
            extracted_text = process_image(image_path)
            print("Extracted Text:")
            print(extracted_text)
        except FileNotFoundError as e:
            print(e)
