import re
from datetime import datetime
from BSoupSpider import BSoupParser

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

bot = Bot(token='552105148:AAH4hH232QZy7aOJ8IJyaXvc_L2Gq9t1Eh8')
dp = Dispatcher(bot)
now = datetime.now()


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply("Салам брат или сестра!\nСледовательно, ты с Компетиторс, раз знаешь обо мне!\nРад знакомству!")


@dp.message_handler(commands=['здравствуй', 'привет', 'ку', 'здорово', 'hi', 'hello'])
async def send_hi(message: types.Message):
    if 6 <= now.hour < 12:
        await message.reply('Добрый утро, {}'.format(message.from_user.first_name))

    elif 12 <= now.hour < 17:
        await message.reply('Добрый день, {}'.format(message.from_user.first_name))

    elif 17 <= now.hour < 23:
        await message.reply('Добрый вечер, {}'.format(message.from_user.first_name))


@dp.message_handler(commands=['чтс', 'что там сегодня?', 'тренировка', 'треня', 'wod'])
async def send_wod(message: types.Message):
    parser = BSoupParser()

    # Remove anything other than digits
    num = re.sub(r'\D', "", parser.get_wod_date())
    wod_date = datetime.strptime(num, '%m%d%y')
    print(wod_date)
    print(now)

    if wod_date.date().__eq__(now.date()):
        await message.reply(parser.get_wod_date() + parser.get_regional_wod() + parser.get_open_wod())
    else:
        await message.reply("Комплекс еще не вышел.\nСорян, брат!!!")


if __name__ == '__main__':
        executor.start_polling(dp)
