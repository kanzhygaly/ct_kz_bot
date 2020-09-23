from datetime import datetime, timedelta
from typing import Iterable

from aiogram import types

from bot.constants import CB_CHOOSE_DAY, CB_IGNORE, CB_SEARCH_RESULT
from bot.constants.date_format import D_M_Y, A_D_B, D_B, WEEKDAY, sD_sB_Y
from bot.db import wod_db
from bot.util.bot_util import rest_day


async def get_add_wod_kb() -> list:
    today = datetime.now()
    keyboard = []
    row = []
    count = 9

    # if today is Thursday then include it
    if today.weekday() == 3:
        count = 8
        btn_name = today.strftime(A_D_B)
        row.append(types.InlineKeyboardButton(btn_name, callback_data=CB_CHOOSE_DAY + '_' + today.strftime(D_M_Y)))

    while count >= 0:
        if len(row) < 3:
            if today.weekday() <= 3:
                delta = 1 + today.weekday()
                today = today - timedelta(days=delta)
            elif today.weekday() > 3:
                delta = today.weekday() - 3
                today = today - timedelta(days=delta)

            btn_name = today.strftime(A_D_B)

            row.append(types.InlineKeyboardButton(btn_name, callback_data=CB_CHOOSE_DAY + '_' + today.strftime(D_M_Y)))
            count -= 1
        else:
            keyboard.append(row)
            row = []

    return keyboard


async def get_find_wod_kb() -> list:
    today = datetime.now()
    keyboard = []
    row = []
    count = 5

    while count > 0:
        if len(row) < 3:
            d = today - timedelta(days=count)
            btn_name = d.strftime(WEEKDAY) if rest_day(d) else d.strftime(D_B)

            row.append(types.InlineKeyboardButton(btn_name, callback_data=CB_CHOOSE_DAY + '_' + d.strftime(D_M_Y)))
            count -= 1
        else:
            keyboard.append(row)
            row = []

    row.append(types.InlineKeyboardButton("Сегодня", callback_data=CB_IGNORE))
    keyboard.append(row)

    return keyboard


async def get_search_wod_kb(wod_list: Iterable[wod_db.WOD]) -> list:
    keyboard = []
    row = []

    for wod in wod_list:
        if len(row) < 3:
            btn_name = wod.wod_day.strftime(sD_sB_Y)

            row.append(types.InlineKeyboardButton(btn_name, callback_data=CB_SEARCH_RESULT + '_' + wod.id.hex))
        else:
            keyboard.append(row)
            row = []

    return keyboard
