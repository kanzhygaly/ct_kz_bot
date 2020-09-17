import datetime

import requests
from aiogram import types

from bot.constants import CB_CHOOSE_DAY
from bot.constants.date_format import D_M_Y, A_D_B
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
    keyboard = []
    row = []
    count = 9
    date = datetime.datetime.now()

    # if today is Thursday then include it
    if date.weekday() == 3:
        count = 8
        btn_name = date.strftime(A_D_B)
        row.append(types.InlineKeyboardButton(btn_name, callback_data=CB_CHOOSE_DAY + '_' + date.strftime(D_M_Y)))

    while count >= 0:
        if len(row) < 3:
            if date.weekday() <= 3:
                delta = 1 + date.weekday()
                date = date - datetime.timedelta(days=delta)
            elif date.weekday() > 3:
                delta = date.weekday() - 3
                date = date - datetime.timedelta(days=delta)

            btn_name = date.strftime(A_D_B)
            row.append(types.InlineKeyboardButton(
                btn_name, callback_data=CB_CHOOSE_DAY + '_' + date.strftime(D_M_Y)))

            count -= 1
        else:
            keyboard.append(row)
            row = []

    return keyboard
