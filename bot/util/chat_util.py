import re
from datetime import datetime

import pytz
from aiogram import types
from aiogram.utils.emoji import emojize

from bot.db import location_db
from bot.exception import LocationNotFoundError, MsgNotRecognizedError

greetings = ['здравствуй', 'привет', 'ку', 'здорово', 'hi', 'hello', 'дд', 'добрый день',
             'доброе утро', 'добрый вечер', 'салем', 'hey']
salem = ['салам', 'слм', 'саламалейкум', 'ассаламуагалейкум', 'ассалямуагалейкум',
         'ассаламуалейкум', 'мирвам', 'миртебе']


def handle_chat_message(message: types.Message):
    msg = ''.join(re.findall('[a-zA-Zа-яА-Я]+', message.text.lower()))

    if msg in greetings:
        try:
            location = await location_db.get_location(message.from_user.id)
            now = datetime.now(pytz.timezone(location.tz))
        except LocationNotFoundError:
            now = datetime.now()

        if 4 <= now.hour < 12:
            reply_msg = f'Доброе утро, {message.from_user.first_name}!'
        elif 12 <= now.hour < 17:
            reply_msg = f'Добрый день, {message.from_user.first_name}!'
        elif 17 <= now.hour < 23:
            reply_msg = f'Добрый вечер, {message.from_user.first_name}!'
        else:
            reply_msg = f'Привет, {message.from_user.first_name}!'

        return reply_msg
    elif msg in salem:
        return f'Уа-Алейкум Ас-Салям, {message.from_user.first_name}!'
    elif msg == 'арау':
        return emojize('Урай! :punch:')

    raise MsgNotRecognizedError
