import os
import sys
import logging
import asyncio
import django
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime, timedelta
from openpyxl import Workbook
from io import BytesIO
import aiohttp
import requests
from telegrambot.telegram_utils3 import download_image, send_photo_as_file
from django.conf import settings
import sys
import os

# Добавляем путь к проекту в sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Настройка пути к Django проекту
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Teleshop.settings')
django.setup()

# Импортируем модели и функции
from flower_shop.models import User
from .db_controller import set_user_telegram_id, get_user_orders

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

# Клавиатуры
def get_main_keyboard(is_staff=False):
    """Возвращает основную клавиатуру для пользователя."""
    buttons = [
        [KeyboardButton(text="Перейти на сайт")],
        [KeyboardButton(text="Статус заказов")]
    ]
    if is_staff:
        buttons.append([KeyboardButton(text="Отчеты")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_start_keyboard():
    """Возвращает стартовую клавиатуру с кнопкой 'Старт'."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Старт")]],
        resize_keyboard=True
    )

def get_status_period_keyboard():
    """Возвращает инлайн-клавиатуру для выбора периода для статуса заказов."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="За сегодня", callback_data="status_period_today")],
        [InlineKeyboardButton(text="За неделю", callback_data="status_period_week")],
        [InlineKeyboardButton(text="За месяц", callback_data="status_period_month")],
        [InlineKeyboardButton(text="За все время", callback_data="status_period_all")]
    ])

def get_order_filter_keyboard():
    """Возвращает инлайн-клавиатуру для фильтрации заказов по статусу."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Все заказы", callback_data="filter_all")],
        [InlineKeyboardButton(text="Только выполненные", callback_data="filter_completed")],
        [InlineKeyboardButton(text="Только в доставке", callback_data="filter_in_delivery")],
        [InlineKeyboardButton(text="Только в работе", callback_data="filter_in_progress")],
        [InlineKeyboardButton(text="Все, кроме выполненных", callback_data="filter_all_except_completed")]
    ])

def get_report_period_keyboard():
    """Возвращает инлайн-клавиатуру для выбора периода для отчетов."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="За сегодня", callback_data="report_period_today")],
        [InlineKeyboardButton(text="За неделю", callback_data="report_period_week")],
        [InlineKeyboardButton(text="За месяц", callback_data="report_period_month")],
        [InlineKeyboardButton(text="За все время", callback_data="report_period_all")]
    ])


