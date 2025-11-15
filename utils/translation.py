# utils/translation.py

import logging
from deep_translator import GoogleTranslator
from deep_translator.exceptions import TranslationNotFound

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def translate_text(text: str, dest_lang: str = 'en', source_lang: str = 'auto') -> dict:
    """
    Translates a given text to a destination language using Google Translate.

    Args:
        text (str): The text to translate.
        dest_lang (str): The destination language code (e.g., 'en', 'sw' for Swahili).
        source_lang (str): The source language code. Defaults to 'auto'.

    Returns:
        dict: A dictionary containing the translated text, source language, and destination language.
              Returns an error message in the dictionary if translation fails.
    """
    if not text or not isinstance(text, str):
        return {"error": "Invalid input text for translation."}

    try:
        # Initialize the translator
        translator = GoogleTranslator(source=source_lang, target=dest_lang)
        
        # Perform the translation
        translated_text = translator.translate(text)
        
        if translated_text:
            result = {
                "translated_text": translated_text,
                "source_language": source_lang if source_lang != 'auto' else 'auto detected',
                "dest_language": dest_lang
            }
            logger.info(f"Translated '{text}' ({result['source_language']}) to '{result['translated_text']}' ({result['dest_language']})")
            return result
        else:
            return {"error": "Translation returned an empty result."}

    except TranslationNotFound as e:
        logger.error(f"Translation not found for text: '{text}'. Error: {e}")
        return {"error": f"Could not translate the text. It might be too short or in an unsupported language. Details: {e}"}
    except Exception as e:
        logger.error(f"Error during translation: {e}")
        return {"error": str(e)}

def get_supported_languages() -> dict:
    """
    Gets a list of supported languages from the translation service.

    Returns:
        dict: A dictionary of language codes and their names.
    """
    return GoogleTranslator().get_supported_languages(as_dict=True)

# Example usage (for testing)
if __name__ == '__main__':
    # --- Test Translation ---
    text_to_translate = "Habari ya asubuhi. Ningependa kuweka miadi na daktari."
    print(f"Original text: {text_to_translate}")
    
    # Translate to English
    translation_result = translate_text(text_to_translate, dest_lang='en')
    print(f"Translation to English: {translation_result}")

    # Translate back to Swahili
    if not translation_result.get("error"):
        english_text = translation_result["translated_text"]
        swahili_result = translate_text(english_text, dest_lang='sw')
        print(f"Translation back to Swahili: {swahili_result}")

    # --- Test Language Detection ---
    # The detect_language function has been removed.
    # If you need language detection, consider using a dedicated library or service.

    # --- Test with another language ---
    french_text = "Bonjour, comment ça va?"
    print(f"\nOriginal text: {french_text}")
    # detected_french = detect_language(french_text) # Removed
    # print(f"Language Detection: {detected_french}") # Removed
    translated_french = translate_text(french_text, dest_lang='en')
    print(f"Translation to English: {translated_french}")
    
    # --- Test supported languages ---
    # print("\nSupported Languages:")
    # print(get_supported_languages())