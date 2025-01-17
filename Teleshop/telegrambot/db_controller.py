import logging
from django.core.exceptions import ObjectDoesNotExist
from flower_shop.models import User, Order
from asgiref.sync import sync_to_async
import os
from django.conf import settings
import requests
from django.utils import timezone
from telegrambot.telegram_utils3 import download_image, send_photo_as_file  # Импортируем функции для работы с изображениями

# Создаем логгер
logger = logging.getLogger(__name__)

async def send_telegram_webhook(telegram_id, message, images=None):
    try:
        # Отправляем текстовое сообщение
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": telegram_id,
            "text": message,
            "parse_mode": "HTML",
        }

        # Логируем сообщение перед отправкой
        logger.info(f"Отправка сообщения в Telegram: {message}")

        response = requests.post(url, data=data)
        if response.status_code != 200:
            logger.error(f"Ошибка при отправке сообщения: {response.text}")

        # Отправка изображений, если они есть
        if images:
            for image_url in images:
                if image_url:
                    try:
                        # Скачиваем изображение на сервер
                        current_directory = os.path.dirname(os.path.abspath(__file__))
                        save_path = os.path.join(current_directory, f"temp_{telegram_id}.jpg")
                        downloaded_file = download_image(image_url, save_path)

                        if downloaded_file and os.path.exists(downloaded_file):
                            # Отправляем изображение как файл
                            await send_photo_as_file(telegram_id, downloaded_file, settings.TELEGRAM_BOT_TOKEN)
                            os.remove(downloaded_file)
                            logger.info(f"Файл {downloaded_file} успешно удален")
                        else:
                            logger.error(f"Файл не найден: {downloaded_file}")
                    except Exception as e:
                        logger.error(f"Ошибка при отправке изображения: {e}")
    except Exception as e:
        logger.error(f"Ошибка при отправке вебхука: {e}")

@sync_to_async
def set_user_telegram_id(link_code, telegram_id):
    """
    Устанавливает Telegram ID пользователя по коду привязки.
    """
    try:
        user = User.objects.get(link_code=link_code)
        user.telegram_id = telegram_id
        user.link_code = None
        user.save()
        logger.info(f"Telegram ID {telegram_id} успешно привязан к пользователю {user.username}.")
        return True
    except ObjectDoesNotExist:
        logger.warning(f"Пользователь с кодом привязки {link_code} не найден.")
        return False
    except Exception as e:
        logger.error(f"Ошибка при обновлении Telegram ID: {e}")
        return False

@sync_to_async
def get_user_orders(user_id, is_staff=False, status_filter=None, start_date=None, end_date=None):
    try:
        user = User.objects.get(id=user_id)
        if is_staff:
            # Для администратора показываем все заказы, кроме "Новый"
            orders = Order.objects.exclude(status='new').order_by('-created_at')
        else:
            # Для обычного пользователя показываем только его заказы, исключая "Выполнен"
            orders = user.order_set.exclude(status='completed').order_by('-created_at')

        # Применяем фильтр по статусу
        if status_filter:
            if status_filter == "all":
                # "Все заказы" — исключаем заказы со статусом "Новый"
                orders = orders.exclude(status='new')
            elif status_filter == "completed":
                # "Только выполненные" — заказы со статусом "Выполнен"
                orders = orders.filter(status='completed')
            elif status_filter == "in_delivery":
                # "Только в доставке" — заказы со статусом "В доставке"
                orders = orders.filter(status='in_delivery')
            elif status_filter == "in_progress":
                # "Только в работе" — заказы со статусом "Принят к работе" и "Находится в работе"
                orders = orders.filter(status__in=['accepted', 'in_progress'])
            elif status_filter == "all_except_completed":
                # "Все, кроме выполненных" — заказы со статусом "Принят к работе", "Находится в работе" и "В доставке"
                orders = orders.filter(status__in=['accepted', 'in_progress', 'in_delivery'])

        # Фильтрация по датам
        if start_date and end_date:
            orders = orders.filter(created_at__gte=start_date, created_at__lte=end_date)

        # Формируем информацию о заказах
        orders_info = []
        for order in orders:
            items = order.items.all()
            item_list = ", ".join([f"{item.product.name} x {item.quantity}" for item in items])
            item_images = [
                f"{settings.BASE_URL}{item.product.image.url}" if item.product.image else None
                for item in items
            ]
            orders_info.append({
                "id": order.id,
                "status": order.status,
                "created_at": timezone.localtime(order.created_at).strftime("%Y-%m-%d %H:%M:%S"),
                "items": item_list,
                "total_price": order.get_total_price(),
                "address": order.address,
                "delivery_time": timezone.localtime(order.delivery_time).strftime("%Y-%m-%d %H:%M") if order.delivery_time else "Не указано",
                "item_images": item_images,
            })

        # Логируем полученные заказы
        logger.info(f"Получены заказы для пользователя {user_id}: {orders_info}")
        logger.info(f"Filter: {status_filter}, Start Date: {start_date}, End Date: {end_date}")
        logger.info(f"Number of orders before filtering: {orders.count()}")
        logger.info(f"Number of orders after filtering: {len(orders_info)}")

        return orders_info
    except ObjectDoesNotExist:
        logger.warning(f"Пользователь с ID {user_id} не найден.")
        return []
    except Exception as e:
        logger.error(f"Ошибка при получении заказов: {e}")
        return []