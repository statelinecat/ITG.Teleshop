from django.db.models.signals import post_save
from django.dispatch import receiver
from flower_shop.models import Order
from telegrambot.bot import bot

@receiver(post_save, sender=Order)
def notify_user(sender, instance, **kwargs):
    if instance.user.telegram_id:
        bot.send_message(instance.user.telegram_id, f"Статус вашего заказа #{instance.id} изменен на {instance.status}")