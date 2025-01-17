# ITG.Teleshop — Интернет-магазин цветов с Telegram ботом

**ITG.Teleshop** — это интернет-магазин цветов с интеграцией Telegram бота для управления заказами и уведомлений. Проект разработан на Django для веб-части и aiogram для Telegram бота.

---

## 📋 Оглавление

1. [Функциональность](#-функциональность)
2. [Технологии](#-технологии)
3. [Установка и настройка](#-установка-и-настройка)
4. [Запуск проекта](#-запуск-проекта)
5. [Тестирование](#-тестирование)
6. [Лицензия](#-лицензия)

---

## 🌟 Функциональность

### Веб-сайт:
- **Регистрация и авторизация пользователей**.
- **Каталог цветов** с возможностью просмотра, фильтрации и добавления в корзину.
- **Оформление заказа** с указанием данных для доставки.
- **История заказов** для каждого пользователя.
- **Аккаунт администратора** для управления заказами и статусами.
- **Отзывы и рейтинги** для товаров.
- **Аналитика и отчеты** по заказам.

### Telegram бот:
- **Уведомления о статусе заказа**.
- **Просмотр заказов** с информацией о букетах и доставке.
- **Аналитика и отчеты** по заказам.

---

## 🛠 Технологии

- **Backend**: Django, Django REST Framework (если используется API).
- **Frontend**: HTML, CSS, JavaScript (если используется).
- **Telegram бот**: aiogram.
- **База данных**: SQLite (для разработки), PostgreSQL (для продакшена).
- **Дополнительно**: pytest для тестирования, Docker для контейнеризации.

---

## 🚀 Установка и настройка

### 1. Клонирование репозитория

```bash
git clone https://github.com/your-username/ITG.Teleshop.git
cd ITG.Teleshop
 
Telegram Bot for Order Management
Этот Telegram-бот предназначен для управления заказами и взаимодействия с пользователями. Бот интегрирован с Django-приложением и предоставляет функциональность для проверки статуса заказов, формирования отчетов и управления правами администратора.

Основные функции
Привязка аккаунта: Пользователи могут привязать свой Telegram-аккаунт к учетной записи на сайте.

Проверка статуса заказов: Пользователи могут проверять статус своих заказов за выбранный период.

Отчеты для администраторов: Администраторы могут формировать отчеты по заказам за выбранный период и скачивать их в формате Excel.

Управление правами администратора: Администраторы могут назначать и снимать права администратора через специальные команды.

Инлайн-клавиатура для ввода кодового слова: Безопасный ввод кодового слова для назначения администратора.

Установка и настройка
Требования
Python 3.8 или выше

Django

Aiogram

PostgreSQL (или другая СУБД, поддерживаемая Django)

Установка
Клонируйте репозиторий:

bash
Copy
git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name
Установите зависимости:

bash
Copy
pip install -r requirements.txt
Настройте базу данных в файле settings.py:

python
Copy
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
Примените миграции:

bash
Copy
python manage.py migrate
Запустите бота:

bash
Copy
python manage.py runbot
Настройка переменных окружения
Создайте файл .env в корне проекта и добавьте следующие переменные:

env
Copy
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
YAADMIN_SECRET_CODE=your_secret_code
BASE_URL=https://your-website.com
Использование
Основные команды
/start — Начать работу с ботом.

/yaadmin — Запросить кодовое слово для назначения администратора.

/yaneadmin — Снять права администратора.

Статус заказов — Проверить статус заказов.

Отчеты — Сформировать отчеты (доступно только администраторам).

Пример работы
Пользователь отправляет команду /start и привязывает свой аккаунт.

Администратор отправляет команду /yaadmin и вводит кодовое слово через инлайн-клавиатуру.

Администратор может формировать отчеты и скачивать их в формате Excel.

Лицензия
Этот проект распространяется под лицензией MIT. Подробнее см. в файле LICENSE.

Дополнительные разделы (по желанию)
Вы можете добавить разделы:

Разработчики: Список разработчиков.

Благодарности: Благодарности за использование сторонних библиотек.

Контрибьютинг: Как можно поучаствовать в разработке.

Если нужно что-то доработать или добавить, дайте знать! 😊

New chat


Flower Shop Application
Это веб-приложение для управления интернет-магазином цветов. Оно включает в себя функциональность для управления пользователями, товарами, заказами, корзиной и отзывами. Приложение интегрировано с Telegram-ботом для уведомлений и управления заказами.

Основные функции
Управление пользователями:

Регистрация и аутентификация пользователей.

Привязка Telegram-аккаунта для получения уведомлений.

Назначение прав администратора.

Управление товарами:

Категории товаров.

Добавление, редактирование и удаление товаров.

Отображение товаров с фильтрацией по категориям.

Корзина и заказы:

Добавление товаров в корзину.

Оформление заказов.

Управление статусами заказов (новый, в работе, в доставке, выполнен).

Повторение заказов.

Отзывы:

Добавление отзывов на товары.

Рейтинг товаров.

Отчеты:

Формирование отчетов по заказам за выбранный период.

Экспорт отчетов в формате CSV и Excel.

Интеграция с Telegram:

Уведомления о статусе заказов.

Управление заказами через Telegram-бота.

Установка и настройка
Требования
Python 3.8 или выше

Django

PostgreSQL (или другая СУБД, поддерживаемая Django)

Aiogram (для Telegram-бота)

Установка
Клонируйте репозиторий:

bash
Copy
git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name
Установите зависимости:

bash
Copy
pip install -r requirements.txt
Настройте базу данных в файле settings.py:

python
Copy
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
Примените миграции:

bash
Copy
python manage.py migrate
Создайте суперпользователя:

bash
Copy
python manage.py createsuperuser
Запустите сервер:

bash
Copy
python manage.py runserver
Запустите Telegram-бота:

bash
Copy
python manage.py runbot
Настройка переменных окружения
Создайте файл .env в корне проекта и добавьте следующие переменные:

env
Copy
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
YAADMIN_SECRET_CODE=your_secret_code
BASE_URL=https://your-website.com
Использование
Пользовательские функции
Регистрация и вход: Пользователи могут зарегистрироваться и войти в систему через email.

Корзина: Пользователи могут добавлять товары в корзину и оформлять заказы.

Заказы: Пользователи могут просматривать свои заказы и их статусы.

Отзывы: Пользователи могут оставлять отзывы на товары.

Административные функции
Управление товарами: Администраторы могут добавлять, редактировать и удалять товары.

Управление заказами: Администраторы могут изменять статусы заказов.

Отчеты: Администраторы могут формировать отчеты по заказам и экспортировать их в CSV или Excel.

Telegram-бот
Уведомления: Пользователи получают уведомления о статусе своих заказов.

Управление заказами: Администраторы могут управлять заказами через Telegram-бота.

Структура проекта
flower_shop: Основное приложение Django.

models.py: Модели данных (пользователи, товары, заказы, отзывы и т.д.).

views.py: Контроллеры для обработки запросов.

forms.py: Формы для регистрации, входа, отзывов и заказов.

templates: Шаблоны для отображения страниц.

urls.py: Маршруты для приложения.

telegrambot: Приложение для Telegram-бота.

bot.py: Основной код бота.

telegram_utils3.py: Вспомогательные функции для работы с Telegram.

Лицензия
Этот проект распространяется под лицензией MIT. Подробнее см. в файле LICENSE.

Дополнительные разделы (по желанию)
Вы можете добавить разделы:

Разработчики: Список разработчиков.

Благодарности: Благодарности за использование сторонних библиотек.

Контрибьютинг: Как можно поучаствовать в разработке.

Если нужно что-то доработать или добавить, дайте знать! 😊

