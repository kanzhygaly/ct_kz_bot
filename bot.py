import os
import re
from datetime import datetime

from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bsoup_spider import BSoupParser
from db import user, subscriber, wod, wod_result, async_db

bot = Bot(token=os.environ['API_TOKEN'])

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

scheduler = AsyncIOScheduler()

greetings = ['здравствуй', 'привет', 'ку', 'здорово', 'hi', 'hello']
wod_requests = ['чтс', 'что там сегодня?', 'тренировка', 'треня', 'wod', 'workout']

info_msg = "CompTrainKZ BOT:\n\n" \
           "/help - справочник\n\n" \
           "/wod - комплекс дня\n\n" \
           "/find - найти комплекс\n\n"

# States
WOD = 'wod'
ADD_WOD_RESULT = 'add_wod_result'
SHOW_RESULTS = 'Show results'


async def get_wod():
    now = datetime.now()
    print(now)

    result = await wod.get_wods(now.date())
    if result:
        wod_id = result[0].id
        title = result[0].title
        description = result[0].description

        return title + "\n\n" + description + "\n\n" + msg, wod_id

    parser = BSoupParser(url=os.environ['WEB_URL'])

    # Remove anything other than digits
    num = re.sub(r'\D', "", parser.get_wod_date())
    wod_date = datetime.strptime(num, '%m%d%y')
    print(wod_date)

    if wod_date.date().__eq__(now.date()):
        title = parser.get_wod_date()
        regional = parser.get_regional_wod()
        description = regional + "\n" + parser.get_open_wod()

        wod_id = None
        if ''.join(regional.split()) == "2018REGIONALSATHLETESRest":
            wod_id = await wod.add_wod(wod_date.date(), title, description)

        return title + "\n\n" + description + "\n\n", wod_id
    else:
        return "Комплекс еще не вышел.\nСорян :(", None


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if not await user.is_user_exist(message.from_user.id):
        await user.add_user(message.from_user.id, message.from_user.first_name, message.from_user.last_name,
                            message.from_user.language_code)

    await bot.send_message(message.chat.id, info_msg + "/subscribe - подписаться на ежедневную рассылку WOD")


@dp.message_handler(commands=['help'])
async def send_info(message: types.Message):
    sub = "/subscribe - подписаться на ежедневную рассылку WOD"
    if await subscriber.is_subscriber(message.from_user.id):
        sub = "/unsubscribe - отписаться от ежедневной рассылки WOD"

    await bot.send_message(message.chat.id, info_msg + sub)


@dp.message_handler(commands=['subscribe'])
async def subscribe(message: types.Message):
    await subscriber.add_subscriber(message.from_user.id)

    await bot.send_message(message.chat.id, 'Вы подписались на ежедневную рассылку WOD')


@dp.message_handler(commands=['unsubscribe'])
async def unsubscribe(message: types.Message):
    await subscriber.unsubscribe(message.from_user.id)

    await bot.send_message(message.chat.id, 'Вы отписались от ежедневной рассылки WOD')


@dp.message_handler(commands=['wod'])
@dp.message_handler(func=lambda message: message.text and message.text.lower() in wod_requests)
async def send_wod(message: types.Message):
    msg, wod_id = await get_wod()

    if wod_id is not None:
        with dp.current_state(chat=message.chat.id, user=message.from_user.id) as state:
            await state.update_data(wod_id=wod_id)
            await  state.set_state(WOD)

    # Configure ReplyKeyboardMarkup
    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    reply_markup.add("Add result", SHOW_RESULTS)
    reply_markup.add("Hide")

    await bot.send_message(message.chat.id, msg, reply_markup=reply_markup)


@dp.message_handler(state=WOD, func=lambda message: message.text == "Hide")
async def hide_keyboard(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    # reset
    await state.reset_state(with_data=True)
    await bot.send_message(message.chat.id, '', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=WOD, func=lambda message: message.text == "Add result")
async def hide_keyboard(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    await state.set_state(ADD_WOD_RESULT)

    await bot.send_message(message.chat.id, 'Please enter your score', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=ADD_WOD_RESULT)
async def add_wod_result(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    data = await state.get_data()

    wod_id = data['wod_id']
    await wod_result.add_wod_result(wod_id, message.from_user.id, message.text, datetime.now().timestamp())

    await bot.send_message(message.chat.id, 'Ваш результат успешно добавлен!')

    # Finish conversation
    # WARNING! This method will destroy all data in storage for current user!
    await state.finish()


@dp.message_handler(state=WOD, func=lambda message: message.text == SHOW_RESULTS)
async def hide_keyboard(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    data = await state.get_data()

    wod_id = data['wod_id']

    msg = ''
    for res in await wod_result.get_wod_results(wod_id):
        title = res.sys_date + ' от ' + res.user_id
        msg += title + '\n' + res.result + '\n\n'

    await bot.send_message(message.chat.id, msg, reply_markup=types.ReplyKeyboardRemove())

    # Finish conversation
    # WARNING! This method will destroy all data in storage for current user!
    await state.finish()


@dp.message_handler(commands=['find'])
async def find_wod(message: types.Message):
    if message.get_args():
        num = re.sub(r'\D', "", message.get_args()[0])
        wod_date = datetime.strptime(num, '%d%m%y')

        result = await wod.get_wods(wod_date)
        if result:
            msg = "/wod_results"

            with dp.current_state(chat=message.chat.id, user=message.from_user.id) as state:
                await state.update_data(wod_id=result[0].id)

            title = result[0].title
            description = result[0].description

            await bot.send_message(message.chat.id, title + "\n\n" + description + "\n\n" + msg)


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
        if await subscriber.is_subscriber(message.from_user.id):
            sub = "/unsubscribe - отписаться от ежедневной рассылки WOD"

        await message.reply(info_msg + sub)


@scheduler.scheduled_job('cron', day_of_week='mon-sun', hour=2)
async def scheduled_job():
    print('This job runs everyday at 8am.')
    subscribers = await subscriber.get_all_subscribers()

    msg, wod_id = await get_wod()

    for sub in subscribers:
        if wod_id is not None:
            with dp.current_state(chat=sub.user_id, user=sub.user_id) as state:
                await state.update_data(wod_id=wod_id)

        await bot.send_message(sub.user_id, msg)


async def startup(dispatcher: Dispatcher):
    print('Startup CompTrainKZ Bot...')
    async with async_db.Entity.connection() as connection:
        # await async_db.drop_all_tables(connection)
        await async_db.create_all_tables(connection)


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


if __name__ == '__main__':
    scheduler.start()

    executor.start_polling(dp, on_startup=startup, on_shutdown=shutdown)
