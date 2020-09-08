import requests
from bs4 import BeautifulSoup

from utils.parser_util import parse_wod_content


class BSoupParser:
    def __init__(self, url):
        headers = {'User-Agent': 'Mozilla/5.0'}
        page = requests.get(url, headers=headers)

        soup = BeautifulSoup(page.text, 'html.parser')
        post = soup.find('div', class_='wod-wrap')

        header = post.find(class_='orange wod-date').find('h5').get_text()
        self.wod_date = " ".join(header.split())

        self.content = post.find(class_='container wod-info').find_all(class_='col-md-6')

    def get_wod_date(self):
        return self.wod_date

    def get_regional_wod(self):
        return parse_wod_content(self.content[1])

    def get_open_wod(self):
        return parse_wod_content(self.content[0])
