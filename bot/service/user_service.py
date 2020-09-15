from aiogram import types

from bot.db import user_db


async def add_user_if_not_exist(message: types.Message) -> None:
    if not await user_db.is_user_exist(message.from_user.id):
        await user_db.add_user(user_id=message.from_user.id, name=message.from_user.first_name,
                               surname=message.from_user.last_name, lang=message.from_user.language_code)
