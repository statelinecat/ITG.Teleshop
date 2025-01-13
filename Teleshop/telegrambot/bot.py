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
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime, timedelta
from openpyxl import Workbook
from io import BytesIO

# Настройка пути к Django проекту
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Teleshop.settings')
django.setup()

# Импортируем модели и функции
from flower_shop.models import User
from telegrambot.db_controller import set_user_telegram_id, get_user_orders

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),  # Логи в файл
        logging.StreamHandler()  # Логи в консоль
    ]
)
logger = logging.getLogger(__name__)

# Инициализация бота
from django.conf import settings
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

# Инициализация диспетчера и роутера
dp = Dispatcher()
router = Router()

# Middleware для логирования входящих обновлений
class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        logger.info(f"Received update: {event}")
        return await handler(event, data)

# Установка middleware
dp.update.outer_middleware(LoggingMiddleware())

# Клавиатура для привязанного аккаунта
def get_main_keyboard(is_staff=False):
    """
    Возвращает основную клавиатуру для пользователя.
    Если пользователь администратор, добавляется кнопка "Отчеты".
    """
    buttons = [
        [KeyboardButton(text="Перейти на сайт")],
        [KeyboardButton(text="Статус заказов")]
    ]
    if is_staff:
        buttons.append([KeyboardButton(text="Отчеты")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# Клавиатура для старта
def get_start_keyboard():
    """
    Возвращает стартовую клавиатуру с кнопкой "Старт".
    """
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Старт")]],
        resize_keyboard=True
    )

# Инлайн-клавиатура для выбора периода
def get_period_keyboard():
    """
    Возвращает инлайн-клавиатуру для выбора периода.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="За сегодня", callback_data="period_today")],
        [InlineKeyboardButton(text="За неделю", callback_data="period_week")],
        [InlineKeyboardButton(text="За месяц", callback_data="period_month")],
        [InlineKeyboardButton(text="За все время", callback_data="period_all")]
    ])

# Инлайн-клавиатура для фильтрации заказов
def get_order_filter_keyboard():
    """
    Возвращает инлайн-клавиатуру для фильтрации заказов по статусу.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Все заказы", callback_data="filter_all")],
        [InlineKeyboardButton(text="Только выполненные", callback_data="filter_completed")],
        [InlineKeyboardButton(text="Только в доставке", callback_data="filter_in_delivery")],
        [InlineKeyboardButton(text="Только в работе", callback_data="filter_in_progress")],
        [InlineKeyboardButton(text="Все, кроме выполненных", callback_data="filter_all_except_completed")]
    ])

# Обработчик команды /start
@router.message(Command("start"))
async def send_welcome(message: types.Message):
    """
    Обработчик команды /start.
    Приветствует пользователя и предлагает начать работу.
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
    Проверяет, привязан ли аккаунт, и предлагает ввести код привязки.
    """
    try:
        user = await sync_to_async(User.objects.get)(telegram_id=message.chat.id)
        await message.reply(
            "Ваш аккаунт уже привязан. Что вы хотите сделать?",
            reply_markup=get_main_keyboard(is_staff=user.is_staff)
        )
    except ObjectDoesNotExist:
        await message.reply(
            "Ваш аккаунт не привязан. Введите код, который вы получили на сайте, чтобы привязать аккаунт."
        )

