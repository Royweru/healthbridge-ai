# utils/whatsapp.py

import os
import logging
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Twilio credentials from environment variables
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")

# Validate that credentials are set
if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER]):
    logger.error("Twilio credentials are not fully configured in the .env file.")
    # You might want to raise an exception here in a real application
    # raise ValueError("Twilio credentials are not fully configured.")
    client = None
else:
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        logger.info("Twilio client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Twilio client: {e}")
        client = None

def send_whatsapp_message(to_number: str, message_body: str) -> str:
    """
    Sends a WhatsApp message to a specified number using Twilio.

    Args:
        to_number (str): The recipient's WhatsApp number in the format 'whatsapp:+1234567890'.
        message_body (str): The text of the message to send.

    Returns:
        str: The SID (unique identifier) of the message if sent successfully, otherwise an error string.
    """
    if not client:
        error_msg = "Twilio client is not initialized. Cannot send message."
        logger.error(error_msg)
        return error_msg

    if not to_number.startswith('whatsapp:'):
        logger.warning(f"Recipient number '{to_number}' does not start with 'whatsapp:'. Prepending it.")
        to_number = f"whatsapp:{to_number}"

    try:
        message = client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=message_body,
            to=to_number
        )
        logger.info(f"Message sent successfully to {to_number}. SID: {message.sid}")
        return message.sid
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message to {to_number}: {e}")
        return f"Error: {e}"

# Example usage (for testing)
if __name__ == '__main__':
    # This is a dummy number. Replace with a real number for testing.
    # The number must be registered with your Twilio sandbox.
    test_recipient_number = os.getenv("TEST_RECIPIENT_WHATSAPP_NUMBER", "whatsapp:+254712345678") # Example Kenyan number

    if "your_twilio" in TWILIO_ACCOUNT_SID or not client:
        print("Twilio is not configured. Skipping test message.")
    else:
        print(f"Attempting to send a test message to {test_recipient_number}...")
        test_message = "Karibu! This is a test message from the HealthBridge AI system. 🇰🇪"
        
        message_sid = send_whatsapp_message(test_recipient_number, test_message)

        if "Error" in message_sid:
            print(f"Test message failed. Reason: {message_sid}")
        else:
            print(f"Test message sent! Message SID: {message_sid}")
            print("Please check your WhatsApp for the message.")
