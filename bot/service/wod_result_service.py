from datetime import datetime

import pytz
from aiogram.utils.emoji import emojize

from bot.constants.date_format import H_M_S_D_B_Y
from bot.db import user_db, location_db, wod_result_db
from bot.exception import LocationNotFoundError, WodResultNotFoundError, NoWodResultsError
from bot.util.parser_util import valid_wod_result


async def get_wod_results(user_id, wod_id) -> str:
    try:
        location = await location_db.get_location(user_id)
        timezone = pytz.timezone(location.tz)
    except LocationNotFoundError:
        timezone = None

    wod_results = await wod_result_db.get_wod_results(wod_id)
    if wod_results:
        str_list = []
        for res in wod_results:
            u = await user_db.get_user(res.user_id)

            dt = res.sys_date.astimezone(timezone) if timezone else res.sys_date
            name = f'{u.name} {u.surname}' if u.surname else u.name

            title = '_' + name + ', ' + dt.strftime(H_M_S_D_B_Y) + '_'
            str_list.append(f'{title}\n{res.result}')

        msg = '\n\n'.join(str_list)
        # replace * with x in text. if it has odd number of * then MARKDOWN will fail
        msg = msg.replace('*', 'x')

        return msg

    raise NoWodResultsError


async def is_allowed_to_see_wod_results(user_id) -> bool:
    try:
        wod_result = await wod_result_db.get_last_wod_result(user_id)

        delta = datetime.now() - wod_result.sys_date
        if delta.days > 3:
            # if user hasn't logged any results within 3 days
            # then he is not allowed to see the results
            return False

        # allowed to see results
        return True
    except WodResultNotFoundError:
        # no results at all, not allowed
        return False


async def persist_wod_result_and_get_message(user_id, wod_id, wod_result_txt: str):
    if not valid_wod_result(wod_result_txt):
        return emojize(":white_check_mark: Ваш результат успешно добавлен!")

    try:
        wod_result = await wod_result_db.get_user_wod_result(wod_id, user_id)

        wod_result.sys_date = datetime.now()
        wod_result.result = wod_result_txt
        await wod_result.save()

        return emojize(":white_check_mark: Ваш результат успешно обновлен!")
    except WodResultNotFoundError:
        await wod_result_db.add_wod_result(wod_id=wod_id, user_id=user_id, result=wod_result_txt,
                                           sys_date=datetime.now())

        return emojize(":white_check_mark: Ваш результат успешно добавлен!")


async def has_wod_result(user_id, wod_id) -> bool:
    try:
        await wod_result_db.get_user_wod_result(wod_id, user_id)
        return True
    except WodResultNotFoundError:
        return False
