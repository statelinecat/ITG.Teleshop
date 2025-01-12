from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from django.conf import settings
from aiogram import Bot

# Ленивая инициализация бота
def get_bot():
    """
    Возвращает экземпляр бота. Инициализация происходит только при первом вызове.
    """
    if not hasattr(get_bot, "bot"):
        get_bot.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    return get_bot.bot

@receiver(post_save, sender=Order)
def notify_user(sender, instance, **kwargs):
    """
    Отправляет уведомление пользователю через Telegram при изменении статуса заказа.
    """
    if instance.user.telegram_id:
        bot = get_bot()  # Получаем экземпляр бота
        try:
            bot.send_message(instance.user.telegram_id, f"Статус вашего заказа #{instance.id} изменен на {instance.status}")
        except Exception as e:
            # Логируем ошибку, если не удалось отправить сообщение
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Ошибка при отправке уведомления: {e}")