def get_code_input_keyboard():
    """Возвращает инлайн-клавиатуру для ввода кодового слова."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1", callback_data="code_1"),
         InlineKeyboardButton(text="2", callback_data="code_2"),
         InlineKeyboardButton(text="3", callback_data="code_3")],
        [InlineKeyboardButton(text="4", callback_data="code_4"),
         InlineKeyboardButton(text="5", callback_data="code_5"),
         InlineKeyboardButton(text="6", callback_data="code_6")],
        [InlineKeyboardButton(text="7", callback_data="code_7"),
         InlineKeyboardButton(text="8", callback_data="code_8"),
         InlineKeyboardButton(text="9", callback_data="code_9")],
        [InlineKeyboardButton(text="0", callback_data="code_0"),
         InlineKeyboardButton(text="Готово", callback_data="code_done")]
    ])

# Добавляем состояние для обработки ввода кодового слова
class AdminState(StatesGroup):
    waiting_for_code = State()

# Инициализация хранилища состояний
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Обработчик команды /yaadmin
@router.message(Command("yaadmin"))
async def handle_yaadmin(message: types.Message, state: FSMContext):
    """Обработчик команды /yaadmin. Запрашивает кодовое слово через инлайн-клавиатуру."""
    await message.answer("Введите кодовое слово, используя кнопки ниже:", reply_markup=get_code_input_keyboard())
    await state.set_state(AdminState.waiting_for_code)
    await state.update_data(code_input="")  # Инициализируем пустую строку для ввода кода

# Обработчик для проверки кодового слова
@router.message(AdminState.waiting_for_code)
async def check_admin_code(message: types.Message, state: FSMContext):
    """Обработчик для проверки кодового слова."""
    try:
        user = await sync_to_async(User.objects.get)(telegram_id=message.chat.id)
        if message.text.strip() == settings.YAADMIN_SECRET_CODE:
            user.is_staff = True
            await sync_to_async(user.save)()
            await message.answer("Поздравляем! Теперь вы администратор.", reply_markup=get_main_keyboard(is_staff=True))
        else:
            await message.answer("Неверное кодовое слово. Попробуйте еще раз.")
        await state.clear()  # Очищаем состояние после проверки
    except ObjectDoesNotExist:
        await message.answer("Ваш аккаунт не привязан. Введите код для привязки.")
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды /yaadmin: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")
        await state.clear()  # Очищаем состояние в случае ошибки

@router.message(Command("yaneadmin"))
async def handle_yaneadmin(message: types.Message):
    """Обработчик команды /yaneadmin. Снимает права администратора."""
    try:
        user = await sync_to_async(User.objects.get)(telegram_id=message.chat.id)
        if user.is_staff:
            user.is_staff = False
            await sync_to_async(user.save)()
            await message.answer("Теперь вы обычный пользователь.", reply_markup=get_main_keyboard(is_staff=False))
        else:
            await message.answer("Вы не являетесь администратором.")
    except ObjectDoesNotExist:
        await message.answer("Ваш аккаунт не привязан. Введите код для привязки.")
    except Exception as e:
        logger.error(f"Ошибка при выполнении команды /yaneadmin: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")

@router.message(Command("start"))
async def send_welcome(message: types.Message):
    """Обработчик команды /start. Приветствует пользователя."""
    await message.reply(
        "Привет! Я бот для управления заказами.\n"
        "Чтобы привязать аккаунт, нажмите кнопку 'Старт'.",
        reply_markup=get_start_keyboard()
    )

# Обработчики кнопок
@router.message(lambda message: message.text == "Старт")
async def handle_start(message: types.Message):
    """Обработчик кнопки 'Старт'. Проверяет привязку аккаунта."""
    try:
        user = await sync_to_async(User.objects.get)(telegram_id=message.chat.id)
        await message.reply(
            "Ваш аккаунт уже привязан. Что вы хотите сделать?",
            reply_markup=get_main_keyboard(is_staff=user.is_staff)
        )
    except ObjectDoesNotExist:
        # Создаем клавиатуру с кнопкой "Перейти на сайт"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Перейти на сайт", url=f"{settings.BASE_URL}")]
        ])

        # Отправляем сообщение с кнопкой
        await message.reply(
            "Ваш аккаунт не привязан. Для авторизации перейдите на сайт магазина.",
            reply_markup=keyboard
        )

@router.message(lambda message: message.text == "Статус заказов")
async def handle_status(message: types.Message):
    """Обработчик кнопки 'Статус заказов'. Показывает заказы."""
    try:
        user = await sync_to_async(User.objects.get)(telegram_id=message.chat.id)
        if user.is_staff:
            await message.answer("Выберите период для заказов:", reply_markup=get_status_period_keyboard())
        else:
            orders = await get_user_orders(user.id, is_staff=False)
            await send_orders(message, orders)
    except ObjectDoesNotExist:
        await message.answer("Ваш аккаунт не привязан. Введите код для привязки.")
    except Exception as e:
        logger.error(f"Ошибка при получении заказов: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчики для статуса заказов
@router.callback_query(lambda callback: callback.data.startswith("status_period_"))
async def handle_status_period(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик для выбора периода статуса заказов."""
    try:
        user = await sync_to_async(User.objects.get)(telegram_id=callback.message.chat.id)
        if user.is_staff:
            period = callback.data.split("_")[-1]
            end_date = datetime.now()
            start_date = {
                "today": end_date.replace(hour=0, minute=0, second=0, microsecond=0),
                "week": end_date - timedelta(days=7),
                "month": end_date - timedelta(days=30),
                "all": None
            }.get(period, None)

            await state.update_data(start_date=start_date, end_date=end_date)
            await callback.message.answer(
                f"Выбран период с {start_date.strftime('%Y-%m-%d') if start_date else 'все время'} по {end_date.strftime('%Y-%m-%d') if end_date else 'все время'}.",
                reply_markup=get_order_filter_keyboard()
            )
        else:
            await callback.message.answer("Эта функция доступна только администраторам.")
    except Exception as e:
        logger.error(f"Ошибка при выборе периода: {e}")
        await callback.message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчики для фильтрации заказов
