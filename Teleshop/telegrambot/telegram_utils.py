import os
import sys
import django
import requests
import time

# Добавляем путь к проекту в PYTHONPATH
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# Инициализация Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Teleshop.settings')
django.setup()

from django.conf import settings

def get_chat_id(bot_token):
    """
    Получает chat_id из последнего сообщения, отправленного боту.
    """
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    time.sleep(2)  # Задержка для обработки сообщения
    response = requests.get(url)
    updates = response.json()
    print(updates)  # Логируем ответ от API
    if updates["ok"] and updates["result"]:
        last_update = updates["result"][-1]  # Берем последнее обновление
        if "message" in last_update:
            chat_id = last_update["message"]["chat"]["id"]
            # Устанавливаем offset для подтверждения обработки обновлений
            update_id = last_update["update_id"]
            requests.get(f"{url}?offset={update_id + 1}")
            return chat_id
    return None

# Остальной код остается без изменений

# Остальной код остается без изменений

def send_photo_to_telegram(chat_id, image_url):
    """
    Отправляет изображение в Telegram.
    """
    bot_token = settings.TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    data = {
        "chat_id": chat_id,  # ID чата, куда отправлять изображение
        "photo": image_url,  # URL изображения
    }
    response = requests.post(url, data=data)
    return response.json()  # Возвращает ответ от Telegram API

# Код для запуска скрипта
if __name__ == "__main__":
    bot_token = settings.TELEGRAM_BOT_TOKEN
    chat_id = get_chat_id(bot_token)

    if chat_id:
        print(f"Chat ID: {chat_id}")
        image_url = "http://176.108.248.61/media/products/photo_2025-01-08_20-23-59_2.jpg"
        response = send_photo_to_telegram(chat_id, image_url)
        print(response)
    else:
        print("Не удалось получить chat_id. Убедитесь, что бот получил сообщение.")
        print("Отправьте любое сообщение боту в Telegram и запустите скрипт снова.")