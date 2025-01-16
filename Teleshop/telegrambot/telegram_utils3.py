import requests
import os
import asyncio

def download_image(image_url, save_path):
    """
    Скачивает изображение по URL и сохраняет его на сервере.
    """
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()

        # Создаем директорию, если она не существует
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        print(f"Изображение успешно скачано и сохранено по пути: {save_path}")
        return save_path

    except Exception as e:
        print(f"Ошибка при скачивании изображения: {e}")
        return None

async def send_photo_as_file(chat_id, image_path, bot_token):
    """
    Отправляет изображение как файл через Telegram API.
    """
    try:
        with open(image_path, "rb") as photo:
            url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            files = {"photo": photo}
            data = {"chat_id": chat_id}

            response = requests.post(url, files=files, data=data)
            response.raise_for_status()

            print("Изображение успешно отправлено.")
            return response.json()

    except Exception as e:
        print(f"Ошибка при отправке изображения: {e}")
        return None

async def main():
    # Пример использования
    image_url = "http://176.108.248.61/media/products/photo_2025-01-08_20-23-59_2.jpg"
    current_directory = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(current_directory, "photo.jpg")

    # Скачиваем изображение
    downloaded_file = download_image(image_url, save_path)
    if downloaded_file:
        print(f"Файл сохранен: {downloaded_file}")

        # Отправляем изображение
        chat_id = "397906696"
        bot_token = "8010538176:AAEnXXncUzx55BhULeRirz_0f43dRw7Hl6o"
        response = await send_photo_as_file(chat_id, downloaded_file, bot_token)
        if response:
            print("Ответ от Telegram API:", response)
            # Удаляем файл после отправки
            os.remove(downloaded_file)
            print(f"Файл {downloaded_file} удален.")
        else:
            print("Не удалось отправить изображение.")
    else:
        print("Не удалось скачать изображение.")

# Запускаем асинхронный код
if __name__ == "__main__":
    asyncio.run(main())