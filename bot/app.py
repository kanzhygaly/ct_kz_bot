import os
from datetime import datetime, timedelta, date

from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.utils.emoji import emojize
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.constants import CB_SEARCH_RESULT, CB_CHOOSE_DAY, CB_ADD_RESULT, CMD_SHOW_ALL_USERS, CMD_SHOW_ALL_SUBS, \
    CMD_RESET_WOD, CMD_DISPATCH_WOD, CMD_START, CMD_HELP, CMD_SUBSCRIBE, CMD_UNSUBSCRIBE, CMD_VIEW_WOD, CMD_SEARCH, \
    CMD_FIND_WOD, CB_IGNORE, CMD_SET_TIMEZONE, CMD_VIEW_WARM_UP, CMD_ADD_WARM_UP, CMD_VIEW_RESULTS, CMD_ADD_RESULT, \
    CMD_ADD_WOD, BTN_SHOW_RESULTS, BTN_CANCEL, BTN_ADD_RESULT, BTN_EDIT_RESULT, BTN_VIEW_RESULT
from bot.constants.config_vars import ENV_API_TOKEN, BOT_NAME, ENV_NOTIFY_TO_ADD_RESULT
from bot.constants.data_keys import WOD_RESULT_TXT, WOD_RESULT_ID, WOD_ID, VIEW_WOD_ID
from bot.constants.date_format import D_M_Y, sD_B_Y, A_M_D_Y
from bot.db import user_db, wod_db, location_db, async_db, subscriber_db, wod_result_db
from bot.exception import UserNotFoundError, WodResultNotFoundError, WodNotFoundError, \
    ValueIsEmptyError, NoWodResultsError, TimezoneRequestError, WodDateNotFoundError, MsgNotRecognizedError
from bot.service import wod_result_service, wod_service
from bot.service.info_service import reply_with_info_msg, get_info_msg, get_add_result_msg, get_wod_full_text, \
    get_full_text, get_commands_list_msg
from bot.service.notification_service import send_wod_to_all_subscribers, notify_all_subscribers_to_add_result
from bot.service.user_service import add_user_if_not_exist
from bot.service.wod_result_service import persist_wod_result_and_get_message
from bot.service.wod_service import dates_are_equal
from bot.util import get_timezone_id
from bot.util.bot_util import handle_reply_to_wod_msg, rest_day, reset_state
from bot.util.chat_util import handle_chat_message
from bot.util.keyboard_util import get_add_wod_kb, get_find_wod_kb, get_search_wod_kb

bot = Bot(token=os.environ[ENV_API_TOKEN])

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
scheduler = AsyncIOScheduler()

env_notify_to_add_result = os.environ[ENV_NOTIFY_TO_ADD_RESULT]
wod_requests = ['чтс', 'что там сегодня', 'тренировка', 'треня', 'wod', 'workout']
warmup_requests = ['разминка', 'warmup']
result_requests = ['результаты', 'results']
add_requests = ['добавить', 'add']

# States
WOD = 'wod'
WOD_RESULT = 'wod_result'
FIND_WOD = 'find_wod'
SEARCH_WOD = 'search_wod'
SET_TIMEZONE = 'set_timezone'
WARM_UP = 'warm_up'
ADD_WOD = 'add_wod'
ADD_WOD_REQ = 'add_wod_req'


