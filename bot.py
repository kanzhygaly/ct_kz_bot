import os
import re
from datetime import datetime

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bsoup_spider import BSoupParser
from database import Database

bot = Bot(token=os.environ['API_TOKEN'])
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()
db = Database()

greetings = ['здравствуй', 'привет', 'ку', 'здорово', 'hi', 'hello']
wod_requests = ['чтс', 'что там сегодня?', 'тренировка', 'треня', 'wod', 'workout']

info_msg = "CompTrainKZ BOT:\n\n" \
            "/wod - комплекс дня\n\n" \
            "/help - справочник\n\n"


def get_wod():
    parser = BSoupParser()

    # Remove anything other than digits
    num = re.sub(r'\D', "", parser.get_wod_date())
    wod_date = datetime.strptime(num, '%m%d%y')
    print(wod_date)
    now = datetime.now()
    print(now)

    if wod_date.date().__eq__(now.date()):
        return parser.get_wod_date() + "\n\n" + parser.get_regional_wod() + "\n" + parser.get_open_wod()
    else:
        return "Комплекс еще не вышел.\nСорян :("


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if not db.is_user_exist(message.from_user.id):
        db.add_user(message.from_user.id, message.from_user.first_name, message.from_user.last_name,
                    message.from_user.language_code)

    await bot.send_message(message.chat.id, info_msg + "/subscribe - подписаться на ежедневную рассылку WOD")


@dp.message_handler(commands=['help'])
async def send_info(message: types.Message):
    sub = "/subscribe - подписаться на ежедневную рассылку WOD"
    if db.is_subscriber(message.from_user.id):
        sub = "/unsubscribe - отписаться от ежедневной рассылки WOD"

    await bot.send_message(message.chat.id, info_msg + sub)


@dp.message_handler(commands=['subscribe'])
async def subscribe(message: types.Message):
    db.add_subscriber(message.from_user.id)

    await bot.send_message(message.chat.id, 'Вы подписались на ежедневную рассылку WOD')


@dp.message_handler(commands=['unsubscribe'])
async def unsubscribe(message: types.Message):
    db.unsubscribe(message.from_user.id)

    await bot.send_message(message.chat.id, 'Вы отписались от ежедневной рассылки WOD')


@dp.message_handler(commands=['wod'])
async def send_wod(message: types.Message):
    await message.reply(get_wod())


@dp.message_handler()
async def echo(message: types.Message):
    msg = str(message.text).lower()

    if msg in greetings:
        # send hi
        now = datetime.now()

        if 6 <= now.hour < 12:
            await message.reply('Доброе утро, {}'.format(message.from_user.first_name))

        elif 12 <= now.hour < 17:
            await message.reply('Добрый день, {}'.format(message.from_user.first_name))

        elif 17 <= now.hour < 23:
            await message.reply('Добрый вечер, {}'.format(message.from_user.first_name))

    elif msg in wod_requests:
        # send wod
        await message.reply(get_wod())

    else:
        # send info
        sub = "/subscribe - подписаться на ежедневную рассылку WOD"
        if db.is_subscriber(message.from_user.id):
            sub = "/unsubscribe - отписаться от ежедневной рассылки WOD"

        await message.reply(info_msg + sub)


@scheduler.scheduled_job('cron', day_of_week='mon-sun', hour=2)
def scheduled_job():
    print('This job runs everyday at 8am.')
    subscribers = db.get_all_subscribers()

    print(subscribers)
    for user_id in subscribers:
        bot.send_message(user_id, get_wod())


if __name__ == '__main__':
    db.init_tables()

    scheduler.start()

    executor.start_polling(dp)
