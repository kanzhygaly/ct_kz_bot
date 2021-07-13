import random

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


def get_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36", \
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.72 Safari/537.36", \
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10) AppleWebKit/600.1.25 (KHTML, like Gecko) Version/8.0 Safari/600.1.25", \
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:33.0) Gecko/20100101 Firefox/33.0", \
        "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36", \
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36", \
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/600.1.17 (KHTML, like Gecko) Version/7.1 Safari/537.85.10", \
        "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko", \
        "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:33.0) Gecko/20100101 Firefox/33.0", \
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.104 Safari/537.36" \
        ]

    return random.choice(user_agents)
