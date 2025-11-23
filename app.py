from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv
import openai

load_dotenv()

app = Flask(__name__)

VERIFY_TOKEN = os.getenv('VERIFY_TOKEN', 'misr_sweets_verify')
PAGE_ACCESS_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

openai.api_key = OPENAI_API_KEY

SYSTEM_PROMPT = """You are a friendly customer service assistant for Misr Sweets.
Always respond in Arabic.
Provide helpful information about our products."""

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if token == VERIFY_TOKEN:
            return challenge
        return 'Invalid token', 403
    
    elif request.method == 'POST':
        data = request.get_json()
        if data.get('object') == 'page':
            for entry in data.get('entry', []):
                for msg in entry.get('messaging', []):
                    if msg.get('message'):
                        sender = msg['sender']['id']
                        text = msg['message'].get('text')
                        if text:
                            response = get_chatgpt_response(text)
                            send_message(sender, response)
        return jsonify({'status': 'ok'}), 200

def get_chatgpt_response(user_msg):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_msg}],
            temperature=0.7, max_tokens=500
        )
        return response['choices'][0]['message']['content']
    except:
        return "Sorry, error"

def send_message(recipient_id, message_text):
    url = f"https://graph.facebook.com/v18.0/me/messages"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    payload = {"recipient": {"id": recipient_id}, "message": {"text": message_text}}
    requests.post(url, json=payload, params=params)

@app.route('/')
def home():
    return '<h1>Misr Sweets Chatbot Running</h1>'

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
