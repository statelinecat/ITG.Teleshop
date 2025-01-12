import os
import sys
import logging
import django
from aiogram import Dispatcher, types
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram import Router
from aiogram.filters import Command

# Добавляем путь к корневой папке проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Teleshop.settings')
django.setup()

from flower_shop.models import User  # Импортируем модель User
from telegrambot.bot_instance import bot  # Импортируем бота из отдельного модуля

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Инициализация диспетчера и роутера
dp = Dispatcher()
router = Router()

# Кастомный middleware для логирования
class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        logger.info(f"Received update: {event}")
        return await handler(event, data)

# Установка middleware
middleware = LoggingMiddleware()
dp.update.outer_middleware(middleware)

# Команда /start
@router.message(Command("start"))
async def send_welcome(message: types.Message):
    """
    Обработчик команды /start.
    """
    await message.reply(
        "Привет! Я бот для управления заказами.\n"
        "Чтобы привязать аккаунт, введите код, который вы получили на сайте."
    )

# Обработчик для привязки telegram_id
@router.message()
async def handle_code(message: types.Message):
    """
    Обработчик для привязки telegram_id.
    """
    code = message.text.strip()
    try:
        # Ищем пользователя с таким кодом
        user = User.objects.get(link_code=code)
        # Привязываем telegram_id
        user.telegram_id = message.chat.id
        user.link_code = None  # Удаляем код после привязки
        user.save()
        await message.reply("Ваш аккаунт успешно привязан! Теперь вы будете получать уведомления.")
        logger.info(f"Пользователь {user.username} привязал Telegram ID: {message.chat.id}")
    except User.DoesNotExist:
        await message.reply("Неверный код. Попробуйте еще раз.")
        logger.warning(f"Неверный код привязки: {code}")
    except Exception as e:
        logger.error(f"Ошибка при привязке аккаунта: {e}")
        await message.reply("Произошла ошибка. Пожалуйста, попробуйте позже.")

# Подключаем роутер к диспетчеру
dp.include_router(router)

# Запуск бота
if __name__ == '__main__':
    try:
        logger.info("Запуск бота...")
        dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")