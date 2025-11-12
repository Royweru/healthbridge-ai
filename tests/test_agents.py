# tests/test_agents.py

import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

from agents.coordinator import CoordinatorAgent
from backend.models.models import Patient

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_db_session():
    """Fixture for a mocked database session."""
    db = MagicMock()
    
    # Mock the query method
    db.query.return_value.filter.return_value.first.return_value = None
    
    # Mock commit and refresh
    db.commit = MagicMock()
    db.refresh = MagicMock()
    db.add = MagicMock()
    
    return db

@pytest.fixture
def coordinator(mock_db_session):
    """Fixture for the CoordinatorAgent with a mocked LLM chain."""
    with patch('agents.coordinator.LLMChain') as mock_llm_chain:
        # Mock the llm_chain to return a predictable intent
        mock_llm_chain.return_value.run.return_value = "greeting"
        
        agent = CoordinatorAgent(db_session=mock_db_session)
        # We can also attach the mock to the instance to change it in tests
        agent.llm_chain = mock_llm_chain.return_value
        return agent

@patch('agents.coordinator.detect_language', return_value={"language": "en"})
@patch('agents.coordinator.translate_text', return_value={"translated_text": "Hello"})
@patch('agents.coordinator.send_whatsapp_message', return_value="mock_message_sid")
async def test_process_message_new_patient_english(
    mock_send_whatsapp, mock_translate, mock_detect_lang, coordinator, mock_db_session
):
    """
    Test processing a message from a new patient in English.
    """
    phone_number = "+12345"
    message = "Hello"

    # Ensure the patient does not exist initially
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    # Process the message
    result = await coordinator.process_message(message, phone_number)

    # 1. Check if language detection was called
    mock_detect_lang.assert_called_with(message)
    
    # 2. Check if a new patient was created
    mock_db_session.add.assert_called()
    assert mock_db_session.add.call_args[0][0].phone_number == phone_number
    
    # 3. Check if intent was classified
    coordinator.llm_chain.run.assert_called_with(message=message)
    assert result["intent"] == "greeting"
    
    # 4. Check if the correct response was sent
    mock_send_whatsapp.assert_called_with(
        to_number=phone_number,
        message_body="Hello! Welcome to HealthBridge AI. How can I help you today? You can ask to book an appointment, or ask a health-related question."
    )
    
    # 5. Check if messages were logged (incoming and outgoing)
    assert mock_db_session.add.call_count >= 3 # Patient + 2 messages

@patch('agents.coordinator.detect_language', return_value={"language": "sw"})
@patch('agents.coordinator.translate_text')
@patch('agents.coordinator.send_whatsapp_message', new_callable=AsyncMock)
async def test_process_message_existing_patient_swahili(
    mock_send_whatsapp, mock_translate, mock_detect_lang, coordinator, mock_db_session
):
    """
    Test processing a message from an existing patient in Swahili.
    """
    phone_number = "+54321"
    message_sw = "Nataka kuweka miadi"
    message_en = "I want to book an appointment"

    # Mock the patient existing in the DB
    existing_patient = Patient(id=1, phone_number=phone_number, language='sw')
    mock_db_session.query.return_value.filter.return_value.first.return_value = existing_patient

    # Mock the translation service
    def translate_side_effect(text, dest_lang):
        if dest_lang == 'en':
            return {"translated_text": message_en}
        if dest_lang == 'sw':
            return {"translated_text": "Ninakusaidia na hilo. Ili kuweka miadi, nahitaji kujua sababu ya ziara yako na tarehe na saa unayopendelea."}
        return {}
    mock_translate.side_effect = translate_side_effect
    
    # Mock the LLM to return the correct intent
    coordinator.llm_chain.run.return_value = "book_appointment"

    # Process the message
    result = await coordinator.process_message(message_sw, phone_number)

    # 1. Check language detection and translation
    mock_detect_lang.assert_called_with(message_sw)
    mock_translate.assert_any_call(message_sw, dest_lang='en')
    
    # 2. Check intent classification was called with the translated message
    coordinator.llm_chain.run.assert_called_with(message=message_en)
    assert result["intent"] == "book_appointment"

    # 3. Check that the English response was translated back to Swahili
    mock_translate.assert_any_call(
        "I can help with that. To book an appointment, I need to know the reason for your visit and your preferred date and time.",
        dest_lang='sw'
    )

    # 4. Check that the final Swahili message was sent
    mock_send_whatsapp.assert_called_with(
        to_number=phone_number,
        message_body="Ninakusaidia na hilo. Ili kuweka miadi, nahitaji kujua sababu ya ziara yako na tarehe na saa unayopendelea."
    )

    # 5. Check that the patient was not created again
    # The first call to add is the incoming message, second is outgoing. No patient add.
    assert mock_db_session.add.call_count == 2
