from aiogram import types

from db import user_db


async def add_user_if_not_exist(message: types.Message) -> None:
    if not await user_db.is_user_exist(message.from_user.id):
        await user_db.add_user(message.from_user.id, message.from_user.first_name, message.from_user.last_name,
                               message.from_user.language_code)
