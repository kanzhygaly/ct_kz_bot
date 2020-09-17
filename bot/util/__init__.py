from datetime import datetime, timedelta

import requests
from aiogram import types

from bot.constants import CB_CHOOSE_DAY, CB_IGNORE, CB_SEARCH_RESULT
from bot.constants.date_format import D_M_Y, A_D_B, D_B, WEEKDAY, sD_sB_Y
from bot.exception import TimezoneRequestError


async def get_timezone_id(latitude: float, longitude: float) -> str:
    try:
        payload = {'username': 'atareao', 'lng': longitude, 'lat': latitude}
        response = requests.get(url='http://api.geonames.org/timezoneJSON', params=payload)
        json_response = response.json()

        if json_response and ('timezoneId' in json_response.keys()):
            return json_response['timezoneId']

        raise Exception
    except Exception as e:
        print('Error requesting timezone identification: %s' % (str(e)))
        try:
            payload = {'lng': longitude, 'lat': latitude, 'by': 'position', 'format': 'json', 'key': '02SRH5M6VFLC'}
            response = requests.get(url='http://api.timezonedb.com/v2/get-time-zone', params=payload)
            json_response = response.json()

            if json_response and ('status' in json_response.keys()) and (json_response['status'] == 'OK'):
                return json_response['zoneName']

            raise Exception
        except Exception as e:
            print('Error requesting timezone identification: %s' % (str(e)))

    raise TimezoneRequestError


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
            btn_name = d.strftime(WEEKDAY) if d.weekday() in (3, 6) else d.strftime(D_B)

            row.append(types.InlineKeyboardButton(btn_name, callback_data=CB_CHOOSE_DAY + '_' + d.strftime(D_M_Y)))
            count -= 1
        else:
            keyboard.append(row)
            row = []

    row.append(types.InlineKeyboardButton("Сегодня", callback_data=CB_IGNORE))
    keyboard.append(row)

    return keyboard


async def get_search_wod_kb(wod_list) -> list:
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
