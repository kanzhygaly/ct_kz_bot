from aiogram import types
from aiogram.utils.emoji import emojize
from aiogram.utils.exceptions import UserDeactivated

from db import subscriber_db
from exception import WodNotFoundError
from service.wod_result_service import has_wod_result
from service.wod_service import get_today_wod, get_today_wod_id


async def send_wod_to_all_subscribers(bot) -> None:
    subscribers = await subscriber_db.get_all_subscribers()

    msg, wod_id = await get_today_wod()

    if wod_id:
        msg += "\n\n/add - записать/изменить результат за СЕГОДНЯ\n" \
               "/results - посмотреть результаты за СЕГОДНЯ"

    print(f'Sending WOD to {len(subscribers)} subscribers')
    for sub in subscribers:
        try:
            await bot.send_message(sub.user_id, msg)
        except UserDeactivated:
            print(f'User {sub.user_id} is deactivated, deleting him from subscribers')
            await subscriber_db.unsubscribe(sub.user_id)


async def notify_all_subscribers_to_add_result(bot) -> None:
    try:
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
