import threading
import os
from flask import Flask
from config import API_TOKEN

import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)  # ЗӨВХӨН ингэж нэг удаа үүсгэнэ!

import mybot.handlers.user
import mybot.handlers.menu

# Flask сервер
app = Flask(__name__)

@app.route("/")
def index():
    return "Your service is live"

def run_polling():
    loop = asyncio.new_event_loop()    # <<< Шинэ event loop-оо thread дээр үүсгэнэ
    asyncio.set_event_loop(loop)       # <<< loop-оо thread-д тохируулна
    executor.start_polling(dp, skip_updates=True)

if __name__ == "__main__":
    polling_thread = threading.Thread(target=run_polling)
    polling_thread.start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
