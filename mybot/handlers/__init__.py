# ==== bot/__init__.py ====
# Ботын үндсэн Dispatcher, Bot, Storage-уудыг тохируулах
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import API_TOKEN

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
