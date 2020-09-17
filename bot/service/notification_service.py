from aiogram import types, Bot
from aiogram.utils.emoji import emojize
from aiogram.utils.exceptions import UserDeactivated

from bot.db import subscriber_db
from bot.exception import WodNotFoundError
from bot.service.wod_result_service import has_wod_result
from bot.service.wod_service import get_today_wod, get_today_wod_id


async def send_wod_to_all_subscribers() -> None:
    bot = Bot.get_current()

    subscribers = await subscriber_db.get_all_subscribers()

    msg, wod_id = await get_today_wod()

    if wod_id:
        msg += "\n\n/add - записать/изменить результат за СЕГОДНЯ\n" \
               "/results - посмотреть результаты за СЕГОДНЯ"

    count = 0
    for sub in subscribers:
        try:
            await bot.send_message(sub.user_id, msg)
            count += 1
        except UserDeactivated:
            print(f'User {sub.user_id} is deactivated, deleting him from subscribers')
            await subscriber_db.unsubscribe(sub.user_id)

    print(f'WOD has been sent to {count} subscribers')


async def notify_all_subscribers_to_add_result() -> None:
    try:
        bot = Bot.get_current()

        wod_id = await get_today_wod_id()

        subscribers = await subscriber_db.get_all_subscribers()

        msg = "Не забудьте записать результат сегодняшней тренировки :grimacing:\n" \
              "Для того чтобы записать результат за СЕГОДНЯ наберите команду /add"

        for sub in subscribers:
            if await has_wod_result(user_id=sub.user_id, wod_id=wod_id):
                continue

            try:
                await bot.send_message(sub.user_id, emojize(msg), reply_markup=types.ReplyKeyboardRemove())
            except UserDeactivated:
                print(f'User {sub.user_id} is deactivated, deleting him from subscribers')
                await subscriber_db.unsubscribe(sub.user_id)
    except WodNotFoundError:
        print('notify_all_subscribers_to_add_result: WOD for today was not found')
