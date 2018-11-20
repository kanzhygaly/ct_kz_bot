import os
import re
from datetime import datetime, timedelta

import pytz
from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.utils.emoji import emojize
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
warmup_requests = ['разминка', 'warmup']
result_requests = ['результаты', 'results']
add_requests = ['добавить', 'add']

info_msg = 'CompTrainKZ BOT:\n\n' \
           '/help - справочник\n\n' \
           '/wod - тренировка на сегодня\n\n' \
           '/results - результаты за сегодня\n\n' \
           '/add - записать результат тренировки за сегодня\n\n' \
           '/find - найти тренировку по дате\n\n' \
           '/timezone - установить часовой пояс\n\n'

# States
WOD = 'wod'
WOD_RESULT = 'wod_result'
FIND_WOD = 'find_wod'
SET_TIMEZONE = 'set_timezone'
WARM_UP = 'warm_up'
# Buttons
ADD_RESULT = 'Добавить'
EDIT_RESULT = 'Изменить'
SHOW_RESULTS = 'Результаты'
CANCEL = 'Отмена'
REFRESH = 'Обновить'
VIEW_RESULT = 'Посмотреть результат'
# Commands
HELP = 'help'
# CALLBACK
CB_CHOOSE_DAY = 'choose_day'
CB_ADD_RESULT = 'add_result'


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


