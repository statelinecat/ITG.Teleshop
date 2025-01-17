from setuptools import setup, find_packages

setup(
    name="Teleshop",
    version="0.1",
    description="Telegram bot for managing orders",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),  # Автоматически находит все пакеты в проекте
    install_requires=[
        "aiogram>=3.0",
        "django>=4.0",
        "requests>=2.0",
        "openpyxl>=3.0",
        "aiohttp>=3.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "teleshop-bot=telegrambot.bot:main",  # Создаёт команду для запуска бота
        ],
    },
)