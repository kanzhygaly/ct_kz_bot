import os
import re
from datetime import datetime

import pytz
from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.types import ParseMode
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import utils
from bsoup_spider import BSoupParser
from db import user_db, subscriber_db, wod_db, wod_result_db, async_db, location_db

bot = Bot(token=os.environ['API_TOKEN'])

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

scheduler = AsyncIOScheduler()

greetings = ['здравствуй', 'привет', 'ку', 'здорово', 'hi', 'hello', 'дд', 'добрый день',
             'доброе утро', 'добрый вечер', 'салем']
salem = ['салам', 'слм', 'саламалейкум', 'ассаламуагалейкум', 'ассалямуагалейкум',
         'ассаламуалейкум', 'мирвам', 'миртебе']
wod_requests = ['чтс', 'что там сегодня', 'тренировка', 'треня', 'wod', 'workout']

info_msg = "CompTrainKZ BOT:\n\n" \
           "/help - справочник\n\n" \
           "/wod - комплекс дня\n\n" \
           "/find - найти комплекс\n\n" \
           "/timezone - установить часовой пояс\n\n\n"

# States
WOD = 'wod'
ADD_WOD_RESULT = 'add_wod_result'
EDIT_WOD_RESULT = 'edit_wod_result'
FIND_WOD = 'find_wod'
SET_TIMEZONE = 'set_timezone'
# Buttons
ADD_RESULT = 'Добавить'
EDIT_RESULT = 'Изменить'
SHOW_RESULTS = 'Результаты'
CANCEL = "Отмена"


async def get_wod():
    now = datetime.now()

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

        return title + "\n\n" + description, wod_id
    else:
        return "Комплекс еще не вышел.\nСорян :(", None


