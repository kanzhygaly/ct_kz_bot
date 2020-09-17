from aiogram import types

from bot.db.subscriber_db import is_subscriber
from bot.db.user_db import is_admin

info_msg = 'CompTrainKZ BOT:\n\n' \
           '/help - справочник\n\n' \
           '/wod - тренировка на сегодня\n\n' \
           '/results - результаты на сегодня\n\n' \
           '/add - записать результат тренировки на сегодня\n\n' \
           '/find - найти тренировку по дате\n\n' \
           '/timezone - установить часовой пояс\n\n' \
           '/search - поиск результатов по тексту комплекса\n\n'

admin_msg = '/sys_all_users - list all users\n\n' \
            '/sys_all_subs - list all subscribers\n\n' \
            '/sys_reset_wod - reset WOD and send it to all subscribers\n\n' \
            '/sys_dispatch_wod - send WOD to all subscribers\n\n' \
            '/sys_add_wod - add custom WOD\n\n'


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
        return "/unsubscribe - отписаться от ежедневной рассылки WOD"

    return "/subscribe - подписаться на ежедневную рассылку WOD"
