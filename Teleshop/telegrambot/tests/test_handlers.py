# telegrambot/tests/test_handlers.py
import pytest
from aiogram import types
from unittest.mock import AsyncMock
from telegrambot.bot import send_welcome

@pytest.mark.asyncio
async def test_send_welcome():
    message = AsyncMock(spec=types.Message)
    message.answer = AsyncMock()
    await send_welcome(message)
    message.answer.assert_called_with(
        "Привет! Я бот для управления заказами.\n"
        "Чтобы привязать аккаунт, нажмите кнопку 'Старт'.",
        reply_markup=get_start_keyboard()
    )