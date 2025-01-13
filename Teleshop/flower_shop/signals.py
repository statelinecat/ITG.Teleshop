from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, User
from django.conf import settings
from aiogram import Bot
import asyncio
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

# Ленивая инициализация бота
def get_bot():
    if not hasattr(get_bot, "bot"):
        get_bot.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    return get_bot.bot

async def send_notification(bot, telegram_id, message, images):
    try:
        await bot.send_message(telegram_id, message, parse_mode="HTML")
        for image_url in images:
            if image_url:
                try:
                    await bot.send_photo(telegram_id, image_url)
                except Exception as e:
                    logger.error(f"Ошибка при отправке изображения: {e}")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления: {e}")

@receiver(post_save, sender=Order)
def notify_user_and_admins(sender, instance, **kwargs):
    if kwargs.get('created') or instance.tracker.has_changed('status'):
        bot = get_bot()
        header = "🆕 <b>Новый заказ</b>\n" if kwargs.get('created') else "🔄 <b>Изменение статуса заказа</b>\n"
        order_items = instance.items.all()
        items_list = "\n".join([f"{item.product.name} x {item.quantity}" for item in order_items])
        total_price = instance.get_total_price()
        item_images = [
            f"https://1ad0-185-21-13-3.ngrok-free.app{item.product.image.url}" if item.product.image else None
            for item in order_items
        ]

        message = (
            f"{header}"
            f"🛒 <b>Заказ #{instance.id}</b>\n"
            f"📊 <b>Статус:</b> {instance.get_status_display()}\n"
            f"📅 <b>Дата оформления:</b> {instance.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"💰 <b>Сумма заказа:</b> {total_price:.2f} руб.\n"
            f"🏠 <b>Адрес доставки:</b> {instance.address if instance.address else 'Самовывоз'}\n"
            f"⏰ <b>Время доставки:</b> {instance.delivery_time.strftime('%Y-%m-%d %H:%M') if instance.delivery_time else 'Не указано'}\n"
            f"📦 <b>Товары:</b>\n{items_list}"
        )

        if instance.tracker.has_changed('status'):
            old_status = instance.tracker.previous('status')
            new_status = instance.status
            message += f"📅 <b>Статус изменен с:</b> {old_status} на {new_status}\n"

        recipients = []
        if instance.user.telegram_id:
            recipients.append(instance.user.telegram_id)

        admins = User.objects.filter(is_staff=True)
        for admin in admins:
            if admin.telegram_id:
                recipients.append(admin.telegram_id)

        # Создаем новый event loop, если его нет
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError as e:
            if str(e).startswith("There is no current event loop in thread"):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            else:
                raise

        # Используем event loop для выполнения асинхронных задач
        tasks = [send_notification(bot, recipient, message, item_images) for recipient in recipients]
        loop.run_until_complete(asyncio.gather(*tasks))