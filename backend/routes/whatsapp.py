# backend/routes/whatsapp.py

import logging
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from sqlalchemy.orm import Session
import asyncio

from agents.coordinator import CoordinatorAgent
from backend.models.models import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/whatsapp",
    tags=["WhatsApp"],
)

@router.post("/webhook",
             summary="Twilio WhatsApp Webhook",
             description="Endpoint to receive incoming messages from Twilio.")
async def whatsapp_webhook(
    request: Request,
    db: Session = Depends(get_db),
    From: str = Form(...), # Patient's number e.g., 'whatsapp:+254712345678'
    Body: str = Form(...)  # The message content
):
    """
    This webhook is called by Twilio every time a user sends a message
    to the configured WhatsApp number.

    - It receives the patient's phone number (`From`) and the message content (`Body`).
    - It initializes the `CoordinatorAgent`.
    - It processes the message asynchronously in the background to avoid timing out the webhook.
    - It immediately returns a 204 No Content response to Twilio to acknowledge receipt.
    """
    patient_phone = From.split('whatsapp:')[1] if 'whatsapp:' in From else From
    incoming_msg = Body
    
    logger.info(f"Webhook received from {patient_phone}: '{incoming_msg}'")

    try:
        # Initialize the coordinator agent with the current DB session
        coordinator = CoordinatorAgent(db_session=db)
        
        # Run the processing in the background.
        # FastAPI will handle the async task.
        # This ensures we can respond to Twilio quickly.
        asyncio.create_task(coordinator.process_message(
            incoming_msg=incoming_msg,
            patient_phone=patient_phone
        ))

        # Twilio expects a quick response. An empty TwiML response is one way,
        # but for a webhook that only receives, returning a 204 is often sufficient
        # and signals that we've successfully received the request but have no content to return.
        # from fastapi.responses import Response
        # return Response(content="", media_type="application/xml")
        
        # For modern webhooks, a simple 200 or 204 is fine.
        return {"status": "Message received and is being processed."}

    except Exception as e:
        logger.error(f"Error in WhatsApp webhook: {e}")
        # It's crucial to still return a success status code to Twilio if possible,
        # to prevent it from retrying the request. Logging the error is key.
        raise HTTPException(status_code=500, detail="An internal error occurred.")

# To test this endpoint with curl, you would run:
# curl -X POST http://localhost:8000/api/whatsapp/webhook \
# -d "From=whatsapp%3A%2B1234567890" \
# -d "Body=Hello"