@router.callback_query(lambda callback: callback.data.startswith("filter_"))
async def handle_filter(callback: types.CallbackQuery, state: FSMContext):
    try:
        user = await sync_to_async(User.objects.get)(telegram_id=callback.message.chat.id)
        if user.is_staff:
            data = await state.get_data()
            start_date = data.get("start_date")
            end_date = data.get("end_date")

            # Извлекаем значение фильтра корректно
            status_filter = callback.data.replace("filter_", "")

            # Логируем значение фильтра
            logger.info(f"Applying filter: {status_filter}")

            orders = await get_user_orders(user.id, is_staff=True, status_filter=status_filter, start_date=start_date,
                                           end_date=end_date)
            await send_orders(callback.message, orders)
        else:
            await callback.message.answer("Эта функция доступна только администраторам.")
    except Exception as e:
        logger.error(f"Ошибка при фильтрации заказов: {e}")
        await callback.message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")

# Функция для отправки заказов
async def send_orders(message: types.Message, orders):
    """Отправляет пользователю список заказов."""
    if orders:
        status_translation = {
            'accepted': 'Принят к работе',
            'in_progress': 'Находится в работе',
            'in_delivery': 'В доставке',
            'completed': 'Выполнен',
        }

        for order in orders:
            status = status_translation.get(order['status'], order['status'])
            address = order['address'] if order['address'] else "Самовывоз"
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
            await message.answer(response, parse_mode="HTML")

            for image_url in order['item_images']:
                if image_url:
                    try:
                        current_directory = os.path.dirname(os.path.abspath(__file__))
                        save_path = os.path.join(current_directory, f"temp_{order['id']}.jpg")
                        downloaded_file = download_image(image_url, save_path)

                        if downloaded_file and os.path.exists(downloaded_file):
                            await send_photo_as_file(message.chat.id, downloaded_file, settings.TELEGRAM_BOT_TOKEN)
                            os.remove(downloaded_file)
                            logger.info(f"Файл {downloaded_file} успешно удален")
                        else:
                            logger.error(f"Файл не найден: {downloaded_file}")
                            await message.answer(f"Не удалось загрузить изображение товара: {image_url}")
                    except Exception as e:
                        logger.error(f"Ошибка при отправке изображения: {e}")
                        await message.answer(f"Не удалось загрузить изображение товара: {image_url}")
    else:
        await message.answer("Заказов с выбранным фильтром нет.")

# Обработчик кнопки "Отчеты"
@router.message(lambda message: message.text == "Отчеты")
async def handle_reports(message: types.Message):
    """Обработчик кнопки 'Отчеты'. Показывает клавиатуру для выбора периода."""
    try:
        user = await sync_to_async(User.objects.get)(telegram_id=message.chat.id)
        if user.is_staff:
            await message.answer("Выберите период для отчета:", reply_markup=get_report_period_keyboard())
        else:
            await message.answer("Эта функция доступна только администраторам.")
    except ObjectDoesNotExist:
        await message.answer("Ваш аккаунт не привязан. Введите код для привязки.")
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса отчетов: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")

# Обработчики для отчетов
@router.callback_query(lambda callback: callback.data.startswith("report_period_"))
async def handle_report_period(callback: types.CallbackQuery):
    """Обработчик для выбора периода отчетов."""
    try:
        user = await sync_to_async(User.objects.get)(telegram_id=callback.message.chat.id)
        if user.is_staff:
            period = callback.data.split("_")[-1]
            end_date = datetime.now()
            start_date = {
                "today": end_date.replace(hour=0, minute=0, second=0, microsecond=0),
                "week": end_date - timedelta(days=7),
                "month": end_date - timedelta(days=30),
                "all": None
            }.get(period, None)

            await handle_report(callback, start_date, end_date)
        else:
            await callback.message.answer("Эта функция доступна только администраторам.")
    except Exception as e:
        logger.error(f"Ошибка при выборе периода: {e}")
        await callback.message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")

