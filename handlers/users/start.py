from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandStart
from utils.db_api.database import DBCommands
from loader import dp


@dp.message_handler(CommandStart())
async def bot_start(message: types.Message):
    await message.answer(f"Привет, {message.from_user.full_name}!")
    await DBCommands().add_new_user()