@dp.message_handler(commands=['sys_all_users'])
async def test(message: types.Message):
    if not await user_db.is_admin(message.from_user.id):
        print(message.from_user.id)
        # send info
        sub = "/subscribe - подписаться на ежедневную рассылку WOD"
        if await subscriber_db.is_subscriber(message.from_user.id):
            sub = "/unsubscribe - отписаться от ежедневной рассылки WOD"

        return await message.reply(info_msg + sub)

    users = await user_db.get_all_users()
    msg = ''
    counter = 1
    for u in users:
        msg += counter + '. ' + u.name + ' ' + u.surname + '\n'
        counter += 1

    await bot.send_message(message.chat.id, msg, parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(commands=['test'])
async def test(message: types.Message):
    msg, wod_id = await get_wod()
    user_id = message.from_user.id

    if wod_id is not None:
        state = dp.current_state(chat=message.chat.id, user=user_id)
        await state.update_data(wod_id=wod_id)
        await state.set_state(WOD)

    # Configure InlineKeyboardMarkup
    reply_markup = types.InlineKeyboardMarkup()
    reply_markup.add(types.InlineKeyboardButton(SHOW_RESULTS, callback_data=SHOW_RESULTS))

    await bot.send_message(message.chat.id, msg, reply_markup=reply_markup)


# @dp.callback_query_handler(func=lambda callback_query: SHOW_RESULTS)
@dp.callback_query_handler()
async def show_results_callback(callback_query: types.CallbackQuery):
    print(callback_query)
    print(callback_query.data)

    state = dp.current_state(chat=callback_query.message.chat.id, user=callback_query.from_user.id)
    data = await state.get_data()

    wod_id = data['wod_id']
    wod_results = await wod_result_db.get_wod_results(wod_id)

    if wod_results:
        msg = ''
        for res in wod_results:
            u = await user_db.get_user(res.user_id)

            location = await location_db.get_location(callback_query.from_user.id)
            dt = res.sys_date.astimezone(pytz.timezone(location.tz)) if location else res.sys_date

            title = '_' + u.name + ' ' + u.surname + ', ' + dt.strftime("%H:%M:%S %d %B %Y") + '_'
            msg += title + '\n' + res.result + '\n\n'

        await bot.send_message(callback_query.message.chat.id, msg, reply_markup=types.ReplyKeyboardRemove(),
                               parse_mode=ParseMode.MARKDOWN)
        # Finish conversation, destroy all data in storage for current user
        await state.finish()
    else:
        return await bot.send_message(callback_query.message.chat.id, 'Результатов пока нет.\n'
                                                                      'Станьте первым кто внесет свой результат!')


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id

    if not await user_db.is_user_exist(user_id):
        await user_db.add_user(user_id, message.from_user.first_name, message.from_user.last_name,
                               message.from_user.language_code)

    sub = "/subscribe - подписаться на ежедневную рассылку WOD"
    if await subscriber_db.is_subscriber(user_id):
        sub = "/unsubscribe - отписаться от ежедневной рассылки WOD"

    await bot.send_message(message.chat.id, info_msg + sub)


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
@dp.message_handler(func=lambda message: message.text.lower() in wod_requests)
async def send_wod(message: types.Message):
    msg, wod_id = await get_wod()
    user_id = message.from_user.id
    res_button = ADD_RESULT

    if wod_id is not None:
        state = dp.current_state(chat=message.chat.id, user=user_id)
        await state.update_data(wod_id=wod_id)
        await state.set_state(WOD)

        wod_result = await wod_result_db.get_user_wod_result(wod_id=wod_id, user_id=user_id)
        if wod_result:
            res_button = EDIT_RESULT
            await state.update_data(wod_result_id=wod_result.id)

    # Configure ReplyKeyboardMarkup
    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    reply_markup.add(res_button, SHOW_RESULTS)
    reply_markup.add(CANCEL)

    await bot.send_message(message.chat.id, msg, reply_markup=reply_markup)


@dp.message_handler(state='*', func=lambda message: message.text.lower() == CANCEL.lower())
async def hide_keyboard(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    # reset
    await state.reset_state(with_data=True)
    await bot.send_message(message.chat.id, info_msg, reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=WOD, func=lambda message: message.text == ADD_RESULT)
async def request_result_for_add(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    await state.set_state(ADD_WOD_RESULT)

    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    reply_markup.add(CANCEL)

    await bot.send_message(message.chat.id, 'Пожалуйста введите ваш результат', reply_markup=reply_markup)


@dp.message_handler(state=ADD_WOD_RESULT)
async def add_wod_result(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    data = await state.get_data()

    wod_id = data['wod_id']
    await wod_result_db.add_wod_result(wod_id, message.from_user.id, message.text, datetime.now())

    await bot.send_message(message.chat.id, 'Ваш результат успешно добавлен!',
                           reply_markup=types.ReplyKeyboardRemove())

    # Finish conversation, destroy all data in storage for current user
    await state.finish()


@dp.message_handler(state=WOD, func=lambda message: message.text == EDIT_RESULT)
async def request_result_for_edit(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    await state.set_state(EDIT_WOD_RESULT)
    data = await state.get_data()

    msg = 'Пожалуйста введите ваш результат'

    wod_result_id = data['wod_result_id']
    wod_result = await wod_result_db.get_wod_result(wod_result_id=wod_result_id)
    if wod_result:
        msg = 'Ваш текущий результат:\n\n_' \
              + wod_result.result + \
              '_\n\nПожалуйста введите ваш новый результат'

    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    reply_markup.add(CANCEL)

    await bot.send_message(message.chat.id, msg, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(state=EDIT_WOD_RESULT)
async def edit_wod_result(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    data = await state.get_data()

    wod_result_id = data['wod_result_id']
    wod_result = await wod_result_db.get_wod_result(wod_result_id=wod_result_id)
    if wod_result:
        wod_result.sys_date = datetime.now()
        wod_result.result = message.text
        await wod_result.save()

    await bot.send_message(message.chat.id, 'Ваш результат успешно обновлен!',
                           reply_markup=types.ReplyKeyboardRemove())

    # Finish conversation, destroy all data in storage for current user
    await state.finish()


@dp.message_handler(state=WOD, func=lambda message: message.text == SHOW_RESULTS)
async def show_wod_results(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    data = await state.get_data()

    wod_id = data['wod_id']
    wod_results = await wod_result_db.get_wod_results(wod_id)

    if wod_results:
        msg = ''
        for res in wod_results:
            u = await user_db.get_user(res.user_id)

            location = await location_db.get_location(message.from_user.id)
            dt = res.sys_date.astimezone(pytz.timezone(location.tz)) if location else res.sys_date

            title = '_' + u.name + ' ' + u.surname + ', ' + dt.strftime("%H:%M:%S %d %B %Y") + '_'
            msg += title + '\n' + res.result + '\n\n'

        await bot.send_message(message.chat.id, msg, reply_markup=types.ReplyKeyboardRemove(),
                               parse_mode=ParseMode.MARKDOWN)
        # Finish conversation, destroy all data in storage for current user
        await state.finish()
    else:
        return await bot.send_message(message.chat.id, 'Результатов пока нет.\n'
                                                       'Станьте первым кто внесет свой результат!')


@dp.message_handler(commands=['find'])
async def find(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    await state.set_state(FIND_WOD)

    await bot.send_message(message.chat.id, 'Пожалуйста введите дату в формате *ДеньМесяцГод*'
                                            '\n\n_Пример: 170518_', parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(state=FIND_WOD)
async def find_wod(message: types.Message):
    try:
        search_date = datetime.strptime(message.text, '%d%m%y')
    except ValueError:
        return await bot.send_message(message.chat.id, 'Пожалуйста введите дату в формате *ДеньМесяцГод*'
                                                       '\n\n_Пример: 170518_', parse_mode=ParseMode.MARKDOWN)

    time_between = datetime.now() - search_date

    wods = await wod_db.get_wods(search_date)
    if wods:
        wod_id = wods[0].id
        title = wods[0].title
        description = wods[0].description
        user_id = message.from_user.id
        res_button = ADD_RESULT

        state = dp.current_state(chat=message.chat.id, user=user_id)
        await state.update_data(wod_id=wod_id)
        await state.set_state(WOD)

        wod_result = await wod_result_db.get_user_wod_result(wod_id=wod_id, user_id=user_id)
        if wod_result:
            res_button = EDIT_RESULT
            await state.update_data(wod_result_id=wod_result.id)

        # Configure ReplyKeyboardMarkup
        reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        if time_between.days > 30 and res_button == EDIT_RESULT:
            # if wod result older than week, then disable edit
            reply_markup.add(SHOW_RESULTS)
        else:
            reply_markup.add(res_button, SHOW_RESULTS)
        reply_markup.add(CANCEL)

        await bot.send_message(message.chat.id, title + "\n\n" + description, reply_markup=reply_markup)


@dp.message_handler(commands=['timezone'])
async def set_timezone(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    await state.set_state(SET_TIMEZONE)

    loc_btn = types.KeyboardButton(text="Локация", request_location=True)
    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    reply_markup.insert(loc_btn)
    reply_markup.add(CANCEL)

    await bot.send_message(message.chat.id, "Мне нужна ваша геолокация для того, чтобы установить "
                                            "правильный часовой пояс", reply_markup=reply_markup)


@dp.message_handler(state=SET_TIMEZONE, content_types=types.ContentType.LOCATION)
async def set_location(message: types.Message):
    user_id = message.from_user.id
    latitude = message.location.latitude
    longitude = message.location.longitude
    state = dp.current_state(chat=message.chat.id, user=user_id)

    timezone_id = await utils.get_timezone_id(latitude=message.location.latitude,
                                              longitude=message.location.longitude)

    if not timezone_id:
        return await bot.send_message(message.chat.id, 'Убедитесь в том что Геолокация включена и у Телеграм '
                                                       'есть права на ее использование и попробуйте снова')

    now = datetime.now(pytz.timezone(timezone_id))
    print(message.from_user.first_name, latitude, longitude, timezone_id, now)

    await location_db.merge(user_id=user_id, latitude=latitude, longitude=longitude,
                            locale=message.from_user.language_code, timezone=timezone_id)

    await bot.send_message(message.chat.id, 'Ваш часовой пояс установлен как ' + timezone_id,
                           reply_markup=types.ReplyKeyboardRemove())

    # Finish conversation, destroy all data in storage for current user
    await state.finish()


@dp.message_handler()
async def echo(message: types.Message):
    msg = "".join(re.findall("[a-zA-Zа-яА-Я]+", message.text.lower()))

    if msg in greetings:
        # send hi
        location = await location_db.get_location(message.from_user.id)
        now = datetime.now(pytz.timezone(location.tz)) if location else datetime.now()

        if 4 <= now.hour < 12:
            await message.reply('Доброе утро, {}!'.format(message.from_user.first_name))

        elif 12 <= now.hour < 17:
            await message.reply('Добрый день, {}!'.format(message.from_user.first_name))

        elif 17 <= now.hour < 23:
            await message.reply('Добрый вечер, {}!'.format(message.from_user.first_name))

        else:
            await message.reply('Привет, {}!'.format(message.from_user.first_name))

    elif msg in salem:
        await message.reply('Уа-Алейкум Ас-Салям, {}!'.format(message.from_user.first_name))

    elif msg == 'арау':
        await message.reply('Урай!')

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

    print(f'Sending WOD to {len(subscribers)} subscribers')
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
