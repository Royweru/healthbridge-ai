# agents/coordinator.py

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
from sqlalchemy.orm import Session

from backend.models import models
from utils.translation import translate_text, detect_language
from utils.whatsapp import send_whatsapp_message

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# --- Intent Classification Prompt ---
# This prompt is designed to be robust and give structured output.
intent_classification_template = """
You are a healthcare assistant for HealthBridge AI in Kenya. Your job is to analyze incoming WhatsApp messages from patients and classify their intent.

The primary language of the clinic is English, but patients may write in Swahili or other local languages.

Here are the possible intents:
- **book_appointment**: The user wants to schedule a new appointment.
- **reschedule_appointment**: The user wants to change an existing appointment.
- **cancel_appointment**: The user wants to cancel an appointment.
- **ask_question**: The user is asking a general health question or a question about the clinic (e.g., "what are your hours?").
- **greeting**: A simple greeting like "hello", "hi", "habari".
- **affirmative**: An affirmative response like "yes", "sawa", "ndio".
- **negative**: A negative response like "no", "hapana".
- **unclear**: The user's intent is not clear from the message.

Analyze the following message and respond with ONLY the intent in lowercase. Do not add any other text.

Message: "{message}"
Intent:
"""

INTENT_PROMPT = PromptTemplate(
    template=intent_classification_template,
    input_variables=["message"]
)

class CoordinatorAgent:
    def __init__(self, db_session: Session):
        if not ANTHROPIC_API_KEY or "your_claude_api_key" in ANTHROPIC_API_KEY:
            logger.warning("Anthropic API key is not configured. Agent will have limited functionality.")
            self.llm_chain = None
        else:
            # Using Claude 3 Haiku for speed and cost-effectiveness
            llm = ChatAnthropic(model="claude-3-haiku-20240307", temperature=0)
            self.llm_chain = LLMChain(llm=llm, prompt=INTENT_PROMPT)
        
        self.db = db_session

    def get_or_create_patient(self, phone_number: str, language: str = 'en') -> models.Patient:
        """
        Retrieves a patient by phone number or creates a new one if they don't exist.
        """
        patient = self.db.query(models.Patient).filter(models.Patient.phone_number == phone_number).first()
        if not patient:
            logger.info(f"Creating new patient for number: {phone_number}")
            patient = models.Patient(phone_number=phone_number, language=language)
            self.db.add(patient)
            self.db.commit()
            self.db.refresh(patient)
        elif patient.language != language:
            # Update language if it has changed
            patient.language = language
            self.db.commit()
        return patient

    def classify_intent(self, message: str) -> str:
        """
        Uses the LLM to classify the intent of the message.
        """
        if not self.llm_chain:
            # Fallback logic if LLM is not available
            if "book" in message.lower() or "appointment" in message.lower():
                return "book_appointment"
            if "hello" in message.lower() or "habari" in message.lower():
                return "greeting"
            return "unclear"
            
        try:
            response = self.llm_chain.run(message=message)
            intent = response.strip().lower()
            logger.info(f"Classified intent as: {intent}")
            return intent
        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            return "unclear"

    def log_message(self, 
                    patient_id: int, 
                    session_id: str, 
                    sender: str,
                    content: str,
                    translated_content: str = None,
                    lang: str = None
                    ):
        """Logs the message to the database."""
        msg = models.Message(
            patient_id=patient_id,
            session_id=session_id,
            sender=sender,
            content=content,
            translated_content=translated_content,
            language=lang
        )
        self.db.add(msg)
        self.db.commit()

    async def process_message(self, incoming_msg: str, patient_phone: str):
        """
        Main method to process an incoming WhatsApp message.
        """
        logger.info(f"Processing message from {patient_phone}: '{incoming_msg}'")

        # 1. Detect language and translate to English if necessary
        lang_detection = detect_language(incoming_msg)
        source_lang = lang_detection.get("language", "en")
        
        message_for_processing = incoming_msg
        if source_lang != 'en' and not lang_detection.get("error"):
            translation = translate_text(incoming_msg, dest_lang='en')
            if not translation.get("error"):
                message_for_processing = translation["translated_text"]
        
        # 2. Get or create patient record
        patient = self.get_or_create_patient(patient_phone, source_lang)
        
        # 3. Log the incoming message
        self.log_message(
            patient_id=patient.id,
            session_id=patient_phone,
            sender='patient',
            content=incoming_msg,
            translated_content=message_for_processing if source_lang != 'en' else None,
            lang=source_lang
        )

        # 4. Classify intent
        intent = self.classify_intent(message_for_processing)

        # 5. Route to the appropriate agent/logic (stubbed for now)
        response_text_en = f"Intent identified: {intent}. The '{intent}' agent will assist you shortly."

        if intent == "greeting":
            response_text_en = "Hello! Welcome to HealthBridge AI. How can I help you today? You can ask to book an appointment, or ask a health-related question."
        elif intent == "book_appointment":
            response_text_en = "I can help with that. To book an appointment, I need to know the reason for your visit and your preferred date and time."
        elif intent == "unclear":
            response_text_en = "I'm sorry, I didn't understand that. Could you please rephrase? You can ask to book an appointment or ask a health question."

        # 6. Translate response back to patient's language
        final_response = response_text_en
        if source_lang != 'en':
            translation_back = translate_text(response_text_en, dest_lang=source_lang)
            if not translation_back.get("error"):
                final_response = translation_back["translated_text"]

        # 7. Send response via WhatsApp and log it
        send_whatsapp_message(to_number=patient_phone, message_body=final_response)
        self.log_message(
            patient_id=patient.id,
            session_id=patient_phone,
            sender='coordinator',
            content=final_response,
            translated_content=response_text_en if source_lang != 'en' else None,
            lang=source_lang
        )

        return {"status": "processed", "intent": intent, "response": final_response}

# Example of how to use it (would be called from the FastAPI route)
if __name__ == '__main__':
    # This is for demonstration purposes.
    # In the app, the DB session will be managed by FastAPI dependencies.
    db = next(models.get_db())
    
    coordinator = CoordinatorAgent(db_session=db)
    
    # Simulate an incoming message
    test_phone_number = "+254712345678" # Dummy number
    test_message_sw = "Habari, nataka kuweka miadi na daktari."
    
    import asyncio
    asyncio.run(coordinator.process_message(test_message_sw, test_phone_number))
    
    db.close()
