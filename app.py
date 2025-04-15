
import os
import logging
from flask import Flask, request
import telegram
from telegram import ReplyKeyboardMarkup
import openai

# Set up logging
logging.basicConfig(level=logging.INFO)

# Bot and GPT setup
TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = "gpt-4"

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)
openai.api_key = OPENAI_API_KEY

lang_keyboard = ReplyKeyboardMarkup([
    ["Русский", "English"]
], resize_keyboard=True)

@app.route(f"/{TOKEN}", methods=["POST"])
def respond():
    update = telegram.Update.de_json(request.get_json(force=True), bot)
    chat_id = update.message.chat.id
    text = update.message.text

    if text in ["/start", "Русский", "English"]:
        language = "ru" if text == "Русский" else "en"
        welcome_msg = {
            "ru": "Привет! Я JassDispatch — твой AI-диспетчер. Чем могу помочь?",
            "en": "Hi! I’m JassDispatch — your AI dispatcher. How can I assist you?"
        }
        bot.sendMessage(chat_id=chat_id, text=welcome_msg[language], reply_markup=lang_keyboard)

    elif "груз" in text.lower() or "load" in text.lower():
        prompt = f"Ты AI-диспетчер. Пользователь пишет: '{text}'. Сгенерируй 2-3 предложения грузов с городами, расстоянием, ставкой."
        if "load" in text.lower():
            prompt = f"You are an AI dispatcher. The user says: '{text}'. Generate 2-3 realistic freight load options with cities, distance, rate."

        response = openai.ChatCompletion.create(
            model=GPT_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        reply = response["choices"][0]["message"]["content"]
        bot.sendMessage(chat_id=chat_id, text=reply)

    elif "брокер" in text.lower() or "broker" in text.lower():
        message = {
            "ru": "Здравствуйте, интересует ваш груз из [город] в [город]. Подскажите, доступен ли он?",
            "en": "Hello, I’m interested in your load from [city] to [city]. Is it still available?"
        }
        language = "ru" if "брокер" in text.lower() else "en"
        bot.sendMessage(chat_id=chat_id, text=message[language])

    elif update.message.document:
        file = update.message.document
        bot.sendMessage(chat_id=chat_id, text="Документ получен. Спасибо!")

    else:
        bot.sendMessage(chat_id=chat_id, text="Пожалуйста, выбери команду или задай вопрос.", reply_markup=lang_keyboard)

    return 'ok'

@app.route('/')
def index():
    return 'JassDispatch bot is running.'

if __name__ == '__main__':
    app.run(port=int(os.environ.get('PORT', 10000)))
