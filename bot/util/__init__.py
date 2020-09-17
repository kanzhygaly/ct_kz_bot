import requests

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

