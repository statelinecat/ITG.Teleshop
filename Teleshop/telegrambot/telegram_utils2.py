import requests
import os

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

# Пример использования
image_url = "http://176.108.248.61/media/products/photo_2025-01-08_20-23-59_2.jpg"

# Указываем путь для сохранения в текущей директории
current_directory = os.path.dirname(os.path.abspath(__file__))
save_path = os.path.join(current_directory, "photo.jpg")

# Скачиваем изображение
downloaded_file = download_image(image_url, save_path)
if downloaded_file:
    print(f"Файл сохранен: {downloaded_file}")
else:
    print("Не удалось скачать изображение.")