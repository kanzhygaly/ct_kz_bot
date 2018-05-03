import os
import re
from datetime import datetime

from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bsoup_spider import BSoupParser
from database import Database

bot = Bot(token=os.environ['API_TOKEN'])
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
scheduler = AsyncIOScheduler()
db = Database()

greetings = ['здравствуй', 'привет', 'ку', 'здорово', 'hi', 'hello']
wod_requests = ['чтс', 'что там сегодня?', 'тренировка', 'треня', 'wod', 'workout']

info_msg = "CompTrainKZ BOT:\n\n" \
           "/help - справочник\n\n" \
           "/wod - комплекс дня\n\n"


def get_wod():
    msg = "/wod_results\n\n" \
          "/add_wod_result"

    now = datetime.now()
    print(now)

    result = db.get_wods(now.date())
    if result:
        wod_id = result[0]['id']
        title = result[0]['title']
        description = result[0]['description']

        return title + "\n\n" + description + "\n\n" + msg, wod_id

    parser = BSoupParser()

    # Remove anything other than digits
    num = re.sub(r'\D', "", parser.get_wod_date())
    wod_date = datetime.strptime(num, '%m%d%y')
    print(wod_date)

    if wod_date.date().__eq__(now.date()):
        title = parser.get_wod_date()
        description = parser.get_regional_wod() + "\n" + parser.get_open_wod()

        wod_id = db.add_wod(wod_date.date(), title, description)

        return title + "\n\n" + description + "\n\n" + msg, wod_id
    else:
        return "Комплекс еще не вышел.\nСорян :(", None


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
@dp.message_handler(func=lambda message: message.text and message.text.lower() in wod_requests)
async def send_wod(message: types.Message):
    wod, wod_id = get_wod()
    if wod_id is not None:
        with dp.current_state(chat=message.chat.id, user=message.from_user.id) as state:
            await state.update_data(wod_id=wod_id)

    await bot.send_message(message.chat.id, wod)


@dp.message_handler(commands=['wod_results'])
async def wod_results(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    data = await state.get_data()

    wod_id = data['wod_id']
    msg = ''

    for wod_result in db.get_wod_results(wod_id):
        title = wod_result['sys_date'] + ' от ' + wod_result['user_id']
        msg += title + '\n' + wod_result['result'] + '\n\n'

    await bot.send_message(message.chat.id, msg)


@dp.message_handler(commands=['add_wod_result'])
async def add_wod_result(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    data = await state.get_data()

    wod_id = data['wod_id']
    db.add_wod_result(wod_id, message.from_user.id, message.text, datetime.now().timestamp())

    await bot.send_message(message.chat.id, 'Ваш результат успешно добавлен')


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

    wod, wod_id = get_wod()

    print(subscribers)
    for user_id in subscribers:
        bot.send_message(user_id, wod)


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


if __name__ == '__main__':
    db.init_tables()

    scheduler.start()

    executor.start_polling(dp, on_shutdown=shutdown)
