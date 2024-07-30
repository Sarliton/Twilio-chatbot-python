import threading
from twilio.rest import Client
import os
from dotenv import load_dotenv
from time import sleep

load_dotenv()  # Inicialização do cliente Twilio
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)

def flatten_messages(messages):
    flat_list = []
    for item in messages:
        if isinstance(item, list):
            flat_list.extend(flatten_messages(item))  # Recursivamente achata a lista
        else:
            flat_list.append(item)
    return flat_list

def send_auto_messages(to_number, messages, my_twilio_number):
    def run():
        flat_messages = flatten_messages(messages)  # Achata a lista de mensagens
        for message in flat_messages:
            if isinstance(message, str) and message.strip():  # Verifica se a mensagem é uma string não vazia
                print(f"Sending message to {to_number}: {message}")
                client.messages.create(
                    body=message,
                    from_=my_twilio_number,
                    to=to_number
                )
                sleep(1)  # Adiciona uma pequena pausa entre as mensagens
            else:
                print(f"Skipped sending a message due to it being None or empty: {message}")

    thread = threading.Thread(target=run)
    thread.start()
