import cv2
import pytesseract

# Function to process an image and extract text

def process_image(image_path):
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Image not found at path: {image_path}")

    # Convert the image to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Use Tesseract to extract text
    text = pytesseract.image_to_string(gray_image)

    return text

# Example usage
if __name__ == "__main__":
    image_path = "path/to/your/chart/image.png"
    try:
        extracted_text = process_image(image_path)
        print("Extracted Text:")
        print(extracted_text)
    except FileNotFoundError as e:
        print(e)
