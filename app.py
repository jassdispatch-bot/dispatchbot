
import os
from flask import Flask, request
import openai
import telegram
from telegram import Bot
from telegram.ext import Dispatcher, MessageHandler, Filters
from telegram.ext import CommandHandler
from telegram.utils.request import Request

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
openai.api_key = OPENAI_API_KEY

@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def respond():
    update = telegram.Update.de_json(request.get_json(force=True), bot)

    text = update.message.text
    chat_id = update.message.chat.id

    lang = "ru" if any(c in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя" for c in text.lower()) else "en"

    prompt = {
        "ru": (
            f"Представь, что ты опытный логист-диспетчер с 10-летним стажем. "
            "Ты свободно говоришь на русском и английском языках, отлично знаешь все нюансы грузоперевозок по США: "
            "законодательство, правила дорожного движения, специфику маршрутов, правила брокеров и грузоотправителей. "
            "Ты честный, грамотный и умеешь доносить свои мысли, умеешь убеждать, продавать, ставить справедливую наценку. "
            f"Пользователь написал: \"{text}\". "
            "Если это запрос на груз — предложи 2-3 маршрута с городами, расстоянием, типом груза и ставкой. "
            "Если это сообщение для брокера — сгенерируй грамотный, деловой текст. "
            "Пиши с тоном профессионального логиста с 10-летним опытом."
        ),
        "en": (
            f"Imagine you are a professional freight dispatcher with 10 years of experience. "
            "You speak both English and Russian fluently and are highly knowledgeable in all U.S. transportation laws, "
            "road regulations, dispatch processes, brokers’ practices, and load booking nuances. "
            "You're honest, articulate, persuasive, and know how to price loads fairly with a solid profit margin. "
            f"The user said: \"{text}\". "
            "If it’s a freight request — suggest 2–3 realistic routes with cities, mileage, cargo type, and rate. "
            "If it’s a broker message — generate a convincing, professional message in business tone."
        )
    }

    try:
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt[lang]}]
        )
        response_text = completion.choices[0].message.content.strip()
        bot.send_message(chat_id=chat_id, text=response_text)
    except Exception as e:
        bot.send_message(chat_id=chat_id, text="Произошла ошибка при обработке запроса. Попробуй ещё раз.")
        print(e)

    return 'ok'

@app.route('/')
def index():
    return 'Bot is running!'

if __name__ == '__main__':
    app.run()
