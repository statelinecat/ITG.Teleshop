from datetime import datetime

from .models import Cart


# def working_time(request):
#     """
#     Контекстный процессор для проверки рабочего времени.
#     Возвращает True, если текущее время в рабочем интервале (Пн-Пт, 9:00-18:00).
#     """
#     now = datetime.now()
#     is_working_time = now.weekday() < 5 and 9 <= now.hour < 18  # Пн-Пт (0-4), 9:00-18:00
#     return {
#         'is_working_time': is_working_time,
#     }


def working_time(request):
    """
    Контекстный процессор для проверки рабочего времени.
    Для тестирования всегда возвращает False.
    """
    return {
        'is_working_time': True,  # Для тестирования
    }

def cart_quantity(request):
    """
    Контекстный процессор для передачи количества товаров в корзине.
    """
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            return {'cart_quantity': cart.get_total_quantity()}
    return {'cart_quantity': 0}