import os
import re
from datetime import datetime

from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bsoup_spider import BSoupParser
from db import user_db, subscriber_db, wod_db, wod_result_db, async_db

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
EDIT_WOD_RESULT = 'edit_wod_result'
# Buttons
ADD_RESULT = 'Add result'
EDIT_RESULT = 'Edit result'
SHOW_RESULTS = 'Show results'
CANCEL = "Cancel"


async def get_wod():
    now = datetime.now()
    print(now.date())

    result = await wod_db.get_wods(now.date())
    if result:
        wod_id = result[0].id
        title = result[0].title
        description = result[0].description

        return title + "\n\n" + description, wod_id

    parser = BSoupParser(url=os.environ['WEB_URL'])

    # Remove anything other than digits
    num = re.sub(r'\D', "", parser.get_wod_date())
    wod_date = datetime.strptime(num, '%m%d%y')
    print(wod_date.date())

    if wod_date.date().__eq__(now.date()):
        title = parser.get_wod_date()
        regional = parser.get_regional_wod()
        description = regional + "\n" + parser.get_open_wod()

        wod_id = await wod_db.add_wod(wod_date.date(), title, description)

        return title + "\n\n" + description + "\n\n", wod_id
    else:
        return "Комплекс еще не вышел.\nСорян :(", None


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if not await user_db.is_user_exist(message.from_user.id):
        await user_db.add_user(message.from_user.id, message.from_user.first_name, message.from_user.last_name,
                               message.from_user.language_code)

    await bot.send_message(message.chat.id, info_msg + "/subscribe - подписаться на ежедневную рассылку WOD")


@dp.message_handler(commands=['help'])
async def send_info(message: types.Message):
    sub = "/subscribe - подписаться на ежедневную рассылку WOD"
    if await subscriber_db.is_subscriber(message.from_user.id):
        sub = "/unsubscribe - отписаться от ежедневной рассылки WOD"

    await bot.send_message(message.chat.id, info_msg + sub)


@dp.message_handler(commands=['subscribe'])
async def subscribe(message: types.Message):
    await subscriber_db.add_subscriber(message.from_user.id)

    await bot.send_message(message.chat.id, 'Вы подписались на ежедневную рассылку WOD')


@dp.message_handler(commands=['unsubscribe'])
async def unsubscribe(message: types.Message):
    await subscriber_db.unsubscribe(message.from_user.id)

    await bot.send_message(message.chat.id, 'Вы отписались от ежедневной рассылки WOD')


@dp.message_handler(commands=['wod'])
@dp.message_handler(func=lambda message: message.text and message.text.lower() in wod_requests)
async def send_wod(message: types.Message):
    msg, wod_id = await get_wod()
    user_id = message.from_user.id
    res_button = ADD_RESULT

    if wod_id is not None:
        result = await wod_result_db.get_user_wod_result(wod_id=wod_id, user_id=user_id)
        if result:
            res_button = EDIT_RESULT

        with dp.current_state(chat=message.chat.id, user=user_id) as state:
            await state.update_data(wod_id=wod_id)
            await state.set_state(WOD)
            if result:
                await state.update_data(wod_result_id=result[0].id)

    # Configure ReplyKeyboardMarkup
    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    reply_markup.add(res_button, SHOW_RESULTS)
    reply_markup.add(CANCEL)

    await bot.send_message(message.chat.id, msg, reply_markup=reply_markup)


@dp.message_handler(state=WOD, func=lambda message: message.text == CANCEL)
async def hide_keyboard(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    # reset
    await state.reset_state(with_data=True)
    await bot.send_message(message.chat.id, '', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=WOD, func=lambda message: message.text == ADD_RESULT)
async def request_result_for_add(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    await state.set_state(ADD_WOD_RESULT)

    await bot.send_message(message.chat.id, 'Пожалуйста введите ваш результат', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=ADD_WOD_RESULT)
async def add_wod_result(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    data = await state.get_data()

    wod_id = data['wod_id']
    await wod_result_db.add_wod_result(wod_id, message.from_user.id, message.text, datetime.now())

    await bot.send_message(message.chat.id, 'Ваш результат успешно добавлен!')

    # Finish conversation
    # WARNING! This method will destroy all data in storage for current user!
    await state.finish()


@dp.message_handler(state=WOD, func=lambda message: message.text == EDIT_RESULT)
async def request_result_for_edit(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    await state.set_state(EDIT_WOD_RESULT)
    data = await state.get_data()

    msg = 'Пожалуйста введите ваш результат'

    wod_result_id = data['wod_result_id']
    wod_result = await wod_result_db.get_one(id=wod_result_id)
    if wod_result:
        msg = 'Ваш текущий результат:\n'
        msg += wod_result.result + '\n\n'
        msg += 'Пожалуйста введите ваш новый результат'

    await bot.send_message(message.chat.id, msg, reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=EDIT_WOD_RESULT)
async def edit_wod_result(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    data = await state.get_data()

    wod_result_id = data['wod_result_id']
    wod_result = await wod_result_db.get_one(id=wod_result_id)
    if wod_result:
        wod_result.sys_date = datetime.now()
        wod_result.result = message.text
        await wod_result.save()

    await bot.send_message(message.chat.id, 'Ваш результат успешно бновлен!')

    # Finish conversation
    # WARNING! This method will destroy all data in storage for current user!
    await state.finish()


@dp.message_handler(state=WOD, func=lambda message: message.text == SHOW_RESULTS)
async def show_wod_results(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    data = await state.get_data()

    wod_id = data['wod_id']

    msg = ''
    for res in await wod_result_db.get_wod_results(wod_id):
        u = await user_db.get_user(res.user_id)
        title = u.name + ' ' + u.surname + ', ' + res.sys_date.strftime("%H:%M:%S %Y-%m-%d")
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

        result = await wod_db.get_wods(wod_date)
        if result:
            with dp.current_state(chat=message.chat.id, user=message.from_user.id) as state:
                await state.update_data(wod_id=result[0].id)

            title = result[0].title
            description = result[0].description

            await bot.send_message(message.chat.id, title + "\n\n" + description)


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
        if await subscriber_db.is_subscriber(message.from_user.id):
            sub = "/unsubscribe - отписаться от ежедневной рассылки WOD"

        await message.reply(info_msg + sub)


@scheduler.scheduled_job('cron', day_of_week='mon-sun', hour=2)
async def scheduled_job():
    print('This job runs everyday at 8am')
    subscribers = await subscriber_db.get_all_subscribers()

    msg, wod_id = await get_wod()

    print('Sending WOD to ' + len(subscribers) + ' subscribers')
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
