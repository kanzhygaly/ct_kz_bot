import requests
import datetime
from aiogram import types


CB_CHOOSE_DAY = 'choose_day'


async def get_timezone_id(latitude, longitude):
    try:
        payload = {'username': 'atareao', 'lng': longitude, 'lat': latitude}
        response = requests.get(url='http://api.geonames.org/timezoneJSON', params=payload)
        json_response = response.json()
        # print(json_response)
        if json_response and 'timezoneId' in json_response.keys():
            return json_response['timezoneId']
        raise Exception
    except Exception as e:
        print('Error requesting timezone identification: %s' % (str(e)))
        try:
            payload = {'lng': longitude, 'lat': latitude, 'by': 'position', 'format': 'json', 'key': '02SRH5M6VFLC'}
            response = requests.get(url='http://api.timezonedb.com/v2/get-time-zone', params=payload)
            json_response = response.json()
            # print(json_response)
            if json_response is not None and 'status' in json_response.keys() and json_response['status'] == 'OK':
                return json_response['zoneName']
            raise Exception
        except Exception as e:
            print('Error requesting timezone identification: %s' % (str(e)))
    return None


async def get_add_rest_wod_kb():
    keyboard = []
    row = []
    count = 9
    date = datetime.datetime.now()

    # if today is Thursday then include it
    if date.weekday() == 3:
        count = 8        
		btn_name = date.strftime("%a %d %b")
		row.append(types.InlineKeyboardButton(
			btn_name, callback_data=CB_CHOOSE_DAY + '_' + date.strftime("%d%m%y")))

    while count >= 0:
        if len(row) < 3:
            if date.weekday() <= 3:
                delta = 1 + date.weekday()
                date = date - datetime.timedelta(days=delta)
            elif date.weekday() > 3:
                delta = date.weekday() - 3
                date = date - datetime.timedelta(days=delta)

            # Thu 18 Apr
            btn_name = date.strftime("%a %d %b")
            row.append(types.InlineKeyboardButton(
                btn_name, callback_data=CB_CHOOSE_DAY + '_' + date.strftime("%d%m%y")))

            count -= 1
        else:
            keyboard.append(row)
            row = []

    return keyboard
