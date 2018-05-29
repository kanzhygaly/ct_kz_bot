import requests
from bs4 import BeautifulSoup


class BSoupParser:

    def __init__(self, url):
        headers = {'User-Agent': 'Mozilla/5.0'}
        page = requests.get(url, headers=headers)

        soup = BeautifulSoup(page.text, 'html.parser')
        post = soup.find('div', class_='single-post')

        self.wod_date = post.find(class_='header-container').find('h1').get_text()

        self.content = post.find_all(class_='vc_col-sm-6')

    def get_wod_date(self):
        return self.wod_date

    def get_regional_wod(self):
        result = ''

        reg_part = self.content[0].find(class_='wpb_wrapper').find(class_='wpb_wrapper')

        for tag in reg_part.find_all(["h3", "p"]):
            if tag.name == 'h3':
                result += tag.get_text().strip() + '\n'
            else:
                result += tag.get_text().strip() + '\n\n'

        return result

    def get_open_wod(self):
        result = ''

        open_part = self.content[1].find(class_='wpb_wrapper').find(class_='wpb_wrapper')

        for tag in open_part.find_all(["h3", "p"]):
            if tag.name == 'h3':
                result += tag.get_text().strip() + '\n'
            else:
                result += tag.get_text().strip() + '\n\n'

        return result
