from aiogram import types

from bot.constants import CMD_UNSUBSCRIBE, CMD_SUBSCRIBE, CMD_SHOW_ALL_USERS, CMD_SHOW_ALL_SUBS, CMD_RESET_WOD, \
    CMD_DISPATCH_WOD, CMD_ADD_WARM_UP, CMD_ADD_WOD, CMD_VIEW_WARM_UP, CMD_SEARCH, CMD_SET_TIMEZONE, CMD_FIND_WOD, \
    CMD_ADD_RESULT, CMD_VIEW_RESULTS, CMD_VIEW_WOD, CMD_HELP, WOD_STR
from bot.db.subscriber_db import is_subscriber
from bot.db.user_db import is_admin

info_msg = (
    'CompTrainKZ BOT:\n\n'
    f'/{CMD_HELP} - справочник\n\n'
    f'/{CMD_VIEW_WOD} - тренировка на сегодня\n\n'
    f'/{CMD_VIEW_RESULTS} - результаты на сегодня\n\n'
    f'/{CMD_ADD_RESULT} - записать результат тренировки на сегодня\n\n'
    f'/{CMD_FIND_WOD} - найти тренировку по дате\n\n'
    f'/{CMD_SET_TIMEZONE} - установить часовой пояс\n\n'
    f'/{CMD_SEARCH} - поиск результатов по тексту комплекса\n\n'
)

admin_msg = (
    f'/{CMD_SHOW_ALL_USERS} - list all users\n\n'
    f'/{CMD_SHOW_ALL_SUBS} - list all subscribers\n\n'
    f'/{CMD_RESET_WOD} - reset WOD and send it to all subscribers\n\n'
    f'/{CMD_DISPATCH_WOD} - send WOD to all subscribers\n\n'
    f'/{CMD_ADD_WOD} - add custom WOD\n\n'
    f'/{CMD_ADD_WARM_UP} - add custom Warm up for today\n\n'
    f'/{CMD_VIEW_WARM_UP} - view Warm up for today\n\n'
)


async def reply_with_info_msg(message: types.Message):
    subscriber_msg = await get_subscriber_msg(message.from_user.id)

    await message.reply(info_msg + subscriber_msg)


async def get_info_msg(user_id):
    subscriber_msg = await get_subscriber_msg(user_id)

    if await is_admin(user_id):
        return info_msg + admin_msg + subscriber_msg

    return info_msg + subscriber_msg


async def get_subscriber_msg(user_id):
    if await is_subscriber(user_id):
        return f'/{CMD_UNSUBSCRIBE} - отписаться от ежедневной рассылки WOD'

    return f'/{CMD_SUBSCRIBE} - подписаться на ежедневную рассылку WOD'


def get_wod_full_text(header: str, body: str) -> str:
    return WOD_STR + ' // ' + header + '\n\n' + body


def get_full_text(header: str, body: str) -> str:
    return header + '\n\n' + body


def get_add_result_msg(wod_result: str) -> str:
    return f'Ваш текущий результат:\n\n_{wod_result}_\n\nПожалуйста введите ваш новый результат'