@dp.callback_query_handler(func=lambda callback_query: callback_query.data == HELP)
async def help_cbq(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    # Destroy all data in storage for current user
    state = dp.current_state(chat=callback_query.chat.id, user=user_id)
    await state.update_data(wod_result_txt=None)

    sub = "/subscribe - подписаться на ежедневную рассылку WOD"
    if await subscriber_db.is_subscriber(user_id):
        sub = "/unsubscribe - отписаться от ежедневной рассылки WOD"

    await bot.answer_callback_query(callback_query.id, text=info_msg + sub)


@dp.message_handler(commands=[HELP])
async def help_msg(message: types.Message):
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
        return await bot.send_message(message.chat.id, emojize("Вы уже подписаны на ежедневную рассылку WOD :alien:"))

    await subscriber_db.add_subscriber(user_id)

    await bot.send_message(message.chat.id, emojize("Вы подписались на ежедневную рассылку WOD :+1:"))


@dp.message_handler(commands=['unsubscribe'])
async def unsubscribe(message: types.Message):
    if not (await subscriber_db.is_subscriber(message.from_user.id)):
        return await bot.send_message(message.chat.id, emojize("Вы уже отписаны от ежедневной рассылки WOD :alien:"))

    await subscriber_db.unsubscribe(message.from_user.id)

    await bot.send_message(message.chat.id, emojize("Вы отписались от ежедневной рассылки WOD :-1:"))


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
        reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        reply_markup.add(res_button, SHOW_RESULTS)
        reply_markup.add(CANCEL)

        await bot.send_message(message.chat.id, msg, reply_markup=reply_markup)
    else:
        await bot.send_message(message.chat.id, msg)


@dp.message_handler(state='*', func=lambda message: message.text.lower() == CANCEL.lower())
async def hide_keyboard(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    # reset
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

    await bot.send_message(message.chat.id, 'Пожалуйста введите ваш результат:', reply_markup=reply_markup)


@dp.message_handler(state=WOD, func=lambda message: message.text == EDIT_RESULT)
async def request_result_for_edit(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    await state.set_state(WOD_RESULT)
    data = await state.get_data()

    msg = 'Пожалуйста введите ваш результат:'

    wod_result_id = data['wod_result_id']
    wod_result = await wod_result_db.get_wod_result(wod_result_id=wod_result_id)
    if wod_result:
        msg = 'Ваш текущий результат:\n\n_' \
              + wod_result.result + \
              '_\n\nПожалуйста введите ваш новый результат:'

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

        await bot.send_message(message.chat.id, emojize(":white_check_mark: Ваш результат успешно обновлен!"),
                               reply_markup=types.ReplyKeyboardRemove())
    else:
        wod_id = data['wod_id']
        await wod_result_db.add_wod_result(wod_id, user_id, message.text, datetime.now())

        await bot.send_message(message.chat.id, emojize(":white_check_mark: Ваш результат успешно добавлен!"),
                               reply_markup=types.ReplyKeyboardRemove())

        # Notify other users that new result was added
        wod = await wod_db.get_wod(wod_id)
        diff = datetime.now().date() - wod.wod_day

        if diff.days < 2:
            author = await user_db.get_user(user_id)
            name = f'{author.name} {author.surname}' if author.surname else author.name
            msg = f'{name} записал результат за {wod.title}'

            wod_results = await wod_result_db.get_wod_results(wod_id)
            for wr in wod_results:
                if wr.user_id == user_id:
                    continue

                st = dp.current_state(chat=wr.user_id, user=wr.user_id)
                await st.update_data(view_wod_id=wod_id)

                reply_markup = types.InlineKeyboardMarkup()
                reply_markup.add(types.InlineKeyboardButton(VIEW_RESULT, callback_data=VIEW_RESULT))

                await bot.send_message(wr.user_id, msg, reply_markup=reply_markup)

    # Finish conversation, destroy all data in storage for current user
    await state.reset_state()
    await state.update_data(wod_id=None)
    await state.update_data(wod_result_id=None)


@dp.message_handler(state=WOD, func=lambda message: message.text == SHOW_RESULTS)
async def show_wod_results(message: types.Message):
    user_id = message.from_user.id

    state = dp.current_state(chat=message.chat.id, user=user_id)
    data = await state.get_data()

    wod_id = data['wod_id']

    msg = await wod_util.get_wod_results(user_id, wod_id)

    if msg:
        # await bot.send_message(message.chat.id, msg, reply_markup=types.ReplyKeyboardRemove(),
        #                        parse_mode=ParseMode.MARKDOWN)
        # Finish conversation, destroy all data in storage for current user
        await state.reset_state()
        await state.update_data(wod_id=None)
        await state.update_data(wod_result_id=None)
        await state.update_data(refresh_wod_id=wod_id)

        wod = await wod_db.get_wod(wod_id)

        await bot.send_message(message.chat.id, wod.title, reply_markup=types.ReplyKeyboardRemove(),
                               parse_mode=ParseMode.MARKDOWN)

        reply_markup = types.InlineKeyboardMarkup()
        reply_markup.add(types.InlineKeyboardButton(REFRESH, callback_data=REFRESH))

        await bot.send_message(message.chat.id, msg, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    else:
        return await bot.send_message(message.chat.id, emojize("На сегодня результатов пока что нет :crying_cat_face:"
                                                               "\nСтаньте первым кто внесет свой "
                                                               "результат :smiley_cat:\n/add"))


@dp.callback_query_handler(func=lambda callback_query: callback_query.data == REFRESH)
async def refresh_wod_results_callback(callback_query: types.CallbackQuery):
    state = dp.current_state(chat=callback_query.message.chat.id, user=callback_query.from_user.id)
    data = await state.get_data()

    wod_id = data['refresh_wod_id'] if ('refresh_wod_id' in data.keys()) else None

    msg = await wod_util.get_wod_results(callback_query.from_user.id, wod_id) if wod_id else None

    if msg:
        await bot.edit_message_text(text=msg, chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    parse_mode=ParseMode.MARKDOWN)

        reply_markup = types.InlineKeyboardMarkup()
        reply_markup.add(types.InlineKeyboardButton(REFRESH, callback_data=REFRESH))

        await bot.edit_message_reply_markup(chat_id=callback_query.message.chat.id,
                                            message_id=callback_query.message.message_id, reply_markup=reply_markup)


@dp.callback_query_handler(func=lambda callback_query: callback_query.data == VIEW_RESULT)
async def view_wod_results_callback(callback_query: types.CallbackQuery):
    state = dp.current_state(chat=callback_query.from_user.id, user=callback_query.from_user.id)
    data = await state.get_data()

    wod_id = data['view_wod_id'] if ('view_wod_id' in data.keys()) else None

    msg = await wod_util.get_wod_results(callback_query.from_user.id, wod_id) if wod_id else None

    if msg:
        await bot.edit_message_text(text=msg, chat_id=callback_query.message.chat.id,
                                    message_id=callback_query.message.message_id,
                                    parse_mode=ParseMode.MARKDOWN)
        await state.update_data(view_wod_id=None)


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
            btn_name = d.strftime("%A") if d.weekday() in (3, 6) else d.strftime("%d %B")

            row.append(types.InlineKeyboardButton(btn_name, callback_data=CB_CHOOSE_DAY + '_' + d.strftime("%d%m%y")))
            count -= 1
        else:
            reply_markup.row(*row)
            row = []

    row.append(types.InlineKeyboardButton("Сегодня", callback_data="ignore"))
    reply_markup.row(*row)

    msg = 'Выберите день из списка либо введите дату в формате *ДеньМесяцГод* (_Пример: 170518_)'
    await bot.send_message(message.chat.id, msg, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)


@dp.callback_query_handler(state=FIND_WOD, func=lambda callback_query: callback_query.data[0:10] == CB_CHOOSE_DAY)
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
        await bot.send_message(chat_id, emojize(":squirrel: На указанную дату тренировка не найдена!"),
                               reply_markup=types.ReplyKeyboardRemove())
        # Finish conversation, destroy all data in storage for current user
        await state.reset_state()


@dp.message_handler(commands=['timezone'])
async def set_timezone(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    await state.set_state(SET_TIMEZONE)

    loc_btn = types.KeyboardButton(text="Локация", request_location=True)
    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    reply_markup.insert(loc_btn)
    reply_markup.add(CANCEL)

    await bot.send_message(message.chat.id, emojize(":earth_asia: Мне нужна ваша геолокация для того,"
                                                    "чтобы установить правильный часовой пояс"),
                           reply_markup=reply_markup)


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
    await state.reset_state()


@dp.message_handler(commands=['warmup'])
@dp.message_handler(func=lambda message: message.text.lower() in warmup_requests)
async def view_warmup(message: types.Message):
    today = datetime.now().date()
    result = await wod_db.get_warmup(today)
    if result:
        await bot.send_message(message.chat.id, result)
    else:
        await bot.send_message(message.chat.id, emojize("На сегодня разминки пока что нет :disappointed:"))


@dp.message_handler(commands=['add_warmup'])
async def add_warmup_request(message: types.Message):
    if not await user_db.is_admin(message.from_user.id):
        # send info
        sub = "/subscribe - подписаться на ежедневную рассылку WOD"
        if await subscriber_db.is_subscriber(message.from_user.id):
            sub = "/unsubscribe - отписаться от ежедневной рассылки WOD"

        return await message.reply(info_msg + sub)

    result = await wod_db.get_wods(datetime.now().date())
    if result:
        wod_id = result[0].id

        state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
        await state.set_state(WARM_UP)
        await state.update_data(wod_id=wod_id)

    await bot.send_message(message.chat.id, 'Пожалуйста введите текст:')


@dp.message_handler(state=WARM_UP)
async def update_warmup(message: types.Message):
    state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
    data = await state.get_data()
    wod_id = data['wod_id']

    if await wod_db.add_warmup(wod_id, message.text):
        await bot.send_message(message.chat.id, emojize(":white_check_mark: Ваши изменения успешно выполнены!"))
    else:
        await bot.send_message(message.chat.id, emojize(":heavy_exclamation_mark: Ошибка при внесении данных!"))

    # Finish conversation, destroy all data in storage for current user
    await state.reset_state()
    await state.update_data(wod_id=None)


@dp.message_handler(commands=['results'])
@dp.message_handler(func=lambda message: message.text.lower() in result_requests)
async def view_results(message: types.Message):
    user_id = message.from_user.id

    wod = await wod_db.get_wod_by_date(datetime.now().date())

    msg = await wod_util.get_wod_results(user_id, wod.id) if wod else None

    if msg:
        await bot.send_message(message.chat.id, f'{wod.title}\n\n{msg}', parse_mode=ParseMode.MARKDOWN)
    else:
        await bot.send_message(message.chat.id, emojize("На сегодня результатов пока что нет :disappointed:"))


@dp.message_handler(commands=['add'])
@dp.message_handler(func=lambda message: message.text.lower() in add_requests)
async def add_result(message: types.Message):
    wod = await wod_db.get_wod_by_date(datetime.now().date())
    if wod:
        user_id = message.from_user.id

        state = dp.current_state(chat=message.chat.id, user=user_id)
        await state.set_state(WOD_RESULT)
        await state.update_data(wod_id=wod.id)

        reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        reply_markup.add(CANCEL)

        wod_result = await wod_result_db.get_user_wod_result(wod_id=wod.id, user_id=user_id)

        msg = 'Пожалуйста введите ваш результат:'
        if wod_result:
            await state.update_data(wod_result_id=wod_result.id)
            msg = 'Ваш текущий результат:\n\n_' + wod_result.result + '_\n\nПожалуйста введите ваш новый результат'

        await bot.send_message(message.chat.id, msg, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    else:
        await bot.send_message(message.chat.id, emojize("На сегодня тренировки пока что нет :disappointed:"))


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
        await message.reply(emojize("Урай! :punch:"))

    else:
        location = await location_db.get_location(message.from_user.id)
        now = datetime.now(pytz.timezone(location.tz)) if location else datetime.now()

        yesterday = (now - timedelta(1)).date()

        reply_markup = types.InlineKeyboardMarkup()

        if yesterday.weekday() not in (3, 6):
            msg = 'За какой день вы хотите добавить результат?'
            reply_markup.add(
                types.InlineKeyboardButton("Вчера", callback_data=CB_ADD_RESULT + '_' + yesterday.strftime("%d%m%y")),
                types.InlineKeyboardButton("Сегодня", callback_data=CB_ADD_RESULT + '_' + now.strftime("%d%m%y"))
            )
        else:
            msg = 'Вы хотите добавить результат за СЕГОДНЯ?'
            reply_markup.add(
                types.InlineKeyboardButton("Да", callback_data=CB_ADD_RESULT + '_' + now.strftime("%d%m%y"))
            )

        reply_markup.add(types.InlineKeyboardButton("Нет!", callback_data=HELP))

        state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
        await state.update_data(wod_result_txt=message.text)

        await bot.send_message(message.chat.id, msg, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)


@dp.callback_query_handler(func=lambda callback_query: callback_query.data[0:10] == CB_ADD_RESULT)
async def add_result_by_date(callback_query: types.CallbackQuery):
    wod_date = datetime.strptime(callback_query.data[11:], '%d%m%y')

    wod = await wod_db.get_wod_by_date(wod_date)
    if wod:
        user_id = callback_query.from_user.id
        chat_id = callback_query.chat.id

        state = dp.current_state(chat=chat_id, user=user_id)
        data = await state.get_data()

        if 'wod_result_txt' in data.keys():
            wod_result_txt = data['wod_result_txt']
            # Destroy all data in storage for current user
            await state.update_data(wod_result_txt=None)

            wod_result = await wod_result_db.get_user_wod_result(wod_id=wod.id, user_id=user_id)

            if wod_result:
                wod_result.sys_date = datetime.now()
                wod_result.result = wod_result_txt
                await wod_result.save()

                await bot.send_message(chat_id, emojize(":white_check_mark: Ваш результат успешно обновлен!"),
                                       reply_markup=types.ReplyKeyboardRemove())
            else:
                await wod_result_db.add_wod_result(wod.id, user_id, wod_result_txt, datetime.now())

                await bot.send_message(chat_id, emojize(":white_check_mark: Ваш результат успешно добавлен!"),
                                       reply_markup=types.ReplyKeyboardRemove())

                # Notify other users that new result was added
                diff = datetime.now().date() - wod.wod_day
                if diff.days < 2:
                    author = await user_db.get_user(user_id)
                    name = f'{author.name} {author.surname}' if author.surname else author.name
                    msg = f'{name} записал результат за {wod.title}'

                    wod_results = await wod_result_db.get_wod_results(wod.id)
                    for wr in wod_results:
                        if wr.user_id == user_id:
                            continue

                        st = dp.current_state(chat=wr.user_id, user=wr.user_id)
                        await st.update_data(view_wod_id=wod.id)

                        reply_markup = types.InlineKeyboardMarkup()
                        reply_markup.add(types.InlineKeyboardButton(VIEW_RESULT, callback_data=VIEW_RESULT))

                        await bot.send_message(wr.user_id, msg, reply_markup=reply_markup)


# Daily WOD subscription at 07:00 GMT+6
@scheduler.scheduled_job('cron', day_of_week='mon-sun', hour=1, id='wod_dispatch')
async def wod_dispatch():
    print('This job runs everyday at 7 am')
    subscribers = await subscriber_db.get_all_subscribers()

    msg, wod_id = await wod_util.get_wod()

    msg += "\n\n/add - записать/изменить результат за СЕГОДНЯ" \
           "/results - посмотреть результаты за СЕГОДНЯ"

    print(f'Sending WOD to {len(subscribers)} subscribers')
    for sub in subscribers:
        await bot.send_message(sub.user_id, msg)


# Notify to add results for Today's WOD at 23:00 GMT+6
@scheduler.scheduled_job('cron', day_of_week='mon-sun', hour=17, id='notify_to_add_result')
async def notify_to_add_result():
    msg, wod_id = await wod_util.get_wod()

    if wod_id:
        subscribers = await subscriber_db.get_all_subscribers()

        msg = "Не забудьте записать результат сегодняшней тренировки :grimacing:\n" \
              "Для того чтобы записать результат за СЕГОДНЯ наберите команду /add"

        for sub in subscribers:
            if await wod_result_db.get_user_wod_result(wod_id=wod_id, user_id=sub.user_id):
                continue

            await bot.send_message(sub.user_id, emojize(msg), reply_markup=types.ReplyKeyboardRemove())


async def startup(dispatcher: Dispatcher):
    print('Startup CompTrainKZ Bot...')
    async with async_db.Entity.connection() as connection:
        await async_db.create_all_tables(connection)


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


if __name__ == '__main__':
    scheduler.start()

    executor.start_polling(dp, on_startup=startup, on_shutdown=shutdown)
