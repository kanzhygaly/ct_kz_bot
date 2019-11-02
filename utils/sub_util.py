from db import subscriber_db
from utils import wod_util


async def send_wod_to_all_subscribers(bot):
    subscribers = await subscriber_db.get_all_subscribers()

    msg, wod_id = await wod_util.get_wod()

    if wod_id:
        msg += "\n\n/add - записать/изменить результат за СЕГОДНЯ\n" \
               "/results - посмотреть результаты за СЕГОДНЯ"

    print(f'Sending WOD to {len(subscribers)} subscribers')
    for sub in subscribers:
        await bot.send_message(sub.user_id, msg)


