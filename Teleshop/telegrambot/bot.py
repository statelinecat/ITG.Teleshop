import os
import sys
import logging
import asyncio
import django
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext  # Импортируем FSMContext
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime, timedelta

# Добавляем путь к корневой папке проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Teleshop.settings')
django.setup()

# Импортируем модель User
from flower_shop.models import User

# Импортируем функции из db_controller.py
from telegrambot.db_controller import set_user_telegram_id, get_user_orders

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),  # Логи будут записываться в файл
        logging.StreamHandler()  # Логи будут выводиться в консоль
    ]
)
logger = logging.getLogger(__name__)

# Инициализация бота
from django.conf import settings

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

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


# Клавиатура для привязанного аккаунта
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Перейти на сайт")],
            [KeyboardButton(text="Статус заказов")]
        ],
        resize_keyboard=True
    )
    return keyboard


# Клавиатура для старта
def get_start_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Старт")]
        ],
        resize_keyboard=True
    )
    return keyboard


# Инлайн-клавиатура для выбора периода
def get_period_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="За сегодня", callback_data="period_today")],
        [InlineKeyboardButton(text="За неделю", callback_data="period_week")],
        [InlineKeyboardButton(text="За месяц", callback_data="period_month")],
        [InlineKeyboardButton(text="Все заказы", callback_data="period_all")],
        # Заменяем "Выбрать период" на "Все заказы"
    ])
    return keyboard


# Инлайн-клавиатура для фильтрации заказов
def get_order_filter_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Все заказы", callback_data="filter_all")],
        [InlineKeyboardButton(text="Только выполненные", callback_data="filter_completed")],
        [InlineKeyboardButton(text="Только в доставке", callback_data="filter_in_delivery")],
        [InlineKeyboardButton(text="Только в работе", callback_data="filter_in_progress")],
        [InlineKeyboardButton(text="Все, кроме выполненных", callback_data="filter_all_except_completed")],
    ])
    return keyboard


# Обработчик команды /start
@router.message(Command("start"))
async def send_welcome(message: types.Message):
    """
    Обработчик команды /start.
    """
    await message.reply(
        "Привет! Я бот для управления заказами.\n"
        "Чтобы привязать аккаунт, нажмите кнопку 'Старт'.",
        reply_markup=get_start_keyboard()
    )


# Обработчик кнопки "Старт"
@router.message(lambda message: message.text == "Старт")
async def handle_start(message: types.Message):
    """
    Обработчик кнопки "Старт".
    """
    try:
        # Проверяем, привязан ли аккаунт
        user = await sync_to_async(User.objects.get)(telegram_id=message.chat.id)
        if user:
            # Если аккаунт привязан, показываем основную клавиатуру
            await message.reply(
                "Ваш аккаунт уже привязан. Что вы хотите сделать?",
                reply_markup=get_main_keyboard()
            )
    except ObjectDoesNotExist:
        # Если аккаунт не привязан, просим ввести код
        await message.reply(
            "Ваш аккаунт не привязан. Введите код, который вы получили на сайте, чтобы привязать аккаунт."
        )


# Обработчик кнопки "Статус заказов"
@router.message(lambda message: message.text == "Статус заказов")
async def handle_status(message: types.Message):
    """
    Обработчик кнопки "Статус заказов".
    """
    try:
        user = await sync_to_async(User.objects.get)(telegram_id=message.chat.id)
        if user.is_staff:
            # Если пользователь администратор, показываем клавиатуру для выбора периода
            await message.answer("Выберите период для заказов:", reply_markup=get_period_keyboard())
        else:
            # Если пользователь не администратор, показываем его заказы
            orders = await get_user_orders(user.id, is_staff=False)
            await send_orders(message, orders)
    except ObjectDoesNotExist:
        await message.answer("Ваш аккаунт не привязан. Введите код для привязки.")
    except Exception as e:
        logger.error(f"Ошибка при получении заказов: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")


