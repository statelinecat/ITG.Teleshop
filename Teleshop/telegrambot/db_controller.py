import logging
from django.core.exceptions import ObjectDoesNotExist
from flower_shop.models import User, Order
from asgiref.sync import sync_to_async
import os
from django.conf import settings
import requests
from django.utils import timezone

# Создаем логгер
logger = logging.getLogger(__name__)

def send_telegram_webhook(telegram_id, message, images=None):
    """
    Отправляет уведомление в Telegram через вебхук.
    """
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": telegram_id,
        "text": message,
        "parse_mode": "HTML",
    }

    # Логируем сообщение перед отправкой
    logger.info(f"Отправка сообщения в Telegram: {message}")

    try:
        response = requests.post(url, data=data)
        if response.status_code != 200:
            logger.error(f"Ошибка при отправке сообщения: {response.text}")

        # Отправка изображений, если они есть
        if images:
            for image_url in images:
                if image_url:
                    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendPhoto"
                    data = {
                        "chat_id": telegram_id,
                        "photo": image_url,
                    }
                    response = requests.post(url, data=data)
                    if response.status_code != 200:
                        logger.error(f"Ошибка при отправке изображения: {response.text}")
    except Exception as e:
        logger.error(f"Ошибка при отправке вебхука: {e}")

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Teleshop.settings')

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
            orders = Order.objects.all().order_by('-created_at')
        else:
            orders = user.order_set.exclude(status='completed').order_by('-created_at')

        if status_filter:
            if status_filter == "all_except_completed":
                orders = orders.exclude(status='completed')
            else:
                orders = orders.filter(status=status_filter)

        if start_date and end_date:
            orders = orders.filter(created_at__gte=start_date, created_at__lte=end_date)

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

        return orders_info
    except ObjectDoesNotExist:
        logger.warning(f"Пользователь с ID {user_id} не найден.")
        return []
    except Exception as e:
        logger.error(f"Ошибка при получении заказов: {e}")
        return []