# Обработчик кнопки "Статус заказов"
@router.message(lambda message: message.text == "Статус заказов")
async def handle_status(message: types.Message):
    """
    Обработчик кнопки "Статус заказов".
    Показывает статус заказов пользователя или администратора.
    """
    try:
        user = await sync_to_async(User.objects.get)(telegram_id=message.chat.id)
        if user.is_staff:
            await message.answer("Выберите период для заказов:", reply_markup=get_period_keyboard())
        else:
            orders = await get_user_orders(user.id, is_staff=False)
            await send_orders(message, orders)
    except ObjectDoesNotExist:
        await message.answer("Ваш аккаунт не привязан. Введите код для привязки.")
    except Exception as e:
        logger.error(f"Ошибка при получении заказов: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик кнопки "Отчеты"
@router.message(lambda message: message.text == "Отчеты")
async def handle_reports(message: types.Message):
    """
    Обработчик кнопки "Отчеты".
    Показывает клавиатуру для выбора периода отчета.
    """
    try:
        user = await sync_to_async(User.objects.get)(telegram_id=message.chat.id)
        if user.is_staff:
            await message.answer("Выберите период для отчета:", reply_markup=get_period_keyboard())
        else:
            await message.answer("Эта функция доступна только администраторам.")
    except ObjectDoesNotExist:
        await message.answer("Ваш аккаунт не привязан. Введите код для привязки.")
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса отчетов: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик для выбора периода "За сегодня"
@router.callback_query(lambda callback: callback.data == "period_today")
async def handle_period_today(callback: types.CallbackQuery, state: FSMContext):
    end_date = datetime.now()
    start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    await handle_report(callback, start_date, end_date)

# Обработчик для выбора периода "За неделю"
@router.callback_query(lambda callback: callback.data == "period_week")
async def handle_period_week(callback: types.CallbackQuery, state: FSMContext):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    await handle_report(callback, start_date, end_date)

# Обработчик для выбора периода "За месяц"
@router.callback_query(lambda callback: callback.data == "period_month")
async def handle_period_month(callback: types.CallbackQuery, state: FSMContext):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    await handle_report(callback, start_date, end_date)

# Обработчик для выбора периода "За все время"
@router.callback_query(lambda callback: callback.data == "period_all")
async def handle_period_all(callback: types.CallbackQuery, state: FSMContext):
    await handle_report(callback, start_date=None, end_date=None)

# Общий обработчик для формирования отчета
async def handle_report(callback: types.CallbackQuery, start_date, end_date):
    """
    Общий обработчик для формирования отчета за выбранный период.
    """
    try:
        user = await sync_to_async(User.objects.get)(telegram_id=callback.message.chat.id)
        if user.is_staff:
            orders = await get_user_orders(user.id, is_staff=True, start_date=start_date, end_date=end_date)
            total_orders = len(orders)
            total_revenue = sum(float(order['total_price']) for order in orders)

            report_message = (
                f"📊 <b>Отчет за период:</b>\n"
                f"📅 <b>Начало:</b> {start_date.strftime('%Y-%m-%d') if start_date else 'все время'}\n"
                f"📅 <b>Конец:</b> {end_date.strftime('%Y-%m-%d') if end_date else 'все время'}\n"
                f"🛒 <b>Общее количество заказов:</b> {total_orders}\n"
                f"💰 <b>Общая выручка:</b> {total_revenue:.2f} руб.\n"
            )

            # Преобразуем даты в строки для callback_data
            start_date_str = start_date.strftime('%Y-%m-%d') if start_date else "None"
            end_date_str = end_date.strftime('%Y-%m-%d') if end_date else "None"

            # Кнопка для скачивания Excel-файла
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Скачать файл Excel", callback_data=f"download_excel:{start_date_str}:{end_date_str}")]
            ])

            await callback.message.answer(report_message, parse_mode="HTML", reply_markup=keyboard)

            if orders:
                daily_stats = {}
                for order in orders:
                    order_date = order['created_at'].split()[0]
                    if order_date not in daily_stats:
                        daily_stats[order_date] = {'total_orders': 0, 'total_revenue': 0.0}
                    daily_stats[order_date]['total_orders'] += 1
                    daily_stats[order_date]['total_revenue'] += float(order['total_price'])

                daily_report = "📅 <b>Детализация по дням:</b>\n"
                for date, stats in daily_stats.items():
                    daily_report += (
                        f"📅 <b>{date}</b>\n"
                        f"🛒 <b>Заказов:</b> {stats['total_orders']}\n"
                        f"💰 <b>Выручка:</b> {stats['total_revenue']:.2f} руб.\n\n"
                    )

                await callback.message.answer(daily_report, parse_mode="HTML")
            else:
                await callback.message.answer("Заказов за выбранный период нет.")
        else:
            await callback.message.answer("Эта функция доступна только администраторам.")
    except Exception as e:
        logger.error(f"Ошибка при формировании отчета: {e}")
        await callback.message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчик для скачивания Excel-файла
@router.callback_query(lambda callback: callback.data.startswith("download_excel"))
async def handle_download_excel(callback: types.CallbackQuery):
    """
    Обработчик для скачивания Excel-файла с отчетом.
    """
    try:
        # Получаем даты из callback_data
        _, start_date_str, end_date_str = callback.data.split(":")

        # Преобразуем строки обратно в datetime
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str != "None" else None
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str != "None" else None

        # Получаем заказы за выбранный период
        user = await sync_to_async(User.objects.get)(telegram_id=callback.message.chat.id)
        orders = await get_user_orders(user.id, is_staff=True, start_date=start_date, end_date=end_date)

        # Генерируем Excel-файл
        excel_file = generate_excel_report(orders, start_date, end_date)

        # Отправляем файл пользователю
        await callback.message.answer_document(
            document=types.BufferedInputFile(excel_file.getvalue(), filename="report.xlsx"),
            caption="Ваш отчет в формате Excel."
        )
    except Exception as e:
        logger.error(f"Ошибка при скачивании Excel-файла: {e}")
        await callback.message.answer("Произошла ошибка при формировании файла. Пожалуйста, попробуйте позже.")

# Функция для генерации Excel-файла
def generate_excel_report(orders, start_date, end_date):
    """
    Генерирует Excel-файл с отчетом за выбранный период.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Отчет по заказам"

    # Заголовки столбцов
    ws.append(["Дата", "Количество заказов", "Выручка"])

    # Заполняем данные
    daily_stats = {}
    for order in orders:
        order_date = order['created_at'].split()[0]
        if order_date not in daily_stats:
            daily_stats[order_date] = {'total_orders': 0, 'total_revenue': 0.0}
        daily_stats[order_date]['total_orders'] += 1
        daily_stats[order_date]['total_revenue'] += float(order['total_price'])

    for date, stats in daily_stats.items():
        ws.append([date, stats['total_orders'], stats['total_revenue']])

    # Сохраняем файл в BytesIO
    excel_file = BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)

    return excel_file

# Обработчик кнопки "Перейти на сайт"
@router.message(lambda message: message.text == "Перейти на сайт")
async def handle_go_to_site(message: types.Message):
    """
    Обработчик кнопки "Перейти на сайт".
    Отправляет пользователю ссылку для авторизации на сайте.
    """
    try:
        user = await sync_to_async(User.objects.get)(telegram_id=message.chat.id)
        auth_url = f"http://127.0.0.1:8000/auth?telegram_id={user.telegram_id}"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Перейти на сайт", url=auth_url)]
        ])
        await message.answer(
            "Нажмите кнопку ниже, чтобы перейти на сайт и автоматически авторизоваться:",
            reply_markup=keyboard
        )
    except ObjectDoesNotExist:
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
    Привязывает Telegram ID пользователя по коду.
    """
    code = message.text.strip()
    try:
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
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    asyncio.run(main())