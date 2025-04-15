from flask import Flask, request
import os
import openai
import telegram
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
openai.api_key = OPENAI_API_KEY

user_state = {}

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def respond():
    update_data = request.get_json(force=True)

    if not update_data:
        return "no update", 400

    update = telegram.Update.de_json(update_data, bot)

    if update.message:
        text = update.message.text.strip()
        chat_id = update.message.chat.id

        if chat_id not in user_state:
            user_state[chat_id] = {"stage": "start"}

        state = user_state[chat_id]

        if state["stage"] == "start":
            bot.send_message(
                chat_id=chat_id,
                text="Hi! 👋 I’m JassDispatch — your AI freight dispatcher.\nПривет! Я JassDispatch — твой AI-диспетчер."
            )
            keyboard = [
                [InlineKeyboardButton("English 🇺🇸", callback_data='lang_en')],
                [InlineKeyboardButton("Русский 🇷🇺", callback_data='lang_ru')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.send_message(
                chat_id=chat_id,
                text="Please choose your language / Пожалуйста, выбери язык:",
                reply_markup=reply_markup
            )
            state["stage"] = "language"

    elif update.callback_query:
        query = update.callback_query
        chat_id = query.message.chat.id
        data = query.data

        if chat_id not in user_state:
            user_state[chat_id] = {}

        state = user_state[chat_id]

        if data.startswith("lang_"):
            lang = data.split("_")[1]
            state["lang"] = lang
            state["stage"] = "role"
            keyboard = [
                [InlineKeyboardButton("Truck Driver", callback_data='role_driver')],
                [InlineKeyboardButton("Broker", callback_data='role_broker')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.send_message(
                chat_id=chat_id,
                text="Are you a truck driver or a broker?\nВы водитель трака или брокер?",
                reply_markup=reply_markup
            )
            return "ok"

        elif data.startswith("role_"):
            role = data.split("_")[1]
            state["role"] = role
            state["stage"] = "prompt"
            bot.send_message(chat_id=chat_id, text="Got it! ✅\nТеперь напиши, что тебе нужно.")
            return "ok"

    elif "message" in update_data and "text" in update_data["message"]:
        chat_id = update_data["message"]["chat"]["id"]
        text = update_data["message"]["text"].strip()
        state = user_state.get(chat_id, {})

        if state.get("stage") == "prompt":
            lang = state.get("lang", "en")
            role = state.get("role", "driver")
            user_message = text

            prompt = {
                "ru": f"""Представь, что ты опытный логист-диспетчер с 10-летним стажем.
Ты свободно говоришь на русском и английском, отлично знаешь все нюансы грузоперевозок по США — законодательство, маршруты, ставки, реалии брокеров и грузоотправителей.
Ты честный, грамотный и умеешь доносить свои мысли, умеешь убеждать, продавать и ставить справедливую маржу.
Роль пользователя: {role.upper()}
Пользователь написал: "{user_message}"
Если это запрос на груз — предложи 2-3 маршрута с городами, расстоянием, типом груза и ставкой.
Если это брокер — составь грамотный, деловой текст от лица профессионального логиста.""",
                "en": f"""Imagine you are a professional freight dispatcher with 10 years of experience.
You speak both English and Russian fluently and are highly knowledgeable in all U.S. transportation laws, road regulations, dispatch processes, brokers’ practices, and load booking nuances.
You're honest, articulate, persuasive, and know how to price loads fairly with a solid profit margin.
Role: {role.upper()}
The user said: "{user_message}"
If it's a freight request — suggest 2-3 realistic routes with cities, mileage, cargo type, and rate.
If it's a broker message — generate a convincing, professional message in business tone."""
            }

            try:
                completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt[lang]}]
                )
                response_text = completion.choices[0].message.content.strip()
                bot.send_message(chat_id=chat_id, text=response_text)
            except Exception as e:
                bot.send_message(chat_id=chat_id, text="Произошла ошибка. Попробуй ещё раз позже.")
                print(f"OpenAI API Error: {e}")

    return "ok"
