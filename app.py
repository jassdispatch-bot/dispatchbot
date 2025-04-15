from flask import Flask, request
import os
import openai
import telegram
from telegram import Bot

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
openai.api_key = OPENAI_API_KEY

# Состояние для каждого пользователя
user_state = {}

@app.route(f"/{TELEGRAM_TOKEN}", methods=["POST"])
def respond():
    update_data = request.get_json(force=True)
    if not update_data:
        return "no update", 400

    update = telegram.Update.de_json(update_data, bot)
    if not update.message or not update.message.text:
        return "no message text", 200

    text = update.message.text.strip()
    chat_id = update.message.chat.id

    if chat_id not in user_state:
        user_state[chat_id] = {"stage": "start"}

    state = user_state[chat_id]

    # Этап 1: Приветствие и выбор языка
    if state["stage"] == "start":
        bot.send_message(chat_id=chat_id, text="Hi! 👋 I'm JassDispatch — your AI freight dispatcher.\n\u041f\u0440\u0438\u0432\u0435\u0442! Я JassDispatch — твой Аи-диспетчер.")
        bot.send_message(chat_id=chat_id, text="Please choose your language / Пожалуйста, выбери язык:\nEnglish или Русский")
        state["stage"] = "language"
        return "ok"

    # Этап 2: Установка языка
    if state["stage"] == "language":
        if "ru" in text.lower() or "рус" in text.lower():
            state["lang"] = "ru"
        else:
            state["lang"] = "en"
        bot.send_message(chat_id=chat_id, text="Are you a truck driver or a broker?\nТы водитель трака или брокер?")
        state["stage"] = "role"
        return "ok"

    # Этап 3: Роль
    if state["stage"] == "role":
        if "broker" in text.lower() or "брокер" in text.lower():
            state["role"] = "broker"
        else:
            state["role"] = "driver"
        bot.send_message(chat_id=chat_id, text="Got it! 🚀\nNow tell me what you need. / Теперь напиши, что тебе нужно.")
        state["stage"] = "prompt"
        return "ok"

    # Этап 4: Обработка запроса
    if state["stage"] == "prompt":
        lang = state.get("lang", "en")
        role = state.get("role", "driver")
        user_message = text

        # Базовый промпт
        base_prompt = {
            "ru": f"""Представь, что ты опытный логист-диспетчер с 10-летним стажем.
Ты свободно говоришь на русском и английском, отлично знаешь все нюансы грузоперевозок по США — законодательство, маршруты, ставки, реалии брокеров и грузоотправителей.
Ты честный, грамотный и умеешь доносить свои мысли, умеешь убеждать, продавать и ставить справедливую маржу.
Роль пользователя: {role.upper()}
Пользователь написал: \"{user_message}\"\n""",
            "en": f"""Imagine you are a seasoned freight dispatcher with 10 years of experience in the U.S.
You speak English and Russian fluently and understand all U.S. trucking laws, broker policies, and route planning.
User role: {role.upper()}
The user said: \"{user_message}\"\n"""
        }

        if role == "driver":
            base_prompt["ru"] += "Если это запрос по грузу — предложи 2-3 маршрута с городами, расстоянием, типом груза и ставкой."
            base_prompt["en"] += "If it's a freight request — suggest 2-3 realistic routes with cities, mileage, cargo type, and rate."
        else:
            base_prompt["ru"] += "Если это брокер — сгенерируй грамотный, деловой текст."
            base_prompt["en"] += "If it's a broker message — generate a convincing, professional message in business tone."

        try:
            completion = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": base_prompt[lang]}]
            )
            response_text = completion.choices[0].message.content.strip()
            bot.send_message(chat_id=chat_id, text=response_text)
        except Exception as e:
            bot.send_message(chat_id=chat_id, text="Something went wrong. Please try again later.")
            print(f"OpenAI API Error: {e}")

        return "ok"
