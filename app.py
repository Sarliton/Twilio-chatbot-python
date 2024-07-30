from flask import Flask, request
from context import ConversationContext
from states import ChatBot, StartState
import twilio_helpers
from dotenv import load_dotenv
from db import get_db, close_connection

app = Flask(__name__)

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

app.teardown_appcontext(close_connection)

bot = ChatBot()

@app.route('/sms', methods=['POST'])
def sms_reply():
    phone_number = request.form['From']
    incoming_msg = request.form['Body']
    my_twilio_number = request.form['To']

    if phone_number not in bot.conversation_state:
        bot.conversation_state[phone_number] = ConversationContext(StartState, phone_number, my_twilio_number)

    response = bot.conversation_state[phone_number].request(incoming_msg)
    print(f"Response to send: {response}")  # Log da resposta antes de enviar

    if isinstance(response, list) and response:
        twilio_helpers.send_auto_messages(phone_number, response, my_twilio_number)
        return ('', 204)
    else:
        print("No valid message to send, received:", response)
        return ('', 204)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
