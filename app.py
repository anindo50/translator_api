from flask import Flask, request, jsonify
from flask_cors import CORS
import srt
from googletrans import Translator as GoogleTranslator
from concurrent.futures import ThreadPoolExecutor
import requests
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

DEEPL_API_KEY = "YOUR_DEEPL_API_KEY"  # Replace with your DeepL API key

# Google Translate function
def google_translate(sub, tolang):
    try:
        translator = GoogleTranslator()  # Initialize the Translator
        translated = translator.translate(text=sub, dest=tolang)
        return translated.text  # Return the translated text
    except Exception as e:
        raise Exception(f"Google Translate failed: {str(e)}")

# DeepL Translation function
def deepl_translate(sub, tolang):
    try:
        # Map language codes between googletrans and DeepL if necessary
        deepl_language_code = tolang  # DeepL supports many of the same language codes
        response = requests.post(
            'https://api.deepl.com/v2/translate',
            data={
                'auth_key': "b725e568-ade3-41ea-bfca-d7e97945dd07",
                'text': sub,
                'target_lang': deepl_language_code.upper(),
            }
        )
        result = response.json()
        print("deepL is using")
        if response.status_code != 200 or 'translations' not in result:
            raise Exception(f"DeepL Translation API failed: {response.text}")
        return result['translations'][0]['text']  # Return the translated text
    except Exception as e:
        raise Exception(f"DeepL Translate failed: {str(e)}")

# Parallel translation function that supports multiple translation models
def translate_in_parallel(subtitles, tolang, model="google"):
    with ThreadPoolExecutor() as executor:
        if model == "deepl":
            translated_contents = list(
                executor.map(
                    lambda sub: deepl_translate(sub.content, tolang),
                    [sub for sub in subtitles if sub.start and sub.end]
                )
            )
        else:  # Fallback to Google Translate
            translated_contents = list(
                executor.map(
                    lambda sub: google_translate(sub.content, tolang),
                    [sub for sub in subtitles if sub.start and sub.end]
                )
            )

    idx = 0
    for sub in subtitles:
        if sub.start and sub.end:
            sub.content = translated_contents[idx]
            idx += 1

# Function to download file from URL
def download_file(url, file_name):
    response = requests.get(url)
    if response.status_code == 200:
        file_path = os.path.join('temp', file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as f:
            f.write(response.content)
        return file_path
    else:
        raise Exception(f"Failed to download file. Status code: {response.status_code}")

@app.route('/trans', methods=['POST'])
def translate_srt():
    print("In the API route")

    # Get JSON data from the request
    data = request.json

    # Debugging: Print the received data
    print("Received data:", data)

    # Check if 'to_lang' is provided in the request
    if 'to_lang' not in data:
        return jsonify({"error": "Target language not provided"}), 400
    
    to_lang = data['to_lang']
    lang_model = data.get('lang_model', 'google').lower()  # Default to Google Translate
    srt_content = ""
    subtitles = []

    # Handle file URL
    if 'file_url' in data and data['file_url']:
        file_url = data['file_url']
        file_name = "downloaded.srt"
        file_path = download_file(file_url, file_name)
        with open(file_path, 'r', encoding='utf-8') as f:
            srt_content = f.read()
        subtitles = list(srt.parse(srt_content))
        os.remove(file_path)  # Clean up the downloaded file
        print(f"Downloaded file: {file_path}")

    # Handle file upload #
    elif 'file' in request.files:
        file = request.files['file']
        srt_content = file.read().decode('utf-8')
        subtitles = list(srt.parse(srt_content))
    else:
        return jsonify({"error": "Provide either an SRT file or file URL"}), 400

    # Translate subtitles based on the selected model
    try:
        translate_in_parallel(subtitles, to_lang, lang_model)
    except Exception as e:
        return jsonify({"error": f"Translation failed: {str(e)}"}), 500

    # Create translated SRT content
    translated_srt = srt.compose(subtitles)

    # Return translated SRT content as JSON
    return jsonify({"translatedSubtitle": translated_srt})


if __name__ == '__main__':
    app.run(debug=True)
