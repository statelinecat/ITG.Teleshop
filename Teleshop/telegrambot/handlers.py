from aiogram import types
from flower_shop.models import Order

async def get_orders(message: types.Message):
    orders = Order.objects.all()
    response = "Список заказов:\n"
    for order in orders:
        response += f"Заказ #{order.id} - {order.status}\n"
    await message.reply(response)