@dp.message_handler(commands=CMD_SHOW_ALL_USERS)
async def sys_all_users(message: types.Message):
    if not await user_db.is_admin(message.from_user.id):
        return await reply_with_info_msg(message)

    users = await user_db.get_all_users()
    str_list = [f'{i}. {u.name} {u.surname} [{u.user_id}]' for i, u in enumerate(users, 1)]
    msg = '\n'.join(str_list)

    await bot.send_message(message.chat.id, msg, parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(commands=CMD_SHOW_ALL_SUBS)
async def sys_all_subs(message: types.Message):
    if not await user_db.is_admin(message.from_user.id):
        return await reply_with_info_msg(message)

    subscribers = await subscriber_db.get_all_subscribers()
    str_list = []

    for i, sub in enumerate(subscribers, 1):
        try:
            u = await user_db.get_user(sub.user_id)
            str_list.append(f'{i}. {u.name} {u.surname} [{u.user_id}]')
        except UserNotFoundError:
            await subscriber_db.unsubscribe(sub.user_id)

    msg = '\n'.join(str_list)
    await bot.send_message(message.chat.id, msg, parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(commands=CMD_RESET_WOD)
async def sys_reset_wod(message: types.Message):
    if not await user_db.is_admin(message.from_user.id):
        return await reply_with_info_msg(message)

    today = datetime.now().date()

    done, msg = await wod_service.reset_today_wod()

    if done:
        msg = f'WOD from {today.strftime(sD_B_Y)} successfully updated!'
        await send_wod_to_all_subscribers(bot)

    await bot.send_message(message.chat.id, msg)


@dp.message_handler(commands=CMD_DISPATCH_WOD)
async def sys_dispatch_wod(message: types.Message):
    if not await user_db.is_admin(message.from_user.id):
        return await reply_with_info_msg(message)

    await send_wod_to_all_subscribers(bot)


@dp.message_handler(commands=CMD_START)
async def start(message: types.Message):
    await add_user_if_not_exist(message)

    info_msg = await get_info_msg(message.from_user.id)

    await bot.send_message(message.chat.id, info_msg)


@dp.callback_query_handler(lambda callback_query: callback_query.data == CMD_HELP)
async def help_cbq(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    info_msg = get_commands_list_msg()

    await bot.edit_message_text(text=info_msg, chat_id=chat_id, message_id=callback_query.message.message_id)

    state = dp.current_state(chat=chat_id, user=user_id)
    await reset_state(state)


@dp.message_handler(commands=CMD_HELP)
async def help_msg(message: types.Message):
    info_msg = await get_info_msg(message.from_user.id)

    await bot.send_message(message.chat.id, info_msg)


@dp.message_handler(commands=CMD_SUBSCRIBE)
async def subscribe(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    await add_user_if_not_exist(message)

    if await subscriber_db.is_subscriber(user_id):
        return await bot.send_message(chat_id, emojize('Вы уже подписаны на ежедневную рассылку WOD :alien:'))

    await subscriber_db.add_subscriber(user_id)

    await bot.send_message(chat_id, emojize('Вы подписались на ежедневную рассылку WOD :+1:'))


@dp.message_handler(commands=CMD_UNSUBSCRIBE)
async def unsubscribe(message: types.Message):
    if not (await subscriber_db.is_subscriber(message.from_user.id)):
        return await bot.send_message(message.chat.id, emojize('Вы уже отписаны от ежедневной рассылки WOD :alien:'))

    await subscriber_db.unsubscribe(message.from_user.id)

    await bot.send_message(message.chat.id, emojize('Вы отписались от ежедневной рассылки WOD :-1:'))


@dp.message_handler(commands=CMD_VIEW_WOD)
@dp.message_handler(lambda message: message.text.lower() in wod_requests)
async def send_wod(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    msg, wod_id = await wod_service.get_today_wod()

    if not msg:
        msg = 'Комплекс еще не вышел.\nСорян :('

    if wod_id:
        result_button = await get_result_button(chat_id=chat_id, user_id=user_id, wod_id=wod_id)

        # Configure ReplyKeyboardMarkup
        reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        reply_markup.add(result_button, BTN_SHOW_RESULTS)
        reply_markup.add(BTN_CANCEL)

        await bot.send_message(chat_id, msg, reply_markup=reply_markup)
    else:
        await bot.send_message(chat_id, msg)


@dp.message_handler(Text(equals=BTN_CANCEL, ignore_case=True), state='*')
@dp.message_handler(lambda message: message.text not in [BTN_ADD_RESULT, BTN_EDIT_RESULT, BTN_SHOW_RESULTS], state=WOD)
async def hide_keyboard(message: types.Message):
    chat_id = message.chat.id

    state = dp.current_state(chat=chat_id, user=message.from_user.id)
    await reset_state(state)

    await bot.send_message(chat_id, get_commands_list_msg(), reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(Text(equals=BTN_ADD_RESULT), state=WOD)
async def request_result_for_add(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    state = dp.current_state(chat=chat_id, user=user_id)
    await state.set_state(WOD_RESULT)

    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    reply_markup.add(BTN_CANCEL)

    await bot.send_message(chat_id, 'Пожалуйста введите ваш результат:', reply_markup=reply_markup)


@dp.message_handler(Text(equals=BTN_EDIT_RESULT), state=WOD)
async def request_result_for_edit(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    state = dp.current_state(chat=chat_id, user=user_id)
    await state.set_state(WOD_RESULT)

    data = await state.get_data()
    wod_result_id = data[WOD_RESULT_ID]

    try:
        wod_result = await wod_result_db.get_wod_result(wod_result_id)
        msg = get_add_result_msg(wod_result.result)
    except WodResultNotFoundError:
        msg = 'Пожалуйста введите ваш результат:'

    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    reply_markup.add(BTN_CANCEL)

    await bot.send_message(chat_id, msg, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)


async def notify_users_about_new_wod_result(user_id, wod) -> None:
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
            reply_markup.add(types.InlineKeyboardButton(BTN_VIEW_RESULT, callback_data=BTN_VIEW_RESULT))

            await bot.send_message(wr.user_id, msg, reply_markup=reply_markup)


@dp.message_handler(state=WOD_RESULT)
async def update_wod_result(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    await add_user_if_not_exist(message)

    state = dp.current_state(chat=chat_id, user=user_id)
    data = await state.get_data()

    try:
        wod_result = await wod_result_db.get_wod_result(wod_result_id=data[WOD_RESULT_ID])
        wod_id = wod_result.wod_id
    except (KeyError, WodResultNotFoundError):
        wod_id = data[WOD_ID]

    msg = await persist_wod_result_and_get_message(user_id=user_id, wod_id=wod_id, wod_result_txt=message.text)

    await bot.send_message(chat_id, msg, reply_markup=types.ReplyKeyboardRemove())

    wod = await wod_db.get_wod(wod_id)
    await notify_users_about_new_wod_result(user_id, wod)

    await reset_state(state)


@dp.message_handler(Text(equals=BTN_SHOW_RESULTS), state=WOD)
async def show_wod_results(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    state = dp.current_state(chat=chat_id, user=user_id)
    data = await state.get_data()

    wod_id = data[WOD_ID]
    try:
        wod_res_msg = await wod_result_service.get_wod_results(user_id=user_id, wod_id=wod_id)
        wod = await wod_db.get_wod(wod_id)
        msg = get_full_text(header=wod.title, body=wod_res_msg)
    except NoWodResultsError:
        msg = emojize('На сегодня результатов пока что нет :crying_cat_face:\n'
                      'Станьте первым кто внесет свой результат :smiley_cat:\n'
                      '/' + CMD_ADD_RESULT)

    await bot.send_message(chat_id, msg, reply_markup=types.ReplyKeyboardRemove(), parse_mode=ParseMode.MARKDOWN)

    await reset_state(state)


@dp.message_handler(commands=CMD_SEARCH)
async def search(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    state = dp.current_state(chat=chat_id, user=user_id)
    await state.set_state(SEARCH_WOD)

    msg = 'Введите текст для поиска: '
    await bot.send_message(chat_id, msg)


@dp.message_handler(state=SEARCH_WOD)
async def search_wod_by_text(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Finish conversation, destroy all resources in storage for current user
    state = dp.current_state(chat=chat_id, user=user_id)
    await state.reset_state()

    wod_list = await wod_service.search_wod(message.text)
    if wod_list:
        keyboard = await get_search_wod_kb(wod_list)
        reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)

        await bot.send_message(chat_id, 'Результат поиска:', reply_markup=reply_markup)
    else:
        await bot.send_message(chat_id, 'По вашему тексту ничего не найдено')


@dp.callback_query_handler(lambda callback_query: callback_query.data[0:10] == CB_SEARCH_RESULT)
async def show_search_result(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    msg, wod_id = await wod_service.get_wod_by_str_id(callback_query.data[11:])

    st = dp.current_state(chat=user_id, user=user_id)
    await st.update_data(view_wod_id=wod_id)

    reply_markup = types.InlineKeyboardMarkup()
    reply_markup.add(types.InlineKeyboardButton(BTN_VIEW_RESULT, callback_data=BTN_VIEW_RESULT))

    await bot.send_message(chat_id, msg, reply_markup=reply_markup)


@dp.callback_query_handler(lambda callback_query: callback_query.data == BTN_VIEW_RESULT)
async def view_wod_results_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    msg_id = callback_query.message.message_id

    state = dp.current_state(chat=user_id, user=user_id)
    data = await state.get_data()

    try:
        wod_id = data[VIEW_WOD_ID]

        wod_res_msg = await wod_result_service.get_wod_results(user_id=user_id, wod_id=wod_id)
        wod_day = await wod_db.get_wod_day(wod_id)

        msg = get_full_text(header=wod_day.strftime(sD_B_Y), body=wod_res_msg)
    except NoWodResultsError:
        msg = 'На этот день нет результатов'
    except KeyError:
        msg = 'Данные устарели'

    await bot.edit_message_text(text=msg, chat_id=chat_id, message_id=msg_id, parse_mode=ParseMode.MARKDOWN)

    await reset_state(state)


@dp.message_handler(commands=CMD_FIND_WOD)
async def find(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    state = dp.current_state(chat=chat_id, user=user_id)
    await state.set_state(FIND_WOD)

    keyboard = await get_find_wod_kb()
    reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)

    msg = 'Выберите день из списка либо введите дату в формате *ДеньМесяцГод* (_Пример: 170518_)'
    await bot.send_message(chat_id, msg, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)


@dp.callback_query_handler(lambda callback_query: callback_query.data[0:10] == CB_CHOOSE_DAY, state=FIND_WOD)
async def find_wod_by_btn(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    search_date = datetime.strptime(callback_query.data[11:], D_M_Y).date()
    msg, reply_markup = await find_and_get_wod(chat_id=chat_id, user_id=user_id, search_date=search_date)

    if reply_markup:
        await bot.edit_message_text(text=emojize('Результат поиска :calendar:'), chat_id=chat_id,
                                    message_id=callback_query.message.message_id, parse_mode=ParseMode.MARKDOWN)

        await bot.send_message(chat_id, msg, reply_markup=reply_markup)
    else:
        await bot.edit_message_text(text=msg, chat_id=chat_id, message_id=callback_query.message.message_id,
                                    parse_mode=ParseMode.MARKDOWN)


@dp.callback_query_handler(lambda callback_query: callback_query.data == CB_IGNORE)
async def ignore(callback_query):
    await bot.answer_callback_query(callback_query.id, text='')


@dp.message_handler(state=FIND_WOD)
async def find_wod_by_text(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    try:
        search_date = datetime.strptime(message.text, D_M_Y).date()
    except ValueError:
        msg = 'Пожалуйста введите дату в формате *ДеньМесяцГод* (_Пример: 170518_)'
        return await bot.send_message(chat_id, msg, parse_mode=ParseMode.MARKDOWN)

    msg, reply_markup = await find_and_get_wod(chat_id=chat_id, user_id=user_id, search_date=search_date)

    if reply_markup:
        await bot.send_message(chat_id, msg, reply_markup=reply_markup)
    else:
        await bot.send_message(chat_id, msg)


async def get_result_button(chat_id, user_id, wod_id) -> str:
    state = dp.current_state(chat=chat_id, user=user_id)
    await state.set_state(WOD)
    # for SHOW_RESULTS
    await state.update_data(wod_id=wod_id)

    try:
        wod_result = await wod_result_db.get_user_wod_result(wod_id=wod_id, user_id=user_id)
        button = BTN_EDIT_RESULT
        await state.update_data(wod_result_id=wod_result.id)
    except WodResultNotFoundError:
        button = BTN_ADD_RESULT

    return button


async def find_and_get_wod(chat_id, user_id, search_date: date):
    try:
        result = await wod_db.get_wod_by_date(search_date)

        result_button = await get_result_button(chat_id=chat_id, user_id=user_id, wod_id=result.id)

        # Configure ReplyKeyboardMarkup
        reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)

        time_between = datetime.now().date() - search_date
        if time_between.days > 30 and result_button == BTN_EDIT_RESULT:
            # if wod result older than month, then disable edit
            reply_markup.add(BTN_SHOW_RESULTS)
        else:
            reply_markup.add(result_button, BTN_SHOW_RESULTS)

        reply_markup.add(BTN_CANCEL)

        return get_wod_full_text(header=result.title, body=result.description), reply_markup
    except WodNotFoundError:
        state = dp.current_state(chat=chat_id, user=user_id)
        # Finish conversation, destroy all resources in storage for current user
        await state.reset_state()

        return emojize(':squirrel: На указанную дату тренировка не найдена!'), None


@dp.message_handler(commands=CMD_SET_TIMEZONE)
async def set_timezone(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    state = dp.current_state(chat=chat_id, user=user_id)
    await state.set_state(SET_TIMEZONE)

    loc_btn = types.KeyboardButton(text='Локация', request_location=True)
    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    reply_markup.insert(loc_btn)
    reply_markup.add(BTN_CANCEL)

    msg = emojize(':earth_asia: Мне нужна ваша геолокация для того, чтобы установить правильный часовой пояс')
    await bot.send_message(chat_id, msg, reply_markup=reply_markup)


@dp.message_handler(content_types=types.ContentType.LOCATION, state=SET_TIMEZONE)
async def set_location(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    latitude = message.location.latitude
    longitude = message.location.longitude

    await add_user_if_not_exist(message)

    try:
        timezone_id = await get_timezone_id(latitude, longitude)

        await location_db.add_location(user_id=user_id, latitude=latitude, longitude=longitude,
                                       locale=message.from_user.language_code, timezone=timezone_id)

        await bot.send_message(chat_id, 'Ваш часовой пояс установлен как ' + timezone_id,
                               reply_markup=types.ReplyKeyboardRemove())
    except TimezoneRequestError:
        msg = 'Убедитесь в том что Геолокация включена и у Телеграм есть права на ее использование и попробуйте снова'
        await bot.send_message(chat_id, msg)


@dp.message_handler(commands=CMD_VIEW_WARM_UP)
@dp.message_handler(lambda message: message.text.lower() in warmup_requests)
async def view_warm_up(message: types.Message):
    chat_id = message.chat.id
    today = datetime.now().date()

    try:
        result = await wod_db.get_warmup(today)
    except (WodNotFoundError, ValueIsEmptyError):
        result = emojize('На сегодня разминки пока что нет :disappointed:')

    await bot.send_message(chat_id, result, parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(commands=CMD_ADD_WARM_UP)
async def add_warm_up_request(message: types.Message):
    if not await user_db.is_admin(message.from_user.id):
        return await reply_with_info_msg(message)

    chat_id = message.chat.id

    try:
        wod_id = await wod_service.get_today_wod_id()

        state = dp.current_state(chat=chat_id, user=message.from_user.id)
        await state.set_state(WARM_UP)
        await state.update_data(wod_id=wod_id)

        msg = 'Пожалуйста введите текст:'
    except WodNotFoundError:
        msg = 'No WOD for today in DB'

    await bot.send_message(chat_id, msg)


@dp.message_handler(state=WARM_UP)
async def update_warm_up(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    state = dp.current_state(chat=chat_id, user=user_id)
    data = await state.get_data()
    wod_id = data[WOD_ID]

    try:
        await wod_db.add_warmup(wod_id, message.text)
        msg = emojize(':white_check_mark: Ваши изменения успешно выполнены!')
    except WodNotFoundError:
        msg = emojize(':heavy_exclamation_mark: Ошибка при внесении данных!')

    await bot.send_message(chat_id, msg)

    await reset_state(state)


@dp.message_handler(commands=CMD_VIEW_RESULTS)
@dp.message_handler(lambda message: message.text.lower() in result_requests)
async def view_results(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if await wod_result_service.is_allowed_to_see_wod_results(user_id):
        try:
            wod = await wod_db.get_wod_by_date(datetime.now().date())
            wod_res_msg = await wod_result_service.get_wod_results(user_id=user_id, wod_id=wod.id)
            msg = get_full_text(header=wod.title, body=wod_res_msg)
        except (WodNotFoundError, NoWodResultsError):
            msg = emojize('На сегодня результатов пока что нет :disappointed:')
    else:
        msg = emojize('На сегодня результатов нет :disappointed:')

    await bot.send_message(chat_id, msg, parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(commands=CMD_ADD_RESULT)
@dp.message_handler(lambda message: message.text.lower() in add_requests)
async def add_result(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    try:
        wod = await wod_db.get_wod_by_date(datetime.now().date())

        state = dp.current_state(chat=chat_id, user=user_id)
        await state.set_state(WOD_RESULT)
        await state.update_data(wod_id=wod.id)

        reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        reply_markup.add(BTN_CANCEL)

        try:
            wod_result = await wod_result_db.get_user_wod_result(wod_id=wod.id, user_id=user_id)
            await state.update_data(wod_result_id=wod_result.id)

            msg = get_add_result_msg(wod_result.result)
        except WodResultNotFoundError:
            msg = 'Пожалуйста введите ваш результат:'

        await bot.send_message(chat_id, msg, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    except WodNotFoundError:
        await bot.send_message(chat_id, emojize('На сегодня тренировки пока что нет :disappointed:'))


@dp.message_handler(commands=CMD_ADD_WOD)
async def sys_add_wod(message: types.Message):
    user_id = message.from_user.id

    if not await user_db.is_admin(user_id):
        return await reply_with_info_msg(message)

    chat_id = message.chat.id

    state = dp.current_state(chat=chat_id, user=user_id)
    await state.set_state(ADD_WOD)

    keyboard = await get_add_wod_kb()
    reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)

    msg = 'Выберите день из списка либо введите дату в формате *ДеньМесяцГод* (_Пример: 170518_)'
    await bot.send_message(chat_id, msg, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)


@dp.callback_query_handler(lambda callback_query: callback_query.data[0:10] == CB_CHOOSE_DAY, state=ADD_WOD)
async def add_wod_by_btn(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    wod_date = datetime.strptime(callback_query.data[11:], D_M_Y).date()

    title = wod_date.strftime(A_M_D_Y)
    wod_id = await wod_service.add_wod(wod_date=wod_date, title=title)

    state = dp.current_state(chat=chat_id, user=user_id)
    await state.set_state(ADD_WOD_REQ)
    await state.update_data(wod_id=wod_id)

    await bot.edit_message_text(text='Пожалуйста введите текст:', chat_id=chat_id,
                                message_id=callback_query.message.message_id)


@dp.message_handler(state=ADD_WOD)
async def add_wod_by_text(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    try:
        wod_date = datetime.strptime(message.text, D_M_Y).date()
    except ValueError:
        msg = 'Пожалуйста введите дату в формате *ДеньМесяцГод* (_Пример: 170518_)'
        return await bot.send_message(chat_id, msg, parse_mode=ParseMode.MARKDOWN)

    title = wod_date.strftime(A_M_D_Y)
    wod_id = await wod_service.add_wod(wod_date=wod_date, title=title)

    state = dp.current_state(chat=chat_id, user=user_id)
    await state.set_state(ADD_WOD_REQ)
    await state.update_data(wod_id=wod_id)

    await bot.send_message(chat_id, 'Пожалуйста введите текст:')


@dp.message_handler(state=ADD_WOD_REQ)
async def update_wod(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    state = dp.current_state(chat=chat_id, user=user_id)
    data = await state.get_data()
    wod_id = data[WOD_ID]

    try:
        wod = await wod_db.edit_wod(id=wod_id, description=message.text)
        msg = emojize(f':white_check_mark: WOD за {wod.wod_day.strftime(sD_B_Y)} успешно добавлен')
    except WodNotFoundError:
        msg = emojize(':heavy_exclamation_mark: Ошибка при внесении данных!')

    await bot.send_message(chat_id, msg)

    await reset_state(state)


@dp.message_handler()
async def echo(message: types.Message):
    try:
        msg = await handle_chat_message(message)
        await message.reply(msg)

    except MsgNotRecognizedError:
        now = datetime.now()
        reply_markup = types.InlineKeyboardMarkup()

        try:
            reply_to_wod_date = handle_reply_to_wod_msg(message)
            date_str = ('СЕГОДНЯ' if dates_are_equal(reply_to_wod_date, now.date())
                        else reply_to_wod_date.strftime(sD_B_Y))

            msg = f'Вы хотите добавить результат за {date_str}?'
            reply_markup.add(
                types.InlineKeyboardButton('Да', callback_data=CB_ADD_RESULT + '_' + reply_to_wod_date.strftime(D_M_Y))
            )
        except WodDateNotFoundError:
            yesterday = (now - timedelta(1)).date()
            if not rest_day(yesterday):
                msg = 'За какой день вы хотите добавить результат?'
                reply_markup.add(
                    types.InlineKeyboardButton('Вчера', callback_data=CB_ADD_RESULT + '_' + yesterday.strftime(D_M_Y)),
                    types.InlineKeyboardButton('Сегодня', callback_data=CB_ADD_RESULT + '_' + now.strftime(D_M_Y))
                )
            else:
                msg = 'Вы хотите добавить результат за СЕГОДНЯ?'
                reply_markup.add(
                    types.InlineKeyboardButton('Да', callback_data=CB_ADD_RESULT + '_' + now.strftime(D_M_Y))
                )

        reply_markup.add(types.InlineKeyboardButton('Отмена!', callback_data=CMD_HELP))

        state = dp.current_state(chat=message.chat.id, user=message.from_user.id)
        await state.update_data(wod_result_txt=message.text)

        await bot.send_message(message.chat.id, msg, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)


@dp.callback_query_handler(lambda callback_query: callback_query.data[0:10] == CB_ADD_RESULT)
async def add_result_by_date(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    msg_id = callback_query.message.message_id
    state = dp.current_state(chat=chat_id, user=user_id)

    wod_date = datetime.strptime(callback_query.data[11:], D_M_Y)

    try:
        # WodNotFoundError
        wod = await wod_db.get_wod_by_date(wod_date.date())

        data = await state.get_data()
        # KeyError
        wod_result_txt = data[WOD_RESULT_TXT]

        msg = await persist_wod_result_and_get_message(user_id=user_id, wod_id=wod.id, wod_result_txt=wod_result_txt)
        await bot.edit_message_text(text=msg, chat_id=chat_id, message_id=msg_id, parse_mode=ParseMode.MARKDOWN)

        await notify_users_about_new_wod_result(user_id, wod)
    except KeyError:
        msg = emojize('Не удалось добавить ваш результат :disappointed:\n Попробуйте снова :smiley:')
        await bot.edit_message_text(text=msg, chat_id=chat_id, message_id=msg_id, parse_mode=ParseMode.MARKDOWN)
    except WodNotFoundError:
        msg = emojize('На сегодня тренировки пока что нет :disappointed:')
        await bot.edit_message_text(text=msg, chat_id=chat_id, message_id=msg_id, parse_mode=ParseMode.MARKDOWN)

    await reset_state(state)


# https://apscheduler.readthedocs.io/en/latest/modules/triggers/cron.html#module-apscheduler.triggers.cron
# Daily WOD subscription at 06:10 GMT+6
# Second WOD dispatch 14:00 GMT+6, except Thursday and Sunday
@scheduler.scheduled_job('cron', day_of_week='mon-sun', hour=0, minute=10, id='wod_dispatch_1')
@scheduler.scheduled_job('cron', day_of_week='mon,tue,wed,fri,sat', hour=8, minute=00, id='wod_dispatch_2')
async def wod_dispatch():
    try:
        await wod_service.get_today_wod_id()
    except WodNotFoundError:
        # save WOD in DB and send it to all subscribers
        await send_wod_to_all_subscribers(bot)


# Notify to add results for Today's WOD at 23:00 GMT+6
@scheduler.scheduled_job('cron', day_of_week='mon-sun', hour=17, id='notify_to_add_result')
async def notify_to_add_result():
    if env_notify_to_add_result and env_notify_to_add_result == 'enabled':
        await notify_all_subscribers_to_add_result(bot)


async def startup(dispatcher: Dispatcher):
    print(f'Startup {BOT_NAME}...')
    async with async_db.Entity.connection() as connection:
        await async_db.create_all_tables(connection)


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


def run():
    scheduler.start()
    executor.start_polling(dispatcher=dp, on_startup=startup, on_shutdown=shutdown, skip_updates=True)


if __name__ == '__main__':
    run()
