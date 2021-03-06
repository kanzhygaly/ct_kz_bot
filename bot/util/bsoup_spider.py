import requests
from bs4 import BeautifulSoup

from bot.util.parser_util import parse_wod_content


class BSoupParser:
    def __init__(self, url: str):
        headers = {'User-Agent': 'Mozilla/5.0'}
        page = requests.get(url, headers=headers)

        soup = BeautifulSoup(page.text, 'html.parser')
        post = soup.find('div', id='wod')

        header = post.find('h5').get_text()
        self.wod_date = " ".join(header.split())

        self.wod_text = parse_wod_content(post)

    def get_wod_date(self) -> str:
        return self.wod_date

    def get_wod_text(self) -> str:
        return self.wod_text
