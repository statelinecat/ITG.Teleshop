import os
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.middlewares.base import BaseMiddleware  # Правильный импорт для aiogram 3.x
from aiogram import Router  # Импортируем Router
from aiogram.filters import Command  # Импортируем Command для фильтрации команд
from django.conf import settings

# Инициализация бота
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()  # Создаем Dispatcher без аргументов
router = Router()  # Создаем Router

# Кастомный middleware для логирования
class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        # Логируем входящее обновление
        print(f"Received update: {event}")
        # Продолжаем обработку обновления
        return await handler(event, data)

# Установка middleware
middleware = LoggingMiddleware()
dp.update.outer_middleware(middleware)  # Используем outer_middleware для настройки middleware

# Команда /start
@router.message(Command("start"))  # Используем Command для фильтрации команды /start
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я бот для управления заказами.")

# Команда /orders
@router.message(Command("orders"))  # Используем Command для фильтрации команды /orders
async def get_orders(message: types.Message):
    # Здесь будет логика получения заказов из базы данных Django
    orders = "Список заказов будет здесь"
    await message.reply(orders, parse_mode="Markdown")

# Подключаем роутер к диспетчеру
dp.include_router(router)

# Запуск бота
if __name__ == '__main__':
    dp.start_polling(bot)  # Передаем бота в start_polling