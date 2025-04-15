
import os
import logging
from flask import Flask, request
import telegram
from telegram import ReplyKeyboardMarkup
from openai import OpenAI, OpenAIError

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)

lang_keyboard = ReplyKeyboardMarkup([
    ["Русский", "English"]
], resize_keyboard=True)

@app.route(f"/{TOKEN}", methods=["POST"])
def respond():
    try:
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        message = update.message

        if not message or not message.text:
            bot.sendMessage(chat_id=update.effective_chat.id, text="Пустое сообщение. Повтори запрос.")
            return "ok"

        chat_id = message.chat.id
        text = message.text.strip()

        if text in ["/start", "Русский", "English"]:
            language = "ru" if text == "Русский" else "en"
            welcome_msg = {
                "ru": "Привет! Я JassDispatch — твой AI-диспетчер. Чем могу помочь?",
                "en": "Hi! I’m JassDispatch — your AI dispatcher. How can I assist you?"
            }
            bot.sendMessage(chat_id=chat_id, text=welcome_msg[language], reply_markup=lang_keyboard)
            return "ok"

        lang = "ru" if any(char in text.lower() for char in "абвгдеёжзийклмнопрстуфхцчшщьыъэюя") else "en"
        prompt = {
            "ru": f"Ты AI-диспетчер. Пользователь написал: "{text}". Если он ищет груз — предложи 2-3 маршрута с городами, расстоянием, типом груза и ставкой. Если пишет брокеру — сгенерируй вежливое деловое сообщение.",
            "en": f"You are an AI dispatcher. The user said: "{text}". If it's a freight request — suggest 2-3 realistic load routes with cities, mileage, cargo type and rate. If it's for a broker — generate a polite business message."
        }

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "user", "content": prompt[lang]}
                ]
            )
            reply = response.choices[0].message.content
            bot.sendMessage(chat_id=chat_id, text=reply)

        except OpenAIError as e:
            bot.sendMessage(chat_id=chat_id, text="OpenAI API ключ не работает или неверен.")
            logging.error(f"OpenAI error: {str(e)}")

    except Exception as e:
        logging.exception("Ошибка в Telegram обработчике")
        if update and update.effective_chat:
            bot.sendMessage(chat_id=update.effective_chat.id, text=f"Ошибка в боте: {str(e)}")

    return "ok"

@app.route('/')
def index():
    return 'JassDispatch bot is running.'

if __name__ == '__main__':
    app.run(port=int(os.environ.get('PORT', 10000)))
