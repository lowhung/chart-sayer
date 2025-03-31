import cv2
import pytesseract
import numpy as np


# Function to process an image and extract text

def process_image(image_path):
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Image not found at path: {image_path}")

    # Convert the image to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Detect edges using Canny
    edges = cv2.Canny(gray_image, 50, 150, apertureSize=3)

    # Detect lines using Hough Line Transform
    lines = cv2.HoughLines(edges, 1, np.pi/180, 200)

    # Draw lines on the original image
    if lines is not None:
        for rho, theta in lines[:, 0]:
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a * rho
            y0 = b * rho
            x1 = int(x0 + 1000 * (-b))
            y1 = int(y0 + 1000 * (a))
            x2 = int(x0 - 1000 * (-b))
            y2 = int(y0 - 1000 * (a))
            cv2.line(image, (x1, y1), (x2, y2), (0, 0, 255), 2)

    # Use Tesseract to extract text
    text = pytesseract.image_to_string(gray_image)

    # Save the image with detected lines
    cv2.imwrite("/workspace/chart-sayer/detected_lines.png", image)

    return text

# Example usage
if __name__ == "__main__":
    image_path = "/workspace/chart-sayer/test_chart_image.png"
    try:
        extracted_text = process_image(image_path)
        print("Extracted Text:")
        print(extracted_text)
    except FileNotFoundError as e:
        print(e)
