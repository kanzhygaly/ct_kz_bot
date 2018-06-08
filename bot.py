import os
import re
from datetime import datetime, timedelta

import pytz
from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.types import ParseMode
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db import user_db, subscriber_db, wod_db, wod_result_db, async_db, location_db
from utils import tz_util
from utils import wod_util

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
WOD_RESULT = 'wod_result'
FIND_WOD = 'find_wod'
SET_TIMEZONE = 'set_timezone'
# Buttons
ADD_RESULT = 'Добавить'
EDIT_RESULT = 'Изменить'
SHOW_RESULTS = 'Результаты'
CANCEL = 'Отмена'
REFRESH = 'Обновить'
# CALLBACK
CHOOSE_DAY = 'choose_day'


@dp.message_handler(commands=['sys_all_users'])
async def sys_all_users(message: types.Message):
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
        msg += f'{counter}. {u.name} {u.surname}\n'
        counter += 1

    await bot.send_message(message.chat.id, msg, parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(commands=['sys_all_subs'])
async def sys_all_subs(message: types.Message):
    if not await user_db.is_admin(message.from_user.id):
        # send info
        sub = "/subscribe - подписаться на ежедневную рассылку WOD"
        if await subscriber_db.is_subscriber(message.from_user.id):
            sub = "/unsubscribe - отписаться от ежедневной рассылки WOD"

        return await message.reply(info_msg + sub)

    subscribers = await subscriber_db.get_all_subscribers()
    msg = ''
    counter = 1
    for sub in subscribers:
        u = await user_db.get_user(sub.user_id)
        if not u:
            await subscriber_db.unsubscribe(sub.user_id)
        else:
            msg += f'{counter}. {u.name} {u.surname}\n'
            counter += 1

    await bot.send_message(message.chat.id, msg, parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(commands=['test'])
async def test(message: types.Message):
    msg, wod_id = await wod_util.get_wod()
    user_id = message.from_user.id

    if wod_id is not None:
        state = dp.current_state(chat=message.chat.id, user=user_id)
        await state.update_data(wod_id=wod_id)

    # Configure InlineKeyboardMarkup
    reply_markup = types.InlineKeyboardMarkup()
    reply_markup.add(types.InlineKeyboardButton(ADD_RESULT, callback_data=ADD_RESULT),
                     types.InlineKeyboardButton(SHOW_RESULTS, callback_data=SHOW_RESULTS))

    await bot.send_message(message.chat.id, msg, reply_markup=reply_markup)


@dp.callback_query_handler(func=lambda callback_query: callback_query.data == SHOW_RESULTS)
async def show_results_callback(callback_query: types.CallbackQuery):
    state = dp.current_state(chat=callback_query.message.chat.id, user=callback_query.from_user.id)
    data = await state.get_data()

    wod_id = data['wod_id']

    msg = await wod_util.get_wod_results(callback_query.from_user.id, wod_id)

    if msg:
        await bot.send_message(callback_query.message.chat.id, msg, parse_mode=ParseMode.MARKDOWN)
        # Finish conversation, destroy all data in storage for current user
        await state.update_data(wod_id=None)
    else:
        return await bot.send_message(callback_query.message.chat.id, 'Результатов пока нет.\n'
                                                                      'Станьте первым кто внесет свой результат!')


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id

    # Check if user exist. If not, then add
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
    user_id = message.from_user.id

    # Check if user exist. If not, then add
    if not await user_db.is_user_exist(user_id):
        await user_db.add_user(user_id, message.from_user.first_name, message.from_user.last_name,
                               message.from_user.language_code)

    if await subscriber_db.is_subscriber(user_id):
        return await bot.send_message(message.chat.id, 'Вы уже подписаны на ежедневную рассылку WOD')

    await subscriber_db.add_subscriber(user_id)

    await bot.send_message(message.chat.id, 'Вы подписались на ежедневную рассылку WOD')


@dp.message_handler(commands=['unsubscribe'])
async def unsubscribe(message: types.Message):
    if not (await subscriber_db.is_subscriber(message.from_user.id)):
        return await bot.send_message(message.chat.id, 'Вы уже отписаны от ежедневной рассылки WOD')

    await subscriber_db.unsubscribe(message.from_user.id)

    await bot.send_message(message.chat.id, 'Вы отписались от ежедневной рассылки WOD')


@dp.message_handler(commands=['wod'])
@dp.message_handler(func=lambda message: message.text.lower() in wod_requests)
async def send_wod(message: types.Message):
    msg, wod_id = await wod_util.get_wod()

    if wod_id:
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
        reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True, one_time_keyboard=True)
        reply_markup.add(res_button, SHOW_RESULTS)
        reply_markup.add(CANCEL)

        await bot.send_message(message.chat.id, msg, reply_markup=reply_markup)
    else:
        await bot.send_message(message.chat.id, msg)


@dp.message_handler(state='*', func=lambda message: message.text.lower() == CANCEL.lower())
async def hide_keyboard(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    # reset
    # await state.reset_state(with_data=True)
    await state.reset_state()
    await state.update_data(wod_id=None)
    await state.update_data(wod_result_id=None)
    await bot.send_message(message.chat.id, info_msg, reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=WOD, func=lambda message: message.text == ADD_RESULT)
async def request_result_for_add(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    await state.set_state(WOD_RESULT)

    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    reply_markup.add(CANCEL)

    await bot.send_message(message.chat.id, 'Пожалуйста введите ваш результат', reply_markup=reply_markup)


@dp.message_handler(state=WOD, func=lambda message: message.text == EDIT_RESULT)
async def request_result_for_edit(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    await state.set_state(WOD_RESULT)
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


@dp.message_handler(state=WOD_RESULT)
async def update_wod_result(message: types.Message):
    user_id = message.from_user.id

    # Check if user exist. If not, then add
    if not await user_db.is_user_exist(user_id):
        await user_db.add_user(user_id, message.from_user.first_name, message.from_user.last_name,
                               message.from_user.language_code)

    state = dp.current_state(chat=message.chat.id, user=user_id)
    data = await state.get_data()

    wod_result = await wod_result_db.get_wod_result(wod_result_id=data['wod_result_id']) \
        if ('wod_result_id' in data.keys()) else None

    if wod_result:
        wod_result.sys_date = datetime.now()
        wod_result.result = message.text
        await wod_result.save()

        await bot.send_message(message.chat.id, 'Ваш результат успешно обновлен!',
                               reply_markup=types.ReplyKeyboardRemove())
    else:
        wod_id = data['wod_id']
        await wod_result_db.add_wod_result(wod_id, user_id, message.text, datetime.now())

        await bot.send_message(message.chat.id, 'Ваш результат успешно добавлен!',
                               reply_markup=types.ReplyKeyboardRemove())

    # Finish conversation, destroy all data in storage for current user
    # await state.finish()
    await state.reset_state()
    await state.update_data(wod_id=None)
    await state.update_data(wod_result_id=None)


@dp.message_handler(state=WOD, func=lambda message: message.text == SHOW_RESULTS)
async def show_wod_results(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    data = await state.get_data()

    wod_id = data['wod_id']

    msg = await wod_util.get_wod_results(message.from_user.id, wod_id)

    if msg:
        # await bot.send_message(message.chat.id, msg, reply_markup=types.ReplyKeyboardRemove(),
        #                        parse_mode=ParseMode.MARKDOWN)
        # Finish conversation, destroy all data in storage for current user
        # await state.finish()
        await state.reset_state()
        await state.update_data(wod_id=None)
        await state.update_data(wod_result_id=None)
        await state.update_data(refresh_wod_id=wod_id)

        reply_markup = types.InlineKeyboardMarkup()
        reply_markup.add(types.InlineKeyboardButton(REFRESH, callback_data=REFRESH))

        # await bot.send_message(message.chat.id, msg, reply_markup=types.ReplyKeyboardRemove(),
        #                        parse_mode=ParseMode.MARKDOWN)
        await bot.send_message(message.chat.id, msg, reply_markup=reply_markup,
                               parse_mode=ParseMode.MARKDOWN)
    else:
        return await bot.send_message(message.chat.id, 'Результатов пока нет.\n'
                                                       'Станьте первым кто внесет свой результат!')


@dp.callback_query_handler(func=lambda callback_query: callback_query.data == REFRESH)
async def refresh_results_callback(callback_query: types.CallbackQuery):
    state = dp.current_state(chat=callback_query.message.chat.id, user=callback_query.from_user.id)
    data = await state.get_data()

    wod_id = data['refresh_wod_id']

    msg = await wod_util.get_wod_results(callback_query.from_user.id, wod_id) if wod_id else None

    if msg:
        await bot.edit_message_text(text=msg, chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    parse_mode=ParseMode.MARKDOWN)
        await bot.answer_callback_query(callback_query.id, text="")


@dp.message_handler(commands=['find'])
async def find(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    await state.set_state(FIND_WOD)

    # Configure InlineKeyboardMarkup
    reply_markup = types.InlineKeyboardMarkup()
    now = datetime.now()

    row = []
    count = 5

    while count > 0:
        if len(row) < 3:
            d = now - timedelta(days=count)
            row.append(types.InlineKeyboardButton(d.strftime("%d %B"),
                                                  callback_data=CHOOSE_DAY + '_' + d.strftime("%d%m%y")))
            count -= 1
        else:
            reply_markup.row(*row)
            row = []

    row.append(types.InlineKeyboardButton("Сегодня", callback_data="ignore"))
    reply_markup.row(*row)

    msg = 'Выберите день из списка либо введите дату в формате *ДеньМесяцГод* (_Пример: 170518_)'
    await bot.send_message(message.chat.id, msg, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)


@dp.callback_query_handler(state=FIND_WOD, func=lambda callback_query: callback_query.data[0:10] == CHOOSE_DAY)
async def find_wod_by_btn(callback_query: types.CallbackQuery):
    search_date = datetime.strptime(callback_query.data[11:], '%d%m%y')
    await find_and_send_wod(callback_query.message.chat.id, callback_query.from_user.id, search_date)
    await bot.answer_callback_query(callback_query.id, text="")


@dp.callback_query_handler(func=lambda callback_query: callback_query.data == 'ignore')
async def ignore(callback_query):
    await bot.answer_callback_query(callback_query.id, text="")


@dp.message_handler(state=FIND_WOD)
async def find_wod_by_text(message: types.Message):
    try:
        search_date = datetime.strptime(message.text, '%d%m%y')
    except ValueError:
        msg = 'Пожалуйста введите дату в формате *ДеньМесяцГод* (_Пример: 170518_)'
        return await bot.send_message(message.chat.id, msg, parse_mode=ParseMode.MARKDOWN)

    await find_and_send_wod(message.chat.id, message.from_user.id, search_date)


async def find_and_send_wod(chat_id, user_id, search_date):
    time_between = datetime.now() - search_date
    state = dp.current_state(chat=chat_id, user=user_id)

    wods = await wod_db.get_wods(search_date)
    if wods:
        wod_id = wods[0].id
        title = wods[0].title
        description = wods[0].description
        res_button = ADD_RESULT

        await state.update_data(wod_id=wod_id)
        await state.set_state(WOD)

        wod_result = await wod_result_db.get_user_wod_result(wod_id=wod_id, user_id=user_id)
        if wod_result:
            res_button = EDIT_RESULT
            await state.update_data(wod_result_id=wod_result.id)

        # Configure ReplyKeyboardMarkup
        reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)

        if time_between.days > 30 and res_button == EDIT_RESULT:
            # if wod result older than month, then disable edit
            reply_markup.add(SHOW_RESULTS)
        else:
            reply_markup.add(res_button, SHOW_RESULTS)

        reply_markup.add(CANCEL)

        await bot.send_message(chat_id, title + "\n\n" + description, reply_markup=reply_markup)
    else:
        await bot.send_message(chat_id, 'На указанную дату комплекс не найден!',
                               reply_markup=types.ReplyKeyboardRemove())
        # Finish conversation, destroy all data in storage for current user
        # await state.finish()
        await state.reset_state()


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

    timezone_id = await tz_util.get_timezone_id(latitude=message.location.latitude,
                                                longitude=message.location.longitude)

    if not timezone_id:
        return await bot.send_message(message.chat.id, 'Убедитесь в том что Геолокация включена и у Телеграм '
                                                       'есть права на ее использование и попробуйте снова')

    now = datetime.now(pytz.timezone(timezone_id))
    print(message.from_user.first_name, latitude, longitude, timezone_id, now)

    # Check if user exist. If not, then add
    if not await user_db.is_user_exist(user_id):
        await user_db.add_user(user_id, message.from_user.first_name, message.from_user.last_name,
                               message.from_user.language_code)

    await location_db.merge(user_id=user_id, latitude=latitude, longitude=longitude,
                            locale=message.from_user.language_code, timezone=timezone_id)

    await bot.send_message(message.chat.id, 'Ваш часовой пояс установлен как ' + timezone_id,
                           reply_markup=types.ReplyKeyboardRemove())

    # Finish conversation, destroy all data in storage for current user
    # await state.finish()
    await state.reset_state()


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

    msg, wod_id = await wod_util.get_wod()

    print(f'Sending WOD to {len(subscribers)} subscribers')
    if wod_id:
        for sub in subscribers:
            res_button = ADD_RESULT

            state = dp.current_state(chat=sub.user_id, user=sub.user_id)
            await state.update_data(wod_id=wod_id)
            await state.set_state(WOD)

            wod_result = await wod_result_db.get_user_wod_result(wod_id=wod_id, user_id=sub.user_id)
            if wod_result:
                res_button = EDIT_RESULT
                await state.update_data(wod_result_id=wod_result.id)

            # Configure ReplyKeyboardMarkup
            reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
            reply_markup.add(res_button, SHOW_RESULTS)
            reply_markup.add(CANCEL)

            await bot.send_message(sub.user_id, msg, reply_markup=reply_markup)
    else:
        for sub in subscribers:
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
