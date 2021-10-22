import requests
from bs4 import BeautifulSoup

from bot.util import get_user_agent
from bot.util.parser_util import parse_wod_content, parse_wod_header


class BSoupParser:
    def __init__(self, url: str):
        headers = {'User-Agent': get_user_agent()}
        try:
            page = requests.get(url, headers=headers)
            soup = BeautifulSoup(page.text, 'html.parser')
        except Exception as e:
            print(f'Error: {str(e)}')

        post = soup.find('div', id='wod')

        self.wod_date = parse_wod_header(post)
        self.wod_text = parse_wod_content(post)

    def get_wod_date(self) -> str:
        return self.wod_date

    def get_wod_text(self) -> str:
        return self.wod_text
