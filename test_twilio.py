# Download the helper library from https://www.twilio.com/docs/python/install
import os
from twilio.rest import Client
import json
from dotenv import load_dotenv

load_dotenv()
# Find your Account SID and Auth Token at twilio.com/console
# and set the environment variables. See http://twil.io/secure


def mainFn():
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        from_=os.getenv('TWILIO_WHATSAPP_NUMBER'),
        to=os.getenv('TEST_RECIPIENT_WHATSAPP_NUMBER'),
        content_sid="HXb5b62575e6e4ff6129ad7c8efe1f983e",
        content_variables=json.dumps({"1": "22 July 2026", "2": "3:15pm"}),
    )

    print(f"This is the twilio message body{message.body}")
    
if __name__ =="__main__" :
    mainFn()