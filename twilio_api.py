import os
import json
from twilio.rest import Client
from dotenv import load_dotenv
import logging

load_dotenv()

account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)

# logging.basicConfig(level=logging.INFO)

def send_message(to: str, message: str) -> None:
    try:
        client.messages.create(
            from_='whatsapp:'+os.getenv('FROM'),
            body=message,
            to=to
        )
        
        logging.info('Message sent successfully to %s', to)
    except Exception as e:
        logging.error(f'Failed to send message to {to}: {e}')


from_='whatsapp:'+os.getenv('FROM')
print(from_)