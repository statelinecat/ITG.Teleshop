import logging
from django.core.exceptions import ObjectDoesNotExist
from flower_shop.models import User, Order  # Импортируем модели Django
from asgiref.sync import sync_to_async  # Импортируем sync_to_async
import os
import django
from django.conf import settings

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Teleshop.settings')
django.setup()

logger = logging.getLogger(__name__)

@sync_to_async
def set_user_telegram_id(link_code, telegram_id):
    """
    Устанавливает Telegram ID пользователя по коду привязки.
    """
    try:
        user = User.objects.get(link_code=link_code)  # Ищем пользователя по link_code
        user.telegram_id = telegram_id
        user.link_code = None  # Удаляем код после привязки
        user.save()
        logger.info(f"Telegram ID {telegram_id} успешно привязан к пользователю {user.username}.")
        return True
    except ObjectDoesNotExist:
        logger.warning(f"Пользователь с кодом привязки {link_code} не найден.")  # Логируем как предупреждение
        return False
    except Exception as e:
        logger.error(f"Ошибка при обновлении Telegram ID: {e}")
        return False

@sync_to_async
def get_user_orders(user_id, is_staff=False, status_filter=None, start_date=None, end_date=None):
    """
    Получает заказы пользователя по его ID.
    Если пользователь администратор (is_staff=True), возвращает все заказы, включая выполненные.
    Если пользователь не администратор, возвращает только его заказы, исключая выполненные.
    Параметр status_filter позволяет фильтровать заказы по статусу.
    Параметры start_date и end_date позволяют фильтровать заказы по дате.
    """
    try:
        user = User.objects.get(id=user_id)
        if is_staff:
            # Для администраторов возвращаем все заказы
            orders = Order.objects.all().order_by('-created_at')
        else:
            # Для обычных пользователей возвращаем только их заказы, исключая выполненные
            orders = user.order_set.exclude(status='completed').order_by('-created_at')

        # Применяем фильтр по статусу, если он указан
        if status_filter:
            if status_filter == "all_except_completed":
                orders = orders.exclude(status='completed')
            else:
                orders = orders.filter(status=status_filter)

        # Применяем фильтр по датам, если они указаны
        if start_date and end_date:
            orders = orders.filter(created_at__gte=start_date, created_at__lte=end_date)

        orders_info = []
        for order in orders:
            items = order.items.all()  # Получаем связанные товары
            item_list = ", ".join([f"{item.product.name} x {item.quantity}" for item in items])
            # Получаем полные URL изображений товаров
            item_images = [
                f"https://1ad0-185-21-13-3.ngrok-free.app{item.product.image.url}" if item.product.image else None
                for item in items
            ]
            orders_info.append({
                "id": order.id,
                "status": order.status,
                "created_at": order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "items": item_list,
                "total_price": order.get_total_price(),  # Сумма заказа
                "address": order.address,  # Адрес доставки
                "delivery_time": order.delivery_time.strftime("%Y-%m-%d %H:%M") if order.delivery_time else "Не указано",  # Время доставки
                "item_images": item_images,  # Список полных URL изображений товаров
            })
        return orders_info
    except ObjectDoesNotExist:
        logger.warning(f"Пользователь с ID {user_id} не найден.")  # Логируем как предупреждение
        return []
    except Exception as e:
        logger.error(f"Ошибка при получении заказов: {e}")
        return []