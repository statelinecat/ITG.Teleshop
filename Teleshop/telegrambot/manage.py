import os
import django
from aiogram import executor
from telegrambot.bot import dp

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Teleshop.settings')
django.setup()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)