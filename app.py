
import os
import logging
from flask import Flask, request
import telegram
from telegram import ReplyKeyboardMarkup
import openai

logging.basicConfig(level=logging.INFO)

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
        return "ok"

    if text:
        # Автоматическое определение языка и обработка GPT
        prompt_ru = f"Ты выступаешь как AI-диспетчер грузов. Пользователь написал: "{text}". Ответь как настоящий логист. Если это запрос на поиск груза — предложи 2-3 маршрута с городами, расстоянием, ставкой и типом груза. Если это обращение к брокеру — сгенерируй вежливое сообщение."
        prompt_en = f"You are acting as an AI freight dispatcher. The user said: "{text}". Respond like a real logistics manager. If it's a freight search — offer 2-3 routes with cities, distance, price and load type. If it's a broker message — generate a polite request."

        # Определим язык текста
        lang = "ru" if any(char in text.lower() for char in "абвгдеёжзийклмнопрстуфхцчшщьыъэюя") else "en"
        prompt = prompt_ru if lang == "ru" else prompt_en

        try:
            response = openai.ChatCompletion.create(
                model=GPT_MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            reply = response["choices"][0]["message"]["content"]
            bot.sendMessage(chat_id=chat_id, text=reply)
        except Exception as e:
            bot.sendMessage(chat_id=chat_id, text=f"Произошла ошибка: {e}")

    return "ok"

@app.route('/')
def index():
    return 'JassDispatch bot is running.'

if __name__ == '__main__':
    app.run(port=int(os.environ.get('PORT', 10000)))
