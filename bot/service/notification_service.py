from aiogram import types, Bot
from aiogram.utils.emoji import emojize
from aiogram.utils.exceptions import UserDeactivated, BotBlocked

from bot.constants import CMD_ADD_RESULT, CMD_VIEW_RESULTS
from bot.db import subscriber_db
from bot.exception import WodNotFoundError
from bot.service.wod_result_service import has_wod_result
from bot.service.wod_service import get_today_wod, get_today_wod_id


async def send_wod_to_all_subscribers(bot: Bot) -> None:
    subscribers = await subscriber_db.get_all_subscribers()

    msg, wod_id = await get_today_wod()

    if not msg:
        return

    if wod_id:
        msg += (f'\n/{CMD_ADD_RESULT} - записать/изменить результат\n'
                f'/{CMD_VIEW_RESULTS} - посмотреть результаты')

    count = 0
    for sub in subscribers:
        try:
            await bot.send_message(sub.user_id, msg)
            count += 1
        except UserDeactivated:
            print(f'User {sub.user_id} is deactivated, deleting him from subscribers')
            await subscriber_db.unsubscribe(sub.user_id)
        except BotBlocked:
            print(f'User {sub.user_id} has blocked the Bot, deleting him from subscribers')
            await subscriber_db.unsubscribe(sub.user_id)

    print(f'WOD has been sent to {count} subscribers')


async def notify_all_subscribers_to_add_result(bot: Bot) -> None:
    try:
        wod_id = await get_today_wod_id()

        subscribers = await subscriber_db.get_all_subscribers()

        msg = (':bell: Не забудьте записать результат сегодняшней тренировки\n\n'
               f'Наберите команду /{CMD_ADD_RESULT} или просто отправьте сообщением')

        for sub in subscribers:
            if await has_wod_result(user_id=sub.user_id, wod_id=wod_id):
                continue

            try:
                await bot.send_message(sub.user_id, emojize(msg), reply_markup=types.ReplyKeyboardRemove())
            except UserDeactivated:
                print(f'User {sub.user_id} is deactivated, deleting him from subscribers')
                await subscriber_db.unsubscribe(sub.user_id)
    except WodNotFoundError:
        print('notify_all_subscribers_to_add_result: WOD was not found. Today is a rest day.')
