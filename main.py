import threading
import os
from flask import Flask
from config import API_TOKEN  # config.py-аас импортолно!

from aiogram import Bot, Dispatcher, executor, types

# --- DP, BOT нэг л удаа тодорхойлно! ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# === Bot handler-ууд энд ===
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.reply("Бот ажиллаж байна!")

# --- Өөрийн handlers-ийг импортлох (user/menu) ---
import mybot.handlers.user
import mybot.handlers.menu

# === Flask сервер ===
app = Flask(__name__)

@app.route("/")
def index():
    return "Bot and web server are running!"

def run_polling():
    executor.start_polling(dp, skip_updates=True)

if __name__ == "__main__":
    # Polling-oo тусдаа thread дээр ажиллуулна
    polling_thread = threading.Thread(target=run_polling)
    polling_thread.start()

    # Flask web серверээ Render-ийн шаардлагад нийцүүлэн порт дээр ажиллуулна
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