# Общий обработчик для формирования отчета
async def handle_report(callback: types.CallbackQuery, start_date, end_date):
    """Формирует отчет за выбранный период."""
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

            # Кнопка для скачивания Excel-файла
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Скачать файл Excel", callback_data=f"download_excel:{start_date.strftime('%Y-%m-%d') if start_date else 'None'}:{end_date.strftime('%Y-%m-%d') if end_date else 'None'}")]
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
    """Обработчик для скачивания Excel-файла с отчетом."""
    try:
        _, start_date_str, end_date_str = callback.data.split(":")
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str != "None" else None
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str != "None" else None

        user = await sync_to_async(User.objects.get)(telegram_id=callback.message.chat.id)
        orders = await get_user_orders(user.id, is_staff=True, start_date=start_date, end_date=end_date)

        excel_file = generate_excel_report(orders, start_date, end_date)
        await callback.message.answer_document(
            document=types.BufferedInputFile(excel_file.getvalue(), filename="report.xlsx"),
            caption="Ваш отчет в формате Excel."
        )
    except Exception as e:
        logger.error(f"Ошибка при скачивании Excel-файла: {e}")
        await callback.message.answer("Произошла ошибка при формировании файла. Пожалуйста, попробуйте позже.")

# Функция для генерации Excel-файла
def generate_excel_report(orders, start_date, end_date):
    """Генерирует Excel-файл с отчетом за выбранный период."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Отчет по заказам"

    ws.append(["Дата", "Количество заказов", "Выручка"])

    daily_stats = {}
    for order in orders:
        order_date = order['created_at'].split()[0]
        if order_date not in daily_stats:
            daily_stats[order_date] = {'total_orders': 0, 'total_revenue': 0.0}
        daily_stats[order_date]['total_orders'] += 1
        daily_stats[order_date]['total_revenue'] += float(order['total_price'])

    for date, stats in daily_stats.items():
        ws.append([date, stats['total_orders'], stats['total_revenue']])

    excel_file = BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)

    return excel_file

# Обработчик кнопки "Перейти на сайт"
@router.message(lambda message: message.text == "Перейти на сайт")
async def handle_go_to_site(message: types.Message):
    """Обработчик кнопки 'Перейти на сайт'. Отправляет ссылку для авторизации."""
    try:
        user = await sync_to_async(User.objects.get)(telegram_id=message.chat.id)
        auth_url = f"{settings.BASE_URL}/auth?telegram_id={user.telegram_id}"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Перейти на сайт", url=auth_url)]
        ])
        await message.answer(
            "Нажмите кнопку ниже, чтобы перейти на сайт и автоматически авторизоваться:",
            reply_markup=keyboard
        )
    except ObjectDoesNotExist:
        auth_url = f"{settings.BASE_URL}/"
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
    """Обработчик для привязки telegram_id по коду."""
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


@router.callback_query(lambda callback: callback.data.startswith("code_"))
async def handle_code_input(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик ввода кодового слова через инлайн-клавиатуру."""
    data = await state.get_data()
    code_input = data.get("code_input", "")

    if callback.data == "code_done":
        # Проверяем введенное кодовое слово
        if code_input == settings.YAADMIN_SECRET_CODE:
            user = await sync_to_async(User.objects.get)(telegram_id=callback.message.chat.id)
            user.is_staff = True
            await sync_to_async(user.save)()
            await callback.message.answer("Поздравляем! Теперь вы администратор.", reply_markup=get_main_keyboard(is_staff=True))
        else:
            await callback.message.answer("Неверное кодовое слово. Попробуйте еще раз.")
        await state.clear()
    else:
        # Добавляем символ к введенному коду
        code_input += callback.data.replace("code_", "")
        await state.update_data(code_input=code_input)
        await callback.answer(f"Введено: {code_input}")


@router.message(AdminState.waiting_for_code)
async def handle_code_input_cancel(message: types.Message, state: FSMContext):
    """Обработчик отмены ввода кодового слова."""
    await message.answer("Ввод кодового слова отменен.")
    await state.clear()



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