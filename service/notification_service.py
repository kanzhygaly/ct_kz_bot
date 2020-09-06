from datetime import datetime

from aiogram import types
from aiogram.utils.emoji import emojize
from aiogram.utils.exceptions import UserDeactivated

from bot import VIEW_RESULT
from db import subscriber_db, wod_result_db, wod_db, user_db
from service import wod_service


async def send_wod_to_all_subscribers(bot):
    subscribers = await subscriber_db.get_all_subscribers()

    msg, wod_id = await wod_service.get_wod()

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


async def notify_all_subscribers_to_add_result(bot):
    wod_id = await wod_service.get_wod_id()

    if wod_id:
        subscribers = await subscriber_db.get_all_subscribers()

        msg = "Не забудьте записать результат сегодняшней тренировки :grimacing:\n" \
              "Для того чтобы записать результат за СЕГОДНЯ наберите команду /add"

        for sub in subscribers:
            if await wod_result_db.get_user_wod_result(wod_id=wod_id, user_id=sub.user_id):
                continue

            try:
                await bot.send_message(sub.user_id, emojize(msg), reply_markup=types.ReplyKeyboardRemove())
            except UserDeactivated:
                print(f'User {sub.user_id} is deactivated, deleting him from subscribers')
                await subscriber_db.unsubscribe(sub.user_id)


async def notify_users_about_new_wod_result(user_id, wod_id, dp, bot):
    wod = await wod_db.get_wod(wod_id)
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
