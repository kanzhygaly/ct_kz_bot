import re
from datetime import datetime

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor

from BSoupSpider import BSoupParser

from apscheduler.schedulers.asyncio import AsyncIOScheduler

bot = Bot(token='552105148:AAH4hH232QZy7aOJ8IJyaXvc_L2Gq9t1Eh8')
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()
now = datetime.now()
greetings = ['здравствуй', 'привет', 'ку', 'здорово', 'hi', 'hello']
wod = ['чтс', 'что там сегодня?', 'тренировка', 'треня', 'wod', 'workout']
start_msg = "CompTrainKZ BOT:\n\n" \
            "/wod - комплекс дня\n\n" \
            "/help - справочник"


def get_wod():
    parser = BSoupParser()

    # Remove anything other than digits
    num = re.sub(r'\D', "", parser.get_wod_date())
    wod_date = datetime.strptime(num, '%m%d%y')
    print(wod_date)
    print(now)

    if wod_date.date().__eq__(now.date()):
        return parser.get_wod_date() + "\n\n" + parser.get_regional_wod() + "\n" + parser.get_open_wod()
    else:
        return "Комплекс еще не вышел.\nСорян ((("


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await bot.send_message(message.chat.id, start_msg)


@dp.message_handler(commands=['wod'])
async def send_wod(message: types.Message):
    await message.reply(get_wod())


@dp.message_handler()
async def send_hi(message: types.Message):
    msg = str(message.text).lower()

    if msg in greetings:
        if 6 <= now.hour < 12:
            await message.reply('Доброе утро, {}'.format(message.from_user.first_name))

        elif 12 <= now.hour < 17:
            await message.reply('Добрый день, {}'.format(message.from_user.first_name))

        elif 17 <= now.hour < 23:
            await message.reply('Добрый вечер, {}'.format(message.from_user.first_name))

    elif msg in wod:
        await message.reply(get_wod())

    else:
        await message.reply(start_msg)


@scheduler.scheduled_job('cron', day_of_week='mon-sun', hour='3-4')
def scheduled_job():
    print('This job runs everyday at 8am.')
    print(now)


if __name__ == '__main__':
    scheduler.start()

    executor.start_polling(dp)
