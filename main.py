# ==== main.py ====
# Ботын ажиллуулалт
from aiogram import executor
from mybot import dp
import mybot.handlers.user
import mybot.handlers.menu


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
