import os
import io
from flask import Flask, request, jsonify
from google.cloud import vision_v1
from google.cloud.vision_v1 import types
import re

app = Flask(__name__)

# Set your Google Cloud service account credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'cloudapi.json'

@app.route('/process_image', methods=['POST'])
def process_image():
    try:
        # Read the uploaded image file from the request
        image_file = request.files['image']
        if not image_file:
            return jsonify({"error": "No image file provided"}), 400

        # Read the image content
        content = image_file.read()

        # Initialize the Vision API client
        client = vision_v1.ImageAnnotatorClient()

        # Create an Image object
        image = vision_v1.types.Image(content=content)

        # Perform text detection on the image
        response = client.text_detection(image=image)

        # Extract the detected text annotations from the response
        texts = response.text_annotations

        if texts:
            # Extract the full detected text
            extracted_text = texts[0].description

            # Define a regular expression pattern to match floating-point values ending with "mm"
            mm_pattern = r'\b\d+\.\d+mm\b'

            # Use re.findall to extract all matching values
            matching_values_mm = re.findall(mm_pattern, extracted_text)

            # Define the list of target text values in the desired order
            target_values = ["BPD", "HC", "AC", "FL"]

            # Initialize a dictionary to associate values ending with "mm" with target values
            value_to_text_mapping = {}

            # Iterate through the target values and assign values ending with "mm" to them
            for target_value in target_values:
                if matching_values_mm:
                    value_to_text_mapping[target_value] = matching_values_mm.pop(0)
                else:
                    break  # Stop if there are no more values ending with "mm"

            # Search for "U/8," "U/S," and "U/B" in the text
            u8_position = extracted_text.find("U/8")
            us_position = extracted_text.find("U/S")
            ub_position = extracted_text.find("U/B")

            # Initialize variables to store the largest values for each pattern
            largest_value = "No 'U/8,' 'U/S,' or 'U/B' found in the text."

            # If "U/8" is found, search for values containing "w" and "d" after it
            if u8_position != -1:
                text_after_u8 = extracted_text[u8_position + 3:]  # Start after "U/8"

                # Define a regular expression pattern to match values with "w" and "d"
                wd_pattern = r'\d+w\d+d'

                # Use re.findall to find all matching values
                matching_values_wd = re.findall(wd_pattern, text_after_u8)

                # Filter and find the largest value containing 'w' and 'd'
                if matching_values_wd:
                    largest_value = max(matching_values_wd, key=lambda x: float(x.replace('w', '.').replace('d', '')))

            # If "U/S" is found, search for values containing "w" and "d" after it
            if us_position != -1:
                text_after_us = extracted_text[us_position + 3:]  # Start after "U/S"

                # Define a regular expression pattern to match values with "w" and "d"
                wd_pattern = r'\d+w\d+d'

                # Use re.findall to find all matching values
                matching_values_wd = re.findall(wd_pattern, text_after_us)

                # Filter and find the largest value containing 'w' and 'd'
                if matching_values_wd:
                    largest_value = max(matching_values_wd, key=lambda x: float(x.replace('w', '.').replace('d', '')))

            # If "U/B" is found, search for values containing "w" and "d" after it
            if ub_position != -1:
                text_after_ub = extracted_text[ub_position + 3:]  # Start after "U/B"

                # Define a regular expression pattern to match values with "w" and "d"
                wd_pattern = r'\d+w\d+d'

                # Use re.findall to find all matching values
                matching_values_wd = re.findall(wd_pattern, text_after_ub)

                # Filter and find the largest value containing 'w' and 'd'
                if matching_values_wd:
                    largest_value = max(matching_values_wd, key=lambda x: float(x.replace('w', '.').replace('d', '')))

            # Define a regular expression pattern to match dates
            date_pattern = r'\d{1,2}/\d{1,2}/\d{4}'

            # Use re.findall to extract all matching dates
            matching_dates = re.findall(date_pattern, extracted_text)

            # Search for "EDD" in the text
            edd_position = extracted_text.find("EDD")

            # If "EDD" is found, search for the date anywhere after it in the text
            if edd_position != -1:
                text_after_edd = extracted_text[edd_position + 3:]  # Start after "EDD"
                edd_dates = re.findall(date_pattern, text_after_edd)
                if edd_dates:
                    edd_date = edd_dates[0]  # Take the first date found
                else:
                    edd_date = "No date found after 'EDD' in the text."
            else:
                edd_date = "No 'EDD' found in the text."

            return jsonify({
                "Biometrics": value_to_text_mapping,
                "GA": largest_value,
                "EDD_Date": edd_date
            })

        else:
            return jsonify({"error": "No text found in the image"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