# Обработчик для выбора периода "За сегодня"
@router.callback_query(lambda callback: callback.data == "period_today")
async def handle_period_today(callback: types.CallbackQuery, state: FSMContext):
    end_date = datetime.now()
    start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    await handle_period(callback, start_date, end_date, state)


# Обработчик для выбора периода "За неделю"
@router.callback_query(lambda callback: callback.data == "period_week")
async def handle_period_week(callback: types.CallbackQuery, state: FSMContext):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    await handle_period(callback, start_date, end_date, state)


# Обработчик для выбора периода "За месяц"
@router.callback_query(lambda callback: callback.data == "period_month")
async def handle_period_month(callback: types.CallbackQuery, state: FSMContext):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    await handle_period(callback, start_date, end_date, state)


# Обработчик для выбора периода "Все заказы"
@router.callback_query(lambda callback: callback.data == "period_all")
async def handle_period_all(callback: types.CallbackQuery, state: FSMContext):
    await handle_period(callback, start_date=None, end_date=None, state=state)


# Общий обработчик для выбора периода
async def handle_period(callback_or_message, start_date, end_date, state: FSMContext):
    """
    Общий обработчик для выбора периода.
    """
    try:
        user = await sync_to_async(User.objects.get)(telegram_id=callback_or_message.message.chat.id)
        # Сохраняем выбранный период в состоянии пользователя
        await state.update_data(start_date=start_date, end_date=end_date)

        # Показываем клавиатуру для фильтрации по статусу
        await callback_or_message.message.answer(
            f"Выбран период с {start_date.strftime('%Y-%m-%d') if start_date else 'все время'} по {end_date.strftime('%Y-%m-%d') if end_date else 'все время'}.",
            reply_markup=get_order_filter_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при выборе периода: {e}")
        await callback_or_message.message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")


# Обработчик для фильтра "Все заказы"
@router.callback_query(lambda callback: callback.data == "filter_all")
async def handle_filter_all(callback: types.CallbackQuery, state: FSMContext):
    await handle_filter(callback, status_filter=None, state=state)


# Обработчик для фильтра "Только выполненные"
@router.callback_query(lambda callback: callback.data == "filter_completed")
async def handle_filter_completed(callback: types.CallbackQuery, state: FSMContext):
    await handle_filter(callback, status_filter="completed", state=state)


# Обработчик для фильтра "Только в доставке"
@router.callback_query(lambda callback: callback.data == "filter_in_delivery")
async def handle_filter_in_delivery(callback: types.CallbackQuery, state: FSMContext):
    await handle_filter(callback, status_filter="in_delivery", state=state)


# Обработчик для фильтра "Только в работе"
@router.callback_query(lambda callback: callback.data == "filter_in_progress")
async def handle_filter_in_progress(callback: types.CallbackQuery, state: FSMContext):
    await handle_filter(callback, status_filter="in_progress", state=state)


# Обработчик для фильтра "Все, кроме выполненных"
@router.callback_query(lambda callback: callback.data == "filter_all_except_completed")
async def handle_filter_all_except_completed(callback: types.CallbackQuery, state: FSMContext):
    await handle_filter(callback, status_filter="all_except_completed", state=state)


# Общий обработчик для фильтрации заказов
async def handle_filter(callback: types.CallbackQuery, status_filter=None, state: FSMContext = None):
    """
    Общий обработчик для фильтрации заказов.
    """
    try:
        user = await sync_to_async(User.objects.get)(telegram_id=callback.message.chat.id)
        # Получаем выбранный период из состояния пользователя
        data = await state.get_data()
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        orders = await get_user_orders(user.id, is_staff=user.is_staff, status_filter=status_filter,
                                       start_date=start_date, end_date=end_date)
        await send_orders(callback.message, orders)
    except Exception as e:
        logger.error(f"Ошибка при фильтрации заказов: {e}")
        await callback.message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")


# Функция для отправки заказов
async def send_orders(message: types.Message, orders):
    """
    Отправляет заказы пользователю.
    """
    if orders:
        # Словарь для перевода статусов
        status_translation = {
            'accepted': 'Принят к работе',
            'in_progress': 'Находится в работе',
            'in_delivery': 'В доставке',
            'completed': 'Выполнен',
        }

        for order in orders:
            # Преобразуем статус заказа
            status = status_translation.get(order['status'], order['status'])
            # Проверяем адрес доставки
            address = order['address'] if order['address'] else "Самовывоз"
            # Формируем текстовое сообщение с улучшенным форматированием
            response = (
                f"🛒 <b>Заказ #{order['id']}</b>\n"
                f"📊 <b>Статус:</b> {status}\n"
                f"📅 <b>Дата оформления:</b> {order['created_at']}\n"
                f"💰 <b>Сумма заказа:</b> {order['total_price']:.2f} руб.\n"
                f"🏠 <b>Адрес доставки:</b> {address}\n"
                f"⏰ <b>Время доставки:</b> {order['delivery_time']}\n"
                f"📦 <b>Товары:</b>\n"
                f"{order['items'].replace(', ', '\n')}\n"
            )
            # Отправляем текстовое сообщение с HTML-разметкой
            await message.answer(response, parse_mode="HTML")

            # Отправляем изображения товаров
            for image_url in order['item_images']:
                if image_url:  # Проверяем, что URL не пустой
                    try:
                        await message.answer_photo(image_url)
                    except Exception as e:
                        logger.error(f"Ошибка при отправке изображения: {e}")
                        await message.answer(f"Не удалось загрузить изображение товара: {image_url}")
    else:
        await message.answer("Заказов с выбранным фильтром нет.")


# Обработчик кнопки "Перейти на сайт"
@router.message(lambda message: message.text == "Перейти на сайт")
async def handle_go_to_site(message: types.Message):
    """
    Обработчик кнопки "Перейти на сайт".
    """
    try:
        user = await sync_to_async(User.objects.get)(telegram_id=message.chat.id)

        # Формируем ссылку для авторизации с Telegram ID
        auth_url = f"http://127.0.0.1:8000/auth?telegram_id={user.telegram_id}"

        # Создаем кнопку с ссылкой
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Перейти на сайт", url=auth_url)]
        ])

        # Отправляем сообщение с кнопкой
        await message.answer(
            "Нажмите кнопку ниже, чтобы перейти на сайт и автоматически авторизоваться:",
            reply_markup=keyboard
        )
    except ObjectDoesNotExist:
        # Если Telegram ID не привязан, отправляем ссылку на главную страницу
        auth_url = "http://127.0.0.1:8000/"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Перейти на сайт", url=auth_url)]
        ])
        await message.answer(
            "Ваш аккаунт не привязан. Нажмите кнопку ниже, чтобы перейти на сайт:",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Ошибка при генерации ссылки: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")


# Обработчик для привязки telegram_id
@router.message()
async def handle_code(message: types.Message):
    """
    Обработчик для привязки telegram_id.
    """
    code = message.text.strip()
    try:
        # Используем функцию из db_controller.py для привязки Telegram ID
        success = await set_user_telegram_id(code, message.chat.id)
        if success:
            await message.reply(
                "Ваш аккаунт успешно привязан! Теперь вы будете получать уведомления.",
                reply_markup=get_main_keyboard()
            )
            logger.info(f"Пользователь привязал Telegram ID: {message.chat.id}")
        else:
            await message.reply("Неверный код. Попробуйте еще раз.")
            logger.warning(f"Неверный код привязки: {code}")
    except Exception as e:
        logger.error(f"Ошибка при привязке аккаунта: {e}")
        await message.reply("Произошла ошибка. Пожалуйста, попробуйте позже.")


# Подключаем роутер к диспетчеру
dp.include_router(router)


# Запуск бота
async def main():
    try:
        logger.info("Запуск бота...")
        await dp.start_polling(bot)  # Используем await для асинхронного вызова
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")


if __name__ == '__main__':
    asyncio.run(main())  # Запускаем асинхронный код