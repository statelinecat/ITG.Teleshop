from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, User
import logging
from django.utils import timezone
from django.conf import settings
import requests
from telegrambot.db_controller import send_telegram_webhook  # Импортируем функцию для отправки вебхуков

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Order)
def notify_user_and_admins(sender, instance, **kwargs):
    """
    Сигнал для отправки уведомлений пользователю и администраторам при изменении статуса заказа.
    """
    # Отправляем уведомления только при изменении статуса
    if instance.tracker.has_changed('status'):
        old_status = instance.tracker.previous('status')
        new_status = instance.status

        # Определяем заголовок в зависимости от изменения статуса
        if old_status == 'new' and new_status == 'accepted':
            header = "🆕 <b>Новый заказ</b>\n"
        else:
            header = "🔄 <b>Изменение статуса заказа</b>\n"

        order_items = instance.items.all()

        # Проверяем, что заказ содержит товары
        if not order_items:
            logger.warning(f"Заказ #{instance.id} не содержит товаров.")
            return
        else:
            logger.info(f"Заказ #{instance.id} содержит товары: {[item.product.name for item in order_items]}")

        # Формируем список товаров
        items_list = "\n".join([f"{item.product.name} x {item.quantity}" for item in order_items])

        # Получаем общую стоимость заказа
        total_price = instance.get_total_price()

        # Логируем сумму заказа для отладки
        logger.info(f"Сумма заказа #{instance.id}: {total_price} руб.")
        if total_price is None or total_price == 0:
            logger.warning(f"Сумма заказа #{instance.id} равна 0 или не определена.")
            return

        # Формируем список URL изображений товаров с использованием BASE_URL
        item_images = [
            f"{settings.BASE_URL}{item.product.image.url}" if item.product.image else None
            for item in order_items
        ]

        # Формируем сообщение с информацией о заказе
        message = (
            f"{header}"
            f"🛒 <b>Заказ #{instance.id}</b>\n"
            f"📊 <b>Статус:</b> {instance.get_status_display()}\n"
            f"📅 <b>Дата оформления:</b> {timezone.localtime(instance.created_at).strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"💰 <b>Сумма заказа:</b> {total_price:.2f} руб.\n"
            f"🏠 <b>Адрес доставки:</b> {instance.address if instance.address else 'Самовывоз'}\n"
            f"⏰ <b>Время доставки:</b> {timezone.localtime(instance.delivery_time).strftime('%Y-%m-%d %H:%M') if instance.delivery_time else 'Не указано'}\n"
            f"📦 <b>Товары:</b>\n{items_list}"
        )

        # Добавляем информацию об изменении статуса, если статус изменился
        if old_status != new_status:
            message += f"\n📅 <b>Статус изменен:</b> с {dict(Order.STATUS_CHOICES).get(old_status, old_status)} на {dict(Order.STATUS_CHOICES).get(new_status, new_status)}\n"

        # Формируем список получателей (пользователь и администраторы)
        recipients = []
        if instance.user.telegram_id:
            recipients.append(instance.user.telegram_id)

        admins = User.objects.filter(is_staff=True)
        for admin in admins:
            if admin.telegram_id:
                recipients.append(admin.telegram_id)

        # Отправляем уведомления через вебхуки
        for recipient in recipients:
            send_telegram_webhook(recipient, message, item